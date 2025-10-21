# conversation_tagger/db/ingestion.py
"""
Incremental ingestion pipeline that processes only new/changed conversations.
"""

import json
from typing import Dict, Any, List, Set, Optional, Tuple
from datetime import datetime
from pathlib import Path

from ..core.conversation import Conversation
from ..core.exchange import Exchange  
from ..core.message import Message
from ..core.exchange_parser import ExchangeParserOAI, ExchangeParserClaude
from .manager import DatabaseManager
from .models import ConversationDB, ExchangeDB, MessageDB, AnnotationDB


class IncrementalIngester:
    """Handles incremental ingestion of conversation data into database."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.parsers = {
            'oai': ExchangeParserOAI(),
            'claude': ExchangeParserClaude()
        }
    
    def ingest_from_export(self, export_data: List[Dict[str, Any]], source: str) -> Dict[str, Any]:
        """Ingest conversations from export data with incremental processing.
        
        Args:
            export_data: List of conversation dictionaries from export
            source: Source type ('oai', 'claude')
            
        Returns:
            Dict with ingestion statistics
        """
        stats = {
            'total_conversations': len(export_data),
            'new_conversations': 0,
            'updated_conversations': 0,
            'unchanged_conversations': 0,
            'conversations_processed': 0
        }
        
        # Detect changes first
        changes = self._detect_changes(export_data, source)
        
        # Process only new/changed conversations
        for conv_data in export_data:
            conv_id = self._get_conversation_id(conv_data, source)
            
            if conv_id in changes['new']:
                self._ingest_conversation(conv_data, source, is_new=True)
                stats['new_conversations'] += 1
                stats['conversations_processed'] += 1
                
            elif conv_id in changes['updated']:
                # Clear existing data and re-ingest
                self.db.clear_conversation_data(conv_id)
                self._ingest_conversation(conv_data, source, is_new=False)
                stats['updated_conversations'] += 1 
                stats['conversations_processed'] += 1
                
            else:
                stats['unchanged_conversations'] += 1
        
        return stats
    
    def _detect_changes(self, export_data: List[Dict[str, Any]], source: str) -> Dict[str, Set[str]]:
        """Detect which conversations are new or updated.
        
        Returns:
            Dict with 'new' and 'updated' sets of conversation IDs
        """
        changes = {'new': set(), 'updated': set()}
        
        # Get existing conversations from database
        existing_convs = {
            conv.conversation_id: conv 
            for conv in self.db.get_conversations_by_source(source)
        }
        
        for conv_data in export_data:
            conv_id = self._get_conversation_id(conv_data, source)
            last_message_time = self._get_last_message_time(conv_data, source)
            
            if conv_id not in existing_convs:
                changes['new'].add(conv_id)
            else:
                existing_conv = existing_convs[conv_id]
                # Check if conversation has new messages
                if last_message_time > existing_conv.last_message_time:
                    changes['updated'].add(conv_id)
        
        return changes
    
    def _ingest_conversation(self, conv_data: Dict[str, Any], source: str, is_new: bool) -> None:
        """Ingest a single conversation into the database."""
        
        # Parse conversation using existing parser
        parser = self.parsers[source]
        conversation = parser.parse_conversation(conv_data)
        
        # Convert to database models
        conv_db = self._conversation_to_db(conversation, source, conv_data)
        
        # Store conversation
        self.db.upsert_conversation(conv_db)
        
        # Store exchanges and messages
        for seq_num, exchange in enumerate(conversation.exchanges):
            exchange_db = self._exchange_to_db(exchange, seq_num)
            self.db.upsert_exchange(exchange_db)
            
            # Store messages for this exchange
            for msg_seq, message in enumerate(exchange.messages):
                message_db = self._message_to_db(message, exchange.exchange_id, conversation.conversation_id, msg_seq)
                self.db.upsert_message(message_db)
            
            # Store exchange annotations
            self._store_annotations(exchange.annotations, conversation.conversation_id, exchange.exchange_id)
        
        # Store conversation-level annotations
        self._store_annotations(conversation.annotations, conversation.conversation_id, None)
    
    def _conversation_to_db(self, conversation: Conversation, source: str, raw_data: Dict[str, Any]) -> ConversationDB:
        """Convert Conversation object to ConversationDB."""
        
        # Calculate timing info
        first_time = min(ex.first_message_time for ex in conversation.exchanges) if conversation.exchanges else 0.0
        last_time = max(ex.last_message_time for ex in conversation.exchanges) if conversation.exchanges else 0.0
        
        conv_db = ConversationDB(
            conversation_id=conversation.conversation_id,
            source=source,
            title=conversation.title,
            first_message_time=first_time,
            last_message_time=last_time,
            last_updated=datetime.now(),
            processed_at=None,  # Will be set after tagging
            exchange_count=conversation.exchange_count,
            total_message_count=conversation.total_message_count,
            total_user_messages=conversation.total_user_messages,
            total_assistant_messages=conversation.total_assistant_messages
        )
        
        # Store raw data and annotations
        conv_db.set_raw_data(raw_data)
        conv_db.set_annotations(conversation.annotations)
        
        return conv_db
    
    def _exchange_to_db(self, exchange: Exchange, sequence_number: int) -> ExchangeDB:
        """Convert Exchange object to ExchangeDB."""
        
        user_messages = exchange.get_user_messages()
        assistant_messages = exchange.get_assistant_messages()
        
        return ExchangeDB(
            exchange_id=exchange.exchange_id,
            conversation_id=exchange.conversation_id,
            sequence_number=sequence_number,
            first_message_time=exchange.first_message_time,
            last_message_time=exchange.last_message_time,
            message_count=len(exchange.messages),
            user_message_count=len(user_messages),
            assistant_message_count=len(assistant_messages),
            has_continuations=exchange.has_continuations(),
            annotations=json.dumps(exchange.annotations) if exchange.annotations else None
        )
    
    def _message_to_db(self, message: Message, exchange_id: str, conversation_id: str, sequence_number: int) -> MessageDB:
        """Convert Message object to MessageDB."""
        
        message_db = MessageDB(
            message_id=message.id,
            exchange_id=exchange_id,
            conversation_id=conversation_id,
            author_role=message.author_role,
            content=message.content,
            created_date=message.created_date,
            sequence_number=sequence_number
        )
        
        # Store raw message data if available
        if hasattr(message, 'data'):
            message_db.set_raw_data(message.data)
        
        return message_db
    
    def _store_annotations(self, annotations: Dict[str, Any], conversation_id: str, exchange_id: Optional[str]) -> None:
        """Store annotations in the searchable annotations table."""
        
        for name, value in annotations.items():
            annotation = AnnotationDB(
                conversation_id=conversation_id,
                exchange_id=exchange_id,
                annotation_name=name
            )
            annotation.set_value(value)
            self.db.upsert_annotation(annotation)
    
    def _get_conversation_id(self, conv_data: Dict[str, Any], source: str) -> str:
        """Extract conversation ID from raw data."""
        if source == 'oai':
            return conv_data.get('conversation_id', '')
        elif source == 'claude':
            return conv_data.get('uuid', '')
        else:
            raise ValueError(f"Unknown source: {source}")
    
    def _get_last_message_time(self, conv_data: Dict[str, Any], source: str) -> float:
        """Extract last message timestamp from raw data."""
        if source == 'oai':
            mapping = conv_data.get('mapping', {})
            max_time = 0.0
            for node in mapping.values():
                message = node.get('message')
                if message:
                    create_time = message.get('create_time', 0.0)
                    max_time = max(max_time, create_time)
            return max_time
            
        elif source == 'claude':
            # Claude conversations have chat_messages array
            messages = conv_data.get('chat_messages', [])
            if messages:
                # Find the latest created_at timestamp
                max_time = 0
                for msg in messages:
                    created_at = msg.get('created_at', 0)
                    if isinstance(created_at, str):
                        # Convert ISO string to timestamp if needed
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            created_at = dt.timestamp()
                        except:
                            created_at = 0
                    max_time = max(max_time, created_at)
                return max_time
            return 0.0
        else:
            raise ValueError(f"Unknown source: {source}")


class DatabaseToObjectConverter:
    """Converts database records back to conversation objects for processing."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from database back to Conversation object."""
        
        # Get conversation record
        conv_db = self.db.get_conversation(conversation_id)
        if not conv_db:
            return None
        
        # Get exchanges
        exchanges_db = self.db.get_exchanges_for_conversation(conversation_id)
        exchanges = []
        
        for exchange_db in exchanges_db:
            # Get messages for this exchange
            messages_db = self.db.get_messages_for_exchange(exchange_db.exchange_id)
            
            # Convert messages back to Message objects
            messages = []
            for msg_db in messages_db:
                # Create a mock Message object with the data we need
                message = MockMessage(
                    id=msg_db.message_id,
                    author_role=msg_db.author_role,
                    content=msg_db.content,
                    created_date=msg_db.created_date,
                    raw_data=msg_db.get_raw_data()
                )
                messages.append(message)
            
            # Create Exchange object
            exchange = Exchange(
                conversation_id=exchange_db.conversation_id,
                messages=messages,
                annotations=exchange_db.get_annotations(),
                exchange_id=exchange_db.exchange_id
            )
            exchanges.append(exchange)
        
        # Create Conversation object
        conversation = Conversation(
            conversation_id=conv_db.conversation_id,
            title=conv_db.title,
            exchanges=exchanges,
            annotations=conv_db.get_annotations(),
            raw=conv_db.get_raw_data()
        )
        
        return conversation
    
    def load_unprocessed_conversations(self, source: Optional[str] = None) -> List[Conversation]:
        """Load all unprocessed conversations."""
        conv_dbs = self.db.get_unprocessed_conversations(source)
        conversations = []
        
        for conv_db in conv_dbs:
            conversation = self.load_conversation(conv_db.conversation_id)
            if conversation:
                conversations.append(conversation)
        
        return conversations


class MockMessage(Message):
    """Mock Message object for database-loaded data."""
    
    def __init__(self, id: str, author_role: str, content: str, created_date: float, raw_data: Optional[Dict[str, Any]] = None):
        self._id = id
        self._author_role = author_role  
        self._content = content
        self._created_date = created_date
        self._raw_data = raw_data or {}
        # Call parent init with raw data
        super().__init__(self._raw_data)
    
    def _get_id(self) -> str:
        return self._id
    
    def _get_author_role(self) -> str:
        return self._author_role
    
    def _get_content(self) -> str:
        return self._content
    
    def _get_created_date(self) -> float:
        return self._created_date
