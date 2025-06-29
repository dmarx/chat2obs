# conversation_tagger/factory.py
"""
Factory to create configured tagger with improved exchange handling.
"""

from .core.tagger import ConversationTagger
from .core.exchange import Exchange

def create_default_tagger() -> ConversationTagger:
    """Create a basic tagger with example rules for the new exchange design."""
    tagger = ConversationTagger()
    
    # # Add custom continuation rule example
    # def numeric_follow_up_rule(previous_exchange: Exchange, current_exchange: Exchange) -> bool:
    #     """Merge exchanges where current starts with a number (like '2.' or 'step 2')."""
    #     user_messages = current_exchange.get_user_messages()
    #     if not user_messages:
    #         return False
        
    #     text = user_messages[0].get('content', {}).get('text', '').strip().lower()
    #     return (text.startswith(('1.', '2.', '3.', '4.', '5.')) or
    #             text.startswith(('step ', 'part ', 'section ')))
    
    # tagger.exchange_parser.add_continuation_rule(numeric_follow_up_rule)
    
    # # Example user rule
    # def user_has_code_blocks(exchange):
    #     """Check if user messages contain code blocks."""
    #     return '```' in exchange.get_user_text()
    
    # # Example assistant rule  
    # def assistant_has_code_blocks(exchange):
    #     """Check if assistant messages contain code blocks."""
    #     return '```' in exchange.get_assistant_text()
    
    # # Example exchange rule using new structure
    # may as well apply this tag when merging exchanges...?
    def has_quote_elaborate(exchange):
        """Check for quote + elaborate continuation pattern."""
        user_messages = exchange.get_user_messages()
        for msg in user_messages:
            text = msg.get('content', {}).get('text', '')
            if (text.startswith('>') and 
                len(text.split('\n')) >= 2 and
                text.split('\n')[-1].strip().lower() == 'elaborate'):
                return True
        return False
    
    # New rule leveraging the improved design
    def has_multiple_turns(exchange):
        """Check if exchange has multiple back-and-forth turns."""
        return len(exchange.messages) > 2
    
    # Rule to detect question vs statement exchanges
    def exchange_type(exchange):
        """Classify exchange as question or statement."""
        user_text = exchange.get_user_text()
        if '?' in user_text or user_text.lower().startswith(('how', 'what', 'why', 'when', 'where', 'can you')):
            return Tag('exchange_type', type='question')
        elif any(word in user_text.lower() for word in ['please', 'could you', 'would you']):
            return Tag('exchange_type', type='request')
        else:
            return Tag('exchange_type', type='statement')
    
    # Register all rules
    #tagger.add_user_rule('user_has_code_blocks', user_has_code_blocks)
    #tagger.add_assistant_rule('assistant_has_code_blocks', assistant_has_code_blocks)
    #tagger.add_exchange_rule('has_quote_elaborate', has_quote_elaborate)
    tagger.add_exchange_rule('has_multiple_turns', has_multiple_turns)
    #tagger.add_exchange_rule('mentions_programming_language', mentions_programming_language)
    tagger.add_exchange_rule('exchange_type', exchange_type)
    
    return tagger
