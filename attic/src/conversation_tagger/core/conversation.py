# conversation_tagger/core/conversation.py
"""
Conversation class updated to use dictionary-based annotations.
"""

from typing import List, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .exchange import Exchange
    from .exchange_parser import ExchangeParser

from .tag import Tag

@dataclass 
class Conversation:
    """A conversation consisting of sequential exchanges with annotations."""
    
    conversation_id: str
    title: str
    exchanges: List['Exchange'] = field(default_factory=list)
    annotations: Dict[str, Any] = field(default_factory=dict)  # Dictionary-based annotations
    raw: Dict[str, Any] | None = field(default=None)  
    
    def __post_init__(self):
        """Post-initialization to ensure annotations are set."""
        if not self.annotations:
            self._add_exchange_annotations()

    def _add_exchange_annotations(self):
        """Aggregate annotations from all exchanges."""
        if not self.annotations:
            # Collect all unique annotations from exchanges
            for exchange in self.exchanges:
                for name, value in exchange.annotations.items():
                    if name not in self.annotations:
                        self.annotations[name] = value

    def add_annotation(self, name: str, value: Any = True) -> None:
        """Add an annotation to this conversation."""
        self.annotations[name] = value
    
    def has_annotation(self, name: str) -> bool:
        """Check if annotation exists."""
        return name in self.annotations
    
    def get_annotation(self, name: str, default: Any = None) -> Any:
        """Get annotation value."""
        return self.annotations.get(name, default)
    
    # Legacy compatibility
    @property
    def tags(self) -> List[Tag]:
        """Convert annotations back to Tag objects for backward compatibility."""
        tags = []
        for name, value in self.annotations.items():
            if value is True:
                tags.append(Tag(name))
            elif isinstance(value, dict):
                tags.append(Tag(name, **value))
            else:
                tags.append(Tag(name, value=value))
        return tags
    
    @tags.setter
    def tags(self, tag_list: List[Tag]) -> None:
        """Convert Tag objects to annotations for backward compatibility."""
        self.annotations = {}
        for tag in tag_list:
            self.annotations.update(tag.to_dict())
    
    @property
    def exchange_count(self) -> int:
        return len(self.exchanges)
    
    @property 
    def total_message_count(self) -> int:
        return sum(len(exchange.messages) for exchange in self.exchanges)
    
    @property
    def total_user_messages(self) -> int:
        return sum(len(exchange.get_user_messages()) for exchange in self.exchanges)
        
    @property
    def total_assistant_messages(self) -> int:
        return sum(len(exchange.get_assistant_messages()) for exchange in self.exchanges)
    
    @property
    def has_continuations(self) -> bool:
        return any(exchange.has_continuations() for exchange in self.exchanges)
    
    def get_all_user_text(self) -> str:
        return ' '.join(' '.join(exchange.get_user_texts()) for exchange in self.exchanges)
    
    def get_all_assistant_text(self) -> str:
        return ' '.join(' '.join(exchange.get_assistant_texts()) for exchange in self.exchanges)
