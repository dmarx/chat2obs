# conversation_tagger/core/conversation_aggregator.py
"""
Aggregate exchange tags to conversation level.
"""

from typing import Dict, Any, List
from collections import Counter
from .tag import Tag


class ConversationAggregator:
    """Aggregate exchange tags into conversation-level insights."""
    
    def aggregate_to_conversation(self, tagged_exchanges: List[Dict[str, Any]], 
                                 conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Roll up exchange tags to conversation level."""
        if not tagged_exchanges:
            return {
                'conversation_id': conversation.get('conversation_id', 'unknown'),
                'title': conversation.get('title', 'Untitled'),
                'tags': [],
                'exchange_count': 0,
                'exchanges': [],
                'conversation': conversation
            }
        
        conversation_id = tagged_exchanges[0]['conversation_id']
        conversation_tags = []
        
        # Basic aggregation: if any exchange has a tag, conversation has it
        all_exchange_tag_names = set()
        for tagged_exchange in tagged_exchanges:
            for tag in tagged_exchange['tags']:
                all_exchange_tag_names.add(tag.name)
        
        # Create presence-based conversation tags
        for tag_name in all_exchange_tag_names:
            conversation_tags.append(Tag(f"has_{tag_name}"))
        
        # Add basic structural info
        exchange_count = len(tagged_exchanges)
        conversation_tags.append(Tag('exchange_count', count=exchange_count))
        
        # Add gizmo/plugin info from conversation
        if conversation.get('gizmo_id'):
            conversation_tags.append(Tag('gizmo', gizmo_id=conversation['gizmo_id']))
        
        plugin_ids = conversation.get('plugin_ids')
        if plugin_ids is not None:
            for plugin_id in plugin_ids:
                conversation_tags.append(Tag('plugin', plugin_id=plugin_id))
        
        return {
            'conversation_id': conversation_id,
            'title': conversation.get('title', 'Untitled'),
            'tags': conversation_tags,
            'exchange_count': exchange_count,
            'exchanges': tagged_exchanges,
            'conversation': conversation
        }
