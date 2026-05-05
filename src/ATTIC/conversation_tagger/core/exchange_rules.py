# conversation_tagger/detection/exchange_rules.py
"""
Detection rules specifically designed for exchange-level analysis.
"""

from typing import Dict, Any
from ..core.exchange import Exchange
from ..core.tag import Tag


# User message detection rules
def user_has_code_blocks(exchange: Exchange) -> bool:
    """Check if user messages contain code blocks."""
    user_text = exchange.get_user_text()
    return '```' in user_text


def user_has_attachments(exchange: Exchange) -> bool:
    """Check if user messages have attachments."""
    for message in exchange.user_messages:
        metadata = message.get('metadata', {})
        if metadata.get('attachments'):
            return True
    return False


def user_has_error_messages(exchange: Exchange) -> bool:
    """Check if user messages contain error patterns."""
    user_text = exchange.get_user_text().lower()
    error_patterns = [
        'error:', 'traceback', 'exception:', 'failed:', 'cannot', 'not working',
        'broken', 'issue', 'problem', 'bug', 'crash', 'threw an error'
    ]
    return any(pattern in user_text for pattern in error_patterns)


def user_prompt_length_category(exchange: Exchange) -> Tag:
    """Categorize user prompt length."""
    user_text = exchange.get_user_text()
    length = len(user_text)
    
    if length < 50:
        category = 'very_short'
    elif length < 200:
        category = 'short'
    elif length < 1000:
        category = 'medium'
    elif length < 3000:
        category = 'long'
    else:
        category = 'very_long'
    
    return Tag('user_prompt_length', length=length, category=category)


def user_is_continuation(exchange: Exchange) -> bool:
    """Check if this exchange started with a continuation prompt."""
    return exchange.has_continuations()


# Assistant message detection rules
def assistant_has_code_blocks(exchange: Exchange) -> bool:
    """Check if assistant messages contain code blocks."""
    assistant_text = exchange.get_assistant_text()
    return '```' in assistant_text


def assistant_has_wiki_links(exchange: Exchange) -> bool:
    """Check if assistant messages contain wiki-style links."""
    assistant_text = exchange.get_assistant_text()
    return '[[' in assistant_text and ']]' in assistant_text


def assistant_has_latex_math(exchange: Exchange) -> bool:
    """Check if assistant messages contain mathematical formulas."""
    assistant_text = exchange.get_assistant_text()
    
    math_indicators = [
        ('$' in assistant_text and assistant_text.count('$') >= 2),
        '$$' in assistant_text,
        ('\\(' in assistant_text and '\\)' in assistant_text),
        any(cmd in assistant_text for cmd in ['\\frac', '\\sum', '\\int', '\\sqrt'])
    ]
    
    return any(math_indicators)


def assistant_response_length_category(exchange: Exchange) -> Tag:
    """Categorize assistant response length."""
    assistant_text = exchange.get_assistant_text()
    length = len(assistant_text)
    
    if length < 100:
        category = 'very_short'
    elif length < 500:
        category = 'short'
    elif length < 2000:
        category = 'medium'
    elif length < 5000:
        category = 'long'
    else:
        category = 'very_long'
    
    return Tag('assistant_response_length', length=length, category=category)


def assistant_has_reasoning(exchange: Exchange) -> bool:
    """Check if assistant messages contain reasoning/thinking content."""
    for message in exchange.assistant_messages:
        content = message.get('content', {})
        if content.get('thoughts'):
            return True
    return False


# Exchange-level detection rules
def exchange_is_coding_focused(exchange: Exchange) -> bool:
    """Check if the entire exchange is focused on coding."""
    return (user_has_code_blocks(exchange) or 
            assistant_has_code_blocks(exchange) or
            exchange.is_code_focused())


def exchange_is_wiki_article_focused(exchange: Exchange) -> bool:
    """Check if exchange is focused on wiki/documentation content."""
    user_text = exchange.get_user_text()
    assistant_text = exchange.get_assistant_text()
    
    wiki_indicators = [
        '[[' in user_text or '[[' in assistant_text,
        'write an article' in user_text.lower(),
        'create a wiki' in user_text.lower(),
        len(assistant_text) > 1000 and ('# ' in assistant_text or '## ' in assistant_text)
    ]
    
    return any(wiki_indicators)


def exchange_has_error_resolution(exchange: Exchange) -> bool:
    """Check if exchange involves error troubleshooting."""
    return (user_has_error_messages(exchange) and 
            len(exchange.assistant_messages) > 0)


def exchange_interaction_pattern(exchange: Exchange) -> Tag:
    """Determine the interaction pattern of this exchange."""
    user_stats = exchange.get_user_prompt_stats()
    assistant_stats = exchange.get_assistant_response_stats()
    
    if user_stats['message_count'] > 1:
        pattern = 'multi_turn'
    elif user_stats['length'] > 2000:
        pattern = 'context_heavy'
    elif assistant_stats['length'] > 3000:
        pattern = 'detailed_response'
    elif user_stats['length'] < 50 and assistant_stats['length'] < 200:
        pattern = 'quick_qa'
    else:
        pattern = 'standard'
    
    return Tag('interaction_pattern', 
               pattern=pattern,
               user_messages=user_stats['message_count'],
               assistant_messages=assistant_stats['message_count'])


# def exchange_timing_stats(exchange: Exchange) -> Tag:
#     """Calculate timing statistics for the exchange."""
#     if exchange.start_time and exchange.end_time:
#         duration = exchange.end_time - exchange.start_time
        
#         if duration < 30:
#             speed = 'very_fast'
#         elif duration < 120:
#             speed = 'fast'
#         elif duration < 300:
#             speed = 'medium'
#         elif duration < 600:
#             speed = 'slow'
#         else:
#             speed = 'very_slow'
        
#         return Tag('exchange_timing', 
#                    duration_seconds=duration,
#                    speed_category=speed)
    
#     return Tag('exchange_timing', duration_seconds=0, speed_category='unknown')