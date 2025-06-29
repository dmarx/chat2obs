# conversation_tagger/core/conversation.py
from typing import List, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .exchange import Exchange
    from .exchange_parser import ExchangeParser

from .tag import Tag

@dataclass 
class Conversation:
    """A conversation consisting of sequential exchanges."""
    
    conversation_id: str
    title: str
    exchanges: List['Exchange'] = field(default_factory=list)
    tags: List[Tag] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def _exchange_tags(self) -> List[Tag]:
        """Get all tags from exchanges."""
        return [tag for exchange in self.exchanges for tag in exchange.tags]
    
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
        return ' '.join(exchange.get_user_text() for exchange in self.exchanges)
    
    def get_all_assistant_text(self) -> str:
        return ' '.join(exchange.get_assistant_text() for exchange in self.exchanges)
