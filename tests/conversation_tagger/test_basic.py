# tests/test_basic.py
"""
Basic test to verify the core works.
"""

import pytest
from conversation_tagger import create_default_tagger, Tag


def create_test_conversation():
    """Create a simple test conversation."""
    return {
        'conversation_id': 'test_conv',
        'title': 'Test Conversation',
        'mapping': {
            'node1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {
                        'text': 'Fix this code:\n```python\nprint("hello")\n```',
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
                        'text': 'The fix adds proper formatting...',
                        'parts': []
                    }
                }
            }
        }
    }


def test_basic_functionality():
    """Test that the basic system works."""
    tagger = create_default_tagger()
    conversation = create_test_conversation()
    
    result = tagger.tag_conversation(conversation)
    
    # Should have basic structure
    assert 'conversation_id' in result
    assert 'tags' in result
    assert 'exchanges' in result
    assert 'exchange_count' in result
    
    # Should have 1 exchange (continuation grouped)
    assert result['exchange_count'] == 1
    
    # Should detect code and quote+elaborate
    tag_names = [tag.name for tag in result['tags']]
    assert 'has_user_has_code_blocks' in tag_names
    assert 'has_assistant_has_code_blocks' in tag_names
    assert 'has_has_quote_elaborate' in tag_names
    
    # Exchange should have continuation
    exchange = result['exchanges'][0]['exchange']
    assert exchange.has_continuations()


def test_tag_creation():
    """Test Tag class works."""
    tag = Tag('test_tag', value=42, category='example')
    
    assert tag.name == 'test_tag'
    assert tag.attributes['value'] == 42
    assert 'value=42' in str(tag)
    assert tag == 'test_tag'  # String comparison


if __name__ == "__main__":
    # Simple manual test
    tagger = create_default_tagger()
    conv = create_test_conversation()
    result = tagger.tag_conversation(conv)
    
    print(f"✅ Tagged conversation with {len(result['tags'])} tags")
    print(f"✅ Found {result['exchange_count']} exchanges")
    print(f"✅ Exchange has continuations: {result['exchanges'][0]['exchange'].has_continuations()}")
    print("✅ Basic system working!")
