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
    metadata: Dict[str, Any] = field(default_factory=dict)  # Original conversation data
    
    # @classmethod
    # def from_json(cls, conversation_data: Dict[str, Any], 
    #               exchange_parser: 'ExchangeParser') -> 'Conversation':
    #     """Create Conversation from raw JSON data."""
        
    #     # Parse into already-tagged exchanges
    #     exchanges = exchange_parser.parse_conversation(conversation_data)
        
    #     # Create conversation
    #     conversation = cls(
    #         conversation_id=conversation_data.get('conversation_id', 'unknown'),
    #         title=conversation_data.get('title', 'Untitled'),
    #         exchanges=exchanges,
    #         metadata=conversation_data
    #     )
        
    #     # Aggregate tags from exchanges
    #     conversation._aggregate_exchange_tags()
    #     conversation._add_metadata_tags()
        
    #     return conversation
    
    def _aggregate_exchange_tags(self):
        """Create conversation-level tags from exchange tags."""
        exchange_tag_names = set()
        for exchange in self.exchanges:
            for tag in exchange.tags:
                exchange_tag_names.add(tag.name)
        
        # Add presence-based conversation tags
        for tag_name in exchange_tag_names:
            self.tags.append(Tag(f"has_{tag_name}"))
    
    def _add_metadata_tags(self):
        """Add tags from original conversation metadata."""
        if self.metadata.get('gizmo_id'):
            self.tags.append(Tag('gizmo', gizmo_id=self.metadata['gizmo_id']))
        
        plugin_ids = self.metadata.get('plugin_ids')
        if plugin_ids:
            for plugin_id in plugin_ids:
                self.tags.append(Tag('plugin', plugin_id=plugin_id))
    
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
