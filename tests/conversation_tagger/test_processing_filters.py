# tests/conversation_tagger/test_processing_filters.py
"""
Tests for processing filters functionality.
"""

import pytest
from unittest.mock import MagicMock

from conversation_tagger.processing.filters import (
    FilterCriteria,
    ConversationFilter,
    create_gizmo_filter,
    create_claude_obsidian_filter,
    create_annotation_filter
)
from conversation_tagger.core.conversation import Conversation


class TestFilterCriteria:
    """Test FilterCriteria dataclass."""
    
    def test_init_defaults(self):
        """Test initialization with default values."""
        criteria = FilterCriteria()
        
        assert criteria.required_annotations == set()
        assert criteria.forbidden_annotations == set()
        assert criteria.custom_filters == []
        assert criteria.required_gizmos == set()
        assert criteria.required_plugins == set()
    
    def test_init_with_values(self):
        """Test initialization with specific values."""
        custom_filter = lambda x: True
        
        criteria = FilterCriteria(
            required_annotations={'annotation1', 'annotation2'},
            forbidden_annotations={'forbidden1'},
            custom_filters=[custom_filter],
            required_gizmos={'gizmo1'},
            required_plugins={'plugin1'}
        )
        
        assert criteria.required_annotations == {'annotation1', 'annotation2'}
        assert criteria.forbidden_annotations == {'forbidden1'}
        assert criteria.custom_filters == [custom_filter]
        assert criteria.required_gizmos == {'gizmo1'}
        assert criteria.required_plugins == {'plugin1'}


class TestConversationFilter:
    """Test ConversationFilter class."""
    
    def create_mock_conversation(self, conversation_id="test_id", annotations=None):
        """Helper to create mock conversation."""
        conv = MagicMock(spec=Conversation)
        conv.conversation_id = conversation_id
        conv.annotations = annotations or {}
        conv.has_annotation.side_effect = lambda name: name in conv.annotations
        return conv
    
    def test_matches_criteria_required_annotations_pass(self):
        """Test matching with required annotations - pass case."""
        conv = self.create_mock_conversation(
            annotations={'has_code': True, 'has_github': True}
        )
        
        criteria = FilterCriteria(
            required_annotations={'has_code', 'has_github'}
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is True
    
    def test_matches_criteria_required_annotations_fail(self):
        """Test matching with required annotations - fail case."""
        conv = self.create_mock_conversation(
            annotations={'has_code': True}
        )
        
        criteria = FilterCriteria(
            required_annotations={'has_code', 'has_github'}
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is False
    
    def test_matches_criteria_forbidden_annotations_pass(self):
        """Test matching with forbidden annotations - pass case."""
        conv = self.create_mock_conversation(
            annotations={'has_code': True}
        )
        
        criteria = FilterCriteria(
            forbidden_annotations={'has_attachments', 'has_errors'}
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is True
    
    def test_matches_criteria_forbidden_annotations_fail(self):
        """Test matching with forbidden annotations - fail case."""
        conv = self.create_mock_conversation(
            annotations={'has_code': True, 'has_attachments': True}
        )
        
        criteria = FilterCriteria(
            forbidden_annotations={'has_attachments'}
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is False
    
    def test_matches_criteria_gizmos_pass(self):
        """Test matching with required gizmos - pass case."""
        conv = self.create_mock_conversation(
            annotations={
                'gizmo_1': {'gizmo_id': 'dalle'},
                'gizmo_2': {'gizmo_id': 'browser'}
            }
        )
        
        criteria = FilterCriteria(
            required_gizmos={'dalle'}
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is True
    
    def test_matches_criteria_gizmos_fail(self):
        """Test matching with required gizmos - fail case."""
        conv = self.create_mock_conversation(
            annotations={
                'gizmo_1': {'gizmo_id': 'browser'}
            }
        )
        
        criteria = FilterCriteria(
            required_gizmos={'dalle'}
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is False
    
    def test_matches_criteria_plugins_pass(self):
        """Test matching with required plugins - pass case."""
        conv = self.create_mock_conversation(
            annotations={
                'plugin_1': {'plugin_id': 'web_search'},
                'plugin_2': {'plugin_id': 'calculator'}
            }
        )
        
        criteria = FilterCriteria(
            required_plugins={'web_search'}
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is True
    
    def test_matches_criteria_plugins_fail(self):
        """Test matching with required plugins - fail case."""
        conv = self.create_mock_conversation(
            annotations={
                'plugin_1': {'plugin_id': 'calculator'}
            }
        )
        
        criteria = FilterCriteria(
            required_plugins={'web_search'}
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is False
    
    def test_matches_criteria_custom_filters_pass(self):
        """Test matching with custom filters - pass case."""
        conv = self.create_mock_conversation()
        conv.exchange_count = 5
        
        criteria = FilterCriteria(
            custom_filters=[
                lambda c: c.exchange_count > 3,
                lambda c: c.conversation_id == "test_id"
            ]
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is True
    
    def test_matches_criteria_custom_filters_fail(self):
        """Test matching with custom filters - fail case."""
        conv = self.create_mock_conversation()
        conv.exchange_count = 2
        
        criteria = FilterCriteria(
            custom_filters=[
                lambda c: c.exchange_count > 3
            ]
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is False
    
    def test_matches_criteria_custom_filter_exception(self):
        """Test handling of custom filter exceptions."""
        conv = self.create_mock_conversation()
        
        def failing_filter(c):
            raise Exception("Filter error")
        
        criteria = FilterCriteria(
            custom_filters=[failing_filter]
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is False
    
    def test_matches_criteria_combined(self):
        """Test matching with multiple criteria types."""
        conv = self.create_mock_conversation(
            annotations={
                'has_code': True,
                'gizmo_1': {'gizmo_id': 'dalle'}
            }
        )
        conv.exchange_count = 5
        
        criteria = FilterCriteria(
            required_annotations={'has_code'},
            forbidden_annotations={'has_errors'},
            required_gizmos={'dalle'},
            custom_filters=[lambda c: c.exchange_count > 3]
        )
        
        result = ConversationFilter.matches_criteria(conv, criteria)
        assert result is True
    
    def test_filter_conversations(self):
        """Test filtering a list of conversations."""
        conv1 = self.create_mock_conversation("id1", {'has_code': True})
        conv2 = self.create_mock_conversation("id2", {'has_attachments': True})
        conv3 = self.create_mock_conversation("id3", {'has_code': True, 'has_github': True})
        
        conversations = [conv1, conv2, conv3]
        
        criteria = FilterCriteria(
            required_annotations={'has_code'},
            forbidden_annotations={'has_attachments'}
        )
        
        filtered = ConversationFilter.filter_conversations(conversations, criteria)
        
        assert len(filtered) == 2
        assert conv1 in filtered
        assert conv3 in filtered
        assert conv2 not in filtered
    
    def test_get_conversation_gizmos(self):
        """Test extracting gizmo IDs from conversation."""
        conv = self.create_mock_conversation(
            annotations={
                'gizmo_1': {'gizmo_id': 'dalle'},
                'gizmo_2': {'gizmo_id': 'browser'},
                'not_gizmo': {'other_field': 'value'},
                'gizmo_3': {'no_gizmo_id': 'value'}
            }
        )
        
        gizmos = ConversationFilter._get_conversation_gizmos(conv)
        
        assert gizmos == {'dalle', 'browser'}
    
    def test_get_conversation_plugins(self):
        """Test extracting plugin IDs from conversation."""
        conv = self.create_mock_conversation(
            annotations={
                'plugin_1': {'plugin_id': 'web_search'},
                'plugin_2': {'plugin_id': 'calculator'},
                'not_plugin': {'other_field': 'value'},
                'plugin_3': {'no_plugin_id': 'value'}
            }
        )
        
        plugins = ConversationFilter._get_conversation_plugins(conv)
        
        assert plugins == {'web_search', 'calculator'}


class TestConvenienceFunctions:
    """Test convenience filter creation functions."""
    
    def test_create_gizmo_filter(self):
        """Test creating gizmo filter."""
        criteria = create_gizmo_filter('dalle')
        
        assert isinstance(criteria, FilterCriteria)
        assert criteria.required_gizmos == {'dalle'}
        assert criteria.required_annotations == set()
        assert criteria.forbidden_annotations == set()
    
    def test_create_claude_obsidian_filter(self):
        """Test creating Claude Obsidian chat filter."""
        chat_ids = {'chat1', 'chat2'}
        criteria = create_claude_obsidian_filter(chat_ids)
        
        assert isinstance(criteria, FilterCriteria)
        assert len(criteria.custom_filters) == 1
        
        # Test the custom filter
        conv = MagicMock()
        conv.conversation_id = 'chat1'
        assert criteria.custom_filters[0](conv) is True
        
        conv.conversation_id = 'other_chat'
        assert criteria.custom_filters[0](conv) is False
    
    def test_create_annotation_filter(self):
        """Test creating annotation-based filter."""
        required = {'has_code', 'has_github'}
        forbidden = {'has_errors', 'has_attachments'}
        
        criteria = create_annotation_filter(required, forbidden)
        
        assert isinstance(criteria, FilterCriteria)
        assert criteria.required_annotations == required
        assert criteria.forbidden_annotations == forbidden
    
    def test_create_annotation_filter_defaults(self):
        """Test creating annotation filter with defaults."""
        criteria = create_annotation_filter()
        
        assert isinstance(criteria, FilterCriteria)
        assert criteria.required_annotations == set()
        assert criteria.forbidden_annotations == set()
