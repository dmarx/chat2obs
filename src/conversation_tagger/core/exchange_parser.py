# conversation_tagger/core/exchange_parser.py
"""
Parse conversations into exchanges using a two-step approach:
1. Segment into dyadic USER-ASSISTANT chunks
2. Merge chunks when continuations are detected
"""

from typing import Dict, Any, List
from .exchange import Exchange


class ExchangeParser:
    """Parses conversations into exchanges using dyadic segmentation + merging."""
    
    def __init__(self):
        self.continuation_patterns = [
            'continue', 'more', 'keep going', 'go on', 'next', 
            'tell me more', 'expand', 'keep writing', 'finish'
        ]
    
    def parse_conversation(self, conversation: Dict[str, Any]) -> List[Exchange]:
        """Parse a conversation into exchanges using two-step approach."""
        mapping = conversation.get('mapping', {})
        
        # Extract and sort messages
        all_messages = []
        for node_id, node in mapping.items():
            message = node.get('message')
            if message and message.get('author'):
                create_time = message.get('create_time') or 0
                all_messages.append((create_time, message))
        
        all_messages.sort(key=lambda x: x[0])
        messages = [msg for _, msg in all_messages]
        
        conversation_id = conversation.get('conversation_id', 'unknown')
        
        # Step 1: Create dyadic exchanges
        dyadic_exchanges = self._create_dyadic_exchanges(messages, conversation_id)
        
        # Step 2: Merge exchanges when continuations are detected
        merged_exchanges = self._merge_continuations(dyadic_exchanges)
        
        return merged_exchanges
    
    def _create_dyadic_exchanges(self, messages: List[Dict[str, Any]], 
                                conversation_id: str) -> List[Exchange]:
        """Step 1: Create simple USER-ASSISTANT dyadic exchanges."""
        dyadic_exchanges = []
        current_pair = []
        
        for message in messages:
            author_role = message.get('author', {}).get('role', '')
            
            if author_role in ['user', 'assistant']:
                current_pair.append(message)
                
                # If we have a user->assistant pair, create exchange
                if (len(current_pair) == 2 and 
                    current_pair[0].get('author', {}).get('role') == 'user' and
                    current_pair[1].get('author', {}).get('role') == 'assistant'):
                    
                    exchange = Exchange.create(conversation_id, current_pair.copy())
                    dyadic_exchanges.append(exchange)
                    current_pair = []
                
                # Handle cases where we have multiple user messages or assistant messages
                elif len(current_pair) > 2:
                    # Create exchange with what we have so far
                    exchange = Exchange.create(conversation_id, current_pair.copy())
                    dyadic_exchanges.append(exchange)
                    current_pair = []
        
        # Handle any remaining messages
        if current_pair:
            exchange = Exchange.create(conversation_id, current_pair)
            dyadic_exchanges.append(exchange)
        
        return dyadic_exchanges
    
    def _merge_continuations(self, dyadic_exchanges: List[Exchange]) -> List[Exchange]:
        """Step 2: Merge exchanges when continuation patterns are detected."""
        if not dyadic_exchanges:
            return []
        
        merged_exchanges = []
        current_exchange = dyadic_exchanges[0]
        
        for i in range(1, len(dyadic_exchanges)):
            next_exchange = dyadic_exchanges[i]
            
            # Check if next exchange starts with a continuation
            if self._is_continuation_exchange(next_exchange):
                # Merge with current exchange (time-ordering handled by __add__)
                current_exchange = current_exchange + next_exchange
            else:
                # Finalize current exchange and start new one
                merged_exchanges.append(current_exchange)
                current_exchange = next_exchange
        
        # Add the final exchange
        merged_exchanges.append(current_exchange)
        
        return merged_exchanges
    
    def _is_continuation_exchange(self, exchange: Exchange) -> bool:
        """Check if an exchange represents a continuation of the previous exchange."""
        user_messages = exchange.get_user_messages()
        
        if not user_messages:
            return False
        
        # Check the first user message in this exchange
        first_user_message = user_messages[0]
        content = first_user_message.get('content', {})
        text = content.get('text', '').strip()
        text_lower = text.lower()
        
        # Quote + elaborate pattern
        if (text.startswith('>') and 
            len(text.split('\n')) >= 2 and 
            text.split('\n')[-1].strip().lower() == 'elaborate'):
            return True
        
        # Simple continuation patterns
        if text_lower in self.continuation_patterns:
            return True
        
        # Short prompts starting with continuation words
        if len(text.split()) <= 3:
            for pattern in self.continuation_patterns:
                if text_lower.startswith(pattern):
                    return True
        
        return False
