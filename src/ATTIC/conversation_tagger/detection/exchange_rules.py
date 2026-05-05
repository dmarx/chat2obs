# conversation_tagger/detection/exchange_rules.py (UPDATED - add quote elaborate detection)
"""
Detection rules specifically designed for exchange-level analysis.
"""

from typing import Dict, Any
from ..core.exchange import Exchange
from ..core.exchange_tagger import ExchangeTagger
from ..core.tag import Tag


def user_has_quote_elaborate(exchange: Exchange) -> bool:
    """Check if user messages contain quote+elaborate continuation pattern."""
    for message in exchange.user_messages:
        content = message.get('content', {})
        text = content.get('text', '').strip()
        
        if not text.startswith('>'):
            continue
        
        lines = text.split('\n')
        if len(lines) >= 2 and lines[-1].strip().lower() == 'elaborate':
            return True
    
    return False


# # Add to create_default_exchange_tagger in factory:
# def create_default_exchange_tagger() -> ExchangeTagger:
#     """Create an exchange tagger with all default rules."""
#     from ..core.exchange_tagger import ExchangeTagger
    
#     tagger = ExchangeTagger()
    
#     # ===== USER MESSAGE RULES =====
#     tagger.add_user_rule('user_has_code_blocks', user_has_code_blocks, 'User messages contain code blocks')
#     tagger.add_user_rule('user_has_attachments', user_has_attachments, 'User messages have attachments')
#     tagger.add_user_rule('user_has_error_messages', user_has_error_messages, 'User messages contain error patterns')
#     tagger.add_user_rule('user_prompt_length', user_prompt_length_category, 'User prompt length statistics')
#     tagger.add_user_rule('user_is_continuation', user_is_continuation, 'Exchange started with continuation prompt')
#     tagger.add_user_rule('user_has_quote_elaborate', user_has_quote_elaborate, 'User messages contain quote+elaborate pattern')
    
#     # ===== ASSISTANT MESSAGE RULES =====
#     tagger.add_assistant_rule('assistant_has_code_blocks', assistant_has_code_blocks, 'Assistant messages contain code blocks')
#     tagger.add_assistant_rule('assistant_has_wiki_links', assistant_has_wiki_links, 'Assistant messages contain wiki-style links')
#     tagger.add_assistant_rule('assistant_has_latex_math', assistant_has_latex_math, 'Assistant messages contain mathematical formulas')
#     tagger.add_assistant_rule('assistant_response_length', assistant_response_length_category, 'Assistant response length statistics')
#     tagger.add_assistant_rule('assistant_has_reasoning', assistant_has_reasoning, 'Assistant messages contain reasoning/thinking')
    
#     # ===== EXCHANGE-LEVEL RULES =====
#     tagger.add_exchange_rule('exchange_is_coding_focused', exchange_is_coding_focused, 'Exchange focuses on coding topics')
#     tagger.add_exchange_rule('exchange_is_wiki_article_focused', exchange_is_wiki_article_focused, 'Exchange focuses on wiki/documentation content')
#     tagger.add_exchange_rule('exchange_has_error_resolution', exchange_has_error_resolution, 'Exchange involves error troubleshooting')
#     tagger.add_exchange_rule('interaction_pattern', exchange_interaction_pattern, 'Pattern of interaction in this exchange')
#     tagger.add_exchange_rule('exchange_timing', exchange_timing_stats, 'Timing statistics for the exchange')
    
#     # ===== SUPPLEMENTAL RULES =====
#     tagger.add_supplemental_rule('coding_exchange', 
#                                 lambda exch, tags: any(tag.name in ['user_has_code_blocks', 'assistant_has_code_blocks', 'exchange_is_coding_focused'] for tag in tags),
#                                 'Exchange involves coding activity')
    
#     tagger.add_supplemental_rule('wiki_exchange',
#                                 lambda exch, tags: any(tag.name in ['assistant_has_wiki_links', 'exchange_is_wiki_article_focused'] for tag in tags),
#                                 'Exchange involves wiki/documentation content')
    
#     tagger.add_supplemental_rule('elaboration_exchange',
#                                 lambda exch, tags: any(tag.name == 'user_has_quote_elaborate' for tag in tags),
#                                 'Exchange contains quote+elaborate continuation pattern')
    
#     return tagger