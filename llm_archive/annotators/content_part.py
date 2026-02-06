# llm_archive/annotators/content_part.py
"""
Content-part level annotators.

These annotators work on individual content_parts within messages,
detecting features like code blocks, LaTeX, and other content types.
"""

import re
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from llm_archive.annotations.core import (
    AnnotationWriter,
    AnnotationReader,
    AnnotationResult,
    EntityType,
    ValueType,
)


@dataclass
class ContentPartData:
    """Data passed to content-part annotation logic."""
    content_part_id: UUID
    message_id: UUID
    dialogue_id: UUID
    sequence: int
    part_type: str
    text_content: str | None
    language: str | None
    role: str
    created_at: datetime | None


class ContentPartAnnotator:
    """
    Base class for annotating content parts.
    
    Iterates over raw.content_parts joined with raw.messages.
    Supports annotation prerequisites and skip conditions.
    """
    
    ENTITY_TYPE = EntityType.CONTENT_PART
    ANNOTATION_KEY: str = ''  # Subclass must define
    VALUE_TYPE: ValueType = ValueType.FLAG
    PRIORITY: int = 50  # Higher = runs first
    
    # Annotation filters
    REQUIRES_FLAGS: list[str] = []
    REQUIRES_STRINGS: list[tuple[str, str]] = []
    SKIP_IF_FLAGS: list[str] = []
    SKIP_IF_STRINGS: list[tuple[str, ...]] = []
    
    # Content filters
    PART_TYPE_FILTER: str | None = None  # Limit to specific part_type
    ROLE_FILTER: str | None = None  # Limit to 'user' or 'assistant'
    
    def __init__(self, session: Session):
        self.session = session
        self.writer = AnnotationWriter(session)
        self.reader = AnnotationReader(session)
    
    def compute(self) -> int:
        """Run annotation over content parts."""
        count = 0
        for data in self._iter_content_parts():
            results = self.annotate(data)
            for result in results:
                if self._write_result(data.content_part_id, result):
                    count += 1
        return count
    
    def _write_result(self, entity_id: UUID, result: AnnotationResult) -> bool:
        """Write an annotation result to the appropriate table."""
        return self.writer.write(EntityType.CONTENT_PART, entity_id, result)
    
    def _iter_content_parts(self) -> Iterator[ContentPartData]:
        """Iterate over content parts, respecting filters."""
        # Build base query
        query = """
            SELECT 
                cp.id as content_part_id,
                cp.message_id,
                m.dialogue_id,
                cp.sequence,
                cp.part_type,
                cp.text_content,
                cp.language,
                m.role,
                m.created_at
            FROM raw.content_parts cp
            JOIN raw.messages m ON m.id = cp.message_id
            WHERE m.deleted_at IS NULL
        """
        
        params = {}
        
        # Add part_type filter
        if self.PART_TYPE_FILTER:
            query += " AND cp.part_type = :part_type"
            params['part_type'] = self.PART_TYPE_FILTER
        
        # Add role filter
        if self.ROLE_FILTER:
            query += " AND m.role = :role"
            params['role'] = self.ROLE_FILTER
        
        query += " ORDER BY m.dialogue_id, m.created_at, cp.sequence"
        
        result = self.session.execute(text(query), params)
        
        for row in result:
            yield ContentPartData(
                content_part_id=row.content_part_id,
                message_id=row.message_id,
                dialogue_id=row.dialogue_id,
                sequence=row.sequence,
                part_type=row.part_type,
                text_content=row.text_content,
                language=row.language,
                role=row.role,
                created_at=row.created_at,
            )
    
    @abstractmethod
    def annotate(self, data: ContentPartData) -> list[AnnotationResult]:
        """
        Analyze content part and return annotations to create.
        
        Args:
            data: ContentPartData with content and metadata
            
        Returns:
            List of AnnotationResult objects (empty list if no match)
        """
        pass


# ============================================================
# Code Detection Annotators
# ============================================================

class CodeBlockAnnotator(ContentPartAnnotator):
    """
    Detect explicit code blocks (```) in text content parts.
    
    Highest priority code detector - explicit markdown code blocks
    are the most reliable signal.
    
    Produces:
    - has_code_block FLAG
    - code_block_count NUMERIC
    - code_languages STRING (multi-value)
    """
    
    ANNOTATION_KEY = 'has_code_block'
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 90
    PART_TYPE_FILTER = 'text'
    ROLE_FILTER = 'assistant'
    
    # Pattern to match complete code blocks: ```lang\n...content...```
    # Captures the optional language specifier
    CODE_BLOCK_PATTERN = re.compile(r'```(\w*)\n?[\s\S]*?```')
    
    def annotate(self, data: ContentPartData) -> list[AnnotationResult]:
        if not data.text_content:
            return []
        
        # Find all complete code blocks
        matches = list(self.CODE_BLOCK_PATTERN.finditer(data.text_content))
        
        if not matches:
            return []
        
        results = []
        
        # Flag annotation
        results.append(AnnotationResult(
            key='has_code_block',
            value_type=ValueType.FLAG,
            reason='markdown_code_block',
            confidence=1.0,
        ))
        
        # Count annotation
        block_count = len(matches)
        results.append(AnnotationResult(
            key='code_block_count',
            value=block_count,
            value_type=ValueType.NUMERIC,
        ))
        
        # Language annotations (multi-value)
        languages = set()
        for match in matches:
            lang = match.group(1).lower()
            if lang:  # Skip empty language specs
                languages.add(lang)
        
        for lang in languages:
            results.append(AnnotationResult(
                key='code_language',
                value=lang,
                value_type=ValueType.STRING,
                reason='code_block_language_spec',
            ))
        
        return results


class ScriptHeaderAnnotator(ContentPartAnnotator):
    """
    Detect script headers and system includes (strong code evidence).
    
    Shebangs and #include are unambiguous code markers.
    
    Produces:
    - has_script_header FLAG
    - script_type STRING
    """
    
    ANNOTATION_KEY = 'has_script_header'
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 85
    PART_TYPE_FILTER = 'text'
    
    SHEBANG_PATTERN = re.compile(r'^#!\s*/(?:usr/)?bin/(?:env\s+)?(\w+)', re.MULTILINE)
    INCLUDE_PATTERN = re.compile(r'^#include\s*[<"]', re.MULTILINE)
    PHP_PATTERN = re.compile(r'<\?php', re.IGNORECASE)
    
    def annotate(self, data: ContentPartData) -> list[AnnotationResult]:
        if not data.text_content:
            return []
        
        results = []
        
        # Check for shebang
        shebang_match = self.SHEBANG_PATTERN.search(data.text_content)
        if shebang_match:
            results.append(AnnotationResult(
                key='has_script_header',
                value_type=ValueType.FLAG,
                reason='shebang',
                confidence=1.0,
            ))
            results.append(AnnotationResult(
                key='script_type',
                value=shebang_match.group(1),
                value_type=ValueType.STRING,
                reason='shebang_interpreter',
            ))
            return results
        
        # Check for C/C++ includes
        if self.INCLUDE_PATTERN.search(data.text_content):
            results.append(AnnotationResult(
                key='has_script_header',
                value_type=ValueType.FLAG,
                reason='c_include',
                confidence=1.0,
            ))
            results.append(AnnotationResult(
                key='script_type',
                value='c',
                value_type=ValueType.STRING,
            ))
            return results
        
        # Check for PHP
        if self.PHP_PATTERN.search(data.text_content):
            results.append(AnnotationResult(
                key='has_script_header',
                value_type=ValueType.FLAG,
                reason='php_tag',
                confidence=1.0,
            ))
            results.append(AnnotationResult(
                key='script_type',
                value='php',
                value_type=ValueType.STRING,
            ))
            return results
        
        return results


# ============================================================
# Content Type Annotators
# ============================================================

class LatexContentAnnotator(ContentPartAnnotator):
    """
    Detect LaTeX/MathJax mathematical notation in content parts.
    
    Produces:
    - has_latex FLAG
    - latex_type STRING ('display', 'inline', 'commands')
    """
    
    ANNOTATION_KEY = 'has_latex'
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 70
    PART_TYPE_FILTER = 'text'
    ROLE_FILTER = 'assistant'
    
    # Display math: $$ ... $$ or \[ ... \]
    DISPLAY_MATH_PATTERN = re.compile(r'\$\$.+?\$\$|\\\[.+?\\\]', re.DOTALL)
    
    # Inline math: $ ... $ (but not $$)
    INLINE_MATH_PATTERN = re.compile(r'(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)')
    
    # LaTeX commands: \frac, \sum, \int, etc.
    LATEX_COMMANDS_PATTERN = re.compile(
        r'\\(?:frac|sum|int|prod|lim|sqrt|begin|end|alpha|beta|gamma|'
        r'delta|epsilon|theta|lambda|sigma|omega|pi|infty|partial|nabla|'
        r'mathbb|mathcal|mathbf|mathrm|text|left|right|cdot|times|div)'
    )
    
    def annotate(self, data: ContentPartData) -> list[AnnotationResult]:
        if not data.text_content:
            return []
        
        results = []
        latex_types = set()
        
        if self.DISPLAY_MATH_PATTERN.search(data.text_content):
            latex_types.add('display')
        
        if self.INLINE_MATH_PATTERN.search(data.text_content):
            latex_types.add('inline')
        
        if self.LATEX_COMMANDS_PATTERN.search(data.text_content):
            latex_types.add('commands')
        
        if not latex_types:
            return []
        
        # Main flag
        results.append(AnnotationResult(
            key='has_latex',
            value_type=ValueType.FLAG,
            confidence=0.95 if 'display' in latex_types else 0.8,
            reason='latex_notation_detected',
        ))
        
        # Type annotations
        for latex_type in latex_types:
            results.append(AnnotationResult(
                key='latex_type',
                value=latex_type,
                value_type=ValueType.STRING,
            ))
        
        return results


class WikiLinkContentAnnotator(ContentPartAnnotator):
    """
    Detect Obsidian-style [[wiki links]] in content parts.
    
    This is a content-part level version for granular detection.
    The prompt-response level WikiCandidateAnnotator aggregates this.
    
    Produces:
    - has_wiki_links FLAG
    - wiki_link_count NUMERIC
    """
    
    ANNOTATION_KEY = 'has_wiki_links'
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 75
    PART_TYPE_FILTER = 'text'
    ROLE_FILTER = 'assistant'
    
    WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')
    
    def annotate(self, data: ContentPartData) -> list[AnnotationResult]:
        if not data.text_content:
            return []
        
        matches = self.WIKI_LINK_PATTERN.findall(data.text_content)
        
        if not matches:
            return []
        
        return [
            AnnotationResult(
                key='has_wiki_links',
                value_type=ValueType.FLAG,
                confidence=1.0,
                reason='wiki_links_detected',
            ),
            AnnotationResult(
                key='wiki_link_count',
                value=len(matches),
                value_type=ValueType.NUMERIC,
            ),
        ]


# ============================================================
# Registry for running all annotators
# ============================================================

CONTENT_PART_ANNOTATORS = [
    CodeBlockAnnotator,
    ScriptHeaderAnnotator,
    LatexContentAnnotator,
    WikiLinkContentAnnotator,
]


def run_content_part_annotators(session: Session) -> dict[str, int]:
    """
    Run all content-part annotators in priority order.
    
    Returns dict mapping annotator name to annotation count.
    """
    # Sort by priority (descending)
    sorted_annotators = sorted(
        CONTENT_PART_ANNOTATORS,
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
