# conversation_tagger/factory.py
"""
Factory to create configured tagger with improved exchange handling.
"""
from .core.tagger import ConversationTagger
from .core.detection import EXCHANGE_RULES, CONVERSATION_RULES


def create_default_tagger() -> ConversationTagger:
    """Create a basic tagger with example rules for the new exchange design."""
    tagger = ConversationTagger()
    for rule_name, rule_func in EXCHANGE_RULES.items():
        tagger.add_exchange_rule(rule_name, rule_func)   
    for rule_name, rule_func in CONVERSATION_RULES.items():
        tagger.add_conversation_rule(rule_name, rule_func)
    
    return tagger
