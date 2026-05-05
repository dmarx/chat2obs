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