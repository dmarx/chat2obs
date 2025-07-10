# src/conversation_tagger/core/detection.py
"""
High-value detection rules for conversations and exchanges.
Updated to use dictionary-based annotations.
"""

import re
from typing import Dict, Any, List
from .exchange import Exchange
from .conversation import Conversation
from .tag import Tag, create_annotation
from .message import Message, MessageOpenAI

######################
#  Conversation Rules #
######################
# These should only do aggregation/summarization, not detection

def create_conversation_length_annotation(conversation: Conversation) -> Dict[str, Any]:
    """Create annotation for conversation length."""
    exchange_count = conversation.exchange_count
    
    # Determine category based on number of exchanges
    if exchange_count == 1:
        category = 'single'
    elif exchange_count <= 3:
        category = 'short'
    elif exchange_count <= 10:
        category = 'medium'
    elif exchange_count <= 25:
        category = 'long'
    else:
        category = 'very_long'
    
    return create_annotation('conversation_length', {
        'count': exchange_count,
        'category': category
    })


def conversation_feature_summary(conversation: Conversation) -> Dict[str, Any]:
    """Aggregate feature usage across all exchanges."""
    feature_counts = {}
    total_exchanges = conversation.exchange_count
    
    # Count exchanges with each feature
    for exchange in conversation.exchanges:
        exchange_features = set()
        for annotation_name in exchange.annotations:
            if annotation_name in ['has_github_repos', 'has_canvas_operations', 'has_web_search', 
                                 'has_reasoning_thoughts', 'has_code_execution', 'has_code_blocks',
                                 'has_script_headers', 'has_code_structure_patterns', 'has_wiki_links',
                                 'has_latex_math', 'user_has_attachments']:
                exchange_features.add(annotation_name)
            elif annotation_name.startswith('gizmo_'):
                exchange_features.add('has_gizmo_usage')
            elif annotation_name.startswith('plugin_'):
                exchange_features.add('has_plugin_usage')
        
        # Count each feature once per exchange
        for feature in exchange_features:
            feature_counts[feature] = feature_counts.get(feature, 0) + 1
    
    annotations = {}
    for feature, count in feature_counts.items():
        percentage = (count / total_exchanges) * 100 if total_exchanges > 0 else 0
        annotations[f'conversation_{feature}'] = {
            'exchange_count': count,
            'total_exchanges': total_exchanges,
            'percentage': round(percentage, 1)
        }
    
    return annotations


def conversation_gizmo_plugin_summary(conversation: Conversation) -> Dict[str, Any]:
    """Aggregate gizmo/plugin usage across all exchanges."""
    all_gizmos = set()
    all_plugins = set()
    gizmo_count = 0
    plugin_count = 0
    
    # Collect from all exchange annotations
    for exchange in conversation.exchanges:
        for name, value in exchange.annotations.items():
            if name.startswith('gizmo_'):
                if isinstance(value, dict) and 'gizmo_id' in value:
                    all_gizmos.add(value['gizmo_id'])
                gizmo_count += 1
            elif name.startswith('plugin_'):
                if isinstance(value, dict) and 'plugin_id' in value:
                    all_plugins.add(value['plugin_id'])
                plugin_count += 1
    
    annotations = {}
    
    # Summary annotations
    if all_gizmos:
        annotations['conversation_gizmo_usage'] = {
            'unique_gizmos': len(all_gizmos),
            'total_usage': gizmo_count,
            'gizmo_list': list(all_gizmos)
        }
    
    if all_plugins:
        annotations['conversation_plugin_usage'] = {
            'unique_plugins': len(all_plugins),
            'total_usage': plugin_count,
            'plugin_list': list(all_plugins)
        }
    
    return annotations


######################
#   Exchange Rules   #
######################
# These do actual detection on individual exchanges

# Feature detection (moved from conversation-level)
def has_github_repos(exchange: Exchange) -> bool:
    if isinstance(exchange.messages[0], MessageOpenAI):
        return has_github_repos_oai(exchange)

def has_github_repos_oai(exchange: Exchange) -> bool:
    """Check if GitHub repositories were selected for context in this exchange."""
    repos = None
    for message in exchange.messages:
        metadata = message.data.get('metadata', {})
        repos = metadata.get('selected_github_repos', [])
        if repos:
            return True
    return False

def has_canvas_operations(exchange: Exchange) -> bool:
    if isinstance(exchange.messages[0], MessageOpenAI):
        return has_canvas_operations_oai(exchange)
    
def has_canvas_operations_oai(exchange: Exchange) -> bool:
    """Check for canvas/document operations in this exchange."""
    for message in exchange.messages:
        metadata = message.data.get('metadata', {})
        if metadata.data.get('canvas'):
            return True
    return False


def has_web_search(exchange: Exchange) -> bool:
    if isinstance(exchange.messages[0], MessageOpenAI):
        return has_web_search_oai(exchange)
    
def has_web_search_oai(exchange: Exchange) -> bool:
    """Check for web search operations in this exchange."""
    for message in exchange.messages:
        metadata = message.data.get('metadata', {})
        if (metadata.data.get('search_queries') or 
            metadata.data.get('search_result_groups') or
            metadata.data.get('content_references')):
            return True
    return False


def has_reasoning_thoughts(exchange: Exchange) -> bool:
    if isinstance(exchange.messages[0], MessageOpenAI):
        return has_reasoning_thoughts_oai(exchange)
    
def has_reasoning_thoughts_oai(exchange: Exchange) -> bool:
    """Check for reasoning/thinking patterns in this exchange."""
    for message in exchange.messages:
        content = message.data.get('content', {})
        if content.get('thoughts'):  # Reasoning thoughts
            return True
    return False

def has_code_execution(exchange: Exchange) -> bool:
    if isinstance(exchange.messages[0], MessageOpenAI):
        return has_code_execution_oai(exchange)
    
def has_code_execution_oai(exchange: Exchange) -> bool:
    """Check for code execution artifacts in this exchange."""
    for message in exchange.messages:
        metadata = message.data.get('metadata', {})
        if (metadata.get('aggregate_result') or 
            metadata.get('jupyter_messages')):
            return True
    return False


def has_code_blocks(exchange: Exchange) -> bool:
    if isinstance(exchange.messages[0], MessageOpenAI):
        return has_code_blocks_oai(exchange)

# Code detection
def has_code_blocks_oai(exchange: Exchange) -> bool:
    """Check for explicit code blocks (``` markdown syntax)."""
    all_texts = exchange.get_user_texts() + exchange.get_assistant_texts()
    return any('```' in text for text in all_texts)


def has_script_headers(exchange: Exchange) -> bool:
    """Check for script headers and system includes."""
    all_texts = exchange.get_user_texts() + exchange.get_assistant_texts()
    script_indicators = ['#!/bin/', '#include', 'using namespace']
    
    for text in all_texts:
        if any(indicator in text for indicator in script_indicators):
            return True
    return False


def has_code_structure_patterns(exchange: Exchange) -> bool:
    """Check for actual code structure patterns (syntax combinations that suggest real code)."""
    all_texts = exchange.get_user_texts() + exchange.get_assistant_texts()
    
    for text in all_texts:
        # Look for combinations that strongly suggest actual code
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


# User behavior detection
def user_has_quote_elaborate(exchange: Exchange) -> bool:
    """Check if user messages contain quote+elaborate continuation pattern."""
    for message in exchange.get_user_messages():
        text = message.content
        if not text.startswith('>'):
            continue
        
        lines = text.split('\n')
        if len(lines) >= 2 and lines[-1].strip().lower() == 'elaborate':
            return True
    
    return False


def user_has_attachments(exchange: Exchange) -> bool:
    if isinstance(exchange.messages[0], MessageOpenAI):
        return user_has_attachments_oai(exchange)
    
def user_has_attachments_oai(exchange: Exchange) -> bool:
    """Check if user messages have attachments."""
    for message in exchange.get_user_messages():
        metadata = message.data.get('metadata', {})
        if metadata.get('attachments'):
            return True
    return False


def user_is_continuation(exchange: Exchange) -> bool:
    """Check if this exchange started with a continuation prompt."""
    return exchange.has_continuations()


# Assistant behavior detection
def assistant_has_reasoning(exchange: Exchange) -> bool:
    """Check if assistant messages contain reasoning/thinking content."""
    for message in exchange.get_assistant_messages():
        content = message.get('content', {})
        if content.get('thoughts'):
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
            # Common LaTeX commands
            any(cmd in text for cmd in ['\\frac', '\\sum', '\\int', '\\sqrt', '\\alpha', 
                                       '\\beta', '\\gamma', '\\theta', '\\pi', '\\sigma', 
                                       '\\infty', '\\partial', '\\nabla']),
        ]
        
        if any(math_indicators):
            return True
    
    return False

def first_user_has_large_content(exchange: Exchange, min_length: int = 2000) -> bool:
    """Check if the first user message has large content."""
    user_messages = exchange.get_user_messages()
    if not user_messages:
        return False
    
    first_message = user_messages[0]
    text = first_message.content
    
    return len(text.strip()) > min_length


def first_user_has_code_patterns(exchange: Exchange) -> bool:
    """Check if the first user message contains code patterns."""
    user_messages = exchange.get_user_messages()
    if not user_messages:
        return False
    
    first_message = user_messages[0]
    content = first_message.get('content', {})
    text = content.get('text', '')
    parts = content.get('parts', [])
    joined = ' '.join(str(p) for p in parts if isinstance(p, str)).strip()
    if joined:
        text = f"{text} {joined}"
    
    # Strong code indicators
    code_indicators = [
        '```',  # Code blocks
        'def ', 'function ', 'class ',  # Definitions
        'import ', 'from ', 'require(',  # Imports
        '#!/bin/', '#include',  # Script headers
    ]
    
    return any(indicator in text for indicator in code_indicators)


def first_user_has_attachments(exchange: Exchange) -> bool:
    """Check if the first user message has attachments."""
    user_messages = exchange.get_user_messages()
    if not user_messages:
        return False
    
    first_message = user_messages[0]
    metadata = first_message.get('metadata', {})
    attachments = metadata.get('attachments', [])
    return len(attachments) > 0


def first_user_has_code_attachments(exchange: Exchange) -> bool:
    """Check if the first user message has code-related attachments."""
    user_messages = exchange.get_user_messages()
    if not user_messages:
        return False
    
    first_message = user_messages[0]
    metadata = first_message.get('metadata', {})
    attachments = metadata.get('attachments', [])
    
    for attachment in attachments:
        mime_type = attachment.get('mime_type', '').lower()
        name = attachment.get('name', '').lower()
        
        # Check for code file extensions
        code_extensions = ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs', 
                          '.ts', '.jsx', '.tsx', '.sql', '.sh', '.rb', '.php']
        if any(ext in name for ext in code_extensions):
            return True
            
        # Check for code-related MIME types
        code_mimes = ['text/x-python', 'text/x-java', 'application/javascript', 'text/x-script']
        if any(mime in mime_type for mime in code_mimes):
            return True
    
    return False


def get_gizmo_annotations(exchange: Exchange) -> dict[str, Any]:
    if isinstance(exchange.messages[0], MessageOpenAI):
        return get_gizmo_annotations_oai(exchange)
    
def get_gizmo_annotations_oai(exchange: Exchange) -> dict[str, Any]:
    """Get annotations for specific gizmos used in this exchange."""
    annotations = {}
    gizmos = set()
    
    for message in exchange.messages:
        metadata = message.data.get('metadata', {})
        if metadata.get('gizmo_id'):
            gizmos.add(metadata['gizmo_id'])
    
    for i, gizmo in enumerate(gizmos):
        annotations[f'gizmo_{i+1}'] = {'gizmo_id': gizmo}
    
    return annotations


def get_plugin_annotations(exchange: Exchange) -> dict[str, Any]:
    if isinstance(exchange.messages[0], MessageOpenAI):
        return get_plugin_annotations_oai(exchange)
    
def get_plugin_annotations_oai(exchange: Exchange) -> dict[str, Any]:
    """Get annotations for specific plugins used in this exchange."""
    annotations = {}
    plugins = set()
    
    for message in exchange.messages:
        metadata = message.data.get('metadata', {})
        invoked_plugin = metadata.get('invoked_plugin', {})
        if invoked_plugin:
            if invoked_plugin.get('plugin_id'):
                plugins.add(invoked_plugin['plugin_id'])
            if invoked_plugin.get('namespace'):
                plugins.add(invoked_plugin['namespace'])
    
    for i, plugin in enumerate(plugins):
        annotations[f'plugin_{i+1}'] = {'plugin_id': plugin}
    
    return annotations


##############################
# Template content inference #
##############################

def naive_title_extraction(text):
    """
    Attempts to detect presence of title in first line of a message.
    """
    # get first line
    top = text.strip().split("\n")[0]

    # title/section header detected
    outv = None
    if top.startswith("#"):
        outv = top.replace("#","").strip()
    elif top.startswith("**") and top.endswith("**"):
        outv = top.replace("**","")
    if outv is not None:
        outv = outv.strip()
    return outv

def extract_proposed_title(exchange: Exchange) -> str:
    """
    Extracts proposed content title from the assistant's response.
    Assumes that an article was generated with a proposed title.
    """
    try:
       text = exchange.get_assistant_texts()[0]
    except IndexError:
        return None
    return naive_title_extraction(text)


######################
#   Rule Registry    #
######################

# High-value conversation-level rules (aggregation only)
CONVERSATION_RULES = {
    'conversation_length': create_conversation_length_annotation,
    'conversation_feature_summary': conversation_feature_summary,
    'conversation_gizmo_plugin_summary': conversation_gizmo_plugin_summary,
}

# High-value exchange-level rules (actual detection)
EXCHANGE_RULES = {
    # Feature detection (moved from conversation-level)
    'has_github_repos': has_github_repos,
    'has_canvas_operations': has_canvas_operations,
    'has_web_search': has_web_search,
    'has_reasoning_thoughts': has_reasoning_thoughts,
    'has_code_execution': has_code_execution,
    
    # Code detection
    'has_code_blocks': has_code_blocks,
    'has_script_headers': has_script_headers,
    'has_code_structure_patterns': has_code_structure_patterns,
    
    # User behavior
    'user_has_quote_elaborate': user_has_quote_elaborate,
    'user_has_attachments': user_has_attachments,
    'user_is_continuation': user_is_continuation,
    
    # Assistant behavior
    'assistant_has_reasoning': assistant_has_reasoning,
    'has_wiki_links': has_wiki_links,
    'has_latex_math': has_latex_math,
    
    # First user message analysis
    'first_user_has_large_content': first_user_has_large_content,
    'first_user_has_code_patterns': first_user_has_code_patterns,
    'first_user_has_attachments': first_user_has_attachments,
    'first_user_has_code_attachments': first_user_has_code_attachments,
    
    # Gizmo/plugin detection
    'get_gizmo_annotations': get_gizmo_annotations,
    'get_plugin_annotations': get_plugin_annotations,

    # Template content inference
    'proposed_title': extract_proposed_title,
}
