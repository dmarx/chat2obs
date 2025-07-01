# src/conversation_tagger/core/detection.py
"""
High-value detection rules for conversations and exchanges.
Reimplemented to use Exchange/Conversation objects with proper API.
"""

import re
from typing import Dict, Any, List
from .exchange import Exchange
from .conversation import Conversation
from .tag import Tag


######################
#  Conversation Rules #
######################

def has_github_repos(conversation: Conversation) -> bool:
    """Check if GitHub repositories were selected for context."""
    for exchange in conversation.exchanges:
        for message in exchange.messages:
            metadata = message.get('metadata', {})
            repos = metadata.get('selected_github_repos', [])
            if repos:  # Non-empty list
                return True
    return False


def has_canvas_operations(conversation: Conversation) -> bool:
    """Check for canvas/document operations."""
    for exchange in conversation.exchanges:
        for message in exchange.messages:
            metadata = message.get('metadata', {})
            if metadata.get('canvas'):
                return True
    return False


def has_web_search(conversation: Conversation) -> bool:
    """Check for web search operations."""
    for exchange in conversation.exchanges:
        for message in exchange.messages:
            metadata = message.get('metadata', {})
            if (metadata.get('search_queries') or 
                metadata.get('search_result_groups') or
                metadata.get('content_references')):
                return True
    return False


def has_reasoning_thoughts(conversation: Conversation) -> bool:
    """Check for reasoning/thinking patterns."""
    for exchange in conversation.exchanges:
        for message in exchange.messages:
            content = message.get('content', {})
            if content.get('thoughts'):  # Reasoning thoughts
                return True
    return False


def has_code_execution(conversation: Conversation) -> bool:
    """Check for code execution artifacts."""
    for exchange in conversation.exchanges:
        for message in exchange.messages:
            metadata = message.get('metadata', {})
            if (metadata.get('aggregate_result') or 
                metadata.get('jupyter_messages')):
                return True
    return False


def create_conversation_length_tag(conversation: Conversation) -> Tag:
    """Create structured tag for conversation length."""
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
    
    return Tag('conversation_length', count=exchange_count, category=category)


def create_gizmo_plugin_tags(conversation: Conversation) -> List[Tag]:
    """Create structured tags for gizmos and plugins."""
    tags = []
    gizmos = set()
    plugins = set()
    
    # Check conversation-level data (if available in raw format)
    # Note: This would need conversation.metadata if we stored raw data
    
    # Check message-level
    for exchange in conversation.exchanges:
        for message in exchange.messages:
            metadata = message.get('metadata', {})
            
            # Invoked plugins
            invoked_plugin = metadata.get('invoked_plugin', {})
            if invoked_plugin:
                if invoked_plugin.get('plugin_id'):
                    plugins.add(invoked_plugin['plugin_id'])
                if invoked_plugin.get('namespace'):
                    plugins.add(invoked_plugin['namespace'])
            
            # Gizmo usage
            if metadata.get('gizmo_id'):
                gizmos.add(metadata['gizmo_id'])
    
    # Create tags
    for gizmo in gizmos:
        tags.append(Tag('gizmo', gizmo_id=gizmo))
    
    for plugin in plugins:
        tags.append(Tag('plugin', plugin_id=plugin))
    
    return tags


######################
#   Exchange Rules   #
######################

def has_code_blocks(exchange: Exchange) -> bool:
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


def user_has_quote_elaborate(exchange: Exchange) -> bool:
    """Check if user messages contain quote+elaborate continuation pattern."""
    for message in exchange.get_user_messages():
        content = message.get('content', {})
        text = content.get('text', '').strip()
        
        if not text.startswith('>'):
            continue
        
        lines = text.split('\n')
        if len(lines) >= 2 and lines[-1].strip().lower() == 'elaborate':
            return True
    
    return False


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


def assistant_has_reasoning(exchange: Exchange) -> bool:
    """Check if assistant messages contain reasoning/thinking content."""
    for message in exchange.get_assistant_messages():
        content = message.get('content', {})
        if content.get('thoughts'):
            return True
    return False


######################
# From exchange_tagger.py #
######################

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
    content = first_message.get('content', {})
    text = content.get('text', '')
    parts = content.get('parts', [])
    joined = ' '.join(str(p) for p in parts if isinstance(p, str)).strip()
    if joined:
        text = f"{text} {joined}"
    
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


######################
#   Rule Registry    #
######################

# High-value conversation-level rules
CONVERSATION_RULES = {
    'has_github_repos': has_github_repos,
    'has_canvas_operations': has_canvas_operations,
    'has_web_search': has_web_search,
    'has_reasoning_thoughts': has_reasoning_thoughts,
    'has_code_execution': has_code_execution,
    'conversation_length': create_conversation_length_tag,
    'gizmo_plugin_tags': create_gizmo_plugin_tags,
}

# High-value exchange-level rules  
EXCHANGE_RULES = {
    'has_code_blocks': has_code_blocks,
    'has_script_headers': has_script_headers,
    'has_code_structure_patterns': has_code_structure_patterns,
    'user_has_quote_elaborate': user_has_quote_elaborate,
    'user_has_attachments': user_has_attachments,
    'user_is_continuation': user_is_continuation,
    'assistant_has_reasoning': assistant_has_reasoning,
    'has_wiki_links': has_wiki_links,
    'has_latex_math': has_latex_math,
    'first_user_has_large_content': first_user_has_large_content,
    'first_user_has_code_patterns': first_user_has_code_patterns,
    'first_user_has_attachments': first_user_has_attachments,
    'first_user_has_code_attachments': first_user_has_code_attachments,
}
