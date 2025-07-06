# src/conversation_tagger/core/tagger.py
"""
Main ConversationTagger that orchestrates the exchange-based analysis.
Updated to use dictionary-based annotations.
"""

from typing import Dict, Any, List, Callable
from .exchange_parser import ExchangeParser
from .exchange_tagger import ExchangeTagger
from .conversation import Conversation
from .exchange import Exchange
from .tag import Tag


class ConversationTagger:
    """Main tagger that uses exchange-based analysis with annotations."""
    
    def __init__(self, exchange_parser: ExchangeParser | None = None):
        if not exchange_parser:
            exchange_parser = ExchangeParser()
        self.exchange_parser = exchange_parser
        self.conversation_rules: Dict[str, Callable] = {}
    
    def add_exchange_rule(self, annotation_name: str, rule_function: Callable):
        """Add rule for analyzing exchanges."""
        self.exchange_parser.exchange_tagger.add_rule(annotation_name, rule_function)

    def add_conversation_rule(self, annotation_name: str, rule_function: Callable):
        """Add rule for analyzing entire conversations."""
        self.conversation_rules[annotation_name] = rule_function
    
    def tag_conversation(self, conversation: Dict[str, Any]) -> Conversation:
        """Tag a conversation using exchange-based analysis."""
        # Parse into tagged exchanges and return Conversation object
        conv = self.exchange_parser.parse_conversation(conversation)
        
        # Apply conversation-level tagging rules
        for annotation_name, rule_func in self.conversation_rules.items():
            try:
                result = rule_func(conv)
                if result:
                    if isinstance(result, bool):
                        conv.add_annotation(annotation_name, True)
                    elif isinstance(result, dict):
                        # Multiple annotations returned
                        for name, value in result.items():
                            conv.add_annotation(name, value)
                    elif isinstance(result, Tag):
                        # Legacy Tag object - convert to annotation
                        conv.annotations.update(result.to_dict())
                    elif isinstance(result, list):
                        # Handle multiple tags returned from one rule
                        for item in result:
                            if isinstance(item, Tag):
                                conv.annotations.update(item.to_dict())
                            elif isinstance(item, dict):
                                conv.annotations.update(item)
                            else:
                                # Treat other items as simple annotations
                                conv.add_annotation(annotation_name, item)
                    else:
                        # Treat other truthy values as simple annotations
                        conv.add_annotation(annotation_name, result)
            except Exception as e:
                # Skip failed rules - could add logging here later
                pass
        
        return conv
