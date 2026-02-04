# llm_archive/annotators/prompt_response.py
"""Prompt-response level annotators.

These annotators work on the prompt_responses table, which is built
without tree dependency. They support:
- Wiki article candidate detection
- Naive title extraction
- Prerequisite/skip annotation filtering
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from llm_archive.annotators.base import Annotator, AnnotationResult
from llm_archive.models import Annotation


# ============================================================
# Data Classes
# ============================================================

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
    created_at: datetime | None


# ============================================================
# Base PromptResponse Annotator
# ============================================================

class PromptResponseAnnotator(Annotator):
    """
    Base class for annotating prompt-response pairs.
    
    Supports annotation prerequisites and skip conditions:
    - REQUIRES_ANNOTATIONS: Only process entities with ALL of these annotations
    - SKIP_IF_ANNOTATIONS: Skip entities with ANY of these annotations
    
    Each entry is a tuple of (annotation_key, annotation_value) or just annotation_key.
    
    Example:
        REQUIRES_ANNOTATIONS = [('exchange_type', 'wiki_article')]
        SKIP_IF_ANNOTATIONS = [('proposed_title',)]  # Skip if any proposed_title exists
    """
    
    ENTITY_TYPE = 'prompt_response'
    
    # Override in subclass for filtering
    REQUIRES_ANNOTATIONS: list[tuple[str, ...]] = []
    SKIP_IF_ANNOTATIONS: list[tuple[str, ...]] = []
    
    def compute(self) -> int:
        """Run annotation over prompt-response pairs."""
        count = 0
        
        for data in self._iter_prompt_responses():
            self.track_entity(data.created_at)
            
            results = self.annotate(data)
            for result in results:
                if self.add_result(data.prompt_response_id, result):
                    count += 1
        
        self.finalize_cursor()
        return count
    
    def _iter_prompt_responses(self) -> Iterator[PromptResponseData]:
        """Iterate over prompt-responses with content, respecting annotation filters."""
        cursor = self.get_cursor()
        
        # Build the base query with annotation filters
        query_parts = ["""
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
                pr.created_at
            FROM derived.prompt_responses pr
            LEFT JOIN derived.prompt_response_content prc 
                ON prc.prompt_response_id = pr.id
        """]
        
        params = {}
        
        # Add REQUIRES joins
        for i, req in enumerate(self.REQUIRES_ANNOTATIONS):
            alias = f"req_{i}"
            if len(req) == 1:
                # Just key required
                query_parts.append(f"""
                    JOIN derived.annotations {alias} ON 
                        {alias}.entity_type = 'prompt_response'
                        AND {alias}.entity_id = pr.id
                        AND {alias}.annotation_key = :req_key_{i}
                        AND {alias}.superseded_at IS NULL
                """)
                params[f'req_key_{i}'] = req[0]
            else:
                # Key + value required
                query_parts.append(f"""
                    JOIN derived.annotations {alias} ON 
                        {alias}.entity_type = 'prompt_response'
                        AND {alias}.entity_id = pr.id
                        AND {alias}.annotation_key = :req_key_{i}
                        AND {alias}.annotation_value = :req_val_{i}
                        AND {alias}.superseded_at IS NULL
                """)
                params[f'req_key_{i}'] = req[0]
                params[f'req_val_{i}'] = req[1]
        
        # Add SKIP exclusions
        for i, skip in enumerate(self.SKIP_IF_ANNOTATIONS):
            alias = f"skip_{i}"
            if len(skip) == 1:
                query_parts.append(f"""
                    LEFT JOIN derived.annotations {alias} ON 
                        {alias}.entity_type = 'prompt_response'
                        AND {alias}.entity_id = pr.id
                        AND {alias}.annotation_key = :skip_key_{i}
                        AND {alias}.superseded_at IS NULL
                """)
                params[f'skip_key_{i}'] = skip[0]
            else:
                query_parts.append(f"""
                    LEFT JOIN derived.annotations {alias} ON 
                        {alias}.entity_type = 'prompt_response'
                        AND {alias}.entity_id = pr.id
                        AND {alias}.annotation_key = :skip_key_{i}
                        AND {alias}.annotation_value = :skip_val_{i}
                        AND {alias}.superseded_at IS NULL
                """)
                params[f'skip_key_{i}'] = skip[0]
                params[f'skip_val_{i}'] = skip[1]
        
        # WHERE clause
        where_clauses = []
        
        if cursor:
            where_clauses.append("pr.created_at > :cursor")
            params['cursor'] = cursor
        
        # Exclude entities that have skip annotations
        for i in range(len(self.SKIP_IF_ANNOTATIONS)):
            where_clauses.append(f"skip_{i}.id IS NULL")
        
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        
        query_parts.append("ORDER BY pr.created_at")
        
        query = text("\n".join(query_parts))
        
        for row in self.session.execute(query, params):
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
                created_at=row.created_at,
            )
    
    @abstractmethod
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        """
        Analyze prompt-response pair and return annotations to create.
        
        Args:
            data: PromptResponseData with texts and metadata
            
        Returns:
            List of AnnotationResult objects (empty list if no match)
        """
        pass


# ============================================================
# Wiki Article Detection
# ============================================================

class WikiCandidateAnnotator(PromptResponseAnnotator):
    """
    Detect wiki-style article candidates.
    
    Looks for [[wiki links]] in assistant responses, which indicate
    the response was likely formatted as a wiki article.
    """
    
    ANNOTATION_TYPE = 'tag'
    ANNOTATION_KEY = 'exchange_type'
    PRIORITY = 60
    VERSION = '1.0'
    
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        if data.response_role != 'assistant':
            return []
        
        response = data.response_text or ''
        
        # Count wiki links
        wiki_link_count = response.count('[[')
        
        if wiki_link_count >= 1:
            # High confidence if multiple links
            confidence = 0.95 if wiki_link_count >= 3 else 0.8
            return [AnnotationResult(
                value='wiki_article',
                key='exchange_type',
                confidence=confidence,
                data={'wiki_link_count': wiki_link_count},
            )]
        
        return []


# ============================================================
# Title Extraction
# ============================================================

class NaiveTitleAnnotator(PromptResponseAnnotator):
    """
    Extract title from first line of response.
    
    Looks for:
    - Markdown headers: # Title
    - Bold headers: **Title**
    
    Should run AFTER wiki candidate detection.
    Only runs on wiki_article candidates.
    """
    
    ANNOTATION_TYPE = 'metadata'
    ANNOTATION_KEY = 'proposed_title'
    PRIORITY = 50
    VERSION = '1.0'
    
    # Only process wiki article candidates
    REQUIRES_ANNOTATIONS = [('exchange_type', 'wiki_article')]
    
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        if data.response_role != 'assistant':
            return []
        
        response = data.response_text or ''
        title = self._extract_title(response)
        
        if title:
            return [AnnotationResult(
                value=title,
                key='proposed_title',
                confidence=0.8,
            )]
        
        return []
    
    def _extract_title(self, text: str) -> str | None:
        """Extract title from first line of text."""
        lines = text.strip().split('\n')
        if not lines:
            return None
        
        first_line = lines[0].strip()
        
        # Markdown header: # Title or ## Title
        if first_line.startswith('#'):
            title = first_line.lstrip('#').strip()
            if title:
                return title
        
        # Bold header: **Title**
        if first_line.startswith('**') and first_line.endswith('**'):
            title = first_line.strip('*').strip()
            if title:
                return title
        
        # Bold header with trailing content: **Title** - some subtitle
        if first_line.startswith('**') and '**' in first_line[2:]:
            end_idx = first_line.index('**', 2)
            title = first_line[2:end_idx].strip()
            if title:
                return title
        
        return None