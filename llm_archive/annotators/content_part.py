# llm_archive/annotators/content_part.py
"""Content-part level annotators.

Annotators work on individual content_parts within messages,
detecting features like code blocks, LaTeX, and wiki links.

All annotators extend ContentPartAnnotator which extends BaseAnnotator,
gaining cursor-based incremental processing automatically.

Entity iteration uses ORM queries (ContentPart + Message models).
"""

import re
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from uuid import UUID

from sqlalchemy.orm import Session

from llm_archive.annotations.core import AnnotationResult, EntityType, ValueType
from llm_archive.annotators.base import BaseAnnotator
from llm_archive.models.raw import ContentPart, Message


# ============================================================
# Data Classes
# ============================================================

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


# ============================================================
# Base Content-Part Annotator
# ============================================================

class ContentPartAnnotator(BaseAnnotator[ContentPartData]):
    """Base class for annotating content parts.

    Iterates over ContentPart joined with Message using ORM queries.
    Supports optional content filters (PART_TYPE_FILTER, ROLE_FILTER).

    Subclass and implement ``annotate()`` to create a new content-part
    annotator.  Everything else (cursor tracking, result writing,
    incremental processing) is handled automatically.
    """

    ENTITY_TYPE = EntityType.CONTENT_PART

    # Content filters — override in subclass
    PART_TYPE_FILTER: str | None = None   # e.g. 'text', 'code'
    ROLE_FILTER: str | None = None        # e.g. 'assistant', 'user'

    # ------------------------------------------------------------------
    # BaseAnnotator interface
    # ------------------------------------------------------------------

    def _iter_entities_after(self, after: datetime) -> Iterator[ContentPartData]:
        """Yield content parts whose message.created_at > *after*."""
        query = (
            self.session.query(
                ContentPart.id,
                ContentPart.message_id,
                Message.dialogue_id,
                ContentPart.sequence,
                ContentPart.part_type,
                ContentPart.text_content,
                ContentPart.language,
                Message.role,
                Message.created_at,
            )
            .join(ContentPart.message)
            .filter(Message.deleted_at.is_(None))
            .filter(Message.created_at > after)
        )

        if self.PART_TYPE_FILTER:
            query = query.filter(ContentPart.part_type == self.PART_TYPE_FILTER)

        if self.ROLE_FILTER:
            query = query.filter(Message.role == self.ROLE_FILTER)

        query = query.order_by(Message.created_at, ContentPart.sequence)

        for row in query:
            yield ContentPartData(
                content_part_id=row[0],
                message_id=row[1],
                dialogue_id=row[2],
                sequence=row[3],
                part_type=row[4],
                text_content=row[5],
                language=row[6],
                role=row[7],
                created_at=row[8],
            )

    def _entity_id(self, data: ContentPartData) -> UUID:
        return data.content_part_id

    def _created_at(self, data: ContentPartData) -> datetime | None:
        return data.created_at

    @abstractmethod
    def annotate(self, data: ContentPartData) -> list[AnnotationResult]:
        """Analyze content part and return annotations to create."""
        ...


# ============================================================
# Code Detection Annotators
# ============================================================

class CodeBlockAnnotator(ContentPartAnnotator):
    """Detect explicit code blocks (```) in text content parts.

    Produces:
    - has_code_block FLAG
    - code_block_count NUMERIC
    - code_language STRING (multi-value, one per detected language)
    """

    ANNOTATION_KEY = "has_code_block"
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 90
    PART_TYPE_FILTER = "text"
    ROLE_FILTER = "assistant"

    CODE_BLOCK_PATTERN = re.compile(r"```(\w*)\n?.*?```", re.DOTALL)

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]:
        if not data.text_content:
            return []

        matches = self.CODE_BLOCK_PATTERN.findall(data.text_content)
        if not matches:
            return []

        results: list[AnnotationResult] = [
            AnnotationResult(
                key="has_code_block",
                value_type=ValueType.FLAG,
                confidence=1.0,
            ),
            AnnotationResult(
                key="code_block_count",
                value=len(matches),
                value_type=ValueType.NUMERIC,
            ),
        ]

        languages = {lang.lower() for lang in matches if lang}
        for lang in sorted(languages):
            results.append(
                AnnotationResult(
                    key="code_language",
                    value=lang,
                    value_type=ValueType.STRING,
                    confidence=1.0,
                )
            )

        return results


# ============================================================
# Script Header Annotator
# ============================================================

class ScriptHeaderAnnotator(ContentPartAnnotator):
    """Detect script headers (shebang lines, file path comments).

    Produces:
    - has_script_header FLAG
    - script_type STRING ('shebang' | 'filepath')
    """

    ANNOTATION_KEY = "has_script_header"
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 85
    PART_TYPE_FILTER = "text"
    ROLE_FILTER = "assistant"

    SHEBANG_PATTERN = re.compile(r"^#!\s*/", re.MULTILINE)
    FILEPATH_PATTERN = re.compile(
        r"^(?:#|//|/\*)\s*(?:File|Path|Filename):\s*\S+",
        re.MULTILINE | re.IGNORECASE,
    )

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]:
        if not data.text_content:
            return []

        results: list[AnnotationResult] = []

        if self.SHEBANG_PATTERN.search(data.text_content):
            results.append(
                AnnotationResult(key="has_script_header", value_type=ValueType.FLAG, confidence=1.0)
            )
            results.append(
                AnnotationResult(key="script_type", value="shebang", value_type=ValueType.STRING)
            )

        if self.FILEPATH_PATTERN.search(data.text_content):
            if not results:
                results.append(
                    AnnotationResult(key="has_script_header", value_type=ValueType.FLAG, confidence=0.9)
                )
            results.append(
                AnnotationResult(key="script_type", value="filepath", value_type=ValueType.STRING)
            )

        return results


# ============================================================
# LaTeX Content Annotator
# ============================================================

class LatexContentAnnotator(ContentPartAnnotator):
    """Detect LaTeX content in text.

    Produces:
    - has_latex FLAG
    - latex_type STRING ('inline' | 'display' | 'commands')
    """

    ANNOTATION_KEY = "has_latex"
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 70
    PART_TYPE_FILTER = "text"

    INLINE_MATH = re.compile(r"(?<!\$)\$(?!\$)(?!\d)[^$\n]+?\$(?!\$)")
    DISPLAY_MATH = re.compile(r"\$\$[^$]+?\$\$", re.DOTALL)
    LATEX_COMMANDS = re.compile(r"\\(?:frac|sqrt|sum|int|prod|lim|begin|end)\b")

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]:
        if not data.text_content:
            return []

        detected: list[str] = []

        if self.DISPLAY_MATH.search(data.text_content):
            detected.append("display")
        if self.INLINE_MATH.search(data.text_content):
            detected.append("inline")
        if self.LATEX_COMMANDS.search(data.text_content):
            detected.append("commands")

        if not detected:
            return []

        results: list[AnnotationResult] = [
            AnnotationResult(key="has_latex", value_type=ValueType.FLAG, confidence=1.0),
        ]
        for latex_type in detected:
            results.append(
                AnnotationResult(key="latex_type", value=latex_type, value_type=ValueType.STRING)
            )
        return results


# ============================================================
# Wiki Link Annotator
# ============================================================

class WikiLinkContentAnnotator(ContentPartAnnotator):
    """Detect [[wiki links]] in content.

    Produces:
    - has_wiki_links FLAG
    - wiki_link_count NUMERIC
    """

    ANNOTATION_KEY = "has_wiki_links"
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 75
    PART_TYPE_FILTER = "text"
    ROLE_FILTER = "assistant"

    WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]:
        if not data.text_content:
            return []

        matches = self.WIKI_LINK_PATTERN.findall(data.text_content)
        if not matches:
            return []

        return [
            AnnotationResult(
                key="has_wiki_links",
                value_type=ValueType.FLAG,
                confidence=1.0,
                reason="wiki_links_detected",
            ),
            AnnotationResult(
                key="wiki_link_count",
                value=len(matches),
                value_type=ValueType.NUMERIC,
            ),
        ]


# ============================================================
# Registry
# ============================================================

CONTENT_PART_ANNOTATORS: list[type[ContentPartAnnotator]] = [
    CodeBlockAnnotator,
    ScriptHeaderAnnotator,
    LatexContentAnnotator,
    WikiLinkContentAnnotator,
]
