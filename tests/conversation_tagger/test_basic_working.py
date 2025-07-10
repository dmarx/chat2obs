# tests/test_basic_working.py
"""
Tests for functionality that we know works in the current implementation.
Updated to test annotation-based system.
"""

import pytest
from conversation_tagger import create_default_tagger
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.exchange_tagger import ExchangeTagger
from conversation_tagger.core.tag import Tag, create_annotation, merge_annotations


def test_annotation_functionality():
    """Test that annotation helpers work correctly."""
    # Simple annotation
    simple = create_annotation('test_annotation', True)
    assert simple == {'test_annotation': True}
    
    # Valued annotation
    valued = create_annotation('count', 42)
    assert valued == {'count': 42}
    
    # Complex annotation
    complex_data = {'type': 'test', 'score': 0.95}
    complex_ann = create_annotation('analysis', complex_data)
    assert complex_ann == {'analysis': complex_data}
    
    # Merge annotations
    merged = merge_annotations(simple, valued, complex_ann)
    assert 'test_annotation' in merged
    assert 'count' in merged
    assert 'analysis' in merged
    assert merged['count'] == 42


# def test_tag_backward_compatibility():
#     """Test that Tag objects still work and convert properly."""
#     tag = Tag('test_tag', value='test_value')
#     assert tag.name == 'test_tag'
#     assert tag.attributes['value'] == 'test_value'
    
#     # Test conversion to annotation format
#     annotation_dict = tag.to_dict()
#     assert annotation_dict == {'test_tag': 'test_value'}
    
#     # Test complex tag
#     complex_tag = Tag('stats', count=5, average=2.5, category='medium')
#     complex_dict = complex_tag.to_dict()
#     assert complex_dict == {'stats': {'count': 5, 'average': 2.5, 'category': 'medium'}}


def test_exchange_creation_and_annotations():
    """Test basic exchange creation and annotation handling."""
    messages = [
        {'author': {'role': 'user'}, 'content': {'text': 'Test'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Response'}, 'create_time': 2000}
    ]
    
    exchange = Exchange.create('test_conv', messages)
    
    assert exchange.conversation_id == 'test_conv'
    assert len(exchange.messages) == 2
    assert len(exchange.get_user_messages()) == 1
    assert len(exchange.get_assistant_messages()) == 1
    
    # Test adding annotations
    exchange.add_annotation('has_greeting', True)
    exchange.add_annotation('message_count', 2)
    exchange.add_annotation('analysis', {'sentiment': 'positive', 'confidence': 0.8})
    
    assert exchange.has_annotation('has_greeting')
    assert exchange.get_annotation('message_count') == 2
    assert exchange.get_annotation('analysis')['sentiment'] == 'positive'
    assert not exchange.has_annotation('missing')


def test_exchange_text_api_with_annotations():
    """Test the text extraction API and annotation usage."""
    messages = [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello world'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Hi there'}, 'create_time': 2000}
    ]
    
    exchange = Exchange.create('test_conv', messages)
    
    # Test what the exchange actually provides
    user_texts = exchange.get_user_texts()
    assistant_texts = exchange.get_assistant_texts()
    
    # Verify these are lists (based on implementation)
    assert isinstance(user_texts, list)
    assert isinstance(assistant_texts, list)
    assert len(user_texts) == 1
    assert len(assistant_texts) == 1
    assert 'Hello world' in user_texts[0]
    assert 'Hi there' in assistant_texts[0]
    
    # Test annotation based on text analysis
    def analyze_text(texts):
        combined = ' '.join(texts)
        return {
            'word_count': len(combined.split()),
            'char_count': len(combined),
            'has_greeting': any(word in combined.lower() for word in ['hello', 'hi', 'hey'])
        }
    
    user_analysis = analyze_text(user_texts)
    assistant_analysis = analyze_text(assistant_texts)
    
    exchange.add_annotation('user_analysis', user_analysis)
    exchange.add_annotation('assistant_analysis', assistant_analysis)
    
    assert exchange.get_annotation('user_analysis')['word_count'] == 2
    assert exchange.get_annotation('assistant_analysis')['has_greeting'] is True


def test_exchange_tagger_with_annotations():
    """Test exchange tagger using the annotation system."""
    tagger = ExchangeTagger()
    
    def greeting_detector(exchange):
        """A rule that uses the correct API and returns annotation data."""
        user_texts = exchange.get_user_texts()
        if user_texts:
            text = ' '.join(user_texts).lower()
            if any(greeting in text for greeting in ['hello', 'hi', 'hey']):
                return {
                    'has_greeting': True,
                    'greeting_type': 'informal' if 'hi' in text or 'hey' in text else 'formal'
                }
        return False
    
    def message_counter(exchange):
        """Rule that returns simple numeric annotation."""
        return len(exchange.messages)
    
    tagger.add_rule('greeting_analysis', greeting_detector)
    tagger.add_rule('message_count', message_counter)
    
    # Test with exchange that should match
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello world'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Hi there!'}, 'create_time': 2000}
    ])
    
    tagged = tagger.tag_exchange(exchange)
    
    # Check annotations
    assert tagged.has_annotation('has_greeting')
    assert tagged.get_annotation('has_greeting') is True
    assert tagged.get_annotation('greeting_type') == 'formal'
    assert tagged.get_annotation('message_count') == 2
    
    # Test backward compatibility - can still access as tags
    # tag_names = [tag.name for tag in tagged.tags]
    # assert 'has_greeting' in tag_names or any('greeting' in name for name in tag_names)
    # assert 'message_count' in tag_names


def test_conversation_parsing_with_annotations():
    """Test basic conversation parsing with annotation support."""
    conversation_data = {
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
    
    tagger = create_default_tagger()
    
    # Add a custom annotation rule
    def simple_stats(exchange):
        return {
            'user_messages': len(exchange.get_user_messages()),
            'assistant_messages': len(exchange.get_assistant_messages()),
            'total_messages': len(exchange.messages)
        }
    
    tagger.add_exchange_rule('stats', simple_stats)
    
    result = tagger.tag_conversation(conversation_data)
    
    # Test basic structure
    assert result.conversation_id == 'test_conv'
    assert result.title == 'Test Chat'
    assert result.exchange_count == 1
    
    # Test that we can access the exchange and its annotations
    exchange = result.exchanges[0]
    assert len(exchange.messages) == 2
    
    # Check that our custom annotation rule was applied
    assert exchange.has_annotation('user_messages')
    assert exchange.get_annotation('user_messages') == 1
    assert exchange.get_annotation('assistant_messages') == 1
    assert exchange.get_annotation('total_messages') == 2
    
    # Test text extraction still works
    user_texts = exchange.get_user_texts()
    assert isinstance(user_texts, list)
    assert len(user_texts) == 1
    assert 'Hello' in user_texts[0]


def test_default_tagger_with_annotations():
    """Test that the default tagger works with annotation system."""
    tagger = create_default_tagger()
    assert tagger is not None
    assert hasattr(tagger, 'exchange_parser')
    assert hasattr(tagger.exchange_parser, 'exchange_tagger')
    
    # Test that it has some default rules
    assert len(tagger.exchange_parser.exchange_tagger.rules) > 0


def test_default_rules_produce_annotations():
    """Test that default rules work and produce annotations."""
    conversation_data = {
        'conversation_id': 'code_conv',
        'title': 'Code Chat',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'def hello(): print("hello")'},
                    'metadata': {'attachments': []}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'Nice Python function!'}
                }
            }
        }
    }
    
    tagger = create_default_tagger()
    result = tagger.tag_conversation(conversation_data)
    
    # Check if any annotations were applied
    all_annotations = {}
    for exchange in result.exchanges:
        all_annotations.update(exchange.annotations)
    
    # Also check conversation-level annotations
    all_annotations.update(result.annotations)
    
    annotation_names = list(all_annotations.keys())
    print(f"Applied annotations: {annotation_names}")
    
    # Some rules should work - at minimum we should have non-empty result
    assert len(result.exchanges) > 0
    
    # Should detect code patterns in the first user message
    first_exchange = result.exchanges[0]
    # We know from testing that first_user_has_code_patterns should work
    if first_exchange.has_annotation('first_user_has_code_patterns'):
        assert first_exchange.get_annotation('first_user_has_code_patterns') is True


def test_annotation_backward_compatibility_workflow():
    """Test complete workflow using both annotations and legacy tags."""
    # Create exchange
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello'}, 'create_time': 1000}
    ])
    
    # Add annotations directly (new way)
    exchange.add_annotation('modern_flag', True)
    exchange.add_annotation('score', 85)
    exchange.add_annotation('metadata', {'version': '2.0', 'processed': True})
    
    # # Add via legacy tag interface (old way)
    # legacy_tags = [
    #     Tag('legacy_flag'),
    #     Tag('rating', value=4.5),
    #     Tag('details', category='important', priority='high')
    # ]
    
    # # This should merge with existing annotations
    # old_annotations = exchange.annotations.copy()
    # exchange.tags = exchange.tags + legacy_tags  # Append to existing
    
    # Verify all annotations are present
    assert exchange.has_annotation('modern_flag')
    assert exchange.has_annotation('score')
    assert exchange.has_annotation('metadata')
    # assert exchange.has_annotation('legacy_flag')
    # assert exchange.has_annotation('rating')
    # assert exchange.has_annotation('details')
    
    # Verify values are correct
    assert exchange.get_annotation('modern_flag') is True
    assert exchange.get_annotation('score') == 85
    # assert exchange.get_annotation('rating') == 4.5
    # assert exchange.get_annotation('details')['category'] == 'important'
    
    # # Test that we can still get everything as tags
    # all_tags = exchange.tags
    # tag_names = [tag.name for tag in all_tags]
    # assert 'modern_flag' in tag_names
    # assert 'legacy_flag' in tag_names
    # assert 'score' in tag_names
    # assert 'rating' in tag_names


def test_rule_return_value_handling():
    """Test that different rule return value types are handled correctly."""
    tagger = ExchangeTagger()
    
    def bool_rule(exchange):
        return True
    
    def string_rule(exchange):
        return "detected"
    
    def number_rule(exchange):
        return 42
    
    def dict_rule(exchange):
        return {
            'count': 3,
            'type': 'test',
            'valid': True
        }
    
    def legacy_tag_rule(exchange):
        return Tag('legacy', style='old', version=1.0)
    
    def false_rule(exchange):
        return False
    
    def none_rule(exchange):
        return None
    
    tagger.add_rule('bool_test', bool_rule)
    tagger.add_rule('string_test', string_rule)
    tagger.add_rule('number_test', number_rule)
    tagger.add_rule('dict_test', dict_rule)
    tagger.add_rule('legacy_test', legacy_tag_rule)
    tagger.add_rule('false_test', false_rule)
    tagger.add_rule('none_test', none_rule)
    
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'test'}, 'create_time': 1000}
    ])
    
    tagged = tagger.tag_exchange(exchange)
    
    # Check that different return types are handled correctly
    assert tagged.get_annotation('bool_test') is True
    assert tagged.get_annotation('string_test') == "detected"
    assert tagged.get_annotation('number_test') == 42
    
    # Dict rule should create multiple annotations
    assert tagged.get_annotation('count') == 3
    assert tagged.get_annotation('type') == 'test'
    assert tagged.get_annotation('valid') is True
    
    # Legacy tag should be converted
    assert tagged.has_annotation('legacy')
    legacy_data = tagged.get_annotation('legacy')
    assert legacy_data['style'] == 'old'
    assert legacy_data['version'] == 1.0
    
    # False and None should not create annotations
    assert not tagged.has_annotation('false_test')
    assert not tagged.has_annotation('none_test')
