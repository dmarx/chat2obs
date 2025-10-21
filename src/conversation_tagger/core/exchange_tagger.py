# src/conversation_tagger/core/exchange_tagger.py
"""
Tag individual exchanges using the improved exchange structure.
Updated to use dictionary-based annotations.
"""
from typing import Dict, Callable, Any
# Tag import removed - using dictionary-based annotations
from .exchange import Exchange


class ExchangeTagger:
    """Tags exchanges with configurable rules using annotations."""
    
    def __init__(self):
        self.rules: Dict[str, Callable] = {}
    
    def add_rule(self, annotation_name: str, rule_function: Callable):
        """Add rule for exchanges."""
        self.rules[annotation_name] = rule_function
    
    def tag_exchange(self, exchange: Exchange) -> Exchange:
        """Tag a single exchange and return the updated exchange."""
        for annotation_name, rule_func in self.rules.items():
            try:
                result = rule_func(exchange)
                if result:
                    if isinstance(result, bool):
                        # Simple boolean annotation
                        exchange.add_annotation(annotation_name, True)
                    elif isinstance(result, dict):
                        # Multiple annotations returned
                        for name, value in result.items():
                            exchange.add_annotation(name, value)
                    # Tag class removed - only dict/bool/value results supported
                    else:
                        # Other truthy value - store as annotation value
                        exchange.add_annotation(annotation_name, result)
            except Exception as e:
                # Skip failed rules silently for now
                pass
        
        return exchange
