# src/conversation_tagger/core/annotator.py
"""
Unified annotator for exchanges and conversations using simple dict-based annotations.
"""

from typing import Dict, Callable, Any, Union
from .models import Exchange, Conversation


class Annotator:
    """Unified annotator for exchanges and conversations."""
    
    def __init__(self):
        self.exchange_rules: Dict[str, Callable[[Exchange], Any]] = {}
        self.conversation_rules: Dict[str, Callable[[Conversation], Any]] = {}
    
    def add_exchange_rule(self, name: str, rule_func: Callable[[Exchange], Any]):
        """Add rule for annotating exchanges.
        
        Args:
            name: Annotation name
            rule_func: Function that takes Exchange and returns:
                - True/False for boolean annotations
                - dict for multiple related annotations
                - any other value for simple value annotations
                - None/False to skip annotation
        """
        self.exchange_rules[name] = rule_func
    
    def add_conversation_rule(self, name: str, rule_func: Callable[[Conversation], Any]):
        """Add rule for annotating conversations.
        
        Args:
            name: Annotation name  
            rule_func: Function that takes Conversation and returns annotation value(s)
        """
        self.conversation_rules[name] = rule_func
    
    def annotate_exchange(self, exchange: Exchange) -> Exchange:
        """Apply all exchange rules to annotate an exchange."""
        for name, rule_func in self.exchange_rules.items():
            try:
                result = rule_func(exchange)
                self._apply_annotation_result(exchange.annotations, name, result)
            except Exception as e:
                # Skip failed rules - could add logging here
                pass
        
        return exchange
    
    def annotate_conversation(self, conversation: Conversation) -> Conversation:
        """Apply all conversation rules to annotate a conversation."""
        for name, rule_func in self.conversation_rules.items():
            try:
                result = rule_func(conversation)
                self._apply_annotation_result(conversation.annotations, name, result)
            except Exception as e:
                # Skip failed rules - could add logging here  
                pass
        
        return conversation
    
    def _apply_annotation_result(self, annotations: Dict[str, Any], 
                               name: str, result: Any) -> None:
        """Apply the result of a rule function to the annotations dict."""
        if result is None or result is False:
            # Skip annotation
            return
        
        if isinstance(result, bool) and result:
            # Simple boolean flag
            annotations[name] = True
            
        elif isinstance(result, dict):
            # Multiple related annotations - prefix with rule name
            for key, value in result.items():
                annotations[f"{name}_{key}"] = value
                
        elif isinstance(result, list):
            # Handle list results (e.g., multiple tags from one rule)
            if len(result) == 1:
                # Single item - treat as simple value
                annotations[name] = result[0]
            else:
                # Multiple items - store as list
                annotations[name] = result
                
        else:
            # Simple value annotation
            annotations[name] = result
    
    def get_rule_names(self) -> Dict[str, list[str]]:
        """Get names of all registered rules."""
        return {
            'exchange_rules': list(self.exchange_rules.keys()),
            'conversation_rules': list(self.conversation_rules.keys())
        }


class AnnotationPipeline:
    """Pipeline for applying multiple annotators in sequence."""
    
    def __init__(self, annotators: list[Annotator] | None = None):
        self.annotators = annotators or []
    
    def add_annotator(self, annotator: Annotator):
        """Add an annotator to the pipeline."""
        self.annotators.append(annotator)
    
    def annotate_exchange(self, exchange: Exchange) -> Exchange:
        """Apply all annotators to an exchange."""
        for annotator in self.annotators:
            exchange = annotator.annotate_exchange(exchange)
        return exchange
    
    def annotate_conversation(self, conversation: Conversation) -> Conversation:
        """Apply all annotators to a conversation."""
        # First annotate all exchanges
        for exchange in conversation.exchanges:
            self.annotate_exchange(exchange)
        
        # Then apply conversation-level rules
        for annotator in self.annotators:
            conversation = annotator.annotate_conversation(conversation)
        
        return conversation


# Utility functions for common annotation patterns

def create_boolean_rule(check_func: Callable[[Exchange], bool]) -> Callable[[Exchange], bool]:
    """Create a simple boolean annotation rule."""
    return check_func

def create_counting_rule(item_func: Callable[[Exchange], list]) -> Callable[[Exchange], int]:
    """Create a rule that counts items."""
    def counting_rule(exchange: Exchange) -> int:
        items = item_func(exchange)
        return len(items) if items else 0
    return counting_rule

def create_categorizing_rule(value_func: Callable[[Exchange], Any], 
                           categories: Dict[Any, str]) -> Callable[[Exchange], Dict[str, Any]]:
    """Create a rule that categorizes a value."""
    def categorizing_rule(exchange: Exchange) -> Dict[str, Any]:
        value = value_func(exchange)
        category = categories.get(value, 'unknown')
        return {'value': value, 'category': category}
    return categorizing_rule

def create_threshold_rule(value_func: Callable[[Exchange], float], 
                         thresholds: Dict[str, float]) -> Callable[[Exchange], Dict[str, Any]]:
    """Create a rule that applies thresholds to a numeric value."""
    def threshold_rule(exchange: Exchange) -> Dict[str, Any]:
        value = value_func(exchange)
        
        # Find appropriate category based on thresholds
        category = 'lowest'
        for cat_name, threshold in sorted(thresholds.items(), key=lambda x: x[1]):
            if value >= threshold:
                category = cat_name
        
        return {'value': value, 'category': category}
    return threshold_rule
