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


def test_tag_backward_compatibility():
    """Test that Tag objects still work and convert properly."""
    tag = Tag('test_tag', value='test_value')
    assert tag.name == 'test_tag'
    assert tag.attributes['value'] == 'test_value'
    
    # Test conversion to annotation format
    annotation_dict = tag.to_dict()
    assert annotation_dict == {'test_tag': 'test_value'}
    
    # Test complex tag
    complex_tag = Tag('stats', count=5, average=2.5, category='medium')
    complex_dict = complex_tag.to_dict()
    assert complex_dict == {'stats': {'count': 5, 'average': 2.5, 'category': 'medium'}}


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
