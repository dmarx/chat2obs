# llm_archive/annotators/prompt_response.py
"""Prompt-response level annotators.

These annotators work on prompt_response pairs, detecting features like
wiki article candidates and extracting titles.

Entity iteration and annotation filtering use ORM queries with
the annotation model registry — no raw SQL string construction.
"""

import re
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session, aliased

from llm_archive.annotations.core import AnnotationResult, EntityType, ValueType
from llm_archive.annotators.base import BaseAnnotator
from llm_archive.models.annotations import get_annotation_model
from llm_archive.models.derived import PromptResponse, PromptResponseContent


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
# Base Prompt-Response Annotator
# ============================================================

class PromptResponseAnnotator(BaseAnnotator[PromptResponseData]):
    """Base class for annotating prompt-response pairs.

    Iterates over PromptResponse joined with PromptResponseContent
    using ORM queries.

    Supports annotation prerequisites and skip conditions via ORM joins:
    - REQUIRES_FLAGS: Only process entities with ALL of these flag annotations
    - REQUIRES_STRINGS: Only process entities with ALL of these (key, value) pairs
    - SKIP_IF_FLAGS: Skip entities with ANY of these flag annotations
    - SKIP_IF_STRINGS: Skip entities with ANY of these (key,) or (key, value) pairs

    Subclass and implement ``annotate()`` to create a new prompt-response
    annotator.
    """

    ENTITY_TYPE = EntityType.PROMPT_RESPONSE

    # Filtering — override in subclass
    REQUIRES_FLAGS: list[str] = []
    REQUIRES_STRINGS: list[tuple[str, str]] = []   # (key, value) pairs
    SKIP_IF_FLAGS: list[str] = []
    SKIP_IF_STRINGS: list[tuple[str, ...]] = []    # (key,) or (key, value)

    # ------------------------------------------------------------------
    # BaseAnnotator interface
    # ------------------------------------------------------------------

    def _iter_entities_after(self, after: datetime) -> Iterator[PromptResponseData]:
        """Yield prompt-response pairs created after *after*."""
        query = (
            self.session.query(
                PromptResponse.id,
                PromptResponse.dialogue_id,
                PromptResponse.prompt_message_id,
                PromptResponse.response_message_id,
                PromptResponseContent.prompt_text,
                PromptResponseContent.response_text,
                PromptResponseContent.prompt_word_count,
                PromptResponseContent.response_word_count,
                PromptResponse.prompt_role,
                PromptResponse.response_role,
                PromptResponse.created_at,
            )
            .join(PromptResponse.content)
            .filter(PromptResponse.created_at > after)
        )

        query = self._apply_annotation_filters(query)
        query = query.order_by(PromptResponse.created_at)

        for row in query:
            yield PromptResponseData(
                prompt_response_id=row[0],
                dialogue_id=row[1],
                prompt_message_id=row[2],
                response_message_id=row[3],
                prompt_text=row[4],
                response_text=row[5],
                prompt_word_count=row[6],
                response_word_count=row[7],
                prompt_role=row[8],
                response_role=row[9],
                created_at=row[10],
            )

    def _apply_annotation_filters(self, query):
        """Apply REQUIRES and SKIP annotation filters using ORM joins."""
        flag_model = get_annotation_model(EntityType.PROMPT_RESPONSE, ValueType.FLAG)
        string_model = get_annotation_model(EntityType.PROMPT_RESPONSE, ValueType.STRING)

        # REQUIRES_FLAGS: inner join ensures entity has each flag
        for flag_key in self.REQUIRES_FLAGS:
            alias = aliased(flag_model)
            query = query.join(
                alias,
                and_(
                    alias.entity_id == PromptResponse.id,
                    alias.annotation_key == flag_key,
                ),
            )

        # REQUIRES_STRINGS: inner join on (key, value) pairs
        for key, value in self.REQUIRES_STRINGS:
            alias = aliased(string_model)
            query = query.join(
                alias,
                and_(
                    alias.entity_id == PromptResponse.id,
                    alias.annotation_key == key,
                    alias.annotation_value == value,
                ),
            )

        # SKIP_IF_FLAGS: left join + filter NULL (exclude matches)
        for flag_key in self.SKIP_IF_FLAGS:
            alias = aliased(flag_model)
            query = query.outerjoin(
                alias,
                and_(
                    alias.entity_id == PromptResponse.id,
                    alias.annotation_key == flag_key,
                ),
            ).filter(alias.id.is_(None))

        # SKIP_IF_STRINGS: left join + filter NULL
        for skip_spec in self.SKIP_IF_STRINGS:
            alias = aliased(string_model)
            conditions = [alias.entity_id == PromptResponse.id]
            conditions.append(alias.annotation_key == skip_spec[0])
            if len(skip_spec) > 1:
                conditions.append(alias.annotation_value == skip_spec[1])
            query = query.outerjoin(alias, and_(*conditions))
            query = query.filter(alias.id.is_(None))

        return query

    def _entity_id(self, data: PromptResponseData) -> UUID:
        return data.prompt_response_id

    def _created_at(self, data: PromptResponseData) -> datetime | None:
        return data.created_at

    @abstractmethod
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        """Analyze prompt-response pair and return annotations to create."""
        ...


# ============================================================
# Wiki Article Detection
# ============================================================

class WikiCandidateAnnotator(PromptResponseAnnotator):
    """Detect wiki-style article candidates.

    Looks for [[wiki links]] in assistant responses.

    Produces:
    - exchange_type STRING 'wiki_article'
    """

    ANNOTATION_KEY = "wiki_candidate"
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 60
    VERSION = "1.0"

    WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")

    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        if not data.response_text:
            return []

        wiki_links = self.WIKI_LINK_PATTERN.findall(data.response_text)
        if len(wiki_links) < 2:
            return []

        return [
            AnnotationResult(
                key=self.ANNOTATION_KEY,
                value_type=ValueType.FLAG,
                confidence=.85,
                reason=f"wiki_links={len(wiki_links)}",
            )
        ]


# ============================================================
# Naive Title Extraction
# ============================================================

class NaiveTitleAnnotator(PromptResponseAnnotator):
    """Extract potential article title from response.

    Only runs on wiki_article candidates.

    Produces:
    - proposed_title STRING
    """

    ANNOTATION_KEY = "proposed_title"
    VALUE_TYPE = ValueType.STRING
    PRIORITY = 50
    VERSION = "1.0"

    REQUIRES_FLAGS = [("wiki_candidate")]

    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        if not data.response_text:
            return []

        reason_suffix = ""
        if data.response_role == "user":
            reason_suffix = " in prompt"

        lines = data.response_text.split("\n")
        for line in lines[:5]:
            if line.startswith("#"):
                title = line.lstrip('#').strip()
                if title:
                    return [
                        AnnotationResult(
                            key=self.ANNOTATION_KEY,
                            value=title,
                            value_type=ValueType.STRING,
                            confidence=0.9,
                            reason="markdown_header"+reason_suffix,
                        )
                    ]

            if line.startswith('**') and line.endswith('**'):
                title = line.strip('*').strip()
                if title:
                    return [
                        AnnotationResult(
                            key=self.ANNOTATION_KEY,
                            value=title,
                            value_type=ValueType.STRING,
                            confidence=0.9,
                            reason="bold_header"+reason_suffix,
                        )
                    ]
                    
            
            # Bold header with trailing content: **Title** - some subtitle
            if line.startswith('**') and '**' in line[2:]:
                end_idx = line.index('**', 2)
                title = line[2:end_idx].strip()
                if title:
                    return [
                        AnnotationResult(
                            key=self.ANNOTATION_KEY,
                            value=title,
                            value_type=ValueType.STRING,
                            confidence=0.9,
                            reason="bold_header_with_suffix"+reason_suffix,
                        )
                    ]
        
        # first_line = lines[0].strip() if lines else ""
        # if 5 <= len(first_line.split()) <= 10:
        #     return [
        #         AnnotationResult(
        #             key="proposed_title",
        #             value=first_line,
        #             value_type=ValueType.STRING,
        #             confidence=0.6,
        #             reason="Used first line",
        #         )
        #     ]

        return []


# ============================================================
# Registry
# ============================================================

PROMPT_RESPONSE_ANNOTATORS: list[type[PromptResponseAnnotator]] = [
    WikiCandidateAnnotator,
    NaiveTitleAnnotator,
]
