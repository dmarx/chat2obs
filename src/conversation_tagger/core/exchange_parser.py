# conversation_tagger/core/exchange_parser.py
"""
Parse conversations into exchanges with continuation handling.
"""

from typing import Dict, Any, List
from .exchange import Exchange


class ExchangeParser:
    """Parses conversations into exchanges."""
    
    def __init__(self):
        self.continuation_patterns = [
            'continue', 'more', 'keep going', 'go on', 'next', 
            'tell me more', 'expand', 'keep writing', 'finish'
        ]
    
    def parse_conversation(self, conversation: Dict[str, Any]) -> List[Exchange]:
        """Parse a conversation into exchanges."""
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
        
        return self._group_into_exchanges(messages, conversation.get('conversation_id', 'unknown'))
    
    def _group_into_exchanges(self, messages: List[Dict[str, Any]], conversation_id: str) -> List[Exchange]:
        """Group messages into exchanges."""
        exchanges = []
        current_user_messages = []
        current_assistant_messages = []
        exchange_index = 0
        
        for message in messages:
            author_role = message.get('author', {}).get('role', '')
            
            if author_role == 'user':
                if (current_user_messages and current_assistant_messages and 
                    self._is_continuation(message)):
                    current_user_messages.append(message)
                else:
                    # Finish previous exchange
                    if current_user_messages:
                        exchange = Exchange(
                            exchange_id=f"{conversation_id}_exchange_{exchange_index}",
                            conversation_id=conversation_id,
                            user_messages=current_user_messages,
                            assistant_messages=current_assistant_messages,
                            exchange_index=exchange_index
                        )
                        exchanges.append(exchange)
                        exchange_index += 1
                    
                    # Start new exchange
                    current_user_messages = [message]
                    current_assistant_messages = []
            
            elif author_role == 'assistant':
                current_assistant_messages.append(message)
        
        # Final exchange
        if current_user_messages:
            exchange = Exchange(
                exchange_id=f"{conversation_id}_exchange_{exchange_index}",
                conversation_id=conversation_id,
                user_messages=current_user_messages,
                assistant_messages=current_assistant_messages,
                exchange_index=exchange_index
            )
            exchanges.append(exchange)
        
        return exchanges
    
    def _is_continuation(self, message: Dict[str, Any]) -> bool:
        """Check if message is a continuation prompt."""
        content = message.get('content', {})
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

