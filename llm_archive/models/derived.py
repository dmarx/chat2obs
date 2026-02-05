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
    
    content = relationship("PromptResponseContent", back_populates="prompt_response", uselist=False, cascade="all, delete-orphan")


