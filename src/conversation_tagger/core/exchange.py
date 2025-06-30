# conversation_tagger/core/exchange.py
"""
Exchange abstraction with sequential message handling and merge capabilities.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
import uuid

if TYPE_CHECKING:
    from .tag import Tag


def get_message_text(message: Dict[str, Any]) -> str:
    """Extract text content from a message."""
    content = message.get('content', {})
    text = content.get('text', '')
    parts = content.get('parts', [])
    joined = ' '.join(str(p) for p in parts if isinstance(p, str)).strip()
    if joined:
        text = f"{text} {joined}"
    return text.strip()


@dataclass
class Exchange:
    """A sequential conversation exchange with merge capabilities."""
    
    exchange_id: str
    conversation_id: str
    messages: List[Dict[str, Any]]  # Sequential messages in this exchange
    tags: List['Tag'] = field(default_factory=list)  # Container for associated tags
    
    @classmethod
    def create(cls, conversation_id: str, messages: List[Dict[str, Any]]) -> 'Exchange':
        """Create a new exchange with a random UUID."""
        return cls(
            exchange_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            messages=messages,
            tags=[]
        )
    
    @property
    def first_message_time(self) -> float:
        """Get the create_time of the first message for ordering."""
        if not self.messages:
            return 0.0
        return self.messages[0].get('create_time', 0.0)
    
    def has_continuations(self) -> bool:
        """Check if this exchange has continuation prompts (multiple user messages)."""
        user_count = sum(1 for msg in self.messages 
                        if msg.get('author', {}).get('role') == 'user')
        return user_count > 1
    
    def get_user_messages(self) -> List[Dict[str, Any]]:
        """Get just the user messages."""
        return [msg for msg in self.messages 
                if msg.get('author', {}).get('role') == 'user']
    
    def get_assistant_messages(self) -> List[Dict[str, Any]]:
        """Get just the assistant messages."""
        return [msg for msg in self.messages 
                if msg.get('author', {}).get('role') == 'assistant']
    
    def get_user_texts(self) -> str:
        """Get combined text from all user messages."""
        return [get_message_text(msg) for msg in self.get_user_messages()]
    
    def get_assistant_texts(self) -> str:
        """Get combined text from all assistant messages."""
        return [get_message_text(msg) for msg in self.get_assistant_messages()]

    def __add__(self, other: 'Exchange') -> 'Exchange':
        """Merge two exchanges by combining and time-ordering their messages."""
        if not isinstance(other, Exchange):
            raise TypeError("Can only add Exchange objects")
        
        if self.conversation_id != other.conversation_id:
            raise ValueError("Cannot merge exchanges from different conversations")
        
        # Combine and sort messages by create_time to ensure proper chronological order
        combined_messages = self.messages + other.messages
        combined_messages.sort(key=lambda msg: msg.get('create_time', 0.0))
        
        # Combine tags from both exchanges
        # probably need to be smarter about how we perform this merge
        combined_tags = self.tags + other.tags
        
        # Create new exchange with combined content
        merged_exchange = Exchange(
            exchange_id=str(uuid.uuid4()),  # New UUID for merged exchange
            conversation_id=self.conversation_id,
            messages=combined_messages,
            tags=combined_tags
        )
        
        return merged_exchange
    
    def __len__(self) -> int:
        """Return number of messages in exchange."""
        return len(self.messages)
    
    def __str__(self) -> str:
        """String representation showing message sequence."""
        roles = [msg.get('author', {}).get('role', 'unknown') for msg in self.messages]
        return f"Exchange({self.exchange_id[:8]}...: {' → '.join(roles)})"
