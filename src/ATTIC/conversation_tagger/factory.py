# conversation_tagger/factory.py (UPDATED)
"""
Updated factory function that creates exchange-enabled tagger.
"""

from .core.tagger import ConversationTagger

# Import detection functions for both levels
from .detection.content import *
from .detection.code_indicators import *
from .detection.wiki_markdown import *
from .detection.structured_tags import *
from .detection.exchange_rules import *


def create_default_tagger() -> ConversationTagger:
    """
    Create a conversation tagger with all default rules.
    
    Args:
        use_exchange_analysis: If True, uses exchange-based analysis (recommended).
                              If False, uses legacy conversation-level analysis only.
    """
    tagger = ConversationTagger(use_exchange_analysis=True)
    return _configure_exchange_based_tagger(tagger)



def _configure_exchange_based_tagger(tagger: ConversationTagger):
    """Configure tagger with exchange-based rules."""
    
    # ===== EXCHANGE-LEVEL RULES =====
    
    # User message rules
    tagger.add_user_rule('user_has_code_blocks', user_has_code_blocks, 'User messages contain code blocks')
    tagger.add_user_rule('user_has_attachments', user_has_attachments, 'User messages have attachments')
    tagger.add_user_rule('user_has_error_messages', user_has_error_messages, 'User messages contain error patterns')
    tagger.add_user_rule('user_prompt_length', user_prompt_length_category, 'User prompt length statistics')
    tagger.add_user_rule('user_is_continuation', user_is_continuation, 'Exchange started with continuation prompt')
    tagger.add_user_rule('user_has_quote_elaborate', user_has_quote_elaborate, 'User messages contain quote+elaborate pattern')
    
    # Assistant message rules
    tagger.add_assistant_rule('assistant_has_code_blocks', assistant_has_code_blocks, 'Assistant messages contain code blocks')
    tagger.add_assistant_rule('assistant_has_wiki_links', assistant_has_wiki_links, 'Assistant messages contain wiki-style links')
    tagger.add_assistant_rule('assistant_has_latex_math', assistant_has_latex_math, 'Assistant messages contain mathematical formulas')
    tagger.add_assistant_rule('assistant_response_length', assistant_response_length_category, 'Assistant response length statistics')
    tagger.add_assistant_rule('assistant_has_reasoning', assistant_has_reasoning, 'Assistant messages contain reasoning/thinking')
    
    # Exchange-level rules
    tagger.add_exchange_rule('exchange_is_coding_focused', exchange_is_coding_focused, 'Exchange focuses on coding topics')
    tagger.add_exchange_rule('exchange_is_wiki_article_focused', exchange_is_wiki_article_focused, 'Exchange focuses on wiki/documentation content')
    tagger.add_exchange_rule('exchange_has_error_resolution', exchange_has_error_resolution, 'Exchange involves error troubleshooting')
    tagger.add_exchange_rule('interaction_pattern', exchange_interaction_pattern, 'Pattern of interaction in this exchange')

    
    # Exchange supplemental rules
    tagger.add_exchange_supplemental_rule('coding_exchange', 
                                         lambda exch, tags: any(tag.name in ['user_has_code_blocks', 'assistant_has_code_blocks', 'exchange_is_coding_focused'] for tag in tags),
                                         'Exchange involves coding activity')
    
    tagger.add_exchange_supplemental_rule('wiki_exchange',
                                         lambda exch, tags: any(tag.name in ['assistant_has_wiki_links', 'exchange_is_wiki_article_focused'] for tag in tags),
                                         'Exchange involves wiki/documentation content')
    
    tagger.add_exchange_supplemental_rule('elaboration_exchange',
                                         lambda exch, tags: any(tag.name == 'user_has_quote_elaborate' for tag in tags),
                                         'Exchange contains quote+elaborate continuation pattern')
    
    # ===== CONVERSATION-LEVEL SUPPLEMENTAL RULES =====
    
    # High-level conversation classifications based on aggregated exchange data
    tagger.add_supplemental_rule('primarily_coding_conversation',
                                lambda conv, tags: any(tag.name == 'has_exchange_is_coding_focused' and tag.attributes.get('level') in ['often', 'always'] for tag in tags),
                                'Conversation is primarily about coding (based on exchange frequency)')
    
    tagger.add_supplemental_rule('primarily_wiki_conversation',
                                lambda conv, tags: any(tag.name == 'has_exchange_is_wiki_article_focused' and tag.attributes.get('level') in ['often', 'always'] for tag in tags),
                                'Conversation is primarily about wiki/documentation content')
    
    tagger.add_supplemental_rule('mixed_conversation',
                                lambda conv, tags: (any(tag.name == 'has_exchange_is_coding_focused' for tag in tags) and 
                                                   any(tag.name == 'has_exchange_is_wiki_article_focused' for tag in tags)),
                                'Conversation mixes coding and wiki/documentation topics')
    
    tagger.add_supplemental_rule('elaboration_heavy_conversation',
                                lambda conv, tags: any(tag.name == 'uses_continuations' and tag.attributes.get('continuation_frequency', 0) > 0.3 for tag in tags),
                                'Conversation makes heavy use of elaboration/continuation patterns')




def has_code_blocks_conversation_level(conversation: Dict[str, Any]) -> bool:
    """Legacy conversation-level code block detection."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        content = message.get('content', {})
        text = content.get('text', '')
        parts = content.get('parts', [])
        all_text = text + ' ' + ' '.join(str(p) for p in parts if isinstance(p, str))
        
        if '```' in all_text:
            return True
    
    return False
