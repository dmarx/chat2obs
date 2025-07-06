# tests/conversation_tagger/test_detection.py
"""
Unit tests for detection.py detection functions.
Updated to test annotation-based system.
"""

import pytest
from conversation_tagger.core.detection import *
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.conversation import Conversation
from conversation_tagger.core.tag import Tag


######################
# Conversation Tests #
######################

def test_create_conversation_length_annotation():
    """Test conversation length annotation creation."""
    # Single exchange
    conv_single = Conversation('test', 'Single', [Exchange.create('test', [])])
    annotation = create_conversation_length_annotation(conv_single)
    assert 'conversation_length' in annotation
    length_data = annotation['conversation_length']
    assert length_data['count'] == 1
    assert length_data['category'] == 'single'
    
    # Short (3 exchanges)
    exchanges = [Exchange.create('test', []) for _ in range(3)]
    conv_short = Conversation('test', 'Short', exchanges)
    annotation = create_conversation_length_annotation(conv_short)
    length_data = annotation['conversation_length']
    assert length_data['count'] == 3
    assert length_data['category'] == 'short'
    
    # Medium (7 exchanges)
    exchanges = [Exchange.create('test', []) for _ in range(7)]
    conv_medium = Conversation('test', 'Medium', exchanges)
    annotation = create_conversation_length_annotation(conv_medium)
    length_data = annotation['conversation_length']
    assert length_data['count'] == 7
    assert length_data['category'] == 'medium'
    
    # Long (15 exchanges)
    exchanges = [Exchange.create('test', []) for _ in range(15)]
    conv_long = Conversation('test', 'Long', exchanges)
    annotation = create_conversation_length_annotation(conv_long)
    length_data = annotation['conversation_length']
    assert length_data['count'] == 15
    assert length_data['category'] == 'long'
    
    # Very long (30 exchanges)
    exchanges = [Exchange.create('test', []) for _ in range(30)]
    conv_very_long = Conversation('test', 'VeryLong', exchanges)
    annotation = create_conversation_length_annotation(conv_very_long)
    length_data = annotation['conversation_length']
    assert length_data['count'] == 30
    assert length_data['category'] == 'very_long'


def test_conversation_feature_summary():
    """Test feature aggregation across exchanges."""
    # Create exchanges with different feature annotations
    exchange1 = Exchange.create('test', [])
    exchange1.add_annotation('has_code_blocks', True)
    exchange1.add_annotation('has_web_search', True)
    exchange1.add_annotation('gizmo_1', {'gizmo_id': 'gpt-4'})
    
    exchange2 = Exchange.create('test', [])
    exchange2.add_annotation('has_code_blocks', True)
    exchange2.add_annotation('has_github_repos', True)
    exchange2.add_annotation('plugin_1', {'plugin_id': 'web'})
    
    exchange3 = Exchange.create('test', [])
    exchange3.add_annotation('has_latex_math', True)
    
    conv = Conversation('test', 'Test', [exchange1, exchange2, exchange3])
    annotations = conversation_feature_summary(conv)
    
    # has_code_blocks appears in 2/3 exchanges
    assert 'conversation_has_code_blocks' in annotations
    code_data = annotations['conversation_has_code_blocks']
    assert code_data['exchange_count'] == 2
    assert code_data['total_exchanges'] == 3
    assert code_data['percentage'] == 66.7
    
    assert 'conversation_has_web_search' in annotations
    search_data = annotations['conversation_has_web_search']
    assert search_data['exchange_count'] == 1
    assert search_data['percentage'] == 33.3
    
    assert 'conversation_has_gizmo_usage' in annotations
    gizmo_data = annotations['conversation_has_gizmo_usage']
    assert gizmo_data['exchange_count'] == 1
    assert gizmo_data['percentage'] == 33.3
    
    assert 'conversation_has_plugin_usage' in annotations
    plugin_data = annotations['conversation_has_plugin_usage']
    assert plugin_data['exchange_count'] == 1
    assert plugin_data['percentage'] == 33.3

    assert 'conversation_has_latex_math' in annotations
    
    # Empty conversation should return empty dict
    empty_conv = Conversation('test', 'Empty', [])
    empty_annotations = conversation_feature_summary(empty_conv)
    assert empty_annotations == {}


def test_conversation_gizmo_plugin_summary():
    """Test gizmo/plugin aggregation across exchanges."""
    # Create exchanges with gizmo/plugin annotations
    exchange1 = Exchange.create('test', [])
    exchange1.add_annotation('gizmo_1', {'gizmo_id': 'gpt-4'})
    exchange1.add_annotation('plugin_1', {'plugin_id': 'web_browser'})
    
    exchange2 = Exchange.create('test', [])
    exchange2.add_annotation('gizmo_2', {'gizmo_id': 'gpt-4'})  # Same gizmo again
    exchange2.add_annotation('plugin_2', {'plugin_id': 'python'})
    
    exchange3 = Exchange.create('test', [])
    exchange3.add_annotation('gizmo_3', {'gizmo_id': 'dalle'})
    
    conv = Conversation('test', 'Test', [exchange1, exchange2, exchange3])
    annotations = conversation_gizmo_plugin_summary(conv)
    
    # Should have gizmo and plugin summary annotations
    assert len(annotations) == 2
    
    gizmo_data = annotations['conversation_gizmo_usage']
    assert gizmo_data['unique_gizmos'] == 2  # gpt-4, dalle
    assert gizmo_data['total_usage'] == 3   # gpt-4 used twice
    assert set(gizmo_data['gizmo_list']) == {'gpt-4', 'dalle'}
    
    plugin_data = annotations['conversation_plugin_usage']
    assert plugin_data['unique_plugins'] == 2  # web_browser, python
    assert plugin_data['total_usage'] == 2
    assert set(plugin_data['plugin_list']) == {'web_browser', 'python'}
    
    # No gizmo/plugin usage should return empty dict
    empty_exchange = Exchange.create('test', [])
    empty_conv = Conversation('test', 'Empty', [empty_exchange])
    empty_annotations = conversation_gizmo_plugin_summary(empty_conv)
    assert empty_annotations == {}


######################
#  Exchange Tests    #
######################

def test_has_github_repos():
    """Test GitHub repository detection."""
    # Exchange with GitHub repos
    msg_with_repos = {
        'author': {'role': 'user'},
        'metadata': {'selected_github_repos': ['owner/repo1', 'owner/repo2']},
        'content': {'text': 'Help with code'}
    }
    exchange_with = Exchange.create('test', [msg_with_repos])
    assert has_github_repos(exchange_with) == True
    
    # Exchange without GitHub repos
    msg_without_repos = {
        'author': {'role': 'user'},
        'metadata': {'selected_github_repos': []},
        'content': {'text': 'General question'}
    }
    exchange_without = Exchange.create('test', [msg_without_repos])
    assert has_github_repos(exchange_without) == False


def test_get_gizmo_annotations():
    """Test gizmo annotation generation."""
    # Exchange with single gizmo
    msg_with_gizmo = {
        'author': {'role': 'assistant'},
        'metadata': {'gizmo_id': 'gpt-4-turbo'},
        'content': {'text': 'Response from specialized model'}
    }
    exchange_single = Exchange.create('test', [msg_with_gizmo])
    annotations = get_gizmo_annotations(exchange_single)
    assert len(annotations) == 1
    assert 'gizmo_1' in annotations
    assert annotations['gizmo_1']['gizmo_id'] == 'gpt-4-turbo'
    
    # Exchange with multiple messages using different gizmos
    msg_gizmo1 = {
        'author': {'role': 'assistant'},
        'metadata': {'gizmo_id': 'gpt-4'},
        'content': {'text': 'First response'}
    }
    msg_gizmo2 = {
        'author': {'role': 'assistant'},
        'metadata': {'gizmo_id': 'dalle'},
        'content': {'text': 'Second response'}
    }
    exchange_multiple = Exchange.create('test', [msg_gizmo1, msg_gizmo2])
    annotations = get_gizmo_annotations(exchange_multiple)
    assert len(annotations) == 2
    gizmo_ids = {data['gizmo_id'] for data in annotations.values()}
    assert gizmo_ids == {'gpt-4', 'dalle'}
    
    # Exchange without gizmo usage
    msg_no_gizmo = {
        'author': {'role': 'assistant'},
        'metadata': {},
        'content': {'text': 'Regular response'}
    }
    exchange_none = Exchange.create('test', [msg_no_gizmo])
    annotations = get_gizmo_annotations(exchange_none)
    assert annotations == {}


def test_get_plugin_annotations():
    """Test plugin annotation generation."""
    # Exchange with plugin_id only
    msg_plugin_id = {
        'author': {'role': 'assistant'},
        'metadata': {'invoked_plugin': {'plugin_id': 'web_browser'}},
        'content': {'text': 'Searching web'}
    }
    exchange_plugin_id = Exchange.create('test', [msg_plugin_id])
    annotations = get_plugin_annotations(exchange_plugin_id)
    assert len(annotations) == 1
    assert 'plugin_1' in annotations
    assert annotations['plugin_1']['plugin_id'] == 'web_browser'
    
    # Exchange with both plugin_id and namespace
    msg_both = {
        'author': {'role': 'assistant'},
        'metadata': {'invoked_plugin': {'plugin_id': 'image_gen', 'namespace': 'dalle'}},
        'content': {'text': 'Generating image'}
    }
    exchange_both = Exchange.create('test', [msg_both])
    annotations = get_plugin_annotations(exchange_both)
    assert len(annotations) == 2
    plugin_ids = {data['plugin_id'] for data in annotations.values()}
    assert plugin_ids == {'image_gen', 'dalle'}
    
    # Exchange without plugin usage
    msg_none = {
        'author': {'role': 'assistant'},
        'metadata': {},
        'content': {'text': 'Regular response'}
    }
    exchange_none = Exchange.create('test', [msg_none])
    annotations = get_plugin_annotations(exchange_none)
    assert annotations == {}


def test_has_code_blocks():
    """Test code block detection."""
    # Exchange with code blocks
    user_msg = {'author': {'role': 'user'}, 'content': {'text': 'Fix this: ```python\nprint("hello")\n```'}}
    assistant_msg = {'author': {'role': 'assistant'}, 'content': {'text': 'Here is the fix: ```python\nprint("Hello!")\n```'}}
    exchange_with = Exchange.create('test', [user_msg, assistant_msg])
    assert has_code_blocks(exchange_with) == True
    
    # Exchange without code blocks
    user_msg_no_code = {'author': {'role': 'user'}, 'content': {'text': 'What is Python?'}}
    assistant_msg_no_code = {'author': {'role': 'assistant'}, 'content': {'text': 'Python is a programming language'}}
    exchange_without = Exchange.create('test', [user_msg_no_code, assistant_msg_no_code])
    assert has_code_blocks(exchange_without) == False


def test_has_latex_math():
    """Test LaTeX math detection."""
    # Block math
    msg_block_math = {
        'author': {'role': 'assistant'},
        'content': {'text': 'The quadratic formula is: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$'}
    }
    exchange_block = Exchange.create('test', [msg_block_math])
    assert has_latex_math(exchange_block) == True
    
    # LaTeX commands
    msg_latex_commands = {
        'author': {'role': 'assistant'},
        'content': {'text': 'The integral \\int_{0}^{\\infty} e^{-x} dx = 1'}
    }
    exchange_commands = Exchange.create('test', [msg_latex_commands])
    assert has_latex_math(exchange_commands) == True
    
    # No math
    msg_no_math = {
        'author': {'role': 'assistant'},
        'content': {'text': 'This is regular text without any mathematical notation'}
    }
    exchange_no_math = Exchange.create('test', [msg_no_math])
    assert has_latex_math(exchange_no_math) == False


def test_first_user_has_large_content():
    """Test large content detection in first user message."""
    # Large content (over 2000 chars)
    large_text = 'x' * 2500
    msg_large = {
        'author': {'role': 'user'},
        'content': {'text': large_text}
    }
    exchange_large = Exchange.create('test', [msg_large])
    assert first_user_has_large_content(exchange_large) == True
    
    # Small content
    msg_small = {
        'author': {'role': 'user'},
        'content': {'text': 'Short question'}
    }
    exchange_small = Exchange.create('test', [msg_small])
    assert first_user_has_large_content(exchange_small) == False
    
    # Custom threshold
    medium_text = 'x' * 1500
    msg_medium = {
        'author': {'role': 'user'},
        'content': {'text': medium_text}
    }
    exchange_medium = Exchange.create('test', [msg_medium])
    assert first_user_has_large_content(exchange_medium, min_length=1000) == True
    assert first_user_has_large_content(exchange_medium, min_length=2000) == False


def test_user_has_attachments():
    """Test user attachment detection."""
    # User with attachments
    msg_with_attachments = {
        'author': {'role': 'user'},
        'metadata': {'attachments': [{'id': 'file1', 'name': 'document.pdf'}]},
        'content': {'text': 'Please analyze this file'}
    }
    exchange_with = Exchange.create('test', [msg_with_attachments])
    assert user_has_attachments(exchange_with) == True
    
    # User without attachments
    msg_without_attachments = {
        'author': {'role': 'user'},
        'metadata': {'attachments': []},
        'content': {'text': 'General question'}
    }
    exchange_without = Exchange.create('test', [msg_without_attachments])
    assert user_has_attachments(exchange_without) == False


def test_extract_proposed_title():
    """Test proposed title extraction from assistant messages."""
    # Test markdown header title (single #)
    msg_markdown_h1 = {
        'author': {'role': 'assistant'},
        'content': {'text': '# Introduction to Python\n\nPython is a programming language...'}
    }
    exchange_h1 = Exchange.create('test', [msg_markdown_h1])
    title_h1 = extract_proposed_title(exchange_h1)
    assert title_h1 == 'Introduction to Python'
    
    # Test bold title
    msg_bold_title = {
        'author': {'role': 'assistant'},
        'content': {'text': '**Machine Learning Basics**\n\nMachine learning is...'}
    }
    exchange_bold = Exchange.create('test', [msg_bold_title])
    title_bold = extract_proposed_title(exchange_bold)
    assert title_bold == 'Machine Learning Basics'
    
    # Test no title format (regular text)
    msg_no_title = {
        'author': {'role': 'assistant'},
        'content': {'text': 'This is just regular text without any title formatting.'}
    }
    exchange_no_title = Exchange.create('test', [msg_no_title])
    title_none = extract_proposed_title(exchange_no_title)
    assert title_none is None


def test_naive_title_extraction():
    """Test the helper function directly."""
    # Test markdown headers
    assert naive_title_extraction('# Simple Title') == 'Simple Title'
    assert naive_title_extraction('## Header Level 2') == 'Header Level 2'
    
    # Test bold titles
    assert naive_title_extraction('**Bold Title**') == 'Bold Title'
    
    # Test no title formats
    assert naive_title_extraction('Regular text') is None
    assert naive_title_extraction('Not a title format') is None
    
    # Test with whitespace
    assert naive_title_extraction('  # Title with spaces  ') == 'Title with spaces'
