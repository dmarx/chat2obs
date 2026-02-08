# llm_archive/models/raw.py
"""SQLAlchemy models for raw.* schema tables."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Text, BigInteger,
    Float, ARRAY, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ============================================================
# Core Tables
# ============================================================

class Source(Base):
    """Registry of dialogue sources."""
    __tablename__ = "sources"
    __table_args__ = {"schema": "raw"}
    
    id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    has_native_trees = Column(Boolean, nullable=False)
    role_vocabulary = Column(ARRAY(String), nullable=False)
    source_metadata = Column(JSONB, name="metadata")  # 'metadata' reserved by SQLAlchemy
    
    dialogues = relationship("Dialogue", back_populates="source_rel")


class Dialogue(Base):
    """Universal dialogue container."""
    __tablename__ = "dialogues"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    source = Column(String, ForeignKey("raw.sources.id"), nullable=False)
    source_id = Column(String, nullable=False)
    
    title = Column(String)
    
    # Source timestamps (from archive)
    source_created_at = Column(DateTime(timezone=True))
    source_updated_at = Column(DateTime(timezone=True))
    
    source_json = Column(JSONB, nullable=False)
    
    # DB timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    source_rel = relationship("Source", back_populates="dialogues")
    messages = relationship("Message", back_populates="dialogue", cascade="all, delete-orphan")


class Message(Base):
    """Universal message with tree structure support."""
    __tablename__ = "messages"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    dialogue_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.dialogues.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String, nullable=False)
    
    # Tree structure
    parent_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"))
    
    # Normalized fields
    role = Column(String, nullable=False)
    author_id = Column(String)
    author_name = Column(String)
    
    # Source timestamps
    source_created_at = Column(DateTime(timezone=True))
    source_updated_at = Column(DateTime(timezone=True))
    
    # Change tracking
    content_hash = Column(String)
    deleted_at = Column(DateTime(timezone=True))
    
    source_json = Column(JSONB, nullable=False)
    
    # DB timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    dialogue = relationship("Dialogue", back_populates="messages")
    content_parts = relationship("ContentPart", back_populates="message", 
                                cascade="all, delete-orphan",
                                order_by="ContentPart.sequence")
    citations = relationship("Citation", back_populates="message",
                           cascade="all, delete-orphan",
                           order_by="Citation.sequence")
    attachments = relationship("Attachment", back_populates="message",
                             cascade="all, delete-orphan")
    
    # Tree relationships
    parent = relationship("Message", remote_side=[id], backref="children")


class ContentPart(Base):
    """Segmented content within a message.
    
    Word count is stored as an annotation in derived.content_part_annotations_numeric,
    not as a column on this table.
    """
    __tablename__ = "content_parts"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    
    part_type = Column(String, nullable=False)
    text_content = Column(Text)
    
    # Code-specific
    language = Column(String)
    
    # Media-specific
    media_type = Column(String)
    url = Column(String)
    
    # Tool use-specific
    tool_name = Column(String)
    tool_use_id = Column(String)
    tool_input = Column(JSONB)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    message = relationship("Message", back_populates="content_parts")


class Citation(Base):
    """Source citations within messages."""
    __tablename__ = "citations"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    
    citation_text = Column(Text)
    url = Column(String)
    title = Column(String)
    
    message = relationship("Message", back_populates="citations")


class Attachment(Base):
    """File attachments associated with messages."""
    __tablename__ = "attachments"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    
    filename = Column(String)
    file_size = Column(BigInteger)
    mime_type = Column(String)
    url = Column(String)
    
    message = relationship("Message", back_populates="attachments")


# ============================================================
# ChatGPT Extensions
# ============================================================

class ChatGPTMessageMeta(Base):
    """ChatGPT-specific message metadata."""
    __tablename__ = "chatgpt_message_meta"
    __table_args__ = {"schema": "raw"}
    
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), primary_key=True)
    
    weight = Column(Float)
    end_turn = Column(Boolean)
    recipient = Column(String)
    model_slug = Column(String)
    is_complete = Column(Boolean)
    finish_details = Column(JSONB)


class ChatGPTSearchGroup(Base):
    """ChatGPT web search groups."""
    __tablename__ = "chatgpt_search_groups"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    
    search_query = Column(Text)
    
    entries = relationship("ChatGPTSearchEntry", back_populates="search_group",
                         cascade="all, delete-orphan",
                         order_by="ChatGPTSearchEntry.sequence")


class ChatGPTSearchEntry(Base):
    """ChatGPT web search result entries."""
    __tablename__ = "chatgpt_search_entries"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    search_group_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.chatgpt_search_groups.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    
    title = Column(Text)
    url = Column(String)
    snippet = Column(Text)
    
    search_group = relationship("ChatGPTSearchGroup", back_populates="entries")


class ChatGPTCodeExecution(Base):
    """ChatGPT code execution."""
    __tablename__ = "chatgpt_code_executions"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    
    language = Column(String)
    code_text = Column(Text)
    
    outputs = relationship("ChatGPTCodeOutput", back_populates="execution",
                         cascade="all, delete-orphan",
                         order_by="ChatGPTCodeOutput.sequence")


class ChatGPTCodeOutput(Base):
    """ChatGPT code execution outputs."""
    __tablename__ = "chatgpt_code_outputs"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    execution_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.chatgpt_code_executions.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    
    output_type = Column(String)
    output_text = Column(Text)
    
    execution = relationship("ChatGPTCodeExecution", back_populates="outputs")


class ChatGPTDalleGeneration(Base):
    """ChatGPT DALL-E image generations."""
    __tablename__ = "chatgpt_dalle_generations"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    
    prompt = Column(Text)
    asset_pointer = Column(String)


class ChatGPTCanvasDoc(Base):
    """ChatGPT Canvas documents."""
    __tablename__ = "chatgpt_canvas_docs"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    
    document_id = Column(String)
    title = Column(String)
    content_type = Column(String)


# ============================================================
# Claude Extensions
# ============================================================

class ClaudeMessageMeta(Base):
    """Claude-specific message metadata."""
    __tablename__ = "claude_message_meta"
    __table_args__ = {"schema": "raw"}
    
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), primary_key=True)
    
    model = Column(String)
    usage_input_tokens = Column(Integer)
    usage_output_tokens = Column(Integer)
