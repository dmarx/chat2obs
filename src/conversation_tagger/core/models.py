# src/conversation_tagger/core/models.py
"""
Core dataclasses for the simplified conversation tagger.
Uses dict-based annotations instead of complex Tag objects.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
import uuid


def extract_message_text(message: Dict[str, Any]) -> str:
    """Extract text content from a message."""
    content = message.get('content', {})
    text = content.get('text', '')
    parts = content.get('parts', [])
    
    # Combine text and parts
    if parts:
        parts_text = ' '.join(str(p) for p in parts if isinstance(p, str))
        if parts_text.strip():
            text = f"{text} {parts_text}".strip()
    
    return text.strip()


@dataclass
class Exchange:
    """A conversation exchange with simple dict-based annotations."""
    
    exchange_id: str
    conversation_id: str
    messages: List[Dict[str, Any]]
    annotations: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(cls, conversation_id: str, messages: List[Dict[str, Any]]) -> 'Exchange':
        """Create a new exchange with a random UUID."""
        return cls(
            exchange_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            messages=messages,
            annotations={}
        )
    
    def get_user_messages(self) -> List[Dict[str, Any]]:
        """Get all user messages in this exchange."""
        return [msg for msg in self.messages 
                if msg.get('author', {}).get('role') == 'user']
    
    def get_assistant_messages(self) -> List[Dict[str, Any]]:
        """Get all assistant messages in this exchange."""
        return [msg for msg in self.messages 
                if msg.get('author', {}).get('role') == 'assistant']
    
    def get_user_texts(self) -> List[str]:
        """Get text content from all user messages."""
        return [extract_message_text(msg) for msg in self.get_user_messages()]
    
    def get_assistant_texts(self) -> List[str]:
        """Get text content from all assistant messages."""
        return [extract_message_text(msg) for msg in self.get_assistant_messages()]
    
    def get_all_texts(self) -> List[str]:
        """Get text content from all messages."""
        return [extract_message_text(msg) for msg in self.messages]
    
    def has_continuations(self) -> bool:
        """Check if this exchange has continuation prompts (multiple user messages)."""
        return len(self.get_user_messages()) > 1
    
    @property
    def first_message_time(self) -> float:
        """Get the create_time of the first message for ordering."""
        if not self.messages:
            return 0.0
        return self.messages[0].get('create_time', 0.0)
    
    def __len__(self) -> int:
        """Return number of messages in exchange."""
        return len(self.messages)
    
    def __add__(self, other: 'Exchange') -> 'Exchange':
        """Merge two exchanges by combining and time-ordering their messages."""
        if not isinstance(other, Exchange):
            raise TypeError("Can only add Exchange objects")
        
        if self.conversation_id != other.conversation_id:
            raise ValueError("Cannot merge exchanges from different conversations")
        
        # Combine and sort messages by create_time
        combined_messages = self.messages + other.messages
        combined_messages.sort(key=lambda msg: msg.get('create_time', 0.0))
        
        # Combine annotations (simple merge, later ones override)
        combined_annotations = {**self.annotations, **other.annotations}
        
        # Create new exchange with combined content
        merged_exchange = Exchange(
            exchange_id=str(uuid.uuid4()),
            conversation_id=self.conversation_id,
            messages=combined_messages,
            annotations=combined_annotations
        )
        
        return merged_exchange


@dataclass
class Conversation:
    """A conversation with multiple exchanges and annotations."""
    
    conversation_id: str
    title: str
    exchanges: List[Exchange] = field(default_factory=list)
    annotations: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] | None = None
    
    @property
    def exchange_count(self) -> int:
        """Number of exchanges in this conversation."""
        return len(self.exchanges)
    
    @property
    def total_message_count(self) -> int:
        """Total number of messages across all exchanges."""
        return sum(len(exchange.messages) for exchange in self.exchanges)
    
    @property
    def total_user_messages(self) -> int:
        """Total number of user messages across all exchanges."""
        return sum(len(exchange.get_user_messages()) for exchange in self.exchanges)
    
    @property
    def total_assistant_messages(self) -> int:
        """Total number of assistant messages across all exchanges."""
        return sum(len(exchange.get_assistant_messages()) for exchange in self.exchanges)
    
    def get_all_user_text(self) -> str:
        """Get combined text from all user messages across all exchanges."""
        all_texts = []
        for exchange in self.exchanges:
            all_texts.extend(exchange.get_user_texts())
        return ' '.join(all_texts)
    
    def get_all_assistant_text(self) -> str:
        """Get combined text from all assistant messages across all exchanges."""
        all_texts = []
        for exchange in self.exchanges:
            all_texts.extend(exchange.get_assistant_texts())
        return ' '.join(all_texts)
    
    def get_all_annotations(self) -> Dict[str, Any]:
        """Get combined view of all annotations (exchange + conversation level)."""
        all_annotations = {}
        
        # Collect exchange-level annotations
        for i, exchange in enumerate(self.exchanges):
            for key, value in exchange.annotations.items():
                # Prefix with exchange index to avoid conflicts
                prefixed_key = f"exchange_{i}_{key}"
                all_annotations[prefixed_key] = value
                
                # Also maintain unprefixed version for convenience (last exchange wins)
                all_annotations[key] = value
        
        # Add conversation-level annotations (these take precedence)
        all_annotations.update(self.annotations)
        
        return all_annotations
    
    def has_annotation(self, annotation_name: str) -> bool:
        """Check if any exchange or the conversation has this annotation."""
        if annotation_name in self.annotations:
            return True
        
        return any(annotation_name in exchange.annotations 
                  for exchange in self.exchanges)
    
    def count_exchanges_with_annotation(self, annotation_name: str) -> int:
        """Count how many exchanges have a specific annotation."""
        return sum(1 for exchange in self.exchanges 
                  if annotation_name in exchange.annotations)
