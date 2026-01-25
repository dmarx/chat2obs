# llm_archive/models/raw.py
"""SQLAlchemy models for raw.* schema tables."""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Text, BigInteger,
    ARRAY, func
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Source(Base):
    """Registry of dialogue sources."""
    __tablename__ = "sources"
    __table_args__ = {"schema": "raw"}
    
    id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    has_native_trees = Column(Boolean, nullable=False)
    role_vocabulary = Column(ARRAY(String), nullable=False)
    source_metadata = Column(JSONB, name="metadata")
    
    dialogues = relationship("Dialogue", back_populates="source_rel")


class Dialogue(Base):
    """Universal dialogue container."""
    __tablename__ = "dialogues"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    source = Column(String, ForeignKey("raw.sources.id"), nullable=False)
    source_id = Column(String, nullable=False)
    
    title = Column(String)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    
    source_json = Column(JSONB, nullable=False)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())
    
    source_rel = relationship("Source", back_populates="dialogues")
    messages = relationship("Message", back_populates="dialogue", cascade="all, delete-orphan")


class Message(Base):
    """Universal message with tree structure support."""
    __tablename__ = "messages"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    dialogue_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.dialogues.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String, nullable=False)
    
    parent_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id"))
    
    role = Column(String, nullable=False)
    author_id = Column(String)
    author_name = Column(String)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    
    source_json = Column(JSONB, nullable=False)
    
    dialogue = relationship("Dialogue", back_populates="messages")
    parent = relationship("Message", remote_side=[id], backref="children")
    content_parts = relationship("ContentPart", back_populates="message", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="message", cascade="all, delete-orphan")


class ContentPart(Base):
    """Content segments within a message."""
    __tablename__ = "content_parts"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    
    part_type = Column(String, nullable=False)
    text_content = Column(Text)
    
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    is_error = Column(Boolean, default=False)
    
    source_json = Column(JSONB, nullable=False)
    
    message = relationship("Message", back_populates="content_parts")
    citations = relationship("Citation", back_populates="content_part", cascade="all, delete-orphan")


class Citation(Base):
    """Citations within content parts."""
    __tablename__ = "citations"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    content_part_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.content_parts.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String)
    
    url = Column(String)
    title = Column(String)
    snippet = Column(Text)
    published_at = Column(DateTime(timezone=True))
    
    start_index = Column(Integer)
    end_index = Column(Integer)
    citation_type = Column(String)
    
    source_json = Column(JSONB)
    
    content_part = relationship("ContentPart", back_populates="citations")


class Attachment(Base):
    """File attachments on messages."""
    __tablename__ = "attachments"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    
    file_name = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    extracted_text = Column(Text)
    
    source_json = Column(JSONB)
    
    message = relationship("Message", back_populates="attachments")


# ChatGPT Extensions

class ChatGPTMessageMeta(Base):
    __tablename__ = "chatgpt_message_meta"
    __table_args__ = {"schema": "raw"}
    
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), primary_key=True)
    model_slug = Column(String)
    status = Column(String)
    end_turn = Column(Boolean)
    gizmo_id = Column(String)
    source_json = Column(JSONB, nullable=False)


class ChatGPTSearchGroup(Base):
    __tablename__ = "chatgpt_search_groups"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    group_type = Column(String)
    domain = Column(String)
    source_json = Column(JSONB, nullable=False)
    
    entries = relationship("ChatGPTSearchEntry", back_populates="group", cascade="all, delete-orphan")


class ChatGPTSearchEntry(Base):
    __tablename__ = "chatgpt_search_entries"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    group_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.chatgpt_search_groups.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    url = Column(String)
    title = Column(String)
    snippet = Column(Text)
    published_at = Column(DateTime(timezone=True))
    attribution = Column(String)
    source_json = Column(JSONB, nullable=False)
    
    group = relationship("ChatGPTSearchGroup", back_populates="entries")


class ChatGPTCodeExecution(Base):
    __tablename__ = "chatgpt_code_executions"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(String)
    status = Column(String)
    code = Column(Text)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    final_output = Column(Text)
    exception_name = Column(String)
    exception_traceback = Column(Text)
    source_json = Column(JSONB, nullable=False)
    
    outputs = relationship("ChatGPTCodeOutput", back_populates="execution", cascade="all, delete-orphan")


class ChatGPTCodeOutput(Base):
    __tablename__ = "chatgpt_code_outputs"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    execution_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.chatgpt_code_executions.id", ondelete="CASCADE"), nullable=False)
    sequence = Column(Integer, nullable=False)
    output_type = Column(String)
    stream_name = Column(String)
    text_content = Column(Text)
    image_url = Column(String)
    source_json = Column(JSONB, nullable=False)
    
    execution = relationship("ChatGPTCodeExecution", back_populates="outputs")


class ChatGPTDalleGeneration(Base):
    __tablename__ = "chatgpt_dalle_generations"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    content_part_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.content_parts.id", ondelete="CASCADE"), nullable=False)
    gen_id = Column(String)
    prompt = Column(Text)
    seed = Column(BigInteger)
    parent_gen_id = Column(String)
    edit_op = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    source_json = Column(JSONB, nullable=False)


class ChatGPTCanvasDoc(Base):
    __tablename__ = "chatgpt_canvas_docs"
    __table_args__ = {"schema": "raw"}
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), nullable=False)
    textdoc_id = Column(String)
    textdoc_type = Column(String)
    version = Column(Integer)
    title = Column(String)
    from_version = Column(Integer)
    content_length = Column(Integer)
    has_user_edit = Column(Boolean)
    source_json = Column(JSONB, nullable=False)


# Claude Extensions

class ClaudeMessageMeta(Base):
    __tablename__ = "claude_message_meta"
    __table_args__ = {"schema": "raw"}
    
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("raw.messages.id", ondelete="CASCADE"), primary_key=True)
    source_json = Column(JSONB, nullable=False)