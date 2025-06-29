# tests/test_basic.py
"""
Basic test to verify the improved exchange system works.
"""

import pytest
from conversation_tagger import create_default_tagger, Tag
from conversation_tagger.core.exchange import Exchange


def create_test_conversation():
    """Create a simple test conversation with continuation."""
    return {
        'conversation_id': 'test_conv',
        'title': 'Test Conversation',
        'mapping': {
            'node1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {
                        'text': 'Fix this Python code:\n```python\nprint("hello")\n```',
                        'parts': []
                    }
                }
            },
            'node2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {
                        'text': 'Here is the fix:\n```python\nprint("Hello, World!")\n```',
                        'parts': []
                    }
                }
            },
            'node3': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 3000,
                    'content': {
                        'text': '> Here is the fix\n\nelaborate',
                        'parts': []
                    }
                }
            },
            'node4': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 4000,
                    'content': {
                        'text': 'The fix adds proper formatting and follows Python conventions...',
                        'parts': []
                    }
                }
            }
        }
    }


def test_exchange_merge_operator():
    """Test that Exchange.__add__ works correctly with time ordering."""
    # Create two simple exchanges with different timestamps
    exchange1 = Exchange(
        exchange_id='test_1',
        conversation_id='conv_1',
        messages=[
            {'author': {'role': 'user'}, 'content': {'text': 'Hello'}, 'create_time': 1000},
            {'author': {'role': 'assistant'}, 'content': {'text': 'Hi there'}, 'create_time': 2000}
        ]
    )
    
    exchange2 = Exchange(
        exchange_id='test_2', 
        conversation_id='conv_1',
        messages=[
            {'author': {'role': 'user'}, 'content': {'text': 'Continue'}, 'create_time': 3000},
            {'author': {'role': 'assistant'}, 'content': {'text': 'Sure thing'}, 'create_time': 4000}
        ]
    )
    
    # Merge them
    merged = exchange1 + exchange2
    
    # Check merged properties
    assert len(merged.messages) == 4
    assert merged.conversation_id == 'conv_1'
    assert len(merged.exchange_id) == 36  # UUID length
    assert merged.exchange_id != exchange1.exchange_id  # New UUID generated
    
    # Check messages are ordered by time
    times = [msg.get('create_time', 0) for msg in merged.messages]
    assert times == [1000, 2000, 3000, 4000]  # Should be in chronological order
    
    # Check message sequence is preserved
    roles = [msg['author']['role'] for msg in merged.messages]
    assert roles == ['user', 'assistant', 'user', 'assistant']
    
    # Check text extraction works
    assert 'Hello' in merged.get_user_text()
    assert 'Continue' in merged.get_user_text()
    assert 'Hi there' in merged.get_assistant_text()
    assert 'Sure thing' in merged.get_assistant_text()


def test_exchange_time_ordering():
    """Test that messages are properly ordered by time during merge."""
    # Create exchanges where the second one actually happened first
    exchange1 = Exchange(
        exchange_id='test_1',
        conversation_id='conv_1',
        messages=[
            {'author': {'role': 'user'}, 'content': {'text': 'Second message'}, 'create_time': 3000},
            {'author': {'role': 'assistant'}, 'content': {'text': 'Second response'}, 'create_time': 4000}
        ]
    )
    
    exchange2 = Exchange(
        exchange_id='test_2',
        conversation_id='conv_1', 
        messages=[
            {'author': {'role': 'user'}, 'content': {'text': 'First message'}, 'create_time': 1000},
            {'author': {'role': 'assistant'}, 'content': {'text': 'First response'}, 'create_time': 2000}
        ]
    )
    
    # Merge them
    merged = exchange1 + exchange2
    
    # Check that messages are now properly ordered by time
    texts = [msg['content']['text'] for msg in merged.messages]
    assert texts == ['First message', 'First response', 'Second message', 'Second response']
    
    # Check first_message_time property
    assert merged.first_message_time == 1000


def test_exchange_create_method():
    """Test the Exchange.create class method."""
    messages = [
        {'author': {'role': 'user'}, 'content': {'text': 'Test'}, 'create_time': 1000}
    ]
    
    exchange = Exchange.create('test_conv', messages)
    
    assert exchange.conversation_id == 'test_conv'
    assert exchange.messages == messages
    assert len(exchange.exchange_id) == 36  # UUID length
    assert exchange.tags == []  # Empty tags list


def test_exchange_methods():
    """Test Exchange helper methods."""
    exchange = Exchange(
        exchange_id='test',
        conversation_id='conv',
        messages=[
            {'author': {'role': 'user'}, 'content': {'text': 'First question'}, 'create_time': 1000},
            {'author': {'role': 'assistant'}, 'content': {'text': 'First answer'}, 'create_time': 2000},
            {'author': {'role': 'user'}, 'content': {'text': 'Follow up'}, 'create_time': 3000},
            {'author': {'role': 'assistant'}, 'content': {'text': 'Second answer'}, 'create_time': 4000}
        ]
    )
    
    # Test message filtering
    assert len(exchange.get_user_messages()) == 2
    assert len(exchange.get_assistant_messages()) == 2
    
    # Test continuation detection
    assert exchange.has_continuations() == True
    
    # Test text extraction
    user_text = exchange.get_user_text()
    assert 'First question' in user_text
    assert 'Follow up' in user_text
    
    assistant_text = exchange.get_assistant_text()
    assert 'First answer' in assistant_text
    assert 'Second answer' in assistant_text
    
    # Test first_message_time
    assert exchange.first_message_time == 1000


def test_improved_parsing():
    """Test that the improved parsing creates proper exchanges."""
    tagger = create_default_tagger()
    conversation = create_test_conversation()
    
    result = tagger.tag_conversation(conversation)
    
    # Should have basic structure
    assert 'conversation_id' in result
    assert 'tags' in result
    assert 'exchanges' in result
    assert 'exchange_count' in result
    
    # Should have 1 exchange (continuation merged)
    assert result['exchange_count'] == 1
    
    # The exchange should have 4 messages (user->asst->user->asst)
    exchange = result['exchanges'][0]['exchange']
    assert len(exchange.messages) == 4
    assert exchange.has_continuations()
    
    # Should detect all the expected tags
    tag_names = [tag.name for tag in result['tags']]
    #assert 'has_user_has_code_blocks' in tag_names
    #assert 'has_assistant_has_code_blocks' in tag_names
    assert 'has_has_quote_elaborate' in tag_names
    #assert 'has_mentions_programming_language' in tag_names
    assert 'has_exchange_type' in tag_names




def test_modular_continuation_rules():
    """Test the modular continuation rule system."""
    from conversation_tagger.core.exchange_parser import ExchangeParser, quote_elaborate_rule, simple_continuation_rule
    
    parser = ExchangeParser()
    
    # Test individual rules
    exchange1 = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Question'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Answer'}, 'create_time': 2000}
    ])
    
    # Quote + elaborate pattern
    exchange2 = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': '> Answer\n\nelaborate'}, 'create_time': 3000}
    ])
    
    assert quote_elaborate_rule(exchange1, exchange2) == True
    assert simple_continuation_rule(exchange1, exchange2) == False
    
    # Simple continuation
    exchange3 = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'continue'}, 'create_time': 3000}
    ])
    
    assert quote_elaborate_rule(exchange1, exchange3) == False
    assert simple_continuation_rule(exchange1, exchange3) == True
    
    # Test adding custom rule
    def custom_rule(prev_exchange: Exchange, curr_exchange: Exchange) -> bool:
        """Custom rule for testing."""
        user_messages = curr_exchange.get_user_messages()
        if not user_messages:
            return False
        text = user_messages[0].get('content', {}).get('text', '').strip()
        return text.startswith('CUSTOM:')
    
    parser.add_continuation_rule(custom_rule)
    assert len(parser.continuation_rules) == 4  # 3 default + 1 custom


def test_continuation_rule_integration():
    """Test that continuation rules work in full parsing."""
    conversation = {
        'conversation_id': 'rule_test',
        'mapping': {
            'node1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'What is Python?'}
                }
            },
            'node2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'Python is a programming language.'}
                }
            },
            'node3': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 3000,
                    'content': {'text': 'more'}  # Simple continuation
                }
            },
            'node4': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 4000,
                    'content': {'text': 'It was created by Guido van Rossum.'}
                }
            }
        }
    }
    
    from conversation_tagger.core.exchange_parser import ExchangeParser
    parser = ExchangeParser()
    exchanges = parser.parse_conversation(conversation)
    
    # Should merge into 1 exchange due to 'more' continuation
    assert len(exchanges) == 1
    assert len(exchanges[0].messages) == 4


def test_tag_creation():
    """Test Tag class works with attributes."""
    tag = Tag('test_tag', value=42, category='example')
    
    assert tag.name == 'test_tag'
    assert tag.attributes['value'] == 42
    assert 'value=42' in str(tag)
    assert tag == 'test_tag'  # String comparison

