# src/conversation_tagger/core/exchange_tagger.py
"""
Tag individual exchanges using the improved exchange structure.
"""

from typing import Dict, Any, List, Callable
from collections import defaultdict
from .tag import Tag
from .exchange import Exchange


class ExchangeTagger:
    """Tags exchanges with configurable rules."""
    
    def __init__(self):
        self.rules: Dict[str, Callable] = {}
    
    def add_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for exchanges."""
        self.rules[tag_name] = rule_function
    
    def tag_exchange(self, exchange: Exchange) -> Exchange:
        """Tag a single exchange and return the updated exchange."""
        tags = exchange.tags or []
        
        for tag_name, rule_func in self.rules.items():
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
        
        # Update the exchange's tags
        exchange.tags = tags
        return exchange
