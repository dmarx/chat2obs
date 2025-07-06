# tests/test_simplified.py
"""
Tests for the simplified conversation tagger design.
"""

import pytest
from conversation_tagger import (
    Exchange, Conversation, Annotator,
    create_default_processor, create_basic_annotator,
    quick_annotate, batch_annotate
)


def test_simple_annotations():
    """Test that annotations are simple dicts."""
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello'}, 'create_time': 1000}
    ])
    
    # Annotations start empty
    assert exchange.annotations == {}
    
    # Simple boolean annotation
    exchange.annotations['has_greeting'] = True
    assert exchange.annotations['has_greeting'] is True
    
    # Numeric annotation  
    exchange.annotations['length'] = 5
    assert exchange.annotations['length'] == 5
    
    # Complex annotation
    exchange.annotations['analysis'] = {'category': 'short', 'word_count': 1}
    assert exchange.annotations['analysis']['category'] == 'short'


def test_annotator_basic():
    """Test basic annotator functionality."""
    annotator = Annotator()
    
    def has_greeting(exchange):
        texts = exchange.get_user_texts() + exchange.get_assistant_texts()
        return any('hello' in text.lower() for text in texts)
    
    def message_length(exchange):
        texts = exchange.get_all_texts()
        total_length = sum(len(text) for text in texts)
        return {'total': total_length, 'average': total_length / len(texts) if texts else 0}
    
    annotator.add_exchange_rule('has_greeting', has_greeting)
    annotator.add_exchange_rule('message_length', message_length)
    
    # Test with greeting
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello world'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Hi there!'}, 'create_time': 2000}
    ])
    
    annotated = annotator.annotate_exchange(exchange)
    
    # Should have boolean annotation
    assert annotated.annotations['has_greeting'] is True
    
    # Should have complex annotation with prefixed keys
    assert 'message_length_total' in annotated.annotations
    assert 'message_length_average' in annotated.annotations
    assert annotated.annotations['message_length_total'] > 0


def test_conversation_processing():
    """Test end-to-end conversation processing."""
    conversation_data = {
        'conversation_id': 'test_conv',
        'title': 'Test Chat',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'Can you help me with Python?'}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'Sure! Here\'s a simple example:\n\n```python\nprint("Hello")\n```'}
                }
            }
        }
    }
    
    processor = create_default_processor()
    conversation = processor.process_conversation(conversation_data)
    
    # Basic structure
    assert conversation.conversation_id == 'test_conv'
    assert conversation.exchange_count == 1
    
    # Should have some annotations
    exchange = conversation.exchanges[0]
    assert 'has_code_blocks' in exchange.annotations
    assert exchange.annotations['has_code_blocks'] is True
    
    # Conversation should have length analysis
    assert 'conversation_length_analysis_category' in conversation.annotations
    assert conversation.annotations['conversation_length_analysis_category'] == 'single'


def test_quick_annotate():
    """Test the quick annotation convenience function."""
    conversation_data = {
        'conversation_id': 'quick_test',
        'title': 'Quick Test',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'Short question'}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'Short answer'}
                }
            }
        }
    }
    
    result = quick_annotate(conversation_data)
    
    assert result['conversation_id'] == 'quick_test'
    assert result['exchange_count'] == 1
    assert 'annotations' in result
    assert isinstance(result['annotations'], dict)


def test_custom_rules():
    """Test adding custom annotation rules."""
    annotator = Annotator()
    
    def mentions_python(exchange):
        texts = exchange.get_user_texts() + exchange.get_assistant_texts()
        return any('python' in text.lower() for text in texts)
    
    def exchange_complexity(exchange):
        user_count = len(exchange.get_user_messages())
        assistant_count = len(exchange.get_assistant_messages()) 
        total_text = sum(len(text) for text in exchange.get_all_texts())
        
        if total_text > 1000:
            complexity = 'high'
        elif total_text > 300:
            complexity = 'medium'
        else:
            complexity = 'low'
        
        return {
            'user_messages': user_count,
            'assistant_messages': assistant_count,
            'total_chars': total_text,
            'complexity': complexity
        }
    
    annotator.add_exchange_rule('mentions_python', mentions_python)
    annotator.add_exchange_rule('exchange_complexity', exchange_complexity)
    
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Tell me about Python programming'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Python is a versatile programming language...'}, 'create_time': 2000}
    ])
    
    annotated = annotator.annotate_exchange(exchange)
    
    assert annotated.annotations['mentions_python'] is True
    assert 'exchange_complexity_complexity' in annotated.annotations
    assert 'exchange_complexity_total_chars' in annotated.annotations


def test_annotation_aggregation():
    """Test conversation-level annotation aggregation."""
    exchange1 = Exchange.create('test', [])
    exchange1.annotations = {'has_code': True, 'length': 100}
    
    exchange2 = Exchange.create('test', [])
    exchange2.annotations = {'has_math': True, 'length': 200}
    
    conversation = Conversation('test', 'Test', [exchange1, exchange2])
    conversation.annotations = {'conversation_type': 'educational'}
    
    all_annotations = conversation.get_all_annotations()
    
    # Should have conversation-level annotations
    assert all_annotations['conversation_type'] == 'educational'
    
    # Should have exchange annotations (last exchange wins for conflicts)
    assert all_annotations['length'] == 200
    
    # Should have prefixed exchange annotations
    assert all_annotations['exchange_0_has_code'] is True
    assert all_annotations['exchange_1_has_math'] is True


def test_error_handling():
    """Test that annotation errors are handled gracefully."""
    annotator = Annotator()
    
    def broken_rule(exchange):
        raise ValueError("This rule always fails")
    
    def working_rule(exchange):
        return True
    
    annotator.add_exchange_rule('broken', broken_rule)
    annotator.add_exchange_rule('working', working_rule)
    
    exchange = Exchange.create('test', [
        {'author': {'role': 'user'}, 'content': {'text': 'Test'}, 'create_time': 1000}
    ])
    
    # Should not raise exception
    annotated = annotator.annotate_exchange(exchange)
    
    # Working rule should apply, broken rule should be skipped
    assert annotated.annotations['working'] is True
    assert 'broken' not in annotated.annotations


def test_batch_processing():
    """Test batch annotation of multiple conversations."""
    conversations = [
        {
            'conversation_id': 'conv1',
            'title': 'First',
            'mapping': {
                'msg1': {'message': {'author': {'role': 'user'}, 'create_time': 1000, 'content': {'text': 'Hello'}}},
                'msg2': {'message': {'author': {'role': 'assistant'}, 'create_time': 2000, 'content': {'text': 'Hi'}}}
            }
        },
        {
            'conversation_id': 'conv2', 
            'title': 'Second',
            'mapping': {
                'msg1': {'message': {'author': {'role': 'user'}, 'create_time': 1000, 'content': {'text': 'Code help'}}},
                'msg2': {'message': {'author': {'role': 'assistant'}, 'create_time': 2000, 'content': {'text': '```python\nprint("hi")\n```'}}}
            }
        }
    ]
    
    results = batch_annotate(conversations, use_basic=True)
    
    assert len(results) == 2
    assert results[0]['conversation_id'] == 'conv1'
    assert results[1]['conversation_id'] == 'conv2'
    
    # Second conversation should have code annotations
    conv2_annotations = results[1]['annotations']
    assert 'has_code_blocks' in conv2_annotations


if __name__ == '__main__':
    pytest.main([__file__])
