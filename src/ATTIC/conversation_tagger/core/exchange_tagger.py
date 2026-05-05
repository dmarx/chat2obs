# conversation_tagger/core/exchange_tagger.py
"""
Tagger for individual exchanges.
"""

from typing import Dict, Any, List, Callable, Union
from collections import defaultdict
from .tag import Tag
from .exchange import Exchange


class ExchangeTagger:
    """Tags individual exchanges with rules specific to exchange-level analysis."""
    
    def __init__(self):
        self.user_rules: Dict[str, Callable] = {}           # Rules for user messages
        self.assistant_rules: Dict[str, Callable] = {}      # Rules for assistant messages  
        self.exchange_rules: Dict[str, Callable] = {}       # Rules for entire exchange
        self.supplemental_rules: Dict[str, Callable] = {}   # Rules depending on existing tags
        self.rule_descriptions: Dict[str, str] = {}
    
    def add_user_rule(self, tag_name: str, rule_function: Callable, description: str = ""):
        """Add rule that analyzes user messages in the exchange."""
        self.user_rules[tag_name] = rule_function
        self.rule_descriptions[tag_name] = description
    
    def add_assistant_rule(self, tag_name: str, rule_function: Callable, description: str = ""):
        """Add rule that analyzes assistant messages in the exchange.""" 
        self.assistant_rules[tag_name] = rule_function
        self.rule_descriptions[tag_name] = description
    
    def add_exchange_rule(self, tag_name: str, rule_function: Callable, description: str = ""):
        """Add rule that analyzes the entire exchange."""
        self.exchange_rules[tag_name] = rule_function
        self.rule_descriptions[tag_name] = description
    
    def add_supplemental_rule(self, tag_name: str, rule_function: Callable, description: str = ""):
        """Add rule that depends on existing tags."""
        self.supplemental_rules[tag_name] = rule_function
        self.rule_descriptions[tag_name] = description
    
    def tag_exchange(self, exchange: Exchange) -> Dict[str, Any]:
        """Apply all tagging rules to an exchange."""
        tags = set()
        debug_info = defaultdict(list)
        
        # Apply user message rules
        for tag_name, rule_func in self.user_rules.items():
            try:
                result = rule_func(exchange)
                if result:
                    tag = self._normalize_tag(result, tag_name)
                    tags.add(tag)
                    debug_info['applied_rules'].append(f"USER: {tag}")
            except Exception as e:
                debug_info['errors'].append(f"USER: {tag_name} - {str(e)}")
        
        # Apply assistant message rules
        for tag_name, rule_func in self.assistant_rules.items():
            try:
                result = rule_func(exchange)
                if result:
                    tag = self._normalize_tag(result, tag_name)
                    tags.add(tag)
                    debug_info['applied_rules'].append(f"ASSISTANT: {tag}")
            except Exception as e:
                debug_info['errors'].append(f"ASSISTANT: {tag_name} - {str(e)}")
        
        # Apply exchange-level rules
        for tag_name, rule_func in self.exchange_rules.items():
            try:
                result = rule_func(exchange)
                if result:
                    tag = self._normalize_tag(result, tag_name)
                    tags.add(tag)
                    debug_info['applied_rules'].append(f"EXCHANGE: {tag}")
            except Exception as e:
                debug_info['errors'].append(f"EXCHANGE: {tag_name} - {str(e)}")
        
        # Apply supplemental rules
        for tag_name, rule_func in self.supplemental_rules.items():
            if any(tag.name == tag_name for tag in tags):
                continue
                
            try:
                result = rule_func(exchange, tags)
                if result:
                    tag = self._normalize_tag(result, tag_name)
                    tags.add(tag)
                    debug_info['applied_rules'].append(f"SUPP: {tag}")
            except Exception as e:
                debug_info['errors'].append(f"SUPP: {tag_name} - {str(e)}")
        
        return {
            'exchange_id': exchange.exchange_id,
            'conversation_id': exchange.conversation_id,
            'exchange_index': exchange.exchange_index,
            'tags': list(tags),
            'debug_info': dict(debug_info),
            'exchange': exchange
        }
    
    def tag_exchanges(self, exchanges: List[Exchange]) -> List[Dict[str, Any]]:
        """Tag multiple exchanges."""
        return [self.tag_exchange(exchange) for exchange in exchanges]
    
    def _normalize_tag(self, result: Union[bool, str, Tag], tag_name: str) -> Tag:
        """Convert rule results to Tag objects."""
        if isinstance(result, bool):
            return Tag(tag_name)
        elif isinstance(result, str):
            return Tag(result)
        elif isinstance(result, Tag):
            return result
        else:
            return Tag(tag_name)