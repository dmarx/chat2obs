# tests/test_integration.py
"""
Integration tests for the complete conversation tagging system.
Updated to test annotation-based system.
"""

import pytest
from conversation_tagger import create_default_tagger, ConversationTagger
from conversation_tagger.core.exchange import Exchange

@pytest.fixture
def sample_coding_conversation():
    """A realistic conversation about coding that should trigger multiple annotations."""
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
    assert 'has_wiki_links' in rule_names


def test_end_to_end_tagging_with_annotations(sample_coding_conversation):
    """Test complete tagging pipeline with realistic conversation."""
    tagger = create_default_tagger()
    
    # Add a custom rule for testing
    def mentions_python(exchange):
        text = (' '.join(exchange.get_user_texts()) + ' ' + ' '.join(exchange.get_assistant_texts())).lower()
        return 'python' in text
    
    def count_code_blocks(exchange):
        """Return annotation with count of code blocks."""
        all_text = ' '.join(exchange.get_user_texts() + exchange.get_assistant_texts())
        count = all_text.count('```')
        if count > 0:
            return {'code_block_markers': count, 'has_code_blocks': True}
        return False
    
    tagger.add_exchange_rule('mentions_python', mentions_python)
    tagger.add_exchange_rule('code_analysis', count_code_blocks)
    
    result = tagger.tag_conversation(sample_coding_conversation)
    
    # Basic structure checks
    assert result.conversation_id == 'coding_conv'
    assert result.exchange_count == 2  # Two separate exchanges
    assert result.total_message_count == 4
    
    # Check that our custom rules fired
    all_annotations = {}
    for exchange in result.exchanges:
        all_annotations.update(exchange.annotations)
    
    assert 'mentions_python' in all_annotations
    assert all_annotations['mentions_python'] is True
    
    # Should detect code blocks
    assert 'has_code_blocks' in all_annotations or any(
        exchange.has_annotation('has_code_blocks') for exchange in result.exchanges
    )
    
    # Test backward compatibility - can still access as tags
    all_tags = []
    for exchange in result.exchanges:
        all_tags.extend(exchange.tags)
    tag_names = [tag.name for tag in all_tags]
    assert 'mentions_python' in tag_names


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
    
    # Should detect attachment-related annotations
    all_annotations = {}
    for exchange in result.exchanges:
        all_annotations.update(exchange.annotations)
    
    assert 'first_user_has_attachments' in all_annotations
    assert 'first_user_has_code_attachments' in all_annotations
    
    # Test values
    assert all_annotations['first_user_has_attachments'] is True
    assert all_annotations['first_user_has_code_attachments'] is True


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
    exchange = result.exchanges[0]
    assert exchange.has_annotation('has_latex_math')
    assert exchange.get_annotation('has_latex_math') is True


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
    
    exchange = result.exchanges[0]
    assert exchange.has_annotation('first_user_has_large_content')
    assert exchange.get_annotation('first_user_has_large_content') is True


def test_conversation_level_annotations():
    """Test conversation-level annotation aggregation."""
    tagger = create_default_tagger()
    
    # Multi-exchange conversation
    conversation_data = {
        'conversation_id': 'multi_conv',
        'title': 'Multi-exchange test',
        'mapping': {
            'msg1': {'message': {'author': {'role': 'user'}, 'create_time': 1000, 'content': {'text': 'First question'}}},
            'msg2': {'message': {'author': {'role': 'assistant'}, 'create_time': 2000, 'content': {'text': 'First answer'}}},
            'msg3': {'message': {'author': {'role': 'user'}, 'create_time': 3000, 'content': {'text': 'Second question'}}},
            'msg4': {'message': {'author': {'role': 'assistant'}, 'create_time': 4000, 'content': {'text': 'Second answer'}}},
            'msg5': {'message': {'author': {'role': 'user'}, 'create_time': 5000, 'content': {'text': 'Third question'}}},
            'msg6': {'message': {'author': {'role': 'assistant'}, 'create_time': 6000, 'content': {'text': 'Third answer'}}}
        }
    }
    
    result = tagger.tag_conversation(conversation_data)
    
    # Should have conversation-level length annotation
    assert result.has_annotation('conversation_length')
    length_data = result.get_annotation('conversation_length')
    assert length_data['count'] == 3
    assert length_data['category'] == 'short'  # 3 exchanges = short


def test_gizmo_plugin_annotations():
    """Test gizmo and plugin annotation detection."""
    gizmo_conversation = {
        'conversation_id': 'gizmo_conv',
        'title': 'Gizmo usage',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'Generate an image'}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'I\'ll generate that for you'},
                    'metadata': {'gizmo_id': 'dalle-3'}
                }
            }
        }
    }
    
    tagger = create_default_tagger()
    result = tagger.tag_conversation(gizmo_conversation)
    
    # Should detect gizmo usage at exchange level
    exchange = result.exchanges[0]
    
    # Check for gizmo annotations (could be gizmo_1, gizmo_2, etc.)
    gizmo_annotations = {k: v for k, v in exchange.annotations.items() if k.startswith('gizmo_')}
    assert len(gizmo_annotations) >= 1
    
    # At least one should have dalle-3 as gizmo_id
    found_dalle = False
    for annotation_value in gizmo_annotations.values():
        if isinstance(annotation_value, dict) and annotation_value.get('gizmo_id') == 'dalle-3':
            found_dalle = True
            break
    assert found_dalle


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
    assert len(result.annotations) >= 0  # May have some conversation-level annotations


def test_annotation_vs_tag_consistency():
    """Test that annotation and tag interfaces give consistent results."""
    tagger = create_default_tagger()
    
    # Add custom rule that returns complex data
    def complex_analysis(exchange):
        return {
            'message_count': len(exchange.messages),
            'user_word_count': len(' '.join(exchange.get_user_texts()).split()),
            'assistant_word_count': len(' '.join(exchange.get_assistant_texts()).split())
        }
    
    tagger.add_exchange_rule('analysis', complex_analysis)
    
    conversation_data = {
        'conversation_id': 'test_conv',
        'title': 'Test',
        'mapping': {
            'msg1': {'message': {'author': {'role': 'user'}, 'create_time': 1000, 'content': {'text': 'Hello world test'}}},
            'msg2': {'message': {'author': {'role': 'assistant'}, 'create_time': 2000, 'content': {'text': 'Hi there friend'}}}
        }
    }
    
    result = tagger.tag_conversation(conversation_data)
    exchange = result.exchanges[0]
    
    # Test annotation interface
    assert exchange.has_annotation('message_count')
    assert exchange.get_annotation('message_count') == 2
    assert exchange.get_annotation('user_word_count') == 3
    assert exchange.get_annotation('assistant_word_count') == 3
    
    # Test tag interface (backward compatibility)
    tags = exchange.tags
    
    # Find the analysis-related tags
    analysis_tags = [tag for tag in tags if 'message_count' in tag.name or 'word_count' in tag.name]
    assert len(analysis_tags) >= 3  # Should have all three annotations as separate tags or one combined tag
    
    # Test round-trip: annotations -> tags -> annotations
    original_annotations = exchange.annotations.copy()
    
    # Convert to tags and back
    tag_list = exchange.tags
    new_exchange = Exchange.create('test', [])
    new_exchange.tags = tag_list
    
    # Should preserve the key data (exact format may differ)
    assert new_exchange.has_annotation('message_count')
    assert new_exchange.get_annotation('message_count') == 2
