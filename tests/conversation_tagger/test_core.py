# tests/test_core.py
"""
Core functionality tests for conversation tagging system.
Updated to test both annotation system and backward compatibility.
"""

import pytest
from conversation_tagger.core.tag import Tag, create_annotation, merge_annotations
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.conversation import Conversation
from conversation_tagger.core.message import MessageOpenAI

def test_annotation_helpers():
    """Test annotation helper functions."""
    # Simple annotation
    simple = create_annotation('has_code', True)
    assert simple == {'has_code': True}
    
    # Annotation with value
    valued = create_annotation('length', 150)
    assert valued == {'length': 150}
    
    # Annotation with structured data
    structured = create_annotation('stats', {'count': 5, 'avg': 2.5})
    assert structured == {'stats': {'count': 5, 'avg': 2.5}}
    
    # Merge annotations
    merged = merge_annotations(simple, valued, structured)
    assert merged == {'has_code': True, 'length': 150, 'stats': {'count': 5, 'avg': 2.5}}


def test_tag_backward_compatibility():
    """Test that Tag objects still work and convert properly."""
    # Simple tag
    simple_tag = Tag('simple')
    assert simple_tag.name == 'simple'
    assert simple_tag.attributes == {}
    assert simple_tag.to_dict() == {'simple': True}
    
    # Tag with single value attribute
    value_tag = Tag('length', value=100)
    assert value_tag.to_dict() == {'length': 100}
    
    # Tag with multiple attributes
    complex_tag = Tag('stats', count=5, avg=2.5)
    assert complex_tag.to_dict() == {'stats': {'count': 5, 'avg': 2.5}}
    
    # Test equality
    assert simple_tag == 'simple'
    assert simple_tag != complex_tag


def test_exchange_annotations():
    """Test exchange annotation functionality."""
    messages = [
        {'author': {'role': 'user'}, 'content': {'text': 'Hello'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Hi!'}, 'create_time': 2000}
    ]
    messages = [MessageOpenAI(data=msg) for msg in messages]
    
    exchange = Exchange.create('conv_1', messages)
    
    # Test adding annotations
    exchange.add_annotation('has_greeting', True)
    exchange.add_annotation('message_count', 2)
    exchange.add_annotation('stats', {'user_msgs': 1, 'assistant_msgs': 1})
    
    assert exchange.has_annotation('has_greeting')
    assert exchange.get_annotation('message_count') == 2
    assert exchange.get_annotation('stats')['user_msgs'] == 1
    assert not exchange.has_annotation('missing_annotation')
    assert exchange.get_annotation('missing_annotation', 'default') == 'default'
    
    # # Test backward compatibility with tags property
    # tags = exchange.tags
    # assert len(tags) == 3
    # tag_names = [tag.name for tag in tags]
    # assert 'has_greeting' in tag_names
    # assert 'message_count' in tag_names
    # assert 'stats' in tag_names


# def test_exchange_tags_compatibility():
#     """Test that setting tags still works via backward compatibility."""
#     exchange = Exchange.create('conv_1', [])
    
#     # Set tags the old way
#     old_tags = [
#         Tag('simple'),
#         Tag('valued', value=42),
#         Tag('complex', count=3, type='test')
#     ]
#     exchange.tags = old_tags
    
#     # Should be converted to annotations
#     assert exchange.has_annotation('simple')
#     assert exchange.get_annotation('simple') is True
#     assert exchange.get_annotation('valued') == 42
#     assert exchange.get_annotation('complex') == {'count': 3, 'type': 'test'}


def test_exchange_merging_annotations():
    """Test merging exchanges preserves annotations."""
    messages1=[
        {'author': {'role': 'user'}, 'content': {'text': 'First'}, 'create_time': 1000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'Response'}, 'create_time': 2000}
    ]
    messages1 = [MessageOpenAI(data=msg) for msg in messages1]
    exchange_1 = Exchange.create('conv_1', messages1)
    exchange_1.add_annotation('has_code', True)
    exchange_1.add_annotation('part', 1)

    messages2=[
        {'author': {'role': 'user'}, 'content': {'text': 'Continue'}, 'create_time': 3000},
        {'author': {'role': 'assistant'}, 'content': {'text': 'More'}, 'create_time': 4000}
    ]
    messages2 = [MessageOpenAI(data=msg) for msg in messages2]
    exchange_2 = Exchange.create('conv_1', messages2)
    exchange_2.add_annotation('has_continuation', True)
    exchange_2.add_annotation('part', 2)
    
    merged = exchange_1 + exchange_2
    
    assert len(merged) == 4
    assert merged.has_annotation('has_code')
    assert merged.has_annotation('has_continuation')
    assert merged.get_annotation('part') == 2  # Second exchange value wins
    
    # Verify time ordering
    times = [msg.created_date for msg in merged.messages]
    assert times == [1000, 2000, 3000, 4000]


def test_conversation_annotations():
    """Test conversation annotation functionality."""
    exchanges = [
        Exchange.create('conv_1', [
            MessageOpenAI(data={'author': {'role': 'user'}, 'content': {'text': 'Q1'}, 'create_time': 1000}),
            MessageOpenAI(data={'author': {'role': 'assistant'}, 'content': {'text': 'A1'}, 'create_time': 2000})
        ]),
        Exchange.create('conv_1', [
            MessageOpenAI(data={'author': {'role': 'user'}, 'content': {'text': 'Q2'}, 'create_time': 3000}),
            MessageOpenAI(data={'author': {'role': 'assistant'}, 'content': {'text': 'A2'}, 'create_time': 4000})
        ])  
    ]
    
    # Add annotations to exchanges
    exchanges[0].add_annotation('has_greeting', True)
    exchanges[1].add_annotation('has_code', True)
    
    conv = Conversation('conv_1', 'Test Chat', exchanges)
    
    # Test conversation-level annotations
    conv.add_annotation('is_technical', True)
    conv.add_annotation('complexity', 'medium')
    
    assert conv.has_annotation('is_technical')
    assert conv.get_annotation('complexity') == 'medium'
    
    # Test aggregated annotations from exchanges
    assert conv.has_annotation('has_greeting')
    assert conv.has_annotation('has_code')
    
    # Test properties still work
    assert conv.exchange_count == 2
    assert conv.total_message_count == 4
    assert 'Q1' in conv.get_all_user_text()


# def test_conversation_tags_compatibility():
#     """Test conversation backward compatibility with tags."""
#     conv = Conversation('conv_1', 'Test', [])
    
#     # Set tags the old way
#     old_tags = [
#         Tag('multi_turn'),
#         Tag('length', category='medium', count=5)
#     ]
#     conv.tags = old_tags
    
#     # Should be converted to annotations
#     assert conv.has_annotation('multi_turn')
#     assert conv.get_annotation('multi_turn') is True
#     assert conv.get_annotation('length') == {'category': 'medium', 'count': 5}
    
#     # Test getting tags back
#     tags = conv.tags
#     tag_names = [tag.name for tag in tags]
#     assert 'multi_turn' in tag_names
#     assert 'length' in tag_names


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
    """Test basic conversation parsing with annotations."""
    from conversation_tagger.core.exchange_parser import ExchangeParserOAI

    parser = ExchangeParserOAI()
    conversation = parser.parse_conversation(sample_conversation_data)
    
    assert isinstance(conversation, Conversation)
    assert conversation.conversation_id == 'test_conv'
    assert conversation.exchange_count == 1
    assert 'Hello' in conversation.get_all_user_text()
    
    # Should have empty annotations initially
    assert len(conversation.annotations) == 0
    
    # Test adding annotations
    conversation.add_annotation('parsed', True)
    assert conversation.has_annotation('parsed')
