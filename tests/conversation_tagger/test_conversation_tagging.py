# tests/conversation_tagger/test_conversation_tagging.py
"""
Tests for conversation-level tagging functionality.
"""

import pytest
from conversation_tagger.core.tagger import ConversationTagger
from conversation_tagger.core.tag import Tag
from conversation_tagger.core.conversation import Conversation
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.factory import create_default_tagger


def test_conversation_rule_addition():
    """Test adding conversation-level rules."""
    tagger = ConversationTagger()
    
    def simple_rule(conversation):
        return conversation.exchange_count > 1
    
    tagger.add_conversation_rule('multi_exchange', simple_rule)
    
    assert 'multi_exchange' in tagger.conversation_rules
    assert tagger.conversation_rules['multi_exchange'] == simple_rule


def test_conversation_tagging_basic():
    """Test basic conversation-level tagging."""
    tagger = ConversationTagger()
    
    # Add a simple rule
    def has_many_exchanges(conversation):
        if conversation.exchange_count >= 3:
            return Tag('conversation_size', size='large', count=conversation.exchange_count)
        return False
    
    tagger.add_conversation_rule('conversation_size', has_many_exchanges)
    
    # Create test conversation data
    conversation_data = {
        'conversation_id': 'test_conv',
        'title': 'Multi-exchange conversation',
        'mapping': {
            'msg1': {'message': {'author': {'role': 'user'}, 'create_time': 1000, 'content': {'text': 'First question'}}},
            'msg2': {'message': {'author': {'role': 'assistant'}, 'create_time': 2000, 'content': {'text': 'First answer'}}},
            'msg3': {'message': {'author': {'role': 'user'}, 'create_time': 3000, 'content': {'text': 'Second question'}}},
            'msg4': {'message': {'author': {'role': 'assistant'}, 'create_time': 4000, 'content': {'text': 'Second answer'}}},
            'msg5': {'message': {'author': {'role': 'user'}, 'create_time': 5000, 'content': {'text': 'Third question'}}},
            'msg6': {'message': {'author': {'role': 'assistant'}, 'create_time': 6000, 'content': {'text': 'Third answer'}}}
        }
    }
    
    # Tag the conversation
    result = tagger.tag_conversation(conversation_data)
    
    # Should have conversation-level tag
    conversation_tags = [tag for tag in result.tags if tag.name == 'conversation_size']
    assert len(conversation_tags) == 1
    
    tag = conversation_tags[0]
    assert tag.attributes['size'] == 'large'
    assert tag.attributes['count'] == 3


def test_conversation_tagging_multiple_rules():
    """Test multiple conversation-level rules."""
    tagger = ConversationTagger()
    
    def length_rule(conversation):
        return Tag('length_info', exchanges=conversation.exchange_count)
    
    def complexity_rule(conversation):
        return conversation.total_message_count > 4
    
    tagger.add_conversation_rule('length_info', length_rule)
    tagger.add_conversation_rule('is_complex', complexity_rule)
    
    # Create test data
    conversation_data = {
        'conversation_id': 'test_conv',
        'title': 'Test conversation',
        'mapping': {
            'msg1': {'message': {'author': {'role': 'user'}, 'create_time': 1000, 'content': {'text': 'Question 1'}}},
            'msg2': {'message': {'author': {'role': 'assistant'}, 'create_time': 2000, 'content': {'text': 'Answer 1'}}},
            'msg3': {'message': {'author': {'role': 'user'}, 'create_time': 3000, 'content': {'text': 'Question 2'}}},
            'msg4': {'message': {'author': {'role': 'assistant'}, 'create_time': 4000, 'content': {'text': 'Answer 2'}}},
            'msg5': {'message': {'author': {'role': 'user'}, 'create_time': 5000, 'content': {'text': 'Question 3'}}},
            'msg6': {'message': {'author': {'role': 'assistant'}, 'create_time': 6000, 'content': {'text': 'Answer 3'}}}
        }
    }
    
    result = tagger.tag_conversation(conversation_data)
    
    # Check both rules applied
    tag_names = [tag.name for tag in result.tags]
    assert 'length_info' in tag_names
    assert 'is_complex' in tag_names
    
    # Check specific tag attributes
    length_tags = [tag for tag in result.tags if tag.name == 'length_info']
    assert len(length_tags) == 1
    assert length_tags[0].attributes['exchanges'] == 3


def test_conversation_rule_error_handling():
    """Test that conversation rule errors are handled gracefully."""
    tagger = ConversationTagger()
    
    def broken_rule(conversation):
        raise ValueError("This rule always fails")
    
    def working_rule(conversation):
        return True
    
    tagger.add_conversation_rule('broken', broken_rule)
    tagger.add_conversation_rule('working', working_rule)
    
    # Simple conversation data
    conversation_data = {
        'conversation_id': 'test_conv',
        'title': 'Test conversation',
        'mapping': {
            'msg1': {'message': {'author': {'role': 'user'}, 'create_time': 1000, 'content': {'text': 'Hello'}}},
            'msg2': {'message': {'author': {'role': 'assistant'}, 'create_time': 2000, 'content': {'text': 'Hi there!'}}}
        }
    }
    
    # Should not raise exception
    result = tagger.tag_conversation(conversation_data)
    
    # Working rule should have applied, broken rule should be skipped
    tag_names = [tag.name for tag in result.tags]
    assert 'working' in tag_names
    assert 'broken' not in tag_names

