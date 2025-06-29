# conversation_tagger/core/tagger.py
"""
Main ConversationTagger that orchestrates the exchange-based analysis.
"""

from typing import Dict, Any, List, Callable
from .exchange_parser import ExchangeParser
from .exchange_tagger import ExchangeTagger
from .conversation_aggregator import ConversationAggregator


class ConversationTagger:
    """Main tagger that uses exchange-based analysis."""
    
    def __init__(self):
        self.exchange_parser = ExchangeParser()
        self.exchange_tagger = ExchangeTagger()
        self.conversation_aggregator = ConversationAggregator()
    
    def add_exchange_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for analyzing user messages in exchanges."""
        self.exchange_tagger.add_rule(tag_name, rule_function)
    
    def add_conversation_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for analyzing assistant messages in exchanges."""
        self.exchange_tagger.add_assistant_rule(tag_name, rule_function)
    
    # we should probably apply these tags in the conversation builder
    def tag_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Tag a conversation using exchange-based analysis."""
        # Parse into exchanges
        exchanges = self.exchange_parser.parse_conversation(conversation)
        
        # Tag each exchange
        tagged_exchanges = self.exchange_tagger.tag_exchanges(exchanges)
        
        # Aggregate to conversation level
        return self.conversation_aggregator.aggregate_to_conversation(tagged_exchanges, conversation)
    
    def tag_conversations(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Tag multiple conversations."""
        return [self.tag_conversation(conv) for conv in conversations]
    
    def get_exchange_analysis(self, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get just the exchange-level analysis."""
        exchanges = self.exchange_parser.parse_conversation(conversation)
        return self.exchange_tagger.tag_exchanges(exchanges)
