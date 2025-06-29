# tests/conversation_tagger/test_simple.py
"""
Simple test suite for main features and happy paths.
"""

import pytest
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.exchange_parser import ExchangeParser
from conversation_tagger.core.exchange_tagger import ExchangeTagger
from conversation_tagger.core.tag import Tag
from conversation_tagger.core.conversation import Conversation


def test_exchange_basic_operations():
    """Test basic Exchange creation and operations."""
    # Create a simple exchange
    messages = [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Hi there!'}, 'create_time': 2000}
    ]
    
    exchange = Exchange.create('test_conv', messages)
    
    # Basic properties
    assert exchange.conversation_id == 'test_conv'
    assert len(exchange.messages) == 2
    assert len(exchange.exchange_id) == 36  # UUID length
    
    # Text extraction
    assert exchange.get_user_text() == 'Hello'
    assert exchange.get_assistant_text() == 'Hi there!'
    
    # Message filtering
    assert len(exchange.get_user_messages()) == 1
    assert len(exchange.get_assistant_messages()) == 1
    
    # No continuations in simple exchange
    assert not exchange.has_continuations()


def test_exchange_merging():
    """Test exchange merging with + operator."""
    exchange1 = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Question'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Answer'}, 'create_time': 2000}
    ])
    
    exchange2 = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Follow up'}, 'create_time': 3000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'More info'}, 'create_time': 4000}
    ])
    
    merged = exchange1 + exchange2
    
    # Check merged properties
    assert len(merged.messages) == 4
    assert merged.conversation_id == 'test'
    assert merged.has_continuations()  # Now has multiple user messages
    
    # Check text contains both exchanges
    assert 'Question' in merged.get_user_text()
    assert 'Follow up' in merged.get_user_text()
    assert 'Answer' in merged.get_assistant_text()
    assert 'More info' in merged.get_assistant_text()
    
    # Check time ordering is preserved
    times = [msg.get('create_time') for msg in merged.messages]
    assert times == [1000, 2000, 3000, 4000]


def test_tag_creation():
    """Test Tag creation and attributes."""
    # Simple tag
    tag1 = Tag('simple_tag')
    assert tag1.name == 'simple_tag'
    assert tag1.attributes == {}
    assert str(tag1) == 'simple_tag'
    
    # Tag with attributes
    tag2 = Tag('complex_tag', count=5, category='test')
    assert tag2.name == 'complex_tag'
    assert tag2.attributes['count'] == 5
    assert tag2.attributes['category'] == 'test'
    assert 'count=5' in str(tag2)
    assert 'category=test' in str(tag2)
    
    # Tag equality
    assert tag1 == 'simple_tag'
    assert tag1 != tag2


def test_exchange_tagger():
    """Test ExchangeTagger with simple rules."""
    tagger = ExchangeTagger()
    
    # Add a simple rule
    def has_greeting(exchange):
        text = exchange.get_user_text().lower()
        return 'hello' in text or 'hi' in text
    
    tagger.add_rule('greeting', has_greeting)
    
    # Test with greeting
    exchange_with_greeting = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello there!'}, 'create_time': 1000}
    ])
    
    tagged_exchange = tagger.tag_exchange(exchange_with_greeting)
    tag_names = [tag.name for tag in tagged_exchange.tags]
    assert 'greeting' in tag_names
    
    # Test without greeting
    exchange_no_greeting = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'What is Python?'}, 'create_time': 1000}
    ])
    
    tagged_exchange = tagger.tag_exchange(exchange_no_greeting)
    tag_names = [tag.name for tag in tagged_exchange.tags]
    assert 'greeting' not in tag_names


def test_conversation_creation():
    """Test Conversation object creation and properties."""
    exchanges = [
        Exchange.create('test_conv', [
            {'author': {'role': 'user'}, 'content': {'text': 'First question'}, 'create_time': 1000},
            {'author': {'role': 'assistant'}, 'content': {'text': 'First answer'}, 'create_time': 2000}
        ]),
        Exchange.create('test_conv', [
            {'author': {'role': 'user'}, 'content': {'text': 'Second question'}, 'create_time': 3000},
            {'author': {'role': 'assistant'}, 'content': {'text': 'Second answer'}, 'create_time': 4000}
        ])
    ]
    
    conversation = Conversation(
        conversation_id='test_conv',
        title='Test Conversation',
        exchanges=exchanges
    )
    
    # Basic properties
    assert conversation.conversation_id == 'test_conv'
    assert conversation.title == 'Test Conversation'
    assert conversation.exchange_count == 2
    assert conversation.total_message_count == 4
    assert conversation.total_user_messages == 2
    assert conversation.total_assistant_messages == 2
    
    # Text aggregation
    user_text = conversation.get_all_user_text()
    assert 'First question' in user_text
    assert 'Second question' in user_text
    
    assistant_text = conversation.get_all_assistant_text()
    assert 'First answer' in assistant_text
    assert 'Second answer' in assistant_text


def test_simple_parsing():
    """Test basic conversation parsing."""
    # Simple test conversation
    conversation_data = {
        'conversation_id': 'test_conv',
        'title': 'Test Chat',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'Hello, how are you?'}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'}, 
                    'create_time': 2000,
                    'content': {'text': 'I\'m doing well, thank you!'}
                }
            }
        }
    }
    
    parser = ExchangeParser()
    conversation = parser.parse_conversation(conversation_data)
    
    assert isinstance(conversation, Conversation)
    assert conversation.conversation_id == 'test_conv'
    assert conversation.title == 'Test Chat'
    assert conversation.exchange_count == 1
    
    exchange = conversation.exchanges[0]
    assert len(exchange.messages) == 2
    assert 'Hello, how are you?' in exchange.get_user_text()
    assert 'I\'m doing well, thank you!' in exchange.get_assistant_text()


def test_continuation_detection():
    """Test that continuation patterns are detected and merged."""
    conversation_data = {
        'conversation_id': 'test_conv',
        'title': 'Test Chat',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'Tell me about Python'}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000, 
                    'content': {'text': 'Python is a programming language...'}
                }
            },
            'msg3': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 3000,
                    'content': {'text': 'continue'}  # Continuation keyword
                }
            },
            'msg4': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 4000,
                    'content': {'text': 'It was created by Guido van Rossum...'}
                }
            }
        }
    }
    
    parser = ExchangeParser()
    conversation = parser.parse_conversation(conversation_data)
    
    # Should merge into single exchange due to continuation
    assert conversation.exchange_count == 1
    
    exchange = conversation.exchanges[0]
    assert len(exchange.messages) == 4
    assert exchange.has_continuations()
    
    # Check all content is preserved
    user_text = exchange.get_user_text()
    assert 'Tell me about Python' in user_text
    assert 'continue' in user_text
    
    assistant_text = exchange.get_assistant_text()
    assert 'Python is a programming language' in assistant_text
    assert 'Guido van Rossum' in assistant_text


def test_quote_elaborate_pattern():
    """Test quote + elaborate continuation pattern."""
    conversation_data = {
        'conversation_id': 'test_conv',
        'title': 'Test Chat',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'What is machine learning?'}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'Machine learning is a subset of AI.'}
                }
            },
            'msg3': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 3000,
                    'content': {'text': '> Machine learning is a subset of AI.\n\nelaborate'}
                }
            },
            'msg4': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 4000,
                    'content': {'text': 'It involves algorithms that improve through experience...'}
                }
            }
        }
    }
    
    parser = ExchangeParser()
    conversation = parser.parse_conversation(conversation_data)
    
    # Should merge due to quote + elaborate pattern
    assert conversation.exchange_count == 1
    
    exchange = conversation.exchanges[0]
    assert len(exchange.messages) == 4
    assert 'What is machine learning?' in exchange.get_user_text()
    assert 'elaborate' in exchange.get_user_text()
    assert 'algorithms that improve' in exchange.get_assistant_text()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
