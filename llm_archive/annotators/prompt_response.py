# llm_archive/annotators/prompt_response.py
"""Prompt-response level annotators.

These annotators work on the prompt_responses table, which is built
without tree dependency. They support:
- Wiki article candidate detection
- Naive title extraction
- Prerequisite/skip annotation filtering

Uses the new typed annotation tables (derived.prompt_response_annotations_*).
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from llm_archive.annotations.core import (
    AnnotationWriter, AnnotationReader, AnnotationResult,
    EntityType, ValueType,
)


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

class PromptResponseAnnotator:
    """
    Base class for annotating prompt-response pairs.
    
    Iterates over derived.prompt_response_content_v (view that joins
    content from raw.content_parts - no denormalized storage).
    
    Supports annotation prerequisites and skip conditions using the
    new typed annotation tables:
    - REQUIRES_FLAGS: Only process entities with ALL of these flag annotations
    - REQUIRES_STRINGS: Only process entities with ALL of these (key, value) string annotations
    - SKIP_IF_FLAGS: Skip entities with ANY of these flag annotations
    - SKIP_IF_STRINGS: Skip entities with ANY of these (key,) or (key, value) string annotations
    
    Example:
        REQUIRES_STRINGS = [('exchange_type', 'wiki_article')]
        SKIP_IF_FLAGS = ['has_preamble']
    """
    
    ENTITY_TYPE = EntityType.PROMPT_RESPONSE
    
    # Annotator metadata
    ANNOTATION_KEY: str = None  # Required: the key this annotator produces
    VALUE_TYPE: ValueType = ValueType.STRING  # What type of annotation this produces
    PRIORITY: int = 50  # Higher runs first
    VERSION: str = '1.0'
    SOURCE: str = 'heuristic'
    
    # Filtering - override in subclass
    REQUIRES_FLAGS: list[str] = []
    REQUIRES_STRINGS: list[tuple[str, str]] = []  # (key, value) pairs
    SKIP_IF_FLAGS: list[str] = []
    SKIP_IF_STRINGS: list[tuple[str, ...]] = []  # (key,) or (key, value)
    
    def __init__(self, session: Session):
        self.session = session
        self.writer = AnnotationWriter(session)
        self.reader = AnnotationReader(session)
    
    def compute(self) -> int:
        """Run annotation over prompt-response pairs."""
        count = 0
        
        for data in self._iter_prompt_responses():
            results = self.annotate(data)
            for result in results:
                if self._write_result(data.prompt_response_id, result):
                    count += 1
        
        return count
    
    def _write_result(self, entity_id: UUID, result: AnnotationResult) -> bool:
        """Write an annotation result to the appropriate table."""
        # Use the result's value_type if specified, otherwise use class default
        value_type = result.value_type if result.value_type else self.VALUE_TYPE
        
        if value_type == ValueType.FLAG:
            return self.writer.write_flag(
                entity_type=self.ENTITY_TYPE,
                entity_id=entity_id,
                key=result.key,
                confidence=result.confidence,
                reason=result.reason,
                source=result.source or self.SOURCE,
                source_version=result.source_version or self.VERSION,
            )
        elif value_type == ValueType.STRING:
            return self.writer.write_string(
                entity_type=self.ENTITY_TYPE,
                entity_id=entity_id,
                key=result.key,
                value=str(result.value),
                confidence=result.confidence,
                reason=result.reason,
                source=result.source or self.SOURCE,
                source_version=result.source_version or self.VERSION,
            )
        elif value_type == ValueType.NUMERIC:
            return self.writer.write_numeric(
                entity_type=self.ENTITY_TYPE,
                entity_id=entity_id,
                key=result.key,
                value=float(result.value),
                confidence=result.confidence,
                reason=result.reason,
                source=result.source or self.SOURCE,
                source_version=result.source_version or self.VERSION,
            )
        elif value_type == ValueType.JSON:
            return self.writer.write_json(
                entity_type=self.ENTITY_TYPE,
                entity_id=entity_id,
                key=result.key,
                value=result.value,
                confidence=result.confidence,
                reason=result.reason,
                source=result.source or self.SOURCE,
                source_version=result.source_version or self.VERSION,
            )
        return False
    
    def _iter_prompt_responses(self) -> Iterator[PromptResponseData]:
        """Iterate over prompt-responses with content, respecting annotation filters."""
        # Base query uses the content view
        query_parts = ["""
            SELECT 
                prc.prompt_response_id,
                prc.dialogue_id,
                prc.prompt_message_id,
                prc.response_message_id,
                prc.prompt_text,
                prc.response_text,
                prc.prompt_word_count,
                prc.response_word_count,
                prc.prompt_role,
                prc.response_role,
                prc.created_at
            FROM derived.prompt_response_content_v prc
        """]
        
        params = {}
        join_idx = 0
        
        # Add REQUIRES_FLAGS joins (must have these flags)
        for flag_key in self.REQUIRES_FLAGS:
            alias = f"req_flag_{join_idx}"
            query_parts.append(f"""
                JOIN derived.prompt_response_annotations_flag {alias} ON 
                    {alias}.entity_id = prc.prompt_response_id
                    AND {alias}.annotation_key = :req_flag_key_{join_idx}
            """)
            params[f'req_flag_key_{join_idx}'] = flag_key
            join_idx += 1
        
        # Add REQUIRES_STRINGS joins (must have these key+value pairs)
        for key, value in self.REQUIRES_STRINGS:
            alias = f"req_str_{join_idx}"
            query_parts.append(f"""
                JOIN derived.prompt_response_annotations_string {alias} ON 
                    {alias}.entity_id = prc.prompt_response_id
                    AND {alias}.annotation_key = :req_str_key_{join_idx}
                    AND {alias}.annotation_value = :req_str_val_{join_idx}
            """)
            params[f'req_str_key_{join_idx}'] = key
            params[f'req_str_val_{join_idx}'] = value
            join_idx += 1
        
        # Add SKIP_IF_FLAGS exclusions
        skip_where_clauses = []
        for flag_key in self.SKIP_IF_FLAGS:
            alias = f"skip_flag_{join_idx}"
            query_parts.append(f"""
                LEFT JOIN derived.prompt_response_annotations_flag {alias} ON 
                    {alias}.entity_id = prc.prompt_response_id
                    AND {alias}.annotation_key = :skip_flag_key_{join_idx}
            """)
            params[f'skip_flag_key_{join_idx}'] = flag_key
            skip_where_clauses.append(f"{alias}.id IS NULL")
            join_idx += 1
        
        # Add SKIP_IF_STRINGS exclusions
        for skip_spec in self.SKIP_IF_STRINGS:
            alias = f"skip_str_{join_idx}"
            if len(skip_spec) == 1:
                # Skip if key exists (any value)
                query_parts.append(f"""
                    LEFT JOIN derived.prompt_response_annotations_string {alias} ON 
                        {alias}.entity_id = prc.prompt_response_id
                        AND {alias}.annotation_key = :skip_str_key_{join_idx}
                """)
                params[f'skip_str_key_{join_idx}'] = skip_spec[0]
            else:
                # Skip if key+value match
                query_parts.append(f"""
                    LEFT JOIN derived.prompt_response_annotations_string {alias} ON 
                        {alias}.entity_id = prc.prompt_response_id
                        AND {alias}.annotation_key = :skip_str_key_{join_idx}
                        AND {alias}.annotation_value = :skip_str_val_{join_idx}
                """)
                params[f'skip_str_key_{join_idx}'] = skip_spec[0]
                params[f'skip_str_val_{join_idx}'] = skip_spec[1]
            skip_where_clauses.append(f"{alias}.id IS NULL")
            join_idx += 1
        
        # WHERE clause for exclusions
        if skip_where_clauses:
            query_parts.append("WHERE " + " AND ".join(skip_where_clauses))
        
        query_parts.append("ORDER BY prc.created_at")
        
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
    
    Produces a STRING annotation: exchange_type = 'wiki_article'
    """
    
    ANNOTATION_KEY = 'exchange_type'
    VALUE_TYPE = ValueType.STRING
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
            
            results = [
                # String annotation for exchange type
                AnnotationResult(
                    key='exchange_type',
                    value='wiki_article',
                    value_type=ValueType.STRING,
                    confidence=confidence,
                    reason='wiki_links_detected',
                ),
                # Numeric annotation for link count
                AnnotationResult(
                    key='wiki_link_count',
                    value=wiki_link_count,
                    value_type=ValueType.NUMERIC,
                    confidence=1.0,
                    reason='counted',
                ),
            ]
            return results
        
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
    
    Produces a STRING annotation: proposed_title = '<extracted title>'
    """
    
    ANNOTATION_KEY = 'proposed_title'
    VALUE_TYPE = ValueType.STRING
    PRIORITY = 50
    VERSION = '1.0'
    
    # Only process wiki article candidates
    REQUIRES_STRINGS = [('exchange_type', 'wiki_article')]
    
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        if data.response_role != 'assistant':
            return []
        
        response = data.response_text or ''
        title, reason = self._extract_title(response)
        
        if title:
            return [AnnotationResult(
                key='proposed_title',
                value=title,
                value_type=ValueType.STRING,
                confidence=0.8,
                reason=reason,
            )]
        
        return []
    
    def _extract_title(self, text: str) -> tuple[str | None, str | None]:
        """Extract title from first line of text. Returns (title, reason)."""
        lines = text.strip().split('\n')
        if not lines:
            return None, None
        
        first_line = lines[0].strip()
        
        # Markdown header: # Title or ## Title
        if first_line.startswith('#'):
            title = first_line.lstrip('#').strip()
            if title:
                return title, 'markdown_header'
        
        # Bold header: **Title**
        if first_line.startswith('**') and first_line.endswith('**'):
            title = first_line.strip('*').strip()
            if title:
                return title, 'bold_header'
        
        # Bold header with trailing content: **Title** - some subtitle
        if first_line.startswith('**') and '**' in first_line[2:]:
            end_idx = first_line.index('**', 2)
            title = first_line[2:end_idx].strip()
            if title:
                return title, 'bold_header_with_suffix'
        
        return None, None


# ============================================================
# Code Detection
# ============================================================

import re


class HasCodeAnnotator(PromptResponseAnnotator):
    """
    Detect if prompt-response pair involves code.
    
    Aggregates evidence from multiple sources:
    - Code blocks (```)
    - Script headers (shebang, #include)
    - Function definitions
    - Import statements
    
    Produces:
    - has_code FLAG
    - code_evidence STRING (multi-value)
    """
    
    ANNOTATION_KEY = 'has_code'
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 55
    VERSION = '1.0'
    
    SKIP_IF_FLAGS = ['has_code']  # Skip if already annotated
    
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        if data.response_role != 'assistant':
            return []
        
        if not data.response_text:
            return []
        
        results = []
        evidence_types = set()
        
        # Check for code blocks
        if '```' in data.response_text:
            evidence_types.add('code_block')
        
        # Check for script headers
        if re.search(r'^#!\s*/(?:usr/)?bin/', data.response_text, re.MULTILINE):
            evidence_types.add('shebang')
        if re.search(r'^#include\s*[<"]', data.response_text, re.MULTILINE):
            evidence_types.add('c_include')
        
        # Check for function definitions
        if re.search(r'\bdef\s+\w+\s*\(', data.response_text):
            evidence_types.add('python_function')
        if re.search(r'function\s+\w+\s*\(', data.response_text):
            evidence_types.add('js_function')
        if re.search(r'const\s+\w+\s*=\s*\([^)]*\)\s*=>', data.response_text):
            evidence_types.add('arrow_function')
        
        # Check for import statements
        if re.search(r'^(?:import|from)\s+\w+', data.response_text, re.MULTILINE):
            evidence_types.add('python_import')
        if re.search(r'^(?:const|let|var)\s+.*=\s*require\s*\(', data.response_text, re.MULTILINE):
            evidence_types.add('js_require')
        
        if not evidence_types:
            return []
        
        # Main flag with confidence based on evidence strength
        strong_evidence = {'code_block', 'shebang', 'c_include'}
        is_strong = bool(evidence_types & strong_evidence)
        
        results.append(AnnotationResult(
            key='has_code',
            value_type=ValueType.FLAG,
            confidence=0.95 if is_strong else 0.75,
            reason=','.join(sorted(evidence_types)),
        ))
        
        # Evidence type annotations (multi-value)
        for evidence in evidence_types:
            results.append(AnnotationResult(
                key='code_evidence',
                value=evidence,
                value_type=ValueType.STRING,
            ))
        
        return results


# ============================================================
# LaTeX Detection
# ============================================================

class HasLatexAnnotator(PromptResponseAnnotator):
    """
    Detect if prompt-response pair contains LaTeX/math notation.
    
    Produces:
    - has_latex FLAG
    - latex_type STRING (multi-value: 'display', 'inline', 'commands')
    """
    
    ANNOTATION_KEY = 'has_latex'
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 54
    VERSION = '1.0'
    
    SKIP_IF_FLAGS = ['has_latex']
    
    # Patterns
    DISPLAY_MATH = re.compile(r'\$\$.+?\$\$|\\\[.+?\\\]', re.DOTALL)
    INLINE_MATH = re.compile(r'(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)')
    LATEX_COMMANDS = re.compile(
        r'\\(?:frac|sum|int|prod|lim|sqrt|begin|end|alpha|beta|gamma|'
        r'delta|epsilon|theta|lambda|sigma|omega|pi|infty|partial|nabla|'
        r'mathbb|mathcal|mathbf|mathrm|text|left|right|cdot|times|div)'
    )
    
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        if data.response_role != 'assistant':
            return []
        
        if not data.response_text:
            return []
        
        results = []
        latex_types = set()
        
        if self.DISPLAY_MATH.search(data.response_text):
            latex_types.add('display')
        
        if self.INLINE_MATH.search(data.response_text):
            latex_types.add('inline')
        
        if self.LATEX_COMMANDS.search(data.response_text):
            latex_types.add('commands')
        
        if not latex_types:
            return []
        
        # Main flag
        results.append(AnnotationResult(
            key='has_latex',
            value_type=ValueType.FLAG,
            confidence=0.95 if 'display' in latex_types else 0.8,
            reason='latex_detected',
        ))
        
        # Type annotations
        for latex_type in latex_types:
            results.append(AnnotationResult(
                key='latex_type',
                value=latex_type,
                value_type=ValueType.STRING,
            ))
        
        return results


# ============================================================
# Annotator Registry
# ============================================================

PROMPT_RESPONSE_ANNOTATORS = [
    WikiCandidateAnnotator,
    NaiveTitleAnnotator,
    HasCodeAnnotator,
    HasLatexAnnotator,
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
