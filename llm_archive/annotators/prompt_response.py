# llm_archive/annotators/prompt_response.py
"""Prompt-response level annotators.

These annotators work on the prompt_responses table, which is built
without tree dependency. They support:
- Wiki article candidate detection
- Naive title extraction
- Prerequisite/skip annotation filtering

Uses the new typed annotation tables (derived.prompt_response_annotations_*).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from uuid import UUID

from sqlalchemy import text

from llm_archive.annotations.core import (
    AnnotationResult,
    EntityType,
    ValueType,
)
from llm_archive.annotators.base import BaseAnnotator


@dataclass
class PromptResponseData:
    """Data passed to prompt-response annotation logic."""
    prompt_response_id: UUID
    dialogue_id: UUID
    prompt_message_id: UUID
    response_message_id: UUID
    prompt_text: str | None
    response_text: str | None
    prompt_word_count: int | None
    response_word_count: int | None
    prompt_role: str
    response_role: str
    prompt_position: int
    response_position: int
    created_at: datetime | None


class PromptResponseAnnotator(BaseAnnotator):
    """
    Base class for annotating prompt-response pairs with runtime tracking.
    
    Extends BaseAnnotator to provide:
    - Cursor-based incremental processing
    - Runtime tracking (per-run and cumulative)
    - Filtering by prerequisites and skip conditions
    
    Subclasses override annotate() to implement specific detection logic.
    """
    
    ENTITY_TYPE = EntityType.PROMPT_RESPONSE
    VALUE_TYPE: ValueType = ValueType.STRING
    
    # Filtering - override in subclass if needed
    REQUIRES_FLAGS: list[str] = []
    REQUIRES_STRINGS: list[tuple[str, str]] = []
    SKIP_IF_FLAGS: list[str] = []
    SKIP_IF_STRINGS: list[tuple[str, ...]] = []
    
    def _iter_entities_after(self, high_water_mark: datetime) -> Iterator[PromptResponseData]:
        """
        Iterate over prompt-responses created after high-water mark.
        
        Applies filtering based on REQUIRES_* and SKIP_IF_* class attributes.
        """
        # Build base query
        query = """
            SELECT 
                pr.id as prompt_response_id,
                pr.dialogue_id,
                pr.prompt_message_id,
                pr.response_message_id,
                prc.prompt_text,
                prc.response_text,
                prc.prompt_word_count,
                prc.response_word_count,
                pr.prompt_role,
                pr.response_role,
                pr.prompt_position,
                pr.response_position,
                pr.created_at
            FROM derived.prompt_responses pr
            LEFT JOIN derived.prompt_response_content prc 
                ON prc.prompt_response_id = pr.id
            WHERE pr.created_at > :high_water_mark
        """
        
        params = {'high_water_mark': high_water_mark}
        
        # Add filtering conditions
        query = self._add_annotation_filters(query)
        query += " ORDER BY pr.created_at"
        
        result = self.session.execute(text(query), params)
        
        for row in result:
            # Check skip conditions for this specific row
            if self._should_skip(row.prompt_response_id):
                continue
            
            yield PromptResponseData(
                prompt_response_id=row.prompt_response_id,
                dialogue_id=row.dialogue_id,
                prompt_message_id=row.prompt_message_id,
                response_message_id=row.response_message_id,
                prompt_text=row.prompt_text,
                response_text=row.response_text,
                prompt_word_count=row.prompt_word_count,
                response_word_count=row.response_word_count,
                prompt_role=row.prompt_role,
                response_role=row.response_role,
                prompt_position=row.prompt_position,
                response_position=row.response_position,
                created_at=row.created_at,
            )
    
    def _add_annotation_filters(self, query: str) -> str:
        """Add JOIN clauses for annotation prerequisites."""
        # Add joins for REQUIRES_FLAGS
        for i, flag_key in enumerate(self.REQUIRES_FLAGS):
            query += f"""
                INNER JOIN derived.prompt_response_annotations_flag req_flag_{i}
                    ON req_flag_{i}.entity_id = pr.id
                    AND req_flag_{i}.annotation_key = '{flag_key}'
            """
        
        # Add joins for REQUIRES_STRINGS
        for i, (key, value) in enumerate(self.REQUIRES_STRINGS):
            query += f"""
                INNER JOIN derived.prompt_response_annotations_string req_str_{i}
                    ON req_str_{i}.entity_id = pr.id
                    AND req_str_{i}.annotation_key = '{key}'
                    AND req_str_{i}.annotation_value = '{value}'
            """
        
        return query
    
    def _should_skip(self, entity_id: UUID) -> bool:
        """Check if entity should be skipped based on SKIP_IF conditions."""
        # Check SKIP_IF_FLAGS
        for flag_key in self.SKIP_IF_FLAGS:
            if self.reader.has_flag(self.ENTITY_TYPE, entity_id, flag_key):
                return True
        
        # Check SKIP_IF_STRINGS
        for skip_spec in self.SKIP_IF_STRINGS:
            if len(skip_spec) == 1:
                # Skip if key exists with any value
                key = skip_spec[0]
                if self.reader.get_string(self.ENTITY_TYPE, entity_id, key):
                    return True
            elif len(skip_spec) == 2:
                # Skip if key has specific value
                key, value = skip_spec
                if self.reader.has_string(self.ENTITY_TYPE, entity_id, key, value):
                    return True
        
        return False
    
    def _write_result(self, entity_data: PromptResponseData, result: AnnotationResult) -> bool:
        """Write annotation result using AnnotationWriter."""
        return self.writer.write(
            entity_type=self.ENTITY_TYPE,
            entity_id=entity_data.prompt_response_id,
            result=result,
        )


# ============================================================
# Example annotator implementations
# ============================================================

class WikiCandidateAnnotator(PromptResponseAnnotator):
    """Detect potential Wikipedia article exchanges."""
    
    ANNOTATION_KEY = 'exchange_type'
    VALUE_TYPE = ValueType.STRING
    PRIORITY = 50
    VERSION = '1.0'
    
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        """Detect wiki article candidates."""
        if not data.response_text:
            return []
        
        # Simple heuristic: look for markdown structure
        if self._looks_like_wiki_article(data.response_text):
            return [
                AnnotationResult(
                    key=self.ANNOTATION_KEY,
                    value='wiki_article',
                    value_type=self.VALUE_TYPE,
                    confidence=0.8,
                    reason='Has markdown structure',
                )
            ]
        
        return []
    
    def _looks_like_wiki_article(self, text: str) -> bool:
        """Check if text looks like a Wikipedia article."""
        if not text:
            return False
        
        # Look for multiple headings
        heading_patterns = ['\n## ', '\n### ', '\n#### ']
        heading_count = sum(text.count(pattern) for pattern in heading_patterns)
        
        return heading_count >= 3


class NaiveTitleAnnotator(PromptResponseAnnotator):
    """Extract potential article title from wiki candidates."""
    
    ANNOTATION_KEY = 'proposed_title'
    VALUE_TYPE = ValueType.STRING
    PRIORITY = 50
    VERSION = '1.0'
    
    # Only process wiki candidates
    REQUIRES_STRINGS = [('exchange_type', 'wiki_article')]
    
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        """Extract potential title from response."""
        if not data.response_text:
            return []
        
        # Strategy: Look for markdown H1
        lines = data.response_text.split('\n')
        for line in lines[:5]:
            if line.startswith('# '):
                title = line[2:].strip()
                if title:
                    return [
                        AnnotationResult(
                            key=self.ANNOTATION_KEY,
                            value=title,
                            value_type=self.VALUE_TYPE,
                            confidence=0.9,
                            reason='Found markdown H1',
                        )
                    ]
        
        return []


# ============================================================
# Annotator Registry
# ============================================================

PROMPT_RESPONSE_ANNOTATORS = [
    WikiCandidateAnnotator,
    NaiveTitleAnnotator,
]


def run_prompt_response_annotators(session: Session) -> dict[str, int]:
    """
    Run all prompt-response annotators in priority order.
    
    Returns dict mapping annotator name to annotation count.
    """
    # Sort by priority (descending)
    sorted_annotators = sorted(
        PROMPT_RESPONSE_ANNOTATORS,
        key=lambda cls: cls.PRIORITY,
        reverse=True,
    )

    results = {}
    for annotator_cls in sorted_annotators:
        annotator = annotator_cls(session)
        count = annotator.compute()
        results[annotator_cls.__name__] = count

    session.commit()
    return results
