# tests/test_tagging.py
"""
Tagging functionality tests for exchanges and conversations.
Updated to test annotation-based system.
"""

import pytest
from conversation_tagger.core.exchange_tagger import ExchangeTagger
from conversation_tagger.core.tagger import ConversationTagger
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.tag import Tag


def test_exchange_tagger_annotations():
    """Test basic exchange tagging with annotations."""
    tagger = ExchangeTagger()
    
    def has_greeting(exchange):
        user_text = ' '.join(exchange.get_user_texts()).lower()
        return 'hello' in user_text or 'hi' in user_text
    
    def message_stats(exchange):
        """Return multiple annotations."""
        user_count = len(exchange.get_user_messages())
        assistant_count = len(exchange.get_assistant_messages())
        return {
            'user_message_count': user_count,
            'assistant_message_count': assistant_count,
            'total_messages': user_count + assistant_count
        }
    
    tagger.add_rule('greeting', has_greeting)
    tagger.add_rule('stats', message_stats)
    
    # Test with greeting
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello world!'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Hi there!'}, 'create_time': 2000}
    ])
    
    tagged = tagger.tag_exchange(exchange)
    
    # Check simple boolean annotation
    assert tagged.has_annotation('greeting')
    assert tagged.get_annotation('greeting') is True
    
    # Check multiple annotations from one rule
    assert tagged.has_annotation('user_message_count')
    assert tagged.get_annotation('user_message_count') == 1
    assert tagged.has_annotation('assistant_message_count')
    assert tagged.get_annotation('assistant_message_count') == 1
    assert tagged.get_annotation('total_messages') == 2
    
    # Test without greeting
    exchange_no_greeting = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'What is Python?'}, 'create_time': 1000}
    ])
    
    tagged_no_greeting = tagger.tag_exchange(exchange_no_greeting)
    assert not tagged_no_greeting.has_annotation('greeting')
    assert tagged_no_greeting.get_annotation('user_message_count') == 1
    assert tagged_no_greeting.get_annotation('assistant_message_count') == 0


# def test_exchange_tagger_with_legacy_tags():
#     """Test exchange tagging with legacy Tag return values."""
#     tagger = ExchangeTagger()
    
#     def length_category(exchange):
#         """Return a legacy Tag object."""
#         text = ' '.join(exchange.get_user_texts())
#         length = len(text)
#         if length > 50:
#             return Tag('message_length', size='long', chars=length)
#         elif length > 10:
#             return Tag('message_length', size='medium', chars=length)
#         return False
    
#     tagger.add_rule('length_category', length_category)
    
#     long_exchange = Exchange.create('test', [
#         {'author': {'role': 'user'}, 'content': {'text': 'This is a very long message that should definitely be tagged as long since it exceeds the threshold'}, 'create_time': 1000}
#     ])
    
#     tagged = tagger.tag_exchange(long_exchange)
    
#     # Should convert Tag to annotation
#     assert tagged.has_annotation('message_length')
#     length_data = tagged.get_annotation('message_length')
#     assert length_data['size'] == 'long'
#     assert length_data['chars'] > 50


def test_exchange_tagger_with_string_values():
    """Test exchange tagging with string return values."""
    tagger = ExchangeTagger()
    
    def get_language(exchange):
        """Return a string value."""
        text = ' '.join(exchange.get_user_texts()).lower()
        if 'python' in text:
            return 'python'
        elif 'javascript' in text:
            return 'javascript'
        return None
    
    tagger.add_rule('language', get_language)
    
    python_exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Help with Python code'}, 'create_time': 1000}
    ])
    
    tagged = tagger.tag_exchange(python_exchange)
    assert tagged.has_annotation('language')
    assert tagged.get_annotation('language') == 'python'


def test_conversation_tagger_annotations():
    """Test conversation-level tagging with annotations."""
    tagger = ConversationTagger()
    
    def is_multi_turn(conversation):
        return conversation.exchange_count > 1
    
    def exchange_summary(conversation):
        """Return structured annotation data."""
        return {
            'exchange_count': conversation.exchange_count,
            'total_messages': conversation.total_message_count,
            'has_continuations': conversation.has_continuations
        }
    
    tagger.add_conversation_rule('multi_turn', is_multi_turn)
    tagger.add_conversation_rule('summary', exchange_summary)
    
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
    
    # Check annotations
    assert result.has_annotation('multi_turn')
    assert result.get_annotation('multi_turn') is True
    
    assert result.has_annotation('exchange_count')
    assert result.get_annotation('exchange_count') == 2
    assert result.has_annotation('total_messages')
    assert result.get_annotation('total_messages') == 4


def test_conversation_tagger_with_legacy_tags():
    """Test conversation tagger with legacy Tag objects."""
    tagger = ConversationTagger()
    
    def complexity_tag(conversation):
        """Return legacy Tag object."""
        if conversation.exchange_count > 5:
            return Tag('complexity', level='high', exchanges=conversation.exchange_count)
        return Tag('complexity', level='low', exchanges=conversation.exchange_count)
    
    tagger.add_conversation_rule('complexity', complexity_tag)
    
    conversation_data = {
        'conversation_id': 'test_conv',
        'title': 'Simple conversation',
        'mapping': {
            'msg1': {'message': {'author': {'role': 'user'}, 'create_time': 1000, 'content': {'text': 'Hello'}}},
            'msg2': {'message': {'author': {'role': 'assistant'}, 'create_time': 2000, 'content': {'text': 'Hi there!'}}}
        }
    }
    
    result = tagger.tag_conversation(conversation_data)
    
    # Should convert Tag to annotation
    assert result.has_annotation('complexity')
    complexity_data = result.get_annotation('complexity')
    assert complexity_data['level'] == 'low'
    assert complexity_data['exchanges'] == 1


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
    assert tagged.has_annotation('working')
    assert tagged.get_annotation('working') is True
    assert not tagged.has_annotation('broken')


def test_exchange_backward_compatibility():
    """Test that old Tag-based code still works."""
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello'}, 'create_time': 1000}
    ])
    
    # Add annotations directly
    exchange.add_annotation('has_greeting', True)
    exchange.add_annotation('length', 50)
    exchange.add_annotation('stats', {'words': 1, 'chars': 5})
    
    # Test getting tags (backward compatibility)
    tags = exchange.tags
    tag_names = [tag.name for tag in tags]
    assert 'has_greeting' in tag_names
    assert 'length' in tag_names
    assert 'stats' in tag_names
    
    # Find specific tags
    greeting_tag = next(tag for tag in tags if tag.name == 'has_greeting')
    assert greeting_tag.attributes == {}  # Simple boolean becomes empty attributes
    
    length_tag = next(tag for tag in tags if tag.name == 'length')
    assert length_tag.attributes == {'value': 50}  # Single value
    
    stats_tag = next(tag for tag in tags if tag.name == 'stats')
    assert stats_tag.attributes == {'words': 1, 'chars': 5}  # Multiple attributes


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


def test_continuation_detection_with_annotations(conversation_with_continuation):
    """Test that continuation patterns merge exchanges correctly."""
    tagger = ConversationTagger()
    
    # Add a rule that detects continuations
    def detect_continuation(exchange):
        return exchange.has_continuations()
    
    tagger.add_exchange_rule('has_continuation', detect_continuation)
    
    result = tagger.tag_conversation(conversation_with_continuation)
    
    # Should merge into single exchange due to continuation
    assert result.exchange_count == 1
    
    exchange = result.exchanges[0]
    assert len(exchange) == 4
    assert exchange.has_continuations()
    
    # Should have continuation annotation
    assert exchange.has_annotation('has_continuation')
    assert exchange.get_annotation('has_continuation') is True
    
    user_text = ' '.join(exchange.get_user_texts())
    assert 'Tell me about Python' in user_text
    assert 'continue' in user_text


def test_mixed_annotation_and_tag_workflow():
    """Test workflow mixing new annotations with legacy Tag objects."""
    tagger = ExchangeTagger()
    
    def modern_rule(exchange):
        """Modern rule returning dict of annotations."""
        return {
            'message_count': len(exchange.messages),
            'has_user': len(exchange.get_user_messages()) > 0,
            'has_assistant': len(exchange.get_assistant_messages()) > 0
        }
    
    def legacy_rule(exchange):
        """Legacy rule returning Tag object."""
        if len(exchange.get_user_texts()) > 0:
            text_length = len(' '.join(exchange.get_user_texts()))
            return Tag('user_text_stats', length=text_length, word_count=len(' '.join(exchange.get_user_texts()).split()))
        return False
    
    tagger.add_rule('modern', modern_rule)
    tagger.add_rule('legacy', legacy_rule)
    
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello world'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Hi there!'}, 'create_time': 2000}
    ])
    
    tagged = tagger.tag_exchange(exchange)
    
    # Modern annotations
    assert tagged.get_annotation('message_count') == 2
    assert tagged.get_annotation('has_user') is True
    assert tagged.get_annotation('has_assistant') is True
    
    # Legacy tag converted to annotation
    assert tagged.has_annotation('user_text_stats')
    stats = tagged.get_annotation('user_text_stats')
    assert stats['length'] == 11  # "Hello world"
    assert stats['word_count'] == 2
    
    # Test backward compatibility - can still get as tags
    tags = tagged.tags
    tag_names = [tag.name for tag in tags]
    assert 'message_count' in tag_names
    assert 'has_user' in tag_names
    assert 'user_text_stats' in tag_names
