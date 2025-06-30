# src/conversation_tagger/core/tagger.py
"""
Main ConversationTagger that orchestrates the exchange-based analysis.
"""

from typing import Dict, Any, List, Callable
from .exchange_parser import ExchangeParser
from .exchange_tagger import ExchangeTagger
from .conversation import Conversation
from .exchange import Exchange
from .tag import Tag


class ConversationTagger:
    """Main tagger that uses exchange-based analysis."""
    
    def __init__(self, exchange_parser: ExchangeParser | None = None):
        if not exchange_parser:
            exchange_parser = ExchangeParser()
        self.exchange_parser = exchange_parser
        self.conversation_rules: Dict[str, Callable] = {}
    
    def add_exchange_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for analyzing exchanges."""
        self.exchange_parser.exchange_tagger.add_rule(tag_name, rule_function)

    def add_conversation_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for analyzing entire conversations."""
        self.conversation_rules[tag_name] = rule_function
    
    def tag_conversation(self, conversation: Dict[str, Any]) -> Conversation:
        """Tag a conversation using exchange-based analysis."""
        # Parse into tagged exchanges and return Conversation object
        conv = self.exchange_parser.parse_conversation(conversation)
        
        # Apply conversation-level tagging rules
        conversation_tags = []
        
        for tag_name, rule_func in self.conversation_rules.items():
            try:
                result = rule_func(conv)
                if result:
                    if isinstance(result, bool):
                        conversation_tags.append(Tag(tag_name))
                    elif isinstance(result, Tag):
                        conversation_tags.append(result)
                    elif isinstance(result, list):
                        # Handle multiple tags returned from one rule
                        for tag in result:
                            if isinstance(tag, Tag):
                                conversation_tags.append(tag)
                            else:
                                conversation_tags.append(Tag(tag_name))
                    else:
                        # Treat other truthy values as simple tags
                        conversation_tags.append(Tag(tag_name))
            except Exception as e:
                # Skip failed rules - could add logging here later
                pass
        
        # Combine exchange tags with conversation-level tags
        all_tags = conv.tags + conversation_tags
        conv.tags = all_tags
        
        return conv
