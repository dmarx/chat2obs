# conversation_tagger/db/models.py
"""
Database models for conversation storage with incremental update support.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class ConversationDB:
    """Database model for conversations."""
    
    # Primary fields
    conversation_id: str  # Primary key
    source: str          # 'oai', 'claude', etc.
    title: str
    
    # Metadata for incremental processing
    first_message_time: float
    last_message_time: float
    last_updated: datetime
    processed_at: Optional[datetime] = None
    
    # Content
    exchange_count: int = 0
    total_message_count: int = 0
    total_user_messages: int = 0
    total_assistant_messages: int = 0
    
    # Store raw data for reprocessing if needed
    raw_data: Optional[str] = None  # JSON string
    
    # Annotations (stored as JSON)
    annotations: Optional[str] = None  # JSON string
    
    def set_raw_data(self, data: Dict[str, Any]) -> None:
        """Set raw conversation data as JSON string."""
        self.raw_data = json.dumps(data) if data else None
    
    def get_raw_data(self) -> Optional[Dict[str, Any]]:
        """Get raw conversation data from JSON string."""
        return json.loads(self.raw_data) if self.raw_data else None
    
    def set_annotations(self, annotations: Dict[str, Any]) -> None:
        """Set annotations as JSON string."""
        self.annotations = json.dumps(annotations) if annotations else None
    
    def get_annotations(self) -> Dict[str, Any]:
        """Get annotations from JSON string."""
        return json.loads(self.annotations) if self.annotations else {}

@dataclass 
class ExchangeDB:
    """Database model for exchanges."""
    
    # Primary fields
    exchange_id: str         # Primary key
    conversation_id: str     # Foreign key
    
    # Ordering and timing
    sequence_number: int     # Order within conversation
    first_message_time: float
    last_message_time: float
    
    # Content metadata
    message_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    has_continuations: bool = False
    
    # Annotations (stored as JSON)
    annotations: Optional[str] = None
    
    def set_annotations(self, annotations: Dict[str, Any]) -> None:
        """Set annotations as JSON string."""
        self.annotations = json.dumps(annotations) if annotations else None
    
    def get_annotations(self) -> Dict[str, Any]:
        """Get annotations from JSON string."""
        return json.loads(self.annotations) if self.annotations else {}

@dataclass
class MessageDB:
    """Database model for messages."""
    
    # Primary fields  
    message_id: str          # Primary key
    exchange_id: str         # Foreign key
    conversation_id: str     # For efficient querying
    
    # Content
    author_role: str         # 'user', 'assistant'
    content: str             # Message text content
    created_date: float      # Timestamp
    
    # Ordering
    sequence_number: int     # Order within exchange
    
    # Raw data for complex message types
    raw_data: Optional[str] = None  # JSON string for metadata, attachments, etc.
    
    def set_raw_data(self, data: Dict[str, Any]) -> None:
        """Set raw message data as JSON string."""
        self.raw_data = json.dumps(data) if data else None
    
    def get_raw_data(self) -> Optional[Dict[str, Any]]:
        """Get raw message data from JSON string."""
        return json.loads(self.raw_data) if self.raw_data else None

@dataclass
class AnnotationDB:
    """Database model for searchable annotations (denormalized for performance)."""
    
    # Primary fields
    id: Optional[int] = None           # Auto-increment primary key
    conversation_id: str = ""          # Foreign key
    exchange_id: Optional[str] = None  # Optional foreign key (conversation-level if None)
    
    # Annotation data
    annotation_name: str = ""          # e.g., 'gizmo', 'conversation_length'
    annotation_value: Optional[str] = None  # JSON string for complex values
    annotation_type: str = "boolean"   # 'boolean', 'string', 'number', 'object'
    
    # For efficient querying of structured data
    string_value: Optional[str] = None
    number_value: Optional[float] = None
    boolean_value: Optional[bool] = None
    
    def set_value(self, value: Any) -> None:
        """Set annotation value with proper typing."""
        if isinstance(value, bool):
            self.annotation_type = "boolean"
            self.boolean_value = value
            self.annotation_value = json.dumps(value)
        elif isinstance(value, (int, float)):
            self.annotation_type = "number" 
            self.number_value = float(value)
            self.annotation_value = json.dumps(value)
        elif isinstance(value, str):
            self.annotation_type = "string"
            self.string_value = value
            self.annotation_value = json.dumps(value)
        else:
            self.annotation_type = "object"
            self.annotation_value = json.dumps(value)
    
    def get_value(self) -> Any:
        """Get typed annotation value."""
        if self.annotation_value:
            return json.loads(self.annotation_value)
        return None

# SQL schema for reference
SQL_SCHEMA = """
-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    first_message_time REAL NOT NULL,
    last_message_time REAL NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    exchange_count INTEGER DEFAULT 0,
    total_message_count INTEGER DEFAULT 0,
    total_user_messages INTEGER DEFAULT 0,
    total_assistant_messages INTEGER DEFAULT 0,
    raw_data TEXT,
    annotations TEXT
);

-- Exchanges table
CREATE TABLE IF NOT EXISTS exchanges (
    exchange_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    first_message_time REAL NOT NULL,
    last_message_time REAL NOT NULL,
    message_count INTEGER DEFAULT 0,
    user_message_count INTEGER DEFAULT 0,
    assistant_message_count INTEGER DEFAULT 0,
    has_continuations BOOLEAN DEFAULT FALSE,
    annotations TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id) ON DELETE CASCADE
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    exchange_id TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    author_role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_date REAL NOT NULL,
    sequence_number INTEGER NOT NULL,
    raw_data TEXT,
    FOREIGN KEY (exchange_id) REFERENCES exchanges (exchange_id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id) ON DELETE CASCADE
);

-- Annotations table (denormalized for efficient querying)
CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    exchange_id TEXT,
    annotation_name TEXT NOT NULL,
    annotation_value TEXT,
    annotation_type TEXT DEFAULT 'boolean',
    string_value TEXT,
    number_value REAL,
    boolean_value BOOLEAN,
    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id) ON DELETE CASCADE,
    FOREIGN KEY (exchange_id) REFERENCES exchanges (exchange_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_source ON conversations (source);
CREATE INDEX IF NOT EXISTS idx_conversations_last_updated ON conversations (last_updated);
CREATE INDEX IF NOT EXISTS idx_conversations_processed_at ON conversations (processed_at);

CREATE INDEX IF NOT EXISTS idx_exchanges_conversation ON exchanges (conversation_id);
CREATE INDEX IF NOT EXISTS idx_exchanges_sequence ON exchanges (conversation_id, sequence_number);

CREATE INDEX IF NOT EXISTS idx_messages_exchange ON messages (exchange_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_date ON messages (created_date);

CREATE INDEX IF NOT EXISTS idx_annotations_conversation ON annotations (conversation_id);
CREATE INDEX IF NOT EXISTS idx_annotations_name ON annotations (annotation_name);
CREATE INDEX IF NOT EXISTS idx_annotations_type_value ON annotations (annotation_type, string_value);
CREATE INDEX IF NOT EXISTS idx_annotations_number ON annotations (annotation_name, number_value);
CREATE INDEX IF NOT EXISTS idx_annotations_boolean ON annotations (annotation_name, boolean_value);
"""
