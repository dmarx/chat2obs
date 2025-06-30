# tests/test_core.py
"""
Core functionality tests for conversation tagging system.
"""

import pytest
from conversation_tagger.core.tag import Tag
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.conversation import Conversation


def test_tag_creation():
    """Test tag creation with and without attributes."""
    simple_tag = Tag('simple')
    assert simple_tag.name == 'simple'
    assert simple_tag.attributes == {}
    assert str(simple_tag) == 'simple'
    
    complex_tag = Tag('complex', count=5, type='test')
    assert complex_tag.attributes['count'] == 5
    assert 'count=5' in str(complex_tag)
    
    # Test equality
    assert simple_tag == 'simple'
    assert simple_tag != complex_tag


def test_exchange_basic():
    """Test exchange creation and basic operations."""
    messages = [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Hi!'}, 'create_time': 2000}
    ]
    
    exchange = Exchange.create('conv_1', messages)
    
    assert exchange.conversation_id == 'conv_1'
    assert len(exchange) == 2
    assert len(exchange.get_user_messages()) == 1
    assert len(exchange.get_assistant_messages()) == 1
    assert not exchange.has_continuations()


def test_exchange_merging():
    """Test merging exchanges preserves chronological order."""
    exchange_1 = Exchange.create('conv_1', [
        {'author': {'role': 'user'}, 'content': {'text': 'First'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Response'}, 'create_time': 2000}
    ])
    
    exchange_2 = Exchange.create('conv_1', [
        {'author': {'role': 'user'}, 'content': {'text': 'Continue'}, 'create_time': 3000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'More'}, 'create_time': 4000}
    ])
    
    merged = exchange_1 + exchange_2
    
    assert len(merged) == 4
    assert merged.has_continuations()
    assert merged.conversation_id == 'conv_1'
    
    # Verify time ordering
    times = [msg['create_time'] for msg in merged.messages]
    assert times == [1000, 2000, 3000, 4000]


def test_conversation_properties():
    """Test conversation aggregation properties."""
    exchanges = [
        Exchange.create('conv_1', [
            {'author': {'role': 'user'}, 'content': {'text': 'Q1'}, 'create_time': 1000},
            {'author': {'role': 'assistant'}, 'content': {'text': 'A1'}, 'create_time': 2000}
        ]),
        Exchange.create('conv_1', [
            {'author': {'role': 'user'}, 'content': {'text': 'Q2'}, 'create_time': 3000},
            {'author': {'role': 'assistant'}, 'content': {'text': 'A2'}, 'create_time': 4000}
        ])
    ]
    
    conv = Conversation('conv_1', 'Test Chat', exchanges)
    
    assert conv.exchange_count == 2
    assert conv.total_message_count == 4
    assert conv.total_user_messages == 2
    assert conv.total_assistant_messages == 2
    assert 'Q1' in conv.get_all_user_text()
    assert 'A1' in conv.get_all_assistant_text()


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for parsing tests."""
    return {
        'conversation_id': 'test_conv',
        'title': 'Test Chat',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'Hello'}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'Hi there!'}
                }
            }
        }
    }


def test_simple_parsing(sample_conversation_data):
    """Test basic conversation parsing."""
    from conversation_tagger.core.exchange_parser import ExchangeParser
    
    parser = ExchangeParser()
    conversation = parser.parse_conversation(sample_conversation_data)
    
    assert isinstance(conversation, Conversation)
    assert conversation.conversation_id == 'test_conv'
    assert conversation.exchange_count == 1
    assert 'Hello' in conversation.get_all_user_text()
