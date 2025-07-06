# src/conversation_tagger/core/rules.py
"""
All annotation rules for exchanges and conversations.
Uses simple return values instead of complex Tag objects.
"""

import re
from typing import Dict, Any, List
from .models import Exchange, Conversation


######################
#   Exchange Rules   #
######################

# Content Detection
def has_code_blocks(exchange: Exchange) -> bool:
    """Check for explicit code blocks (``` markdown syntax)."""
    all_texts = exchange.get_user_texts() + exchange.get_assistant_texts()
    return any('```' in text for text in all_texts)

def has_code_structure_patterns(exchange: Exchange) -> bool:
    """Check for actual code structure patterns."""
    all_texts = exchange.get_user_texts() + exchange.get_assistant_texts()
    
    for text in all_texts:
        patterns = [
            # Function definition pattern
            ('def ' in text and '(' in text and ':' in text and 'return' in text),
            # Class definition pattern  
            ('class ' in text and '(' in text and ':' in text and 'def ' in text),
            # JavaScript function pattern
            ('function(' in text or 'function ' in text) and '{' in text and '}' in text,
            # Multiple assignment pattern
            text.count('=') >= 3 and ('let ' in text or 'const ' in text or 'var ' in text),
        ]
        
        if any(pattern for pattern in patterns):
            return True
    
    return False

def has_wiki_links(exchange: Exchange) -> bool:
    """Check for Obsidian-style wiki links [[link text]]."""
    assistant_texts = exchange.get_assistant_texts()
    return any(bool(re.search(r'\[\[.+?\]\]', text)) for text in assistant_texts)

def has_latex_math(exchange: Exchange) -> bool:
    """Check for LaTeX/MathJax mathematical formulas."""
    assistant_texts = exchange.get_assistant_texts()
    
    for text in assistant_texts:
        math_indicators = [
            re.search(r'\$\$.+?\$\$', text) is not None,
            re.search(r'\\\((.+?)\\\)', text) is not None,
            re.search(r'\\\[(.+?)\\\]', text) is not None,
            any(cmd in text for cmd in ['\\frac', '\\sum', '\\int', '\\sqrt', '\\alpha', 
                                       '\\beta', '\\gamma', '\\theta', '\\pi', '\\sigma', 
                                       '\\infty', '\\partial', '\\nabla']),
        ]
        
        if any(math_indicators):
            return True
    
    return False

# User Behavior
def user_has_attachments(exchange: Exchange) -> bool:
    """Check if user messages have attachments."""
    for message in exchange.get_user_messages():
        metadata = message.get('metadata', {})
        if metadata.get('attachments'):
            return True
    return False

def user_is_continuation(exchange: Exchange) -> bool:
    """Check if this exchange started with a continuation prompt."""
    return exchange.has_continuations()

def user_first_message_length(exchange: Exchange) -> int:
    """Get length of first user message."""
    user_messages = exchange.get_user_messages()
    if not user_messages:
        return 0
    
    from .models import extract_message_text
    first_text = extract_message_text(user_messages[0])
    return len(first_text)

# Message Statistics
def message_counts(exchange: Exchange) -> Dict[str, int]:
    """Get message count statistics."""
    return {
        'total': len(exchange.messages),
        'user': len(exchange.get_user_messages()),
        'assistant': len(exchange.get_assistant_messages())
    }

def text_lengths(exchange: Exchange) -> Dict[str, int]:
    """Get text length statistics."""
    user_texts = exchange.get_user_texts()
    assistant_texts = exchange.get_assistant_texts()
    
    return {
        'user_total': sum(len(text) for text in user_texts),
        'assistant_total': sum(len(text) for text in assistant_texts),
        'user_avg': sum(len(text) for text in user_texts) // max(len(user_texts), 1),
        'assistant_avg': sum(len(text) for text in assistant_texts) // max(len(assistant_texts), 1)
    }

# Feature Detection
def has_web_search(exchange: Exchange) -> bool:
    """Check for web search operations."""
    for message in exchange.messages:
        metadata = message.get('metadata', {})
        if (metadata.get('search_queries') or 
            metadata.get('search_result_groups') or
            metadata.get('content_references')):
            return True
    return False

def has_code_execution(exchange: Exchange) -> bool:
    """Check for code execution artifacts."""
    for message in exchange.messages:
        metadata = message.get('metadata', {})
        if (metadata.get('aggregate_result') or 
            metadata.get('jupyter_messages')):
            return True
    return False

def has_canvas_operations(exchange: Exchange) -> bool:
    """Check for canvas/document operations."""
    for message in exchange.messages:
        metadata = message.get('metadata', {})
        if metadata.get('canvas'):
            return True
    return False

# Complex Detection
def first_user_analysis(exchange: Exchange) -> Dict[str, Any]:
    """Analyze the first user message comprehensively."""
    user_messages = exchange.get_user_messages()
    if not user_messages:
        return {}
    
    from .models import extract_message_text
    first_message = user_messages[0]
    text = extract_message_text(first_message)
    metadata = first_message.get('metadata', {})
    attachments = metadata.get('attachments', [])
    
    analysis = {
        'length': len(text),
        'has_attachments': len(attachments) > 0,
        'attachment_count': len(attachments)
    }
    
    # Length category
    if analysis['length'] < 50:
        analysis['length_category'] = 'very_short'
    elif analysis['length'] < 200:
        analysis['length_category'] = 'short'
    elif analysis['length'] < 1000:
        analysis['length_category'] = 'medium'
    elif analysis['length'] < 2000:
        analysis['length_category'] = 'long'
    else:
        analysis['length_category'] = 'very_long'
    
    # Code patterns
    code_indicators = ['```', 'def ', 'function ', 'class ', 'import ', 'from ', 'require(', '#!/bin/', '#include']
    analysis['has_code_patterns'] = any(indicator in text for indicator in code_indicators)
    
    # Code attachments
    analysis['has_code_attachments'] = False
    for attachment in attachments:
        mime_type = attachment.get('mime_type', '').lower()
        name = attachment.get('name', '').lower()
        
        code_extensions = ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs', 
                          '.ts', '.jsx', '.tsx', '.sql', '.sh', '.rb', '.php']
        code_mimes = ['text/x-python', 'text/x-java', 'application/javascript', 'text/x-script']
        
        if (any(ext in name for ext in code_extensions) or 
            any(mime in mime_type for mime in code_mimes)):
            analysis['has_code_attachments'] = True
            break
    
    return analysis

def gizmo_plugin_usage(exchange: Exchange) -> Dict[str, Any]:
    """Detect gizmo and plugin usage."""
    gizmos = set()
    plugins = set()
    
    for message in exchange.messages:
        metadata = message.get('metadata', {})
        
        # Gizmo detection
        if metadata.get('gizmo_id'):
            gizmos.add(metadata['gizmo_id'])
        
        # Plugin detection
        invoked_plugin = metadata.get('invoked_plugin', {})
        if invoked_plugin:
            if invoked_plugin.get('plugin_id'):
                plugins.add(invoked_plugin['plugin_id'])
            if invoked_plugin.get('namespace'):
                plugins.add(invoked_plugin['namespace'])
    
    result = {}
    if gizmos:
        result['gizmos'] = list(gizmos)
        result['gizmo_count'] = len(gizmos)
    
    if plugins:
        result['plugins'] = list(plugins)
        result['plugin_count'] = len(plugins)
    
    return result if result else None


######################
# Conversation Rules #
######################

def conversation_length_analysis(conversation: Conversation) -> Dict[str, Any]:
    """Analyze conversation length and categorize."""
    count = conversation.exchange_count
    
    # Categorize
    if count == 1:
        category = 'single'
    elif count <= 3:
        category = 'short'
    elif count <= 10:
        category = 'medium'
    elif count <= 25:
        category = 'long'
    else:
        category = 'very_long'
    
    return {
        'exchange_count': count,
        'category': category,
        'message_count': conversation.total_message_count,
        'user_messages': conversation.total_user_messages,
        'assistant_messages': conversation.total_assistant_messages
    }

def feature_usage_summary(conversation: Conversation) -> Dict[str, Any]:
    """Summarize feature usage across all exchanges."""
    features = ['has_code_blocks', 'has_web_search', 'has_code_execution', 
               'has_canvas_operations', 'user_has_attachments', 'has_wiki_links', 
               'has_latex_math']
    
    summary = {}
    total_exchanges = conversation.exchange_count
    
    if total_exchanges == 0:
        return {}
    
    for feature in features:
        count = sum(1 for exchange in conversation.exchanges 
                   if exchange.annotations.get(feature, False))
        
        if count > 0:
            percentage = (count / total_exchanges) * 100
            summary[f'{feature}_usage'] = {
                'exchange_count': count,
                'percentage': round(percentage, 1)
            }
    
    return summary

def gizmo_plugin_summary(conversation: Conversation) -> Dict[str, Any]:
    """Aggregate gizmo/plugin usage across all exchanges."""
    all_gizmos = set()
    all_plugins = set()
    gizmo_usage_count = 0
    plugin_usage_count = 0
    
    for exchange in conversation.exchanges:
        gizmo_data = exchange.annotations.get('gizmo_plugin_usage')
        if gizmo_data:
            if 'gizmos' in gizmo_data:
                all_gizmos.update(gizmo_data['gizmos'])
                gizmo_usage_count += 1
            
            if 'plugins' in gizmo_data:
                all_plugins.update(gizmo_data['plugins'])
                plugin_usage_count += 1
    
    result = {}
    
    if all_gizmos:
        result['gizmo_summary'] = {
            'unique_gizmos': len(all_gizmos),
            'gizmo_list': sorted(list(all_gizmos)),
            'exchanges_with_gizmos': gizmo_usage_count
        }
    
    if all_plugins:
        result['plugin_summary'] = {
            'unique_plugins': len(all_plugins),
            'plugin_list': sorted(list(all_plugins)),
            'exchanges_with_plugins': plugin_usage_count
        }
    
    return result if result else None

def content_analysis_summary(conversation: Conversation) -> Dict[str, Any]:
    """Analyze content patterns across the conversation."""
    total_user_length = len(conversation.get_all_user_text())
    total_assistant_length = len(conversation.get_all_assistant_text())
    
    # Analyze first messages across exchanges
    large_first_messages = 0
    code_first_messages = 0
    attachment_first_messages = 0
    
    for exchange in conversation.exchanges:
        first_analysis = exchange.annotations.get('first_user_analysis', {})
        
        if first_analysis.get('length_category') in ['long', 'very_long']:
            large_first_messages += 1
        
        if first_analysis.get('has_code_patterns'):
            code_first_messages += 1
            
        if first_analysis.get('has_attachments'):
            attachment_first_messages += 1
    
    return {
        'total_length': {
            'user': total_user_length,
            'assistant': total_assistant_length,
            'ratio': round(total_assistant_length / max(total_user_length, 1), 2)
        },
        'first_message_patterns': {
            'large_content': large_first_messages,
            'code_patterns': code_first_messages,
            'with_attachments': attachment_first_messages
        }
    }


######################
#   Rule Registry    #
######################

# Exchange rules for the default annotator
EXCHANGE_RULES = {
    # Content detection
    'has_code_blocks': has_code_blocks,
    'has_code_structure_patterns': has_code_structure_patterns,
    'has_wiki_links': has_wiki_links,
    'has_latex_math': has_latex_math,
    
    # User behavior
    'user_has_attachments': user_has_attachments,
    'user_is_continuation': user_is_continuation,
    'user_first_message_length': user_first_message_length,
    
    # Message statistics
    'message_counts': message_counts,
    'text_lengths': text_lengths,
    
    # Feature detection
    'has_web_search': has_web_search,
    'has_code_execution': has_code_execution,
    'has_canvas_operations': has_canvas_operations,
    
    # Complex analysis
    'first_user_analysis': first_user_analysis,
    'gizmo_plugin_usage': gizmo_plugin_usage,
}

# Conversation rules for the default annotator
CONVERSATION_RULES = {
    'conversation_length_analysis': conversation_length_analysis,
    'feature_usage_summary': feature_usage_summary,
    'gizmo_plugin_summary': gizmo_plugin_summary,
    'content_analysis_summary': content_analysis_summary,
}
