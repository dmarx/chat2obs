# conversation_tagger/core/exchange.py
"""
Exchange abstraction with sequential message handling and merge capabilities.
Updated to use dictionary-based annotations.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
import uuid


if TYPE_CHECKING:
    from .tag import Tag

from .message import Message



@dataclass
class Exchange:
    """A sequential conversation exchange with merge capabilities."""
    conversation_id: str
    messages: list[Message]
    annotations: Dict[str, Any] = field(default_factory=dict)  # Dictionary-based annotations
    exchange_id: str|None = '' # this should just be the message id of the last assistant response, otherwise won't properly handle forks/leaves
    
    def __post_init__(self):
        _id = None
        if self.exchange_id:
            return
        #print(self.messages)
        if self.messages:
            _id = self.messages[-1].id
        if _id is None:
            _id = str(uuid.uuid4())
        self.exchange_id = _id

    @classmethod
    def create(cls, conversation_id: str, messages: List[Message]) -> 'Exchange':
        """Create a new exchange with a random UUID."""
        return cls(
            #exchange_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            messages=messages,
            annotations={}
        )
    
    @property
    def last_message_time(self) -> float:
        """Get the create_time of the last message for ordering."""
        if not self.messages:
            return 0.0
        return self.messages[-1].created_date
    
    @property
    def first_message_time(self) -> float:
        """Get the create_time of the first message for ordering."""
        if not self.messages:
            return 0.0
        return self.messages[0].created_date
    
    def has_continuations(self) -> bool:
        """Check if this exchange has continuation prompts (multiple user messages)."""
        return len(self.get_user_messages()) > 1
    
    def get_message_ids(self) -> List[str]:
        """Get the IDs of all messages in this exchange."""
        return [msg.id for msg in self.messages if msg.id]

    def get_user_messages(self) -> List[Dict[str, Any]]:
        """Get just the user messages."""
        return [msg for msg in self.messages if msg.author_role == 'user']
    
    def get_assistant_messages(self) -> List[Dict[str, Any]]:
        """Get just the assistant messages."""
        return [msg for msg in self.messages if msg.author_role == 'assistant']
    
    def get_user_texts(self) -> List[str]:
        """Get text from all user messages."""
        return [msg.content for msg in self.get_user_messages()]
    
    def get_assistant_texts(self) -> List[str]:
        """Get text from all assistant messages."""
        return [msg.content for msg in self.get_assistant_messages()]

    def add_annotation(self, name: str, value: Any = True) -> None:
        """Add an annotation to this exchange."""
        self.annotations[name] = value
    
    def has_annotation(self, name: str) -> bool:
        """Check if annotation exists."""
        return name in self.annotations
    
    def get_annotation(self, name: str, default: Any = None) -> Any:
        """Get annotation value."""
        return self.annotations.get(name, default)

    # # Legacy compatibility
    # @property 
    # def tags(self) -> List['Tag']:
    #     """Convert annotations back to Tag objects for backward compatibility."""
    #     from .tag import Tag
    #     tags = []
    #     for name, value in self.annotations.items():
    #         if value is True:
    #             tags.append(Tag(name))
    #         elif isinstance(value, dict):
    #             tags.append(Tag(name, **value))
    #         else:
    #             tags.append(Tag(name, value=value))
    #     return tags
    
    # @tags.setter
    # def tags(self, tag_list: List['Tag']) -> None:
    #     """Convert Tag objects to annotations for backward compatibility."""
    #     self.annotations = {}
    #     for tag in tag_list:
    #         self.annotations.update(tag.to_dict())

    def __add__(self, other: 'Exchange') -> 'Exchange':
        """Merge two exchanges by combining and time-ordering their messages."""
        if not isinstance(other, Exchange):
            raise TypeError("Can only add Exchange objects")
        
        if self.conversation_id != other.conversation_id:
            raise ValueError("Cannot merge exchanges from different conversations")
        
        # Combine and sort messages by create_time to ensure proper chronological order
        combined_messages = self.messages + other.messages
        combined_messages.sort(key=lambda msg: msg.created_date)
        
        # Merge annotations from both exchanges
        combined_annotations = {}
        combined_annotations.update(self.annotations)
        combined_annotations.update(other.annotations)
        
        # Create new exchange with combined content
        merged_exchange = Exchange(
            exchange_id=str(uuid.uuid4()),  # New UUID for merged exchange
            conversation_id=self.conversation_id,
            messages=combined_messages,
            annotations=combined_annotations
        )
        
        return merged_exchange
    
    def __len__(self) -> int:
        """Return number of messages in exchange."""
        return len(self.messages)
    
    @property
    def content(self) -> str:
        """Get concatenated content of all messages in this exchange."""
        return '\n'.join(str(msg) for msg in self.messages if msg.content).strip()
    
    # def __str__(self) -> str:
    #     """String representation showing message sequence."""
    #     roles = [msg.get('author', {}).get('role', 'unknown') for msg in self.messages]
    #     return f"Exchange({self.exchange_id[:8]}...: {' → '.join(roles)})"
