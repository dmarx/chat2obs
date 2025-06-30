# tests/test_integration.py
"""
Integration tests for the complete conversation tagging system.
"""

import pytest
from conversation_tagger import create_default_tagger, ConversationTagger


@pytest.fixture
def sample_coding_conversation():
    """A realistic conversation about coding that should trigger multiple tags."""
    return {
        'conversation_id': 'coding_conv',
        'title': 'Python help session',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'Can you help me write a Python function to calculate fibonacci numbers?'}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'Sure! Here\'s a simple fibonacci function:\n\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```'}
                }
            },
            'msg3': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 3000,
                    'content': {'text': 'Can you make it more efficient?'}
                }
            },
            'msg4': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 4000,
                    'content': {'text': 'Yes, here\'s a dynamic programming version:\n\n```python\ndef fibonacci_dp(n):\n    if n <= 1:\n        return n\n    \n    dp = [0, 1]\n    for i in range(2, n + 1):\n        dp.append(dp[i-1] + dp[i-2])\n    \n    return dp[n]\n```'}
                }
            }
        }
    }


def test_default_tagger_creation():
    """Test that default tagger is created with expected rules."""
    tagger = create_default_tagger()
    
    assert isinstance(tagger, ConversationTagger)
    assert len(tagger.exchange_parser.exchange_tagger.rules) > 0
    
    # Should have some default exchange rules
    rule_names = list(tagger.exchange_parser.exchange_tagger.rules.keys())
    assert 'exchange_type' in rule_names
    assert 'has_multiple_turns' in rule_names


def test_end_to_end_tagging(sample_coding_conversation):
    """Test complete tagging pipeline with realistic conversation."""
    tagger = create_default_tagger()
    
    # Add a custom rule for testing
    def mentions_python(exchange):
        text = (exchange.get_user_text() + ' ' + exchange.get_assistant_text()).lower()
        return 'python' in text
    
    tagger.add_exchange_rule('mentions_python', mentions_python)
    
    result = tagger.tag_conversation(sample_coding_conversation)
    
    # Basic structure checks
    assert result.conversation_id == 'coding_conv'
    assert result.exchange_count == 2  # Two separate exchanges
    assert result.total_message_count == 4
    
    # Check that our custom rule fired
    all_tags = [tag for exchange in result.exchanges for tag in exchange.tags]
    tag_names = [tag.name for tag in all_tags]
    assert 'mentions_python' in tag_names
    
    # Should have detected questions
    exchange_type_tags = [tag for tag in all_tags if tag.name == 'exchange_type']
    assert len(exchange_type_tags) > 0
    
    # At least one should be classified as a question
    question_tags = [tag for tag in exchange_type_tags if tag.attributes.get('type') == 'question']
    assert len(question_tags) > 0


def test_conversation_with_attachments():
    """Test conversation that includes file attachments."""
    conversation_with_file = {
        'conversation_id': 'file_conv',
        'title': 'File analysis',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'Can you analyze this Python file?'},
                    'metadata': {
                        'attachments': [
                            {'id': 'file1', 'name': 'script.py', 'mime_type': 'text/x-python'}
                        ]
                    }
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'I can help analyze your Python script...'}
                }
            }
        }
    }
    
    tagger = create_default_tagger()
    result = tagger.tag_conversation(conversation_with_file)
    
    # Should detect attachment-related tags
    all_tags = [tag for exchange in result.exchanges for tag in exchange.tags]
    tag_names = [tag.name for tag in all_tags]
    
    assert 'first_user_has_attachments' in tag_names
    assert 'first_user_has_code_attachments' in tag_names


def test_math_conversation():
    """Test conversation with mathematical content."""
    math_conversation = {
        'conversation_id': 'math_conv',
        'title': 'Math help',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'Explain the quadratic formula'}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'The quadratic formula is: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$'}
                }
            }
        }
    }
    
    tagger = create_default_tagger()
    result = tagger.tag_conversation(math_conversation)
    
    # Should detect LaTeX math
    all_tags = [tag for exchange in result.exchanges for tag in exchange.tags]
    tag_names = [tag.name for tag in all_tags]
    
    assert 'has_latex_math' in tag_names


def test_large_content_detection():
    """Test detection of large content messages."""
    large_content = 'x' * 2500  # Over the threshold
    
    large_message_conversation = {
        'conversation_id': 'large_conv',
        'title': 'Large content',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': large_content}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'That\'s a lot of content!'}
                }
            }
        }
    }
    
    tagger = create_default_tagger()
    result = tagger.tag_conversation(large_message_conversation)
    
    all_tags = [tag for exchange in result.exchanges for tag in exchange.tags]
    tag_names = [tag.name for tag in all_tags]
    
    assert 'first_user_has_large_content' in tag_names


def test_empty_conversation_handling():
    """Test handling of edge cases like empty conversations."""
    empty_conversation = {
        'conversation_id': 'empty_conv',
        'title': 'Empty',
        'mapping': {}
    }
    
    tagger = create_default_tagger()
    result = tagger.tag_conversation(empty_conversation)
    
    assert result.conversation_id == 'empty_conv'
    assert result.exchange_count == 0
    assert result.total_message_count == 0
