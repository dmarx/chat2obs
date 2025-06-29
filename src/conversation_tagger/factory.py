# conversation_tagger/factory.py
"""
Factory to create configured tagger.
"""

from .core.tagger import ConversationTagger


def create_default_tagger() -> ConversationTagger:
    """Create a basic tagger with minimal example rules."""
    tagger = ConversationTagger()
    
    # Example user rule
    def user_has_code_blocks(exchange):
        return '```' in exchange.get_user_text()
    
    # Example assistant rule  
    def assistant_has_code_blocks(exchange):
        return '```' in exchange.get_assistant_text()
    
    # Example exchange rule
    def has_quote_elaborate(exchange):
        for msg in exchange.user_messages:
            text = msg.get('content', {}).get('text', '')
            if (text.startswith('>') and 
                text.split('\n')[-1].strip().lower() == 'elaborate'):
                return True
        return False
    
    tagger.add_user_rule('user_has_code_blocks', user_has_code_blocks)
    tagger.add_assistant_rule('assistant_has_code_blocks', assistant_has_code_blocks)
    tagger.add_exchange_rule('has_quote_elaborate', has_quote_elaborate)
    
    return tagger