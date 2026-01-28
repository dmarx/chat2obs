# conversation_tagger/factory.py
"""
Factory to create configured tagger with improved exchange handling.
"""
#from ATTIC.conversation_tagger.core import exchange_parser
from .core.tagger import ConversationTagger
from .core.detection import EXCHANGE_RULES, CONVERSATION_RULES

# todo: use enum for source types
def create_default_tagger(source="oai") -> ConversationTagger:
    """Create a basic tagger with example rules for the new exchange design."""

    if source == "oai":
        from .core.exchange_parser import ExchangeParserOAI
        exchange_parser = ExchangeParserOAI()
    elif source == "claude":
        from .core.exchange_parser import ExchangeParserClaude
        exchange_parser = ExchangeParserClaude()
    else:
        raise ValueError(f"Unsupported source: {source}")
    
    tagger = ConversationTagger(exchange_parser=exchange_parser)
    for rule_name, rule_func in EXCHANGE_RULES.items():
        tagger.add_exchange_rule(rule_name, rule_func)   
    for rule_name, rule_func in CONVERSATION_RULES.items():
        tagger.add_conversation_rule(rule_name, rule_func)
    
    return tagger
