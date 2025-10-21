# conversation_tagger/processing/filters.py
"""
Filtering machinery for processed conversations.
"""

from typing import List, Dict, Any, Set, Callable, Optional
from dataclasses import dataclass
from ..core.conversation import Conversation


@dataclass
class FilterCriteria:
    """Criteria for filtering conversations."""
    
    # Annotation-based filters
    required_annotations: Set[str] = None
    forbidden_annotations: Set[str] = None
    
    # Custom filter functions
    custom_filters: List[Callable[[Conversation], bool]] = None
    
    # Gizmo/plugin filters  
    required_gizmos: Set[str] = None
    required_plugins: Set[str] = None
    
    def __post_init__(self):
        if self.required_annotations is None:
            self.required_annotations = set()
        if self.forbidden_annotations is None:
            self.forbidden_annotations = set()
        if self.custom_filters is None:
            self.custom_filters = []
        if self.required_gizmos is None:
            self.required_gizmos = set()
        if self.required_plugins is None:
            self.required_plugins = set()


class ConversationFilter:
    """Filters conversations based on annotations and other criteria."""
    
    @staticmethod
    def matches_criteria(conversation: Conversation, criteria: FilterCriteria) -> bool:
        """
        Check if a conversation matches the filter criteria.
        
        Args:
            conversation: Conversation to check
            criteria: Filter criteria
            
        Returns:
            True if conversation matches all criteria
        """
        # Check required annotations
        for annotation in criteria.required_annotations:
            if not conversation.has_annotation(annotation):
                return False
        
        # Check forbidden annotations
        for annotation in criteria.forbidden_annotations:
            if conversation.has_annotation(annotation):
                return False
        
        # Check gizmo requirements
        if criteria.required_gizmos:
            conversation_gizmos = ConversationFilter._get_conversation_gizmos(conversation)
            if not criteria.required_gizmos.issubset(conversation_gizmos):
                return False
        
        # Check plugin requirements
        if criteria.required_plugins:
            conversation_plugins = ConversationFilter._get_conversation_plugins(conversation)
            if not criteria.required_plugins.issubset(conversation_plugins):
                return False
        
        # Check custom filters
        for custom_filter in criteria.custom_filters:
            try:
                if not custom_filter(conversation):
                    return False
            except Exception:
                # Skip failed filters
                return False
        
        return True
    
    @staticmethod
    def filter_conversations(conversations: List[Conversation], 
                           criteria: FilterCriteria) -> List[Conversation]:
        """
        Filter a list of conversations based on criteria.
        
        Args:
            conversations: List of conversations to filter
            criteria: Filter criteria
            
        Returns:
            Filtered list of conversations
        """
        return [
            conv for conv in conversations 
            if ConversationFilter.matches_criteria(conv, criteria)
        ]
    
    @staticmethod
    def _get_conversation_gizmos(conversation: Conversation) -> Set[str]:
        """Extract gizmo IDs from conversation annotations."""
        gizmos = set()
        
        for name, value in conversation.annotations.items():
            if name.startswith('gizmo_') and isinstance(value, dict):
                gizmo_id = value.get('gizmo_id')
                if gizmo_id:
                    gizmos.add(gizmo_id)
        
        return gizmos
    
    @staticmethod
    def _get_conversation_plugins(conversation: Conversation) -> Set[str]:
        """Extract plugin IDs from conversation annotations."""
        plugins = set()
        
        for name, value in conversation.annotations.items():
            if name.startswith('plugin_') and isinstance(value, dict):
                plugin_id = value.get('plugin_id')
                if plugin_id:
                    plugins.add(plugin_id)
        
        return plugins


# Convenience functions for common filtering patterns
def create_gizmo_filter(gizmo_id: str) -> FilterCriteria:
    """Create filter for specific gizmo usage."""
    return FilterCriteria(required_gizmos={gizmo_id})


def create_claude_obsidian_filter(obsidian_chat_ids: Set[str]) -> FilterCriteria:
    """Create filter for Claude Obsidian chat conversations."""
    return FilterCriteria(
        custom_filters=[
            lambda conv: conv.conversation_id in obsidian_chat_ids
        ]
    )


def create_annotation_filter(required: Set[str] = None, 
                           forbidden: Set[str] = None) -> FilterCriteria:
    """Create filter based on required and forbidden annotations."""
    return FilterCriteria(
        required_annotations=required or set(),
        forbidden_annotations=forbidden or set()
    )
