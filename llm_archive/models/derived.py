# llm_archive/models/derived.py
"""SQLAlchemy models for derived.* schema tables."""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Float, ForeignKey, Text,
    ARRAY, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
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
    
    Content is accessed via the prompt_response_content_v view,
    which aggregates text from raw.content_parts and word_count
    from annotations.
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


# ----------------------------------------------------------------------
# Annotator Cursors
# ----------------------------------------------------------------------

class AnnotatorCursor(Base):
    """
    Tracks processing state for each annotator version.
    Allows incremental annotation without re-processing old entities.
    
    cumulative_runtime_seconds tracks total time spent by this annotator
    across all runs, useful for identifying performance bottlenecks.
    """
    __tablename__ = "annotator_cursors"
    __table_args__ = {"schema": "derived"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    annotator_name = Column(String, nullable=False)
    annotator_version = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    
    # High water mark: last entity created_at timestamp processed
    high_water_mark = Column(DateTime(timezone=True), nullable=False)
    
    # Stats
    entities_processed = Column(Integer, nullable=False, default=0)
    annotations_created = Column(Integer, nullable=False, default=0)
    cumulative_runtime_seconds = Column(Float, nullable=False, default=0.0)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
