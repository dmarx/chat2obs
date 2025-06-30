# tests/test_tagging.py
"""
Tagging functionality tests for exchanges and conversations.
"""

import pytest
from conversation_tagger.core.exchange_tagger import ExchangeTagger
from conversation_tagger.core.tagger import ConversationTagger
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.tag import Tag


def test_exchange_tagger_basic():
    """Test basic exchange tagging functionality."""
    tagger = ExchangeTagger()
    
    def has_greeting(exchange):
        user_text = ' '.join(exchange.get_user_texts()).lower()
        return 'hello' in user_text or 'hi' in user_text
    
    tagger.add_rule('greeting', has_greeting)
    
    # Test with greeting
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello world!'}, 'create_time': 1000}
    ])
    
    tagged = tagger.tag_exchange(exchange)
    assert any(tag.name == 'greeting' for tag in tagged.tags)
    
    # Test without greeting
    exchange_no_greeting = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'What is Python?'}, 'create_time': 1000}
    ])
    
    tagged_no_greeting = tagger.tag_exchange(exchange_no_greeting)
    assert not any(tag.name == 'greeting' for tag in tagged_no_greeting.tags)


def test_exchange_tagger_with_attributes():
    """Test exchange tagging with tag attributes."""
    tagger = ExchangeTagger()
    
    def message_length(exchange):
        text = exchange.get_user_text()
        length = len(text)
        if length > 50:
            return Tag('message_length', size='long', chars=length)
        elif length > 10:
            return Tag('message_length', size='medium', chars=length)
        return False
    
    tagger.add_rule('message_length', message_length)
    
    long_exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'This is a very long message that should definitely be tagged as long since it exceeds the threshold'}, 'create_time': 1000}
    ])
    
    tagged = tagger.tag_exchange(long_exchange)
    length_tags = [tag for tag in tagged.tags if tag.name == 'message_length']
    
    assert len(length_tags) == 1
    assert length_tags[0].attributes['size'] == 'long'
    assert length_tags[0].attributes['chars'] > 50


def test_conversation_tagger():
    """Test conversation-level tagging."""
    tagger = ConversationTagger()
    
    def is_multi_turn(conversation):
        return conversation.exchange_count > 1
    
    def exchange_count_info(conversation):
        return Tag('exchange_info', count=conversation.exchange_count)
    
    tagger.add_conversation_rule('multi_turn', is_multi_turn)
    tagger.add_conversation_rule('exchange_info', exchange_count_info)
    
    # Create conversation data with multiple exchanges
    conversation_data = {
        'conversation_id': 'test_conv',
        'title': 'Multi-turn conversation',
        'mapping': {
            'msg1': {'message': {'author': {'role': 'user'}, 'create_time': 1000, 'content': {'text': 'First'}}},
            'msg2': {'message': {'author': {'role': 'assistant'}, 'create_time': 2000, 'content': {'text': 'Response 1'}}},
            'msg3': {'message': {'author': {'role': 'user'}, 'create_time': 3000, 'content': {'text': 'Second'}}},
            'msg4': {'message': {'author': {'role': 'assistant'}, 'create_time': 4000, 'content': {'text': 'Response 2'}}}
        }
    }
    
    result = tagger.tag_conversation(conversation_data)
    
    tag_names = [tag.name for tag in result.tags]
    assert 'multi_turn' in tag_names
    assert 'exchange_info' in tag_names
    
    # Check specific attributes
    exchange_info_tags = [tag for tag in result.tags if tag.name == 'exchange_info']
    assert exchange_info_tags[0].attributes['count'] == 2


def test_tagging_error_handling():
    """Test that tagging rules handle errors gracefully."""
    tagger = ExchangeTagger()
    
    def broken_rule(exchange):
        raise ValueError("This rule always fails")
    
    def working_rule(exchange):
        return True
    
    tagger.add_rule('broken', broken_rule)
    tagger.add_rule('working', working_rule)
    
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello'}, 'create_time': 1000}
    ])
    
    # Should not raise exception
    tagged = tagger.tag_exchange(exchange)
    
    # Working rule should apply, broken rule should be skipped
    tag_names = [tag.name for tag in tagged.tags]
    assert 'working' in tag_names
    assert 'broken' not in tag_names


@pytest.fixture
def conversation_with_continuation():
    """Conversation data that should trigger continuation merging."""
    return {
        'conversation_id': 'test_conv',
        'title': 'Continuation test',
        'mapping': {
            'msg1': {'message': {'author': {'role': 'user'}, 'create_time': 1000, 'content': {'text': 'Tell me about Python'}}},
            'msg2': {'message': {'author': {'role': 'assistant'}, 'create_time': 2000, 'content': {'text': 'Python is a language...'}}},
            'msg3': {'message': {'author': {'role': 'user'}, 'create_time': 3000, 'content': {'text': 'continue'}}},
            'msg4': {'message': {'author': {'role': 'assistant'}, 'create_time': 4000, 'content': {'text': 'It was created by Guido...'}}}
        }
    }


def test_continuation_detection(conversation_with_continuation):
    """Test that continuation patterns merge exchanges correctly."""
    tagger = ConversationTagger()
    result = tagger.tag_conversation(conversation_with_continuation)
    
    # Should merge into single exchange due to continuation
    assert result.exchange_count == 1
    
    exchange = result.exchanges[0]
    assert len(exchange) == 4
    assert exchange.has_continuations()
    
    user_text = ' '.join(exchange.get_user_texts())
    assert 'Tell me about Python' in user_text
    assert 'continue' in user_text
