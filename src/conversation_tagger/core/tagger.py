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
    
    def __init__(self, exchange_parser: ExchangeParser | None):
        if not exchange_parser:
            exchange_parser = ExchangeParser()
        self.exchange_parser = exchange_parser
        self.rules = []
    
    def add_exchange_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for analyzing exchanges."""
        self.exchange_tagger.add_rule(tag_name, rule_function)

    def add_conversation_rule(self, tag_name: str, rule_function: Callable):
        # to do
        pass
    
    def tag_conversation(self, conversation: Dict[str, Any]) -> Conversation:
        """Tag a conversation using exchange-based analysis."""
        # Parse into tagged exchanges and return Conversation object
        conv = self.exchange_parser.parse_conversation(conversation)
        # to do: apply conversation-level rules
        return conv
    
