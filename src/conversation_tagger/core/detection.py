"""
NB: The intention is to collect rule functions in this file for organizaitonal purposes, but at present
probably none of these will work out of the box. They were ported from an older brainstorming version of the
codebase and at minimum need to be updated to account for the new Exchange/Conversation objects, and several
probably need to have their logic re-implemented to just be better classifiers.

In the future, would be great if we could compress documents into vectors which could be used for these classifications.
"""
from typing import Dict, Any

from .exchange import Exchange


### Already implemented elsewhere, need to be moved here
# - wiki markdown
#   - TODO: add a "see also:{bullleted list}" detector
# - user first message?




### Content ###

def has_large_content(conversation: Dict[str, Any], min_length: int = 2000) -> bool:
    """Check if conversation has unusually large content anywhere."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        content = message.get('content', {})
        text = content.get('text', '')
        if len(text) > min_length:
            return True
            
        parts = content.get('parts', [])
        for part in parts:
            if isinstance(part, str) and len(part) > min_length:
                return True
    
    return False


def has_github_repos(conversation: Dict[str, Any]) -> bool:
    """Check if GitHub repositories were selected for context."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        metadata = message.get('metadata', {})
        repos = metadata.get('selected_github_repos', [])
        if repos:  # Non-empty list
            return True
    
    return False


def has_canvas_operations(conversation: Dict[str, Any]) -> bool:
    """Check for canvas/document operations."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        metadata = message.get('metadata', {})
        if metadata.get('canvas'):
            return True
    
    return False


def has_web_search(conversation: Dict[str, Any]) -> bool:
    """Check for web search operations."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        metadata = message.get('metadata', {})
        if (metadata.get('search_queries') or 
            metadata.get('search_result_groups') or
            metadata.get('content_references')):
            return True
    
    return False


def has_reasoning_thoughts(conversation: Dict[str, Any]) -> bool:
    """Check for reasoning/thinking patterns."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        content = message.get('content', {})
        if content.get('thoughts'):  # Reasoning thoughts
            return True
    
    return False


def has_code_execution(conversation: Dict[str, Any]) -> bool:
    """Check for code execution artifacts."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        metadata = message.get('metadata', {})
        if (metadata.get('aggregate_result') or 
            metadata.get('jupyter_messages')):
            return True
    
    return False


### Code Indicators ###

# conversation_tagger/detection/code_indicators.py
"""
Individual code detection functions - each detects a specific type of code evidence.
"""

from typing import Dict, Any

from .helpers import get_all_text_from_message


def has_code_blocks(conversation: Dict[str, Any]) -> bool:
    """Check for explicit code blocks (``` markdown syntax)."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        if '```' in all_text:
            return True
    
    return False


def has_function_definitions(conversation: Dict[str, Any]) -> bool:
    """Check for function/class definition keywords."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        definition_keywords = ['def ', 'function ', 'class ']
        if any(keyword in all_text for keyword in definition_keywords):
            return True
    
    return False


def has_import_statements(conversation: Dict[str, Any]) -> bool:
    """Check for import/require statements."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        import_keywords = ['import ', 'from ', 'require(']
        if any(keyword in all_text for keyword in import_keywords):
            return True
    
    return False


def has_script_headers(conversation: Dict[str, Any]) -> bool:
    """Check for script headers and system includes."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        script_indicators = ['#!/bin/', '#include', 'using namespace']
        if any(indicator in all_text for indicator in script_indicators):
            return True
    
    return False


def has_high_keyword_density(conversation: Dict[str, Any]) -> bool:
    """Check for high density of programming keywords in large text."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        
        # Only check substantial text
        if len(all_text) <= 1000:
            continue
        
        coding_keywords = ['function', 'class', 'import', 'def ', 'const ', 'let ', 'var ', 'return', 'if ', 'for ', 'while ']
        keyword_count = sum(1 for keyword in coding_keywords if keyword in all_text.lower())
        
        # High threshold to avoid false positives in articles
        if keyword_count >= 5:
            return True
    
    return False


def has_code_structure_patterns(conversation: Dict[str, Any]) -> bool:
    """Check for actual code structure patterns (syntax combinations that suggest real code)."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        
        # Look for combinations that strongly suggest actual code
        patterns = [
            # Function definition pattern
            ('def ' in all_text and '(' in all_text and ':' in all_text and 'return' in all_text),
            # Class definition pattern  
            ('class ' in all_text and '(' in all_text and ':' in all_text and 'def ' in all_text),
            # JavaScript function pattern
            ('function(' in all_text or 'function ' in all_text) and '{' in all_text and '}' in all_text,
            # Multiple assignment pattern
            all_text.count('=') >= 3 and ('let ' in all_text or 'const ' in all_text or 'var ' in all_text),
        ]
        
        if any(pattern for pattern in patterns):
            return True
    
    return False


def has_code_patterns(conversation: Dict[str, Any]) -> bool:
    """Check for any code patterns (combines individual indicators)."""
    return (has_code_blocks(conversation) or 
            has_function_definitions(conversation) or 
            has_import_statements(conversation) or 
            has_script_headers(conversation) or
            has_code_structure_patterns(conversation) or
            has_high_keyword_density(conversation))

  
### Continuation Rules ###

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

### Exchange Rules

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


# #  For exchange no, but something like this could be interesting for Conversation level analysis.
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

### User 1st message
# possibly already implemented some or all of this elsewhere?

def first_user_has_large_content(conversation: Dict[str, Any], min_length: int = 2000) -> bool:
    """Check if the first user message has large content."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    
    all_text = get_all_text_from_message(first_message)
    return len(all_text) > min_length


def first_user_has_code_patterns(conversation: Dict[str, Any]) -> bool:
    """Check if the first user message contains code patterns."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    
    all_text = get_all_text_from_message(first_message)
    
    # Strong code indicators
    code_indicators = [
        '```',  # Code blocks
        'def ', 'function ', 'class ',  # Definitions
        'import ', 'from ', 'require(',  # Imports
        '#!/bin/', '#include',  # Script headers
    ]
    
    return any(indicator in all_text for indicator in code_indicators)


def first_user_has_attachments(conversation: Dict[str, Any]) -> bool:
    """Check if the first user message has attachments."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    
    metadata = first_message.get('metadata', {})
    attachments = metadata.get('attachments', [])
    return len(attachments) > 0


def first_user_has_code_attachments(conversation: Dict[str, Any]) -> bool:
    """Check if the first user message has code-related attachments."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    
    metadata = first_message.get('metadata', {})
    attachments = metadata.get('attachments', [])
    
    for attachment in attachments:
        mime_type = attachment.get('mime_type', '').lower()
        name = attachment.get('name', '').lower()
        
        # Check for code file extensions
        code_extensions = ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs', '.ts', '.jsx', '.tsx', '.sql', '.sh', '.rb', '.php']
        if any(ext in name for ext in code_extensions):
            return True
            
        # Check for code-related MIME types
        code_mimes = ['text/x-python', 'text/x-java', 'application/javascript', 'text/x-script']
        if any(mime in mime_type for mime in code_mimes):
            return True
    
    return False


### Structured Tags

# conversation_tagger/detection/structured_tags.py
"""
Functions that create structured tags with attributes.
"""

from typing import Dict, Any, List

from ..core.tag import Tag
from .helpers import get_all_user_messages


def create_conversation_length_tag(conversation: Dict[str, Any]) -> Tag:
    """Create structured tag for conversation length."""
    user_count = len(get_all_user_messages(conversation))
    
    # Determine category
    if user_count == 1:
        category = 'single'
    elif user_count <= 3:
        category = 'short'
    elif user_count <= 10:
        category = 'medium'
    elif user_count <= 25:
        category = 'long'
    else:
        category = 'very_long'
    
    return Tag('conversation_length', count=user_count, category=category)


def create_prompt_stats_tag(conversation: Dict[str, Any]) -> Tag:
    """Create structured tag for prompt statistics."""
    from .helpers import get_all_text_from_message
    
    user_messages = get_all_user_messages(conversation)
    
    if not user_messages:
        return Tag('prompt_stats', count=0, mean=0, median=0, variance=0, 
                  length_category='none', consistency='none')
    
    # Calculate message lengths
    lengths = []
    for message in user_messages:
        all_text = get_all_text_from_message(message)
        lengths.append(len(all_text))
    
    # Calculate statistics
    mean_length = sum(lengths) / len(lengths)
    sorted_lengths = sorted(lengths)
    n = len(sorted_lengths)
    median_length = (sorted_lengths[n//2] if n % 2 == 1 
                    else (sorted_lengths[n//2-1] + sorted_lengths[n//2]) / 2)
    variance = sum((x - mean_length) ** 2 for x in lengths) / len(lengths) if len(lengths) > 1 else 0
    
    # Determine categories
    if mean_length < 50:
        length_category = 'very_short'
    elif mean_length < 200:
        length_category = 'short'
    elif mean_length < 1000:
        length_category = 'medium'
    elif mean_length < 3000:
        length_category = 'long'
    else:
        length_category = 'very_long'
    
    if variance < 1000:
        consistency = 'consistent'
    elif variance < 10000:
        consistency = 'mixed'
    else:
        consistency = 'variable'
    
    return Tag('prompt_stats', 
               count=len(lengths),
               mean=round(mean_length, 1),
               median=round(median_length, 1),
               variance=round(variance, 1),
               length_category=length_category,
               consistency=consistency)


def create_gizmo_plugin_tags(conversation: Dict[str, Any]) -> List[Tag]:
    """Create structured tags for gizmos and plugins."""
    tags = []
    gizmos = set()
    plugins = set()
    
    # Check conversation-level
    if conversation.get('gizmo_id'):
        gizmos.add(conversation['gizmo_id'])
    
    plugin_ids = conversation.get('plugin_ids', [])
    if plugin_ids:
        plugins.update(plugin_ids)
    
    # Check message-level
    mapping = conversation.get('mapping', {})
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
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
