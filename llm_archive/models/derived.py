# llm_archive/models/derived.py
"""SQLAlchemy models for derived.* schema tables."""

from sqlalchemy import (
    Column, String, Integer, DateTime, Float, ForeignKey, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from llm_archive.models.raw import Base


# ----------------------------------------------------------------------
# Prompt-Response Pairs (unique by response)
# ----------------------------------------------------------------------

class PromptResponse(Base):
    """
    Direct prompt-response association without tree dependency.

    Each record pairs a user prompt with one of its responses.
    A prompt can have multiple responses (regenerations).
    Each response appears in exactly one record.
    """
    __tablename__ = "prompt_responses"
    __table_args__ = {"schema": "derived"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    dialogue_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.dialogues.id", ondelete="CASCADE"), nullable=False)

    prompt_message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"), nullable=False)
    response_message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"), nullable=False)

    prompt_position = Column(Integer, nullable=False)
    response_position = Column(Integer, nullable=False)

    prompt_role = Column(String, nullable=False)
    response_role = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    dialogue = relationship("Dialogue", back_populates="prompt_responses")
    prompt_message = relationship("Message", foreign_keys=[prompt_message_id])
    response_message = relationship("Message", foreign_keys=[response_message_id])
    content = relationship(
        "PromptResponseContent",
        uselist=False,
        back_populates="prompt_response",
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------
    # Computed text properties (aggregate from content_parts via message)
    # These provide a normalized access path without requiring the
    # denormalized prompt_response_content table.
    # ------------------------------------------------------------------

    @property
    def prompt_text(self) -> str | None:
        """Aggregate text content from prompt message content_parts."""
        if not self.prompt_message or not self.prompt_message.content_parts:
            return None
        text_parts = [
            cp.text_content
            for cp in sorted(self.prompt_message.content_parts, key=lambda c: c.sequence)
            if cp.text_content and cp.part_type == 'text'
        ]
        return '\n'.join(text_parts) if text_parts else None

    @property
    def response_text(self) -> str | None:
        """Aggregate text content from response message content_parts."""
        if not self.response_message or not self.response_message.content_parts:
            return None
        text_parts = [
            cp.text_content
            for cp in sorted(self.response_message.content_parts, key=lambda c: c.sequence)
            if cp.text_content and cp.part_type == 'text'
        ]
        return '\n'.join(text_parts) if text_parts else None

    @property
    def prompt_word_count(self) -> int:
        text = self.prompt_text
        return len(text.split()) if text else 0

    @property
    def response_word_count(self) -> int:
        text = self.response_text
        return len(text.split()) if text else 0


# ----------------------------------------------------------------------
# Prompt-Response Content (denormalized text — legacy / optional)
# ----------------------------------------------------------------------

class PromptResponseContent(Base):
    """
    Denormalized text content for annotation/search without joins.

    NOTE: This table is maintained for backward compatibility with views.
    Prefer PromptResponse.prompt_text / .response_text properties which
    derive content from the source-of-truth content_parts table.
    """
    __tablename__ = "prompt_response_content"
    __table_args__ = {"schema": "derived"}

    prompt_response_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("derived.prompt_responses.id", ondelete="CASCADE"),
        primary_key=True,
    )

    prompt_text = Column(Text)
    response_text = Column(Text)

    prompt_word_count = Column(Integer)
    response_word_count = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    prompt_response = relationship("PromptResponse", back_populates="content")


# ----------------------------------------------------------------------
# Annotator Cursors — incremental processing state
# ----------------------------------------------------------------------

class AnnotatorCursor(Base):
    """
    Tracks processing state for an annotator version.

    Each (annotator_name, annotator_version, entity_type) triple gets its
    own cursor.  Bumping VERSION in annotator code creates a fresh cursor,
    triggering full reprocessing.
    """
    __tablename__ = "annotator_cursors"
    __table_args__ = {"schema": "derived"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    annotator_name = Column(String, nullable=False)
    annotator_version = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)

    high_water_mark = Column(DateTime(timezone=True), nullable=False)

    entities_processed = Column(Integer, nullable=False, default=0)
    annotations_created = Column(Integer, nullable=False, default=0)
    cumulative_runtime_seconds = Column(Float, nullable=False, default=0.0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return (
            f"<AnnotatorCursor {self.annotator_name} v{self.annotator_version} "
            f"[{self.entity_type}] hwm={self.high_water_mark} "
            f"processed={self.entities_processed} created={self.annotations_created} "
            f"runtime={self.cumulative_runtime_seconds:.1f}s>"
        )
