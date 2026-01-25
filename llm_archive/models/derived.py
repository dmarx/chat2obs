# llm_archive/models/derived.py
"""SQLAlchemy models for derived.* schema tables."""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Float, ForeignKey, Text,
    ARRAY, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from llm_archive.models.raw import Base


class DialogueTree(Base):
    """Tree analysis results for a dialogue."""
    __tablename__ = "dialogue_trees"
    __table_args__ = {"schema": "derived"}
    
    dialogue_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.dialogues.id", ondelete="CASCADE"), primary_key=True)
    
    total_nodes = Column(Integer, nullable=False)
    max_depth = Column(Integer, nullable=False)
    branch_count = Column(Integer, nullable=False)
    leaf_count = Column(Integer, nullable=False)
    
    primary_leaf_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"))
    primary_path_length = Column(Integer)
    
    has_regenerations = Column(Boolean, nullable=False, default=False)
    has_edits = Column(Boolean, nullable=False, default=False)
    
    computed_at = Column(DateTime(timezone=True), server_default=func.now())


class MessagePath(Base):
    """Materialized path for a message in the tree."""
    __tablename__ = "message_paths"
    __table_args__ = {"schema": "derived"}
    
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), primary_key=True)
    dialogue_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.dialogues.id", ondelete="CASCADE"), nullable=False)
    
    ancestor_path = Column(ARRAY(PG_UUID(as_uuid=True)), nullable=False)
    depth = Column(Integer, nullable=False)
    
    is_root = Column(Boolean, nullable=False)
    is_leaf = Column(Boolean, nullable=False)
    child_count = Column(Integer, nullable=False)
    sibling_index = Column(Integer, nullable=False)
    
    is_on_primary_path = Column(Boolean, nullable=False)
    
    computed_at = Column(DateTime(timezone=True), server_default=func.now())


class LinearSequence(Base):
    """A root-to-leaf path as a linear sequence."""
    __tablename__ = "linear_sequences"
    __table_args__ = {"schema": "derived"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    dialogue_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.dialogues.id", ondelete="CASCADE"), nullable=False)
    leaf_message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"), nullable=False)
    
    sequence_length = Column(Integer, nullable=False)
    is_primary = Column(Boolean, nullable=False)
    
    branch_reason = Column(String)
    branched_at_message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"))
    branched_at_depth = Column(Integer)
    
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    sequence_messages = relationship("SequenceMessage", back_populates="sequence", cascade="all, delete-orphan")
    exchanges = relationship("Exchange", back_populates="sequence", cascade="all, delete-orphan")


class SequenceMessage(Base):
    """Message membership in a linear sequence."""
    __tablename__ = "sequence_messages"
    __table_args__ = {"schema": "derived"}
    
    sequence_id = Column(PG_UUID(as_uuid=True), ForeignKey("derived.linear_sequences.id", ondelete="CASCADE"), primary_key=True)
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"), primary_key=True)
    position = Column(Integer, nullable=False)
    
    sequence = relationship("LinearSequence", back_populates="sequence_messages")


class Exchange(Base):
    """Logical interaction unit within a sequence."""
    __tablename__ = "exchanges"
    __table_args__ = {"schema": "derived"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    sequence_id = Column(PG_UUID(as_uuid=True), ForeignKey("derived.linear_sequences.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    
    first_message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"), nullable=False)
    last_message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"), nullable=False)
    
    message_count = Column(Integer, nullable=False)
    user_message_count = Column(Integer, nullable=False)
    assistant_message_count = Column(Integer, nullable=False)
    
    is_continuation = Column(Boolean, default=False)
    continuation_of_id = Column(PG_UUID(as_uuid=True), ForeignKey("derived.exchanges.id"))
    merged_count = Column(Integer, default=1)
    
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    sequence = relationship("LinearSequence", back_populates="exchanges")
    exchange_messages = relationship("ExchangeMessage", back_populates="exchange", cascade="all, delete-orphan")
    content = relationship("ExchangeContent", back_populates="exchange", uselist=False, cascade="all, delete-orphan")


class ExchangeMessage(Base):
    """Message membership in an exchange."""
    __tablename__ = "exchange_messages"
    __table_args__ = {"schema": "derived"}
    
    exchange_id = Column(PG_UUID(as_uuid=True), ForeignKey("derived.exchanges.id", ondelete="CASCADE"), primary_key=True)
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"), primary_key=True)
    position = Column(Integer, nullable=False)
    
    exchange = relationship("Exchange", back_populates="exchange_messages")


class ExchangeContent(Base):
    """Aggregated content for an exchange."""
    __tablename__ = "exchange_content"
    __table_args__ = {"schema": "derived"}
    
    exchange_id = Column(PG_UUID(as_uuid=True), ForeignKey("derived.exchanges.id", ondelete="CASCADE"), primary_key=True)
    
    user_text = Column(Text)
    assistant_text = Column(Text)
    full_text = Column(Text)
    
    user_text_hash = Column(String)
    assistant_text_hash = Column(String)
    full_text_hash = Column(String)
    
    user_word_count = Column(Integer)
    assistant_word_count = Column(Integer)
    total_word_count = Column(Integer)
    
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    exchange = relationship("Exchange", back_populates="content")


class Label(Base):
    """Polymorphic label for any entity."""
    __tablename__ = "labels"
    __table_args__ = {"schema": "derived"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    entity_type = Column(String, nullable=False)
    entity_id = Column(PG_UUID(as_uuid=True), nullable=False)
    
    label_type = Column(String, nullable=False)
    label_value = Column(String, nullable=False)
    label_data = Column(JSONB)
    
    confidence = Column(Float)
    source = Column(String, nullable=False)
    source_version = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    superseded_at = Column(DateTime(timezone=True))
    superseded_by = Column(PG_UUID(as_uuid=True), ForeignKey("derived.labels.id"))


class ContentHash(Base):
    """Content hash for deduplication."""
    __tablename__ = "content_hashes"
    __table_args__ = {"schema": "derived"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    entity_type = Column(String, nullable=False)
    entity_id = Column(PG_UUID(as_uuid=True), nullable=False)
    hash_scope = Column(String, nullable=False)
    
    hash_sha256 = Column(String, nullable=False)
    hash_simhash = Column(String)
    
    normalization = Column(String, nullable=False, default='none')
    
    computed_at = Column(DateTime(timezone=True), server_default=func.now())