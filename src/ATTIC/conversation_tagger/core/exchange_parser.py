# conversation_tagger/core/exchange_parser.py (UPDATED)
"""
Parser to extract exchanges from conversation data.
"""

from typing import Dict, Any, List
from .exchange import Exchange


class ExchangeParser:
    """Parses conversations into exchanges."""
    
    def __init__(self):
        # Patterns that indicate continuation prompts
        self.continuation_patterns = [
            'continue', 'more', 'keep going', 'go on', 'next', 'and then',
            'what else', 'anything else', 'tell me more', 'expand',
            'keep writing', 'finish', 'complete', 'continue writing'
        ]
    
    def parse_conversation(self, conversation: Dict[str, Any]) -> List[Exchange]:
        """Parse a conversation into a list of exchanges."""
        mapping = conversation.get('mapping', {})
        
        # Extract and sort all messages chronologically
        all_messages = []
        for node_id, node in mapping.items():
            message = node.get('message')
            if message and message.get('author'):
                create_time = message.get('create_time', 0)
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
        
        for i, message in enumerate(messages):
            author_role = message.get('author', {}).get('role', '')
            
            if author_role == 'user':
                # Check if this is a continuation of the current exchange
                if (current_user_messages and current_assistant_messages and 
                    self._is_continuation_prompt(message)):
                    # Add to current exchange
                    current_user_messages.append(message)
                else:
                    # Start new exchange (finish previous if exists)
                    if current_user_messages:
                        exchange = self._create_exchange(
                            current_user_messages, current_assistant_messages,
                            conversation_id, exchange_index
                        )
                        exchanges.append(exchange)
                        exchange_index += 1
                    
                    # Start new exchange
                    current_user_messages = [message]
                    current_assistant_messages = []
            
            elif author_role == 'assistant':
                # Add to current exchange
                current_assistant_messages.append(message)
        
        # Don't forget the last exchange
        if current_user_messages:
            exchange = self._create_exchange(
                current_user_messages, current_assistant_messages,
                conversation_id, exchange_index
            )
            exchanges.append(exchange)
        
        return exchanges
    
    def _is_continuation_prompt(self, message: Dict[str, Any]) -> bool:
        """Check if a user message is a continuation prompt."""
        content = message.get('content', {})
        text = content.get('text', '').strip()
        text_lower = text.lower()
        
        # Check for quote + elaborate pattern
        if self._is_quote_elaborate_pattern(text):
            return True
        
        # Check for exact matches or patterns
        if text_lower in self.continuation_patterns:
            return True
        
        # Check for short prompts that start with continuation words
        if len(text.split()) <= 3:
            for pattern in self.continuation_patterns:
                if text_lower.startswith(pattern):
                    return True
        
        return False
    
    def _is_quote_elaborate_pattern(self, text: str) -> bool:
        """Check if text follows the quote + elaborate pattern."""
        if not text.startswith('>'):
            return False
        
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return False
        
        # Check if last line is just "elaborate"
        last_line = lines[-1].strip().lower()
        return last_line == 'elaborate'
    
    def _create_exchange(self, user_messages: List[Dict[str, Any]], 
                        assistant_messages: List[Dict[str, Any]],
                        conversation_id: str, exchange_index: int) -> Exchange:
        """Create an Exchange object from messages."""
        
        # Calculate timing
        start_time = None
        end_time = None
        
        if user_messages:
            start_time = user_messages[0].get('create_time')
        
        if assistant_messages:
            end_time = assistant_messages[-1].get('create_time')
        elif user_messages:
            end_time = user_messages[-1].get('create_time')
        
        exchange_id = f"{conversation_id}_exchange_{exchange_index}"
        
        return Exchange(
            exchange_id=exchange_id,
            conversation_id=conversation_id,
            user_messages=user_messages,
            assistant_messages=assistant_messages,
            start_time=start_time,
            end_time=end_time,
            exchange_index=exchange_index
        )