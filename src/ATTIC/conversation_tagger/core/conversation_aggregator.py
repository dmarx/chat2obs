# conversation_tagger/core/conversation_aggregator.py
"""
Aggregates exchange-level tags to conversation-level insights.
"""

from typing import Dict, Any, List
from collections import defaultdict, Counter
from .tag import Tag
from .exchange import Exchange


class ConversationAggregator:
    """Aggregates exchange tags into conversation-level tags."""
    
    def aggregate_to_conversation(self, tagged_exchanges: List[Dict[str, Any]], 
                                 conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate exchange tags to conversation level."""
        if not tagged_exchanges:
            return {
                'conversation_id': conversation.get('conversation_id', 'unknown'),
                'title': conversation.get('title', 'Untitled'),
                'tags': [],
                'exchange_count': 0,
                'aggregation_stats': {},
                'conversation': conversation
            }
        
        conversation_id = tagged_exchanges[0]['conversation_id']
        conversation_tags = set()
        
        # Collect all exchange tags
        all_exchange_tags = []
        for tagged_exchange in tagged_exchanges:
            all_exchange_tags.extend(tagged_exchange['tags'])
        
        # Aggregate different types of tags
        conversation_tags.update(self._aggregate_presence_tags(all_exchange_tags))
        conversation_tags.update(self._aggregate_frequency_tags(all_exchange_tags, len(tagged_exchanges)))
        conversation_tags.update(self._aggregate_statistical_tags(all_exchange_tags))
        conversation_tags.update(self._aggregate_conversation_structure_tags(tagged_exchanges))
        conversation_tags.update(self._aggregate_gizmo_plugin_tags(conversation))
        
        # Calculate aggregation statistics
        stats = self._calculate_aggregation_stats(tagged_exchanges, all_exchange_tags)
        
        return {
            'conversation_id': conversation_id,
            'title': conversation.get('title', 'Untitled'),
            'tags': list(conversation_tags),
            'exchange_count': len(tagged_exchanges),
            'aggregation_stats': stats,
            'exchanges': tagged_exchanges,
            'conversation': conversation
        }
    
    def _aggregate_presence_tags(self, all_exchange_tags: List[Tag]) -> List[Tag]:
        """Create conversation tags based on presence of exchange tags."""
        conversation_tags = []
        
        # Simple presence aggregation (if any exchange has it, conversation has it)
        presence_tags = {
            'user_has_code_blocks', 'assistant_has_code_blocks', 'user_has_attachments',
            'assistant_has_wiki_links', 'assistant_has_latex_math', 'user_has_error_messages',
            'exchange_is_coding_focused', 'exchange_is_wiki_article_focused'
        }
        
        found_tags = {tag.name for tag in all_exchange_tags}
        
        for tag_name in presence_tags:
            if tag_name in found_tags:
                conversation_tags.append(Tag(f"has_{tag_name}"))
        
        return conversation_tags
    
    def _aggregate_frequency_tags(self, all_exchange_tags: List[Tag], 
                                 exchange_count: int) -> List[Tag]:
        """Create tags based on frequency of exchange tags."""
        conversation_tags = []
        
        # Count frequency of each tag
        tag_counts = Counter(tag.name for tag in all_exchange_tags)
        
        # Create frequency-based tags
        for tag_name, count in tag_counts.items():
            frequency = count / exchange_count
            
            if frequency >= 0.8:
                frequency_level = 'always'
            elif frequency >= 0.5:
                frequency_level = 'often'
            elif frequency >= 0.2:
                frequency_level = 'sometimes'
            else:
                frequency_level = 'rarely'
            
            # Only create tags for interesting patterns
            if tag_name in ['user_has_code_blocks', 'assistant_has_code_blocks', 
                          'assistant_has_wiki_links', 'exchange_is_coding_focused']:
                conversation_tags.append(Tag(f"{tag_name}_frequency", 
                                           count=count, 
                                           frequency=round(frequency, 2),
                                           level=frequency_level))
        
        return conversation_tags
    
    def _aggregate_statistical_tags(self, all_exchange_tags: List[Tag]) -> List[Tag]:
        """Create statistical aggregation tags."""
        conversation_tags = []
        
        # Aggregate length statistics
        user_lengths = []
        assistant_lengths = []
        
        for tag in all_exchange_tags:
            if tag.name == 'user_prompt_length':
                user_lengths.append(tag.attributes.get('length', 0))
            elif tag.name == 'assistant_response_length':
                assistant_lengths.append(tag.attributes.get('length', 0))
        
        if user_lengths:
            conversation_tags.append(Tag('user_prompt_stats',
                                       mean_length=round(sum(user_lengths) / len(user_lengths), 1),
                                       min_length=min(user_lengths),
                                       max_length=max(user_lengths),
                                       total_exchanges=len(user_lengths)))
        
        if assistant_lengths:
            conversation_tags.append(Tag('assistant_response_stats',
                                       mean_length=round(sum(assistant_lengths) / len(assistant_lengths), 1),
                                       min_length=min(assistant_lengths),
                                       max_length=max(assistant_lengths),
                                       total_exchanges=len(assistant_lengths)))
        
        return conversation_tags
    
    def _aggregate_conversation_structure_tags(self, tagged_exchanges: List[Dict[str, Any]]) -> List[Tag]:
        """Create tags about conversation structure."""
        conversation_tags = []
        
        exchange_count = len(tagged_exchanges)
        
        # Conversation length category
        if exchange_count == 1:
            length_category = 'single_exchange'
        elif exchange_count <= 3:
            length_category = 'short'
        elif exchange_count <= 8:
            length_category = 'medium'
        elif exchange_count <= 15:
            length_category = 'long'
        else:
            length_category = 'very_long'
        
        conversation_tags.append(Tag('conversation_structure',
                                   exchange_count=exchange_count,
                                   length_category=length_category))
        
        # Interaction patterns
        pattern_counts = Counter()
        for tagged_exchange in tagged_exchanges:
            for tag in tagged_exchange['tags']:
                if tag.name == 'interaction_pattern':
                    pattern = tag.attributes.get('pattern', 'unknown')
                    pattern_counts[pattern] += 1
        
        if pattern_counts:
            dominant_pattern = pattern_counts.most_common(1)[0][0]
            conversation_tags.append(Tag('dominant_interaction_pattern',
                                       pattern=dominant_pattern,
                                       pattern_distribution=dict(pattern_counts)))
        
        # Continuation usage
        continuation_count = 0
        for tagged_exchange in tagged_exchanges:
            exchange = tagged_exchange['exchange']
            if exchange.has_continuations():
                continuation_count += 1
        
        if continuation_count > 0:
            conversation_tags.append(Tag('uses_continuations',
                                       continuation_exchanges=continuation_count,
                                       continuation_frequency=round(continuation_count / exchange_count, 2)))
        
        return conversation_tags
    
    def _aggregate_gizmo_plugin_tags(self, conversation: Dict[str, Any]) -> List[Tag]:
        """Add gizmo/plugin tags from conversation metadata."""
        tags = []
        
        if conversation.get('gizmo_id'):
            tags.append(Tag('gizmo', gizmo_id=conversation['gizmo_id']))
        
        plugin_ids = conversation.get('plugin_ids', [])
        for plugin_id in plugin_ids:
            tags.append(Tag('plugin', plugin_id=plugin_id))
        
        return tags
    
    def _calculate_aggregation_stats(self, tagged_exchanges: List[Dict[str, Any]], 
                                   all_exchange_tags: List[Tag]) -> Dict[str, Any]:
        """Calculate detailed aggregation statistics."""
        stats = {
            'total_exchanges': len(tagged_exchanges),
            'total_exchange_tags': len(all_exchange_tags),
            'unique_tag_types': len(set(tag.name for tag in all_exchange_tags)),
            'exchange_tag_distribution': Counter(tag.name for tag in all_exchange_tags),
        }
        
        # Calculate per-exchange statistics
        tags_per_exchange = [len(tagged_exchange['tags']) for tagged_exchange in tagged_exchanges]
        if tags_per_exchange:
            stats['tags_per_exchange'] = {
                'mean': round(sum(tags_per_exchange) / len(tags_per_exchange), 1),
                'min': min(tags_per_exchange),
                'max': max(tags_per_exchange)
            }
        
        return stats