# src/conversation_tagger/core/parser.py
"""
Parse conversations into exchanges with annotation support.
Simplified version with cleaner continuation detection.
"""

from typing import Dict, Any, List, Callable
from .models import Exchange, Conversation
from .annotator import Annotator


def simple_continuation_rule(previous_exchange: Exchange, current_exchange: Exchange) -> bool:
    """Check for simple continuation keywords."""
    continuation_patterns = [
        'continue', 'more', 'keep going', 'go on', 'next', 
        'tell me more', 'expand', 'keep writing', 'finish',
        'elaborate', 'do go on', 'make it so', 'yes', 'please', 'do it'
    ]
    
    user_messages = current_exchange.get_user_messages()
    if not user_messages:
        return False
    
    first_user_message = user_messages[0]
    from .models import extract_message_text
    text = extract_message_text(first_user_message).strip().lower()
    
    # Check for exact matches or short prompts starting with continuation words
    if text in continuation_patterns:
        return True
    
    # Check for short prompts (3 words or less) starting with continuation words
    if len(text.split()) <= 3:
        for pattern in continuation_patterns:
            if text.startswith(pattern):
                return True
    
    return False


def quote_elaborate_rule(previous_exchange: Exchange, current_exchange: Exchange) -> bool:
    """Check for quote + elaborate continuation pattern."""
    user_messages = current_exchange.get_user_messages()
    if not user_messages:
        return False
    
    first_user_message = user_messages[0]
    from .models import extract_message_text
    text = extract_message_text(first_user_message).strip()
    
    return (text.startswith('>') and 
            len(text.split('\n')) >= 2 and 
            text.split('\n')[-1].strip().lower() == 'elaborate')


class ExchangeParser:
    """Parse conversations into exchanges with annotation support."""
    
    def __init__(self, annotator: Annotator | None = None):
        self.annotator = annotator
        self.continuation_rules: List[Callable[[Exchange, Exchange], bool]] = [
            simple_continuation_rule,
            quote_elaborate_rule
        ]
    
    def add_continuation_rule(self, rule_function: Callable[[Exchange, Exchange], bool]):
        """Add a custom continuation detection rule."""
        self.continuation_rules.append(rule_function)
    
    def parse_conversation(self, conversation_data: Dict[str, Any]) -> Conversation:
        """Parse conversation data into annotated Conversation object."""
        # Extract and sort messages
        messages = self._extract_messages(conversation_data)
        conversation_id = conversation_data.get('conversation_id', 'unknown')
        
        # Create initial dyadic exchanges
        dyadic_exchanges = self._create_dyadic_exchanges(messages, conversation_id)
        
        # Merge exchanges based on continuation patterns
        merged_exchanges = self._merge_continuations(dyadic_exchanges)
        
        # Annotate exchanges if annotator provided
        if self.annotator:
            for exchange in merged_exchanges:
                self.annotator.annotate_exchange(exchange)
        
        # Create conversation object
        conversation = Conversation(
            conversation_id=conversation_id,
            title=conversation_data.get('title', ''),
            exchanges=merged_exchanges,
            raw=conversation_data
        )
        
        # Annotate conversation if annotator provided
        if self.annotator:
            self.annotator.annotate_conversation(conversation)
        
        return conversation
    
    def _extract_messages(self, conversation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and sort messages from conversation mapping."""
        mapping = conversation_data.get('mapping', {})
        all_messages = []
        
        for node in mapping.values():
            message = node.get('message')
            if message and message.get('author'):
                create_time = message.get('create_time', 0)
                all_messages.append((create_time, message))
        
        # Sort by creation time
        all_messages.sort(key=lambda x: x[0])
        return [msg for _, msg in all_messages]
    
    def _create_dyadic_exchanges(self, messages: List[Dict[str, Any]], 
                                conversation_id: str) -> List[Exchange]:
        """Create simple USER-ASSISTANT dyadic exchanges."""
        exchanges = []
        current_pair = []
        
        for message in messages:
            author_role = message.get('author', {}).get('role', '')
            
            if author_role in ['user', 'assistant']:
                current_pair.append(message)
                
                # Check if we have a complete user->assistant exchange
                if (len(current_pair) >= 2 and 
                    current_pair[0].get('author', {}).get('role') == 'user' and
                    current_pair[-1].get('author', {}).get('role') == 'assistant'):
                    
                    # Create exchange with current pair
                    exchange = Exchange.create(conversation_id, current_pair.copy())
                    exchanges.append(exchange)
                    current_pair = []
                
                # Handle overflow (more than 2 messages without completion)
                elif len(current_pair) > 10:  # Prevent runaway accumulation
                    if current_pair:
                        exchange = Exchange.create(conversation_id, current_pair.copy())
                        exchanges.append(exchange)
                    current_pair = []
        
        # Handle any remaining messages
        if current_pair:
            exchange = Exchange.create(conversation_id, current_pair)
            exchanges.append(exchange)
        
        return exchanges
    
    def _merge_continuations(self, dyadic_exchanges: List[Exchange]) -> List[Exchange]:
        """Merge exchanges when continuation patterns are detected."""
        if not dyadic_exchanges:
            return []
        
        merged_exchanges = []
        current_exchange = dyadic_exchanges[0]
        
        for i in range(1, len(dyadic_exchanges)):
            next_exchange = dyadic_exchanges[i]
            
            # Check if next exchange is a continuation using any rule
            should_merge = any(rule(current_exchange, next_exchange) 
                             for rule in self.continuation_rules)
            
            if should_merge:
                # Merge with current exchange
                current_exchange = current_exchange + next_exchange
            else:
                # Finalize current exchange and start new one
                merged_exchanges.append(current_exchange)
                current_exchange = next_exchange
        
        # Add the final exchange
        merged_exchanges.append(current_exchange)
        
        return merged_exchanges


class ConversationProcessor:
    """High-level processor that combines parsing and annotation."""
    
    def __init__(self, parser: ExchangeParser | None = None, 
                 annotator: Annotator | None = None):
        self.parser = parser or ExchangeParser()
        self.annotator = annotator
        
        # If separate annotator provided, use it with parser
        if annotator and not self.parser.annotator:
            self.parser.annotator = annotator
    
    def process_conversation(self, conversation_data: Dict[str, Any]) -> Conversation:
        """Process a conversation through parsing and annotation."""
        return self.parser.parse_conversation(conversation_data)
    
    def process_conversations(self, conversations: List[Dict[str, Any]]) -> List[Conversation]:
        """Process multiple conversations."""
        return [self.process_conversation(conv) for conv in conversations]
    
    def add_exchange_rule(self, name: str, rule_func: Callable):
        """Add an exchange annotation rule."""
        if self.parser.annotator:
            self.parser.annotator.add_exchange_rule(name, rule_func)
    
    def add_conversation_rule(self, name: str, rule_func: Callable):
        """Add a conversation annotation rule."""
        if self.parser.annotator:
            self.parser.annotator.add_conversation_rule(name, rule_func)
    
    def add_continuation_rule(self, rule_func: Callable[[Exchange, Exchange], bool]):
        """Add a continuation detection rule."""
        self.parser.add_continuation_rule(rule_func)
