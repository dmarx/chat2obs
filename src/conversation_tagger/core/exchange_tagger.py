# conversation_tagger/core/exchange_tagger.py
"""
Tag individual exchanges using the improved exchange structure.
"""

from typing import Dict, Any, List, Callable
from collections import defaultdict
from .tag import Tag
from .exchange import Exchange


class ExchangeTagger:
    """Tags exchanges with user/assistant/exchange-level rules."""
    
    def __init__(self):
        self.user_rules: Dict[str, Callable] = {}
        self.assistant_rules: Dict[str, Callable] = {}
        self.exchange_rules: Dict[str, Callable] = {}
    
    def add_user_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for user messages."""
        self.user_rules[tag_name] = rule_function
    
    def add_assistant_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for assistant messages."""
        self.assistant_rules[tag_name] = rule_function
    
    def add_exchange_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for entire exchange."""
        self.exchange_rules[tag_name] = rule_function
    
    def tag_exchange(self, exchange: Exchange) -> Dict[str, Any]:
        """Tag a single exchange and populate its tags attribute."""
        #tags = []
        tags = exchange.tags or []
        
        # Apply user rules
        for tag_name, rule_func in self.user_rules.items():
            try:
                result = rule_func(exchange)
                if result:
                    if isinstance(result, bool):
                        tags.append(Tag(tag_name))
                    elif isinstance(result, Tag):
                        tags.append(result)
                    else:
                        tags.append(Tag(tag_name))
            except Exception as e:
                # Skip failed rules silently for now
                pass
        
        # Apply assistant rules
        for tag_name, rule_func in self.assistant_rules.items():
            try:
                result = rule_func(exchange)
                if result:
                    if isinstance(result, bool):
                        tags.append(Tag(tag_name))
                    elif isinstance(result, Tag):
                        tags.append(result)
                    else:
                        tags.append(Tag(tag_name))
            except Exception as e:
                pass
        
        # Apply exchange rules
        for tag_name, rule_func in self.exchange_rules.items():
            try:
                result = rule_func(exchange)
                if result:
                    if isinstance(result, bool):
                        tags.append(Tag(tag_name))
                    elif isinstance(result, Tag):
                        tags.append(result)
                    else:
                        tags.append(Tag(tag_name))
            except Exception as e:
                pass
        
        # Add exchange metadata tags
        tags.append(Tag('message_count', count=len(exchange.messages)))
        
        user_msg_count = len(exchange.get_user_messages())
        assistant_msg_count = len(exchange.get_assistant_messages())
        
        tags.append(Tag('user_message_count', count=user_msg_count))
        tags.append(Tag('assistant_message_count', count=assistant_msg_count))
        
        if exchange.has_continuations():
            tags.append(Tag('has_continuations'))
        
        # Populate the exchange's tags attribute
        exchange.tags = tags
        
        return {
            'exchange_id': exchange.exchange_id,
            'conversation_id': exchange.conversation_id,
            'tags': tags,
            'exchange': exchange
        }
    
    def tag_exchanges(self, exchanges: List[Exchange]) -> List[Dict[str, Any]]:
        """Tag multiple exchanges."""
        return [self.tag_exchange(exchange) for exchange in exchanges]
