# src/conversation_tagger/core/tagger.py
"""
Main ConversationTagger that orchestrates the exchange-based analysis.
"""

from typing import Dict, Any, List, Callable
from .exchange_parser import ExchangeParser
from .exchange_tagger import ExchangeTagger
from .conversation import Conversation
from .exchange import Exchange


class ConversationTagger:
    """Main tagger that uses exchange-based analysis."""
    
    def __init__(self):
        self.exchange_tagger = ExchangeTagger()
        self.exchange_parser = ExchangeParser(self.exchange_tagger)
    
    def add_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for analyzing exchanges."""
        self.exchange_tagger.add_rule(tag_name, rule_function)
    
    def tag_conversation(self, conversation: Dict[str, Any]) -> Conversation:
        """Tag a conversation using exchange-based analysis."""
        # Parse into tagged exchanges and return Conversation object
        return self.exchange_parser.parse_conversation(conversation)
    
    def tag_conversations(self, conversations: List[Dict[str, Any]]) -> List[Conversation]:
        """Tag multiple conversations."""
        return [self.tag_conversation(conv) for conv in conversations]
    
    def get_exchange_analysis(self, conversation: Dict[str, Any]) -> List[Exchange]:
        """Get just the exchange-level analysis."""
        conv = self.exchange_parser.parse_conversation(conversation)
        return conv.exchanges
