# conversation_tagger/db/manager.py
"""
Database manager for conversation storage with SQLite/PostgreSQL support.
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pathlib import Path

from .models import ConversationDB, ExchangeDB, MessageDB, AnnotationDB, SQL_SCHEMA


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_path: Union[str, Path] = "conversations.db"):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file, or PostgreSQL connection string
        """
        self.db_path = str(db_path)
        self.connection = None
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Enable column access by name
        
        # Execute schema
        self.connection.executescript(SQL_SCHEMA)
        self.connection.commit()
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # Conversation operations
    def upsert_conversation(self, conv: ConversationDB) -> None:
        """Insert or update conversation."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO conversations (
                conversation_id, source, title, first_message_time, last_message_time,
                last_updated, processed_at, exchange_count, total_message_count,
                total_user_messages, total_assistant_messages, raw_data, annotations
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conv.conversation_id, conv.source, conv.title, conv.first_message_time,
            conv.last_message_time, conv.last_updated, conv.processed_at,
            conv.exchange_count, conv.total_message_count, conv.total_user_messages,
            conv.total_assistant_messages, conv.raw_data, conv.annotations
        ))
        self.connection.commit()
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationDB]:
        """Get conversation by ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM conversations WHERE conversation_id = ?", (conversation_id,))
        row = cursor.fetchone()
        
        if row:
            return ConversationDB(
                conversation_id=row['conversation_id'],
                source=row['source'],
                title=row['title'],
                first_message_time=row['first_message_time'],
                last_message_time=row['last_message_time'],
                last_updated=row['last_updated'],
                processed_at=row['processed_at'],
                exchange_count=row['exchange_count'],
                total_message_count=row['total_message_count'],
                total_user_messages=row['total_user_messages'],
                total_assistant_messages=row['total_assistant_messages'],
                raw_data=row['raw_data'],
                annotations=row['annotations']
            )
        return None
    
    def get_conversations_by_source(self, source: str) -> List[ConversationDB]:
        """Get all conversations from a specific source."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM conversations WHERE source = ? ORDER BY last_message_time DESC", (source,))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append(ConversationDB(
                conversation_id=row['conversation_id'],
                source=row['source'],
                title=row['title'],
                first_message_time=row['first_message_time'],
                last_message_time=row['last_message_time'],
                last_updated=row['last_updated'],
                processed_at=row['processed_at'],
                exchange_count=row['exchange_count'],
                total_message_count=row['total_message_count'],
                total_user_messages=row['total_user_messages'],
                total_assistant_messages=row['total_assistant_messages'],
                raw_data=row['raw_data'],
                annotations=row['annotations']
            ))
        return conversations
    
    def get_unprocessed_conversations(self, source: Optional[str] = None) -> List[ConversationDB]:
        """Get conversations that haven't been processed yet."""
        cursor = self.connection.cursor()
        
        if source:
            cursor.execute("""
                SELECT * FROM conversations 
                WHERE source = ? AND processed_at IS NULL 
                ORDER BY last_message_time DESC
            """, (source,))
        else:
            cursor.execute("""
                SELECT * FROM conversations 
                WHERE processed_at IS NULL 
                ORDER BY last_message_time DESC
            """)
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append(ConversationDB(
                conversation_id=row['conversation_id'],
                source=row['source'],
                title=row['title'],
                first_message_time=row['first_message_time'],
                last_message_time=row['last_message_time'],
                last_updated=row['last_updated'],
                processed_at=row['processed_at'],
                exchange_count=row['exchange_count'],
                total_message_count=row['total_message_count'],
                total_user_messages=row['total_user_messages'],
                total_assistant_messages=row['total_assistant_messages'],
                raw_data=row['raw_data'],
                annotations=row['annotations']
            ))
        return conversations
    
    # Exchange operations
    def upsert_exchange(self, exchange: ExchangeDB) -> None:
        """Insert or update exchange."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO exchanges (
                exchange_id, conversation_id, sequence_number, first_message_time,
                last_message_time, message_count, user_message_count,
                assistant_message_count, has_continuations, annotations
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            exchange.exchange_id, exchange.conversation_id, exchange.sequence_number,
            exchange.first_message_time, exchange.last_message_time, exchange.message_count,
            exchange.user_message_count, exchange.assistant_message_count,
            exchange.has_continuations, exchange.annotations
        ))
        self.connection.commit()
    
    def get_exchanges_for_conversation(self, conversation_id: str) -> List[ExchangeDB]:
        """Get all exchanges for a conversation."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM exchanges 
            WHERE conversation_id = ? 
            ORDER BY sequence_number
        """, (conversation_id,))
        
        exchanges = []
        for row in cursor.fetchall():
            exchanges.append(ExchangeDB(
                exchange_id=row['exchange_id'],
                conversation_id=row['conversation_id'],
                sequence_number=row['sequence_number'],
                first_message_time=row['first_message_time'],
                last_message_time=row['last_message_time'],
                message_count=row['message_count'],
                user_message_count=row['user_message_count'],
                assistant_message_count=row['assistant_message_count'],
                has_continuations=row['has_continuations'],
                annotations=row['annotations']
            ))
        return exchanges
    
    # Message operations
    def upsert_message(self, message: MessageDB) -> None:
        """Insert or update message."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO messages (
                message_id, exchange_id, conversation_id, author_role,
                content, created_date, sequence_number, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message.message_id, message.exchange_id, message.conversation_id,
            message.author_role, message.content, message.created_date,
            message.sequence_number, message.raw_data
        ))
        self.connection.commit()
    
    def get_messages_for_exchange(self, exchange_id: str) -> List[MessageDB]:
        """Get all messages for an exchange."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM messages 
            WHERE exchange_id = ? 
            ORDER BY sequence_number
        """, (exchange_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append(MessageDB(
                message_id=row['message_id'],
                exchange_id=row['exchange_id'],
                conversation_id=row['conversation_id'],
                author_role=row['author_role'],
                content=row['content'],
                created_date=row['created_date'],
                sequence_number=row['sequence_number'],
                raw_data=row['raw_data']
            ))
        return messages
    
    # Annotation operations
    def upsert_annotation(self, annotation: AnnotationDB) -> None:
        """Insert or update annotation."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO annotations (
                conversation_id, exchange_id, annotation_name, annotation_value,
                annotation_type, string_value, number_value, boolean_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            annotation.conversation_id, annotation.exchange_id, annotation.annotation_name,
            annotation.annotation_value, annotation.annotation_type, annotation.string_value,
            annotation.number_value, annotation.boolean_value
        ))
        self.connection.commit()
    
    def get_annotations_for_conversation(self, conversation_id: str) -> List[AnnotationDB]:
        """Get all annotations for a conversation."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM annotations 
            WHERE conversation_id = ?
        """, (conversation_id,))
        
        annotations = []
        for row in cursor.fetchall():
            annotations.append(AnnotationDB(
                id=row['id'],
                conversation_id=row['conversation_id'],
                exchange_id=row['exchange_id'],
                annotation_name=row['annotation_name'],
                annotation_value=row['annotation_value'],
                annotation_type=row['annotation_type'],
                string_value=row['string_value'],
                number_value=row['number_value'],
                boolean_value=row['boolean_value']
            ))
        return annotations
    
    # Utility methods
    def clear_conversation_data(self, conversation_id: str) -> None:
        """Delete all data for a conversation (for reprocessing)."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM annotations WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM exchanges WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
        self.connection.commit()
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        cursor = self.connection.cursor()
        
        stats = {}
        for table in ['conversations', 'exchanges', 'messages', 'annotations']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        return stats
    
    def mark_conversation_processed(self, conversation_id: str) -> None:
        """Mark conversation as processed."""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE conversations 
            SET processed_at = CURRENT_TIMESTAMP 
            WHERE conversation_id = ?
        """, (conversation_id,))
        self.connection.commit()
