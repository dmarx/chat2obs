# src/conversation_tagger/core/exchange_parser.py
"""
Parse conversations into exchanges using a two-step approach:
1. Segment into dyadic USER-ASSISTANT chunks
2. Merge chunks when continuations are detected
"""

from typing import Dict, Any, List, Callable
from .exchange import Exchange
from .conversation import Conversation

from .message import Message, MessageOpenAI
from .exchange_tagger import ExchangeTagger


def quote_elaborate_rule(previous_exchange: Exchange, current_exchange: Exchange) -> bool:
    """Check for quote + elaborate continuation pattern."""
    user_messages = current_exchange.get_user_messages()
    if not user_messages:
        return False
    
    first_user_message = user_messages[0]
    #content = first_user_message.get('content', {})
    #text = content.get('text', '').strip()
    text = first_user_message.content
    
    return (text.startswith('>') and 
            len(text.split('\n')) >= 2 and 
            text.split('\n')[-1].strip().lower() == 'elaborate')


def simple_continuation_rule(previous_exchange: Exchange, current_exchange: Exchange) -> bool:
    """Check for simple continuation keywords."""
    continuation_patterns = [
        'continue', 'more', 'keep going', 'go on', 'next', 
        'tell me more', 'expand', 'keep writing', 'finish'
    ]
    
    user_messages = current_exchange.get_user_messages()
    if not user_messages:
        return False
    
    first_user_message = user_messages[0]
    text = first_user_message.content
    
    return text in continuation_patterns


def short_continuation_rule(previous_exchange: Exchange, current_exchange: Exchange) -> bool:
    """Check for short prompts starting with continuation words."""
    continuation_starters = [
        'continue', 'more', 'keep going', 'go on', 'next', 
        'tell me more', 'expand', 'keep writing', 'finish', 'elaborate','do go on', 'make it so', 'yes', 'please', 'do it'
    ]
    
    user_messages = current_exchange.get_user_messages()
    if not user_messages:
        return False
    
    first_user_message = user_messages[0]
    text = first_user_message.content
    
    if len(text.split()) <= 3:
        for pattern in continuation_starters:
            if text.startswith(pattern):
                return True
    
    return False


class ExchangeParser:
    """Parses conversations into tagged exchanges."""
    
    def __init__(self, exchange_tagger: ExchangeTagger | None = None):
        self.continuation_rules: List[Callable[[Exchange, Exchange], bool]] = [
            quote_elaborate_rule,
            simple_continuation_rule,
            short_continuation_rule
        ]
        if exchange_tagger is None:
            exchange_tagger = ExchangeTagger()
        self.exchange_tagger = exchange_tagger

    def add_continuation_rule(self, rule_function: Callable[[Exchange, Exchange], bool]):
        """Add a new continuation detection rule."""
        self.continuation_rules.append(rule_function)

    def get_messages(self, conversation: dict):
        raise NotImplementedError

    def parse_conversation(self, conversation: Dict[str, Any]) -> Conversation:
        """Parse a conversation into a Conversation object with fully-tagged exchanges."""
        messages = self.get_messages(conversation)
        
        conversation_id = conversation.get('conversation_id')
        title = conversation.get('title', '')
        
        dyadic_exchanges = self._create_dyadic_exchanges(messages, conversation_id)
        merged_exchanges = self._merge_continuations(dyadic_exchanges)
        
        # Tag exchanges as they're finalized
        if self.exchange_tagger:
            tagged_exchanges = []
            for exchange in merged_exchanges:
                tagged_exchange = self.exchange_tagger.tag_exchange(exchange)
                tagged_exchanges.append(tagged_exchange)
        else:
            tagged_exchanges = merged_exchanges
        
        # Create and return Conversation object
        conv = Conversation(
            conversation_id=conversation_id,
            title=title,
            exchanges=tagged_exchanges,
            raw=conversation,
        )
        
        return conv
    
    def _create_dyadic_exchanges(self, messages: list[Message], 
                                conversation_id: str) -> List[Exchange]:
        """Step 1: Create simple USER-ASSISTANT dyadic exchanges."""
        dyadic_exchanges = []
        current_pair = []
        
        for message in messages:
            
            if message.author_role in ['user', 'assistant']:
                current_pair.append(message)
                
                # If we have a user->assistant pair, create exchange
                if (len(current_pair) == 2 and 
                    current_pair[0].author_role == 'user' and
                    current_pair[1].author_role == 'assistant'):
                    
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
            
            # Check if next exchange is a continuation using any rule
            should_merge = any(rule(current_exchange, next_exchange) 
                             for rule in self.continuation_rules)
            
            if should_merge:
                # Merge with current exchange (time-ordering handled by __add__)
                current_exchange = current_exchange + next_exchange
            else:
                # Finalize current exchange and start new one
                merged_exchanges.append(current_exchange)
                current_exchange = next_exchange
        
        # Add the final exchange
        merged_exchanges.append(current_exchange)
        
        return merged_exchanges


# TODO: 
# * Attach appropriate Message type to parser
#   - currently, determination of source delegated to
#     `message.msg_factory`, which is invoked in Exchange.create
# * Rename to ConversationParser?
class ExchangeParserOAI(ExchangeParser):
    def get_messages(self, conversation: dict):
        mapping = conversation.get('mapping', {})
        all_messages = []
        for node_id, node in mapping.items():
            message = node.get('message')
            if message and message.get('author'):
                create_time = message.get('create_time') or 0
                all_messages.append((create_time, message))
        all_messages.sort(key=lambda x: x[0])
        return [MessageOpenAI(data=msg) for _, msg in all_messages] 