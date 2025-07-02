# tests/conversation_tagger/test_detection.py
"""
Unit tests for detection.py detection functions.
One test function per detection function with multiple asserts.
"""

import pytest
from conversation_tagger.core.detection import *
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.conversation import Conversation
from conversation_tagger.core.tag import Tag


######################
# Conversation Tests #
######################

def test_create_conversation_length_tag():
    """Test conversation length categorization."""
    # Single exchange
    conv_single = Conversation('test', 'Single', [Exchange.create('test', [])])
    tag = create_conversation_length_tag(conv_single)
    assert tag.name == 'conversation_length'
    assert tag.attributes['count'] == 1
    assert tag.attributes['category'] == 'single'
    
    # Short (3 exchanges)
    exchanges = [Exchange.create('test', []) for _ in range(3)]
    conv_short = Conversation('test', 'Short', exchanges)
    tag = create_conversation_length_tag(conv_short)
    assert tag.attributes['count'] == 3
    assert tag.attributes['category'] == 'short'
    
    # Medium (7 exchanges)
    exchanges = [Exchange.create('test', []) for _ in range(7)]
    conv_medium = Conversation('test', 'Medium', exchanges)
    tag = create_conversation_length_tag(conv_medium)
    assert tag.attributes['count'] == 7
    assert tag.attributes['category'] == 'medium'
    
    # Long (15 exchanges)
    exchanges = [Exchange.create('test', []) for _ in range(15)]
    conv_long = Conversation('test', 'Long', exchanges)
    tag = create_conversation_length_tag(conv_long)
    assert tag.attributes['count'] == 15
    assert tag.attributes['category'] == 'long'
    
    # Very long (30 exchanges)
    exchanges = [Exchange.create('test', []) for _ in range(30)]
    conv_very_long = Conversation('test', 'VeryLong', exchanges)
    tag = create_conversation_length_tag(conv_very_long)
    assert tag.attributes['count'] == 30
    assert tag.attributes['category'] == 'very_long'


def test_conversation_feature_summary():
    """Test feature aggregation across exchanges."""
    # Create exchanges with different feature tags
    exchange1 = Exchange.create('test', [])
    exchange1.tags = [Tag('has_code_blocks'), Tag('has_web_search'), Tag('gizmo', gizmo_id='gpt-4')]
    
    exchange2 = Exchange.create('test', [])
    exchange2.tags = [Tag('has_code_blocks'), Tag('has_github_repos'), Tag('plugin', plugin_id='web')]
    
    exchange3 = Exchange.create('test', [])
    exchange3.tags = [Tag('has_latex_math')]
    
    conv = Conversation('test', 'Test', [exchange1, exchange2, exchange3])
    tags = conversation_feature_summary(conv)
    
    # Convert to dict for easier testing
    tag_dict = {tag.name: tag for tag in tags}
    
    # has_code_blocks appears in 2/3 exchanges
    assert 'conversation_has_code_blocks' in tag_dict
    code_tag = tag_dict['conversation_has_code_blocks']
    assert code_tag.attributes['exchange_count'] == 2
    assert code_tag.attributes['total_exchanges'] == 3
    assert code_tag.attributes['percentage'] == 66.7
    
    assert 'conversation_has_web_search' in tag_dict
    search_tag = tag_dict['conversation_has_web_search']
    assert search_tag.attributes['exchange_count'] == 1
    assert search_tag.attributes['percentage'] == 33.3
    
    assert 'conversation_has_gizmo_usage' in tag_dict
    gizmo_tag = tag_dict['conversation_has_gizmo_usage']
    assert gizmo_tag.attributes['exchange_count'] == 1
    assert gizmo_tag.attributes['percentage'] == 33.3
    
    assert 'conversation_has_plugin_usage' in tag_dict
    plugin_tag = tag_dict['conversation_has_plugin_usage']
    assert plugin_tag.attributes['exchange_count'] == 1
    assert plugin_tag.attributes['percentage'] == 33.3

    assert 'conversation_has_latex_math' in tag_dict
    
    # Features not in the tracking list should not appear
    # ... maybe later
    
    # Empty conversation should return empty list
    empty_conv = Conversation('test', 'Empty', [])
    empty_tags = conversation_feature_summary(empty_conv)
    assert empty_tags == []


def test_conversation_gizmo_plugin_summary():
    """Test gizmo/plugin aggregation across exchanges."""
    # Create exchanges with gizmo/plugin tags
    exchange1 = Exchange.create('test', [])
    exchange1.tags = [
        Tag('gizmo', gizmo_id='gpt-4'),
        Tag('plugin', plugin_id='web_browser')
    ]
    
    exchange2 = Exchange.create('test', [])
    exchange2.tags = [
        Tag('gizmo', gizmo_id='gpt-4'),  # Same gizmo again
        Tag('plugin', plugin_id='python')
    ]
    
    exchange3 = Exchange.create('test', [])
    exchange3.tags = [Tag('gizmo', gizmo_id='dalle')]
    
    conv = Conversation('test', 'Test', [exchange1, exchange2, exchange3])
    tags = conversation_gizmo_plugin_summary(conv)
    
    # Should have gizmo and plugin summary tags
    assert len(tags) == 2
    
    gizmo_tag = next(t for t in tags if t.name == 'conversation_gizmo_usage')
    assert gizmo_tag.attributes['unique_gizmos'] == 2  # gpt-4, dalle
    assert gizmo_tag.attributes['total_usage'] == 3   # gpt-4 used twice
    assert set(gizmo_tag.attributes['gizmo_list']) == {'gpt-4', 'dalle'}
    
    plugin_tag = next(t for t in tags if t.name == 'conversation_plugin_usage')
    assert plugin_tag.attributes['unique_plugins'] == 2  # web_browser, python
    assert plugin_tag.attributes['total_usage'] == 2
    assert set(plugin_tag.attributes['plugin_list']) == {'web_browser', 'python'}
    
    # No gizmo/plugin usage should return empty list
    empty_exchange = Exchange.create('test', [])
    empty_conv = Conversation('test', 'Empty', [empty_exchange])
    empty_tags = conversation_gizmo_plugin_summary(empty_conv)
    assert empty_tags == []
    
    # Only gizmo usage
    gizmo_only_exchange = Exchange.create('test', [])
    gizmo_only_exchange.tags = [Tag('gizmo', gizmo_id='claude')]
    gizmo_only_conv = Conversation('test', 'GizmoOnly', [gizmo_only_exchange])
    gizmo_only_tags = conversation_gizmo_plugin_summary(gizmo_only_conv)
    assert len(gizmo_only_tags) == 1
    assert gizmo_only_tags[0].name == 'conversation_gizmo_usage'
    assert gizmo_only_tags[0].attributes['unique_gizmos'] == 1
    assert gizmo_only_tags[0].attributes['gizmo_list'] == ['claude']


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
    
    # Exchange with no metadata
    msg_no_metadata = {
        'author': {'role': 'user'},
        'content': {'text': 'Simple question'}
    }
    exchange_no_meta = Exchange.create('test', [msg_no_metadata])
    assert has_github_repos(exchange_no_meta) == False


def test_has_canvas_operations():
    """Test canvas/document operations detection."""
    # Exchange with canvas
    msg_with_canvas = {
        'author': {'role': 'assistant'},
        'metadata': {'canvas': {'textdoc_id': 'doc123', 'version': 1}},
        'content': {'text': 'Document created'}
    }
    exchange_with = Exchange.create('test', [msg_with_canvas])
    assert has_canvas_operations(exchange_with) == True
    
    # Exchange without canvas
    msg_without_canvas = {
        'author': {'role': 'assistant'},
        'metadata': {},
        'content': {'text': 'Regular response'}
    }
    exchange_without = Exchange.create('test', [msg_without_canvas])
    assert has_canvas_operations(exchange_without) == False


def test_has_web_search():
    """Test web search detection."""
    # Exchange with search queries
    msg_with_search = {
        'author': {'role': 'assistant'},
        'metadata': {'search_queries': [{'q': 'python tutorial', 'type': 'web'}]},
        'content': {'text': 'Let me search for that'}
    }
    exchange_with_queries = Exchange.create('test', [msg_with_search])
    assert has_web_search(exchange_with_queries) == True
    
    # Exchange with search results
    msg_with_results = {
        'author': {'role': 'assistant'},
        'metadata': {'search_result_groups': [{'type': 'web', 'entries': []}]},
        'content': {'text': 'Found some results'}
    }
    exchange_with_results = Exchange.create('test', [msg_with_results])
    assert has_web_search(exchange_with_results) == True
    
    # Exchange with content references
    msg_with_refs = {
        'author': {'role': 'assistant'},
        'metadata': {'content_references': [{'matched_text': 'citation'}]},
        'content': {'text': 'According to sources'}
    }
    exchange_with_refs = Exchange.create('test', [msg_with_refs])
    assert has_web_search(exchange_with_refs) == True
    
    # Exchange without search
    msg_without_search = {
        'author': {'role': 'assistant'},
        'metadata': {},
        'content': {'text': 'Regular response'}
    }
    exchange_without = Exchange.create('test', [msg_without_search])
    assert has_web_search(exchange_without) == False


def test_has_reasoning_thoughts():
    """Test reasoning/thinking pattern detection."""
    # Exchange with thoughts
    msg_with_thoughts = {
        'author': {'role': 'assistant'},
        'content': {
            'text': 'Let me think about this',
            'thoughts': [{'content': 'I need to analyze this step by step'}]
        }
    }
    exchange_with = Exchange.create('test', [msg_with_thoughts])
    assert has_reasoning_thoughts(exchange_with) == True
    
    # Exchange without thoughts
    msg_without_thoughts = {
        'author': {'role': 'assistant'},
        'content': {'text': 'Here is the answer'}
    }
    exchange_without = Exchange.create('test', [msg_without_thoughts])
    assert has_reasoning_thoughts(exchange_without) == False


def test_has_code_execution():
    """Test code execution detection."""
    # Exchange with aggregate result
    msg_with_aggregate = {
        'author': {'role': 'assistant'},
        'metadata': {'aggregate_result': {'status': 'completed', 'code': 'print("hello")'}},
        'content': {'text': 'Running code'}
    }
    exchange_with_agg = Exchange.create('test', [msg_with_aggregate])
    assert has_code_execution(exchange_with_agg) == True
    
    # Exchange with jupyter messages
    msg_with_jupyter = {
        'author': {'role': 'assistant'},
        'metadata': {'jupyter_messages': [{'msg_type': 'execute_result'}]},
        'content': {'text': 'Code executed'}
    }
    exchange_with_jupyter = Exchange.create('test', [msg_with_jupyter])
    assert has_code_execution(exchange_with_jupyter) == True
    
    # Exchange without code execution
    msg_without_exec = {
        'author': {'role': 'assistant'},
        'metadata': {},
        'content': {'text': 'Regular text response'}
    }
    exchange_without = Exchange.create('test', [msg_without_exec])
    assert has_code_execution(exchange_without) == False


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
    
    # Empty exchange
    exchange_empty = Exchange.create('test', [])
    assert has_code_blocks(exchange_empty) == False


def test_has_script_headers():
    """Test script header detection."""
    # Exchange with shebang
    msg_with_shebang = {'author': {'role': 'user'}, 'content': {'text': '#!/bin/bash\necho "hello"'}}
    exchange_with_shebang = Exchange.create('test', [msg_with_shebang])
    assert has_script_headers(exchange_with_shebang) == True
    
    # Exchange with #include
    msg_with_include = {'author': {'role': 'assistant'}, 'content': {'text': '#include <stdio.h>\nint main() { return 0; }'}}
    exchange_with_include = Exchange.create('test', [msg_with_include])
    assert has_script_headers(exchange_with_include) == True
    
    # Exchange with using namespace
    msg_with_namespace = {'author': {'role': 'user'}, 'content': {'text': 'using namespace std;\nint main() {}'}}
    exchange_with_namespace = Exchange.create('test', [msg_with_namespace])
    assert has_script_headers(exchange_with_namespace) == True
    
    # Exchange without script headers
    msg_without = {'author': {'role': 'user'}, 'content': {'text': 'How do I write a script?'}}
    exchange_without = Exchange.create('test', [msg_without])
    assert has_script_headers(exchange_without) == False


def test_has_code_structure_patterns():
    """Test code structure pattern detection."""
    # Python function pattern
    msg_python = {'author': {'role': 'assistant'}, 'content': {'text': 'def calculate(x):\n    return x * 2'}}
    exchange_python = Exchange.create('test', [msg_python])
    assert has_code_structure_patterns(exchange_python) == True
    
    # Python class pattern
    msg_class = {'author': {'role': 'user'}, 'content': {'text': 'class MyClass():\n    def __init__(self):\n        pass'}}
    exchange_class = Exchange.create('test', [msg_class])
    assert has_code_structure_patterns(exchange_class) == True
    
    # JavaScript function pattern
    msg_js = {'author': {'role': 'assistant'}, 'content': {'text': 'function hello() {\n    console.log("hi");\n}'}}
    exchange_js = Exchange.create('test', [msg_js])
    assert has_code_structure_patterns(exchange_js) == True
    
    # Multiple assignments pattern
    msg_assignments = {'author': {'role': 'user'}, 'content': {'text': 'let x = 1;\nlet y = 2;\nlet z = 3;\nconst result = x + y + z;'}}
    exchange_assignments = Exchange.create('test', [msg_assignments])
    assert has_code_structure_patterns(exchange_assignments) == True
    
    # No code structure
    msg_no_code = {'author': {'role': 'user'}, 'content': {'text': 'Explain what a function is'}}
    exchange_no_code = Exchange.create('test', [msg_no_code])
    assert has_code_structure_patterns(exchange_no_code) == False


def test_user_has_quote_elaborate():
    """Test quote+elaborate pattern detection."""
    # Valid quote+elaborate pattern
    msg_quote_elaborate = {
        'author': {'role': 'user'}, 
        'content': {'text': '> Python is a programming language\nelaborate'}
    }
    exchange_with = Exchange.create('test', [msg_quote_elaborate])
    assert user_has_quote_elaborate(exchange_with) == True
    
    # Quote without elaborate
    msg_quote_only = {
        'author': {'role': 'user'}, 
        'content': {'text': '> Python is a programming language\nTell me more'}
    }
    exchange_quote_only = Exchange.create('test', [msg_quote_only])
    assert user_has_quote_elaborate(exchange_quote_only) == False
    
    # Elaborate without quote
    msg_elaborate_only = {
        'author': {'role': 'user'}, 
        'content': {'text': 'elaborate'}
    }
    exchange_elaborate_only = Exchange.create('test', [msg_elaborate_only])
    assert user_has_quote_elaborate(exchange_elaborate_only) == False
    
    # No user messages
    msg_assistant = {'author': {'role': 'assistant'}, 'content': {'text': 'Response'}}
    exchange_no_user = Exchange.create('test', [msg_assistant])
    assert user_has_quote_elaborate(exchange_no_user) == False


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
    
    # No user messages
    msg_assistant = {'author': {'role': 'assistant'}, 'content': {'text': 'Response'}}
    exchange_no_user = Exchange.create('test', [msg_assistant])
    assert user_has_attachments(exchange_no_user) == False


def test_user_is_continuation():
    """Test continuation detection."""
    # Create exchange with multiple user messages (continuation)
    user_msg1 = {'author': {'role': 'user'}, 'content': {'text': 'First message'}}
    assistant_msg = {'author': {'role': 'assistant'}, 'content': {'text': 'Response'}}
    user_msg2 = {'author': {'role': 'user'}, 'content': {'text': 'Continue please'}}
    exchange_continuation = Exchange.create('test', [user_msg1, assistant_msg, user_msg2])
    assert user_is_continuation(exchange_continuation) == True
    
    # Regular exchange (single user message)
    user_msg = {'author': {'role': 'user'}, 'content': {'text': 'Question'}}
    assistant_response = {'author': {'role': 'assistant'}, 'content': {'text': 'Answer'}}
    exchange_regular = Exchange.create('test', [user_msg, assistant_response])
    assert user_is_continuation(exchange_regular) == False


def test_assistant_has_reasoning():
    """Test assistant reasoning detection."""
    # Assistant with reasoning thoughts
    msg_with_reasoning = {
        'author': {'role': 'assistant'},
        'content': {
            'text': 'Let me think about this',
            'thoughts': [{'content': 'I should consider multiple angles'}]
        }
    }
    exchange_with = Exchange.create('test', [msg_with_reasoning])
    assert assistant_has_reasoning(exchange_with) == True
    
    # Assistant without reasoning
    msg_without_reasoning = {
        'author': {'role': 'assistant'},
        'content': {'text': 'Here is the answer'}
    }
    exchange_without = Exchange.create('test', [msg_without_reasoning])
    assert assistant_has_reasoning(exchange_without) == False
    
    # No assistant messages
    user_msg = {'author': {'role': 'user'}, 'content': {'text': 'Question'}}
    exchange_no_assistant = Exchange.create('test', [user_msg])
    assert assistant_has_reasoning(exchange_no_assistant) == False


def test_has_wiki_links():
    """Test wiki link detection."""
    # Assistant with wiki links
    msg_with_wiki = {
        'author': {'role': 'assistant'},
        'content': {'text': 'See [[Python Programming]] and [[Data Structures]] for more info'}
    }
    exchange_with = Exchange.create('test', [msg_with_wiki])
    assert has_wiki_links(exchange_with) == True
    
    # Assistant without wiki links
    msg_without_wiki = {
        'author': {'role': 'assistant'},
        'content': {'text': 'Python is a programming language'}
    }
    exchange_without = Exchange.create('test', [msg_without_wiki])
    assert has_wiki_links(exchange_without) == False
    
    # User with wiki links (should not count)
    user_msg_wiki = {'author': {'role': 'user'}, 'content': {'text': 'Tell me about [[Python]]'}}
    assistant_msg_no_wiki = {'author': {'role': 'assistant'}, 'content': {'text': 'Python is great'}}
    exchange_user_wiki = Exchange.create('test', [user_msg_wiki, assistant_msg_no_wiki])
    assert has_wiki_links(exchange_user_wiki) == False


def test_has_latex_math():
    """Test LaTeX math detection."""
    # Block math
    msg_block_math = {
        'author': {'role': 'assistant'},
        'content': {'text': 'The quadratic formula is: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$'}
    }
    exchange_block = Exchange.create('test', [msg_block_math])
    assert has_latex_math(exchange_block) == True
    
    # Inline math with \\( \\)
    msg_inline_math = {
        'author': {'role': 'assistant'},
        'content': {'text': 'The result is \\(x = 5\\) which is correct'}
    }
    exchange_inline = Exchange.create('test', [msg_inline_math])
    assert has_latex_math(exchange_inline) == True
    
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
    
    # No user messages
    msg_assistant = {'author': {'role': 'assistant'}, 'content': {'text': 'Response'}}
    exchange_no_user = Exchange.create('test', [msg_assistant])
    assert first_user_has_large_content(exchange_no_user) == False


def test_first_user_has_code_patterns():
    """Test code pattern detection in first user message."""
    # Message with code blocks
    msg_code_blocks = {
        'author': {'role': 'user'},
        'content': {'text': 'Fix this: ```python\nprint("hello")\n```'}
    }
    exchange_code_blocks = Exchange.create('test', [msg_code_blocks])
    assert first_user_has_code_patterns(exchange_code_blocks) == True
    
    # Message with function definition
    msg_def = {
        'author': {'role': 'user'},
        'content': {'text': 'Help with: def my_function(): pass'}
    }
    exchange_def = Exchange.create('test', [msg_def])
    assert first_user_has_code_patterns(exchange_def) == True
    
    # Message with imports
    msg_import = {
        'author': {'role': 'user'},
        'content': {'text': 'import numpy as np\nHow to use this?'}
    }
    exchange_import = Exchange.create('test', [msg_import])
    assert first_user_has_code_patterns(exchange_import) == True
    
    # Message with shebang
    msg_shebang = {
        'author': {'role': 'user'},
        'content': {'text': '#!/bin/bash\necho "hello"'}
    }
    exchange_shebang = Exchange.create('test', [msg_shebang])
    assert first_user_has_code_patterns(exchange_shebang) == True
    
    # No code patterns
    msg_no_code = {
        'author': {'role': 'user'},
        'content': {'text': 'What is programming?'}
    }
    exchange_no_code = Exchange.create('test', [msg_no_code])
    assert first_user_has_code_patterns(exchange_no_code) == False


def test_first_user_has_attachments():
    """Test attachment detection in first user message."""
    # First user message with attachments
    msg_with_attachments = {
        'author': {'role': 'user'},
        'metadata': {'attachments': [{'id': 'file1', 'name': 'data.csv'}]},
        'content': {'text': 'Analyze this file'}
    }
    exchange_with = Exchange.create('test', [msg_with_attachments])
    assert first_user_has_attachments(exchange_with) == True
    
    # First user message without attachments
    msg_without_attachments = {
        'author': {'role': 'user'},
        'metadata': {'attachments': []},
        'content': {'text': 'General question'}
    }
    exchange_without = Exchange.create('test', [msg_without_attachments])
    assert first_user_has_attachments(exchange_without) == False
    
    # Second user message with attachments (should not count)
    msg_first = {'author': {'role': 'user'}, 'content': {'text': 'First message'}}
    msg_second = {
        'author': {'role': 'user'},
        'metadata': {'attachments': [{'id': 'file1', 'name': 'data.csv'}]},
        'content': {'text': 'Second message with file'}
    }
    exchange_second_attachment = Exchange.create('test', [msg_first, msg_second])
    assert first_user_has_attachments(exchange_second_attachment) == False


def test_first_user_has_code_attachments():
    """Test code attachment detection in first user message."""
    # Python file attachment
    msg_python_file = {
        'author': {'role': 'user'},
        'metadata': {'attachments': [{'id': 'file1', 'name': 'script.py', 'mime_type': 'text/x-python'}]},
        'content': {'text': 'Review this code'}
    }
    exchange_python = Exchange.create('test', [msg_python_file])
    assert first_user_has_code_attachments(exchange_python) == True
    
    # JavaScript file attachment
    msg_js_file = {
        'author': {'role': 'user'},
        'metadata': {'attachments': [{'id': 'file1', 'name': 'app.js', 'mime_type': 'application/javascript'}]},
        'content': {'text': 'Help with this JS'}
    }
    exchange_js = Exchange.create('test', [msg_js_file])
    assert first_user_has_code_attachments(exchange_js) == True
    
    # Multiple files, one is code
    msg_mixed_files = {
        'author': {'role': 'user'},
        'metadata': {'attachments': [
            {'id': 'file1', 'name': 'data.csv', 'mime_type': 'text/csv'},
            {'id': 'file2', 'name': 'script.cpp', 'mime_type': 'text/x-c++'}
        ]},
        'content': {'text': 'Review these files'}
    }
    exchange_mixed = Exchange.create('test', [msg_mixed_files])
    assert first_user_has_code_attachments(exchange_mixed) == True
    
    # Non-code attachments
    msg_non_code = {
        'author': {'role': 'user'},
        'metadata': {'attachments': [{'id': 'file1', 'name': 'document.pdf', 'mime_type': 'application/pdf'}]},
        'content': {'text': 'Analyze this document'}
    }
    exchange_non_code = Exchange.create('test', [msg_non_code])
    assert first_user_has_code_attachments(exchange_non_code) == False
    
    # No attachments
    msg_no_attachments = {
        'author': {'role': 'user'},
        'content': {'text': 'General coding question'}
    }
    exchange_no_attachments = Exchange.create('test', [msg_no_attachments])
    assert first_user_has_code_attachments(exchange_no_attachments) == False


def test_get_gizmo_tags():
    """Test gizmo tag generation."""
    # Exchange with single gizmo
    msg_with_gizmo = {
        'author': {'role': 'assistant'},
        'metadata': {'gizmo_id': 'gpt-4-turbo'},
        'content': {'text': 'Response from specialized model'}
    }
    exchange_single = Exchange.create('test', [msg_with_gizmo])
    tags_single = get_gizmo_tags(exchange_single)
    assert len(tags_single) == 1
    assert tags_single[0].name == 'gizmo'
    assert tags_single[0].attributes['gizmo_id'] == 'gpt-4-turbo'
    
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
    tags_multiple = get_gizmo_tags(exchange_multiple)
    assert len(tags_multiple) == 2
    gizmo_ids = {tag.attributes['gizmo_id'] for tag in tags_multiple}
    assert gizmo_ids == {'gpt-4', 'dalle'}
    
    # Exchange with same gizmo used multiple times (should deduplicate)
    msg_dup1 = {
        'author': {'role': 'assistant'},
        'metadata': {'gizmo_id': 'gpt-4'},
        'content': {'text': 'First'}
    }
    msg_dup2 = {
        'author': {'role': 'assistant'},
        'metadata': {'gizmo_id': 'gpt-4'},
        'content': {'text': 'Second'}
    }
    exchange_dup = Exchange.create('test', [msg_dup1, msg_dup2])
    tags_dup = get_gizmo_tags(exchange_dup)
    assert len(tags_dup) == 1
    assert tags_dup[0].attributes['gizmo_id'] == 'gpt-4'
    
    # Exchange without gizmo usage
    msg_no_gizmo = {
        'author': {'role': 'assistant'},
        'metadata': {},
        'content': {'text': 'Regular response'}
    }
    exchange_none = Exchange.create('test', [msg_no_gizmo])
    tags_none = get_gizmo_tags(exchange_none)
    assert tags_none == []


def test_get_plugin_tags():
    """Test plugin tag generation."""
    # Exchange with plugin_id only
    msg_plugin_id = {
        'author': {'role': 'assistant'},
        'metadata': {'invoked_plugin': {'plugin_id': 'web_browser'}},
        'content': {'text': 'Searching web'}
    }
    exchange_plugin_id = Exchange.create('test', [msg_plugin_id])
    tags_plugin_id = get_plugin_tags(exchange_plugin_id)
    assert len(tags_plugin_id) == 1
    assert tags_plugin_id[0].name == 'plugin'
    assert tags_plugin_id[0].attributes['plugin_id'] == 'web_browser'
    
    # Exchange with namespace only
    msg_namespace = {
        'author': {'role': 'assistant'},
        'metadata': {'invoked_plugin': {'namespace': 'browser_tools'}},
        'content': {'text': 'Using browser tools'}
    }
    exchange_namespace = Exchange.create('test', [msg_namespace])
    tags_namespace = get_plugin_tags(exchange_namespace)
    assert len(tags_namespace) == 1
    assert tags_namespace[0].attributes['plugin_id'] == 'browser_tools'
    
    # Exchange with both plugin_id and namespace
    msg_both = {
        'author': {'role': 'assistant'},
        'metadata': {'invoked_plugin': {'plugin_id': 'image_gen', 'namespace': 'dalle'}},
        'content': {'text': 'Generating image'}
    }
    exchange_both = Exchange.create('test', [msg_both])
    tags_both = get_plugin_tags(exchange_both)
    assert len(tags_both) == 2
    plugin_ids = {tag.attributes['plugin_id'] for tag in tags_both}
    assert plugin_ids == {'image_gen', 'dalle'}
    
    # Exchange with multiple different plugins
    msg_plugin1 = {
        'author': {'role': 'assistant'},
        'metadata': {'invoked_plugin': {'plugin_id': 'web_browser'}},
        'content': {'text': 'First'}
    }
    msg_plugin2 = {
        'author': {'role': 'assistant'},
        'metadata': {'invoked_plugin': {'plugin_id': 'calculator'}},
        'content': {'text': 'Second'}
    }
    exchange_multiple = Exchange.create('test', [msg_plugin1, msg_plugin2])
    tags_multiple = get_plugin_tags(exchange_multiple)
    assert len(tags_multiple) == 2
    plugin_ids = {tag.attributes['plugin_id'] for tag in tags_multiple}
    assert plugin_ids == {'web_browser', 'calculator'}
    
    # Exchange with empty invoked_plugin
    msg_empty = {
        'author': {'role': 'assistant'},
        'metadata': {'invoked_plugin': {}},
        'content': {'text': 'No plugin'}
    }
    exchange_empty = Exchange.create('test', [msg_empty])
    tags_empty = get_plugin_tags(exchange_empty)
    assert tags_empty == []
    
    # Exchange without plugin usage
    msg_none = {
        'author': {'role': 'assistant'},
        'metadata': {},
        'content': {'text': 'Regular response'}
    }
    exchange_none = Exchange.create('test', [msg_none])
    tags_none = get_plugin_tags(exchange_none)
    assert tags_none == []

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
    
    # Test markdown header title (multiple #)
    msg_markdown_h2 = {
        'author': {'role': 'assistant'},
        'content': {'text': '## Getting Started\n\nFirst, install Python...'}
    }
    exchange_h2 = Exchange.create('test', [msg_markdown_h2])
    title_h2 = extract_proposed_title(exchange_h2)
    assert title_h2 == 'Getting Started'
    
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
        'content': {'text': 'This is just regular text without any title formatting.\nMore content here.'}
    }
    exchange_no_title = Exchange.create('test', [msg_no_title])
    title_none = extract_proposed_title(exchange_no_title)
    assert title_none is None
    
    # Test malformed bold (only starts with **)
    msg_malformed_bold = {
        'author': {'role': 'assistant'},
        'content': {'text': '**This is not properly closed\nSome content here.'}
    }
    exchange_malformed = Exchange.create('test', [msg_malformed_bold])
    title_malformed = extract_proposed_title(exchange_malformed)
    assert title_malformed is None
    
    # Test title with extra whitespace
    msg_whitespace = {
        'author': {'role': 'assistant'},
        'content': {'text': '#   Data Science Guide   \n\nThis guide covers...'}
    }
    exchange_whitespace = Exchange.create('test', [msg_whitespace])
    title_whitespace = extract_proposed_title(exchange_whitespace)
    assert title_whitespace == 'Data Science Guide'
    
    # Test single line with title only
    msg_title_only = {
        'author': {'role': 'assistant'},
        'content': {'text': '# Quick Reference'}
    }
    exchange_title_only = Exchange.create('test', [msg_title_only])
    title_only = extract_proposed_title(exchange_title_only)
    assert title_only == 'Quick Reference'
    
    # Test multiple markdown headers (should only get first line)
    msg_multiple_headers = {
        'author': {'role': 'assistant'},
        'content': {'text': '# Main Title\n\n## Subtitle\n\nContent here...'}
    }
    exchange_multiple = Exchange.create('test', [msg_multiple_headers])
    title_multiple = extract_proposed_title(exchange_multiple)
    assert title_multiple == 'Main Title'
    
    # Test empty first line followed by title
    msg_empty_first = {
        'author': {'role': 'assistant'},
        'content': {'text': '\n# Not First Line\n\nContent...'}
    }
    exchange_empty_first = Exchange.create('test', [msg_empty_first])
    title = extract_proposed_title(exchange_empty_first)
    assert title == 'Not First Line'
    
    # Test exchange with multiple assistant messages (should use first one)
    msg_first = {
        'author': {'role': 'assistant'},
        'content': {'text': '# First Message Title\n\nFirst response...'}
    }
    msg_second = {
        'author': {'role': 'assistant'},
        'content': {'text': '# Second Message Title\n\nSecond response...'}
    }
    exchange_multiple_msgs = Exchange.create('test', [msg_first, msg_second])
    title_first_msg = extract_proposed_title(exchange_multiple_msgs)
    assert title_first_msg == 'First Message Title'
    
    # Test exchange with no assistant messages (edge case)
    user_msg = {
        'author': {'role': 'user'},
        'content': {'text': 'Just a user message'}
    }
    exchange_no_assistant = Exchange.create('test', [user_msg])
    title_no_assistant = extract_proposed_title(exchange_no_assistant)
    assert title_no_assistant is None
    
    # Test empty exchange
    exchange_empty = Exchange.create('test', [])
    title_empty = extract_proposed_title(exchange_empty)
    assert title_empty is None


def test_naive_title_extraction():
    """Test the helper function directly."""
    # Test markdown headers
    assert naive_title_extraction('# Simple Title') == 'Simple Title'
    assert naive_title_extraction('## Header Level 2') == 'Header Level 2'
    assert naive_title_extraction('### Deep Header') == 'Deep Header'
    
    # Test bold titles
    assert naive_title_extraction('**Bold Title**') == 'Bold Title'
    assert naive_title_extraction('**Another Bold**') == 'Another Bold'
    
    # Test no title formats
    assert naive_title_extraction('Regular text') is None
    assert naive_title_extraction('Not a title format') is None
    
    # Test malformed formats
    assert naive_title_extraction('**Not closed properly') is None
    assert naive_title_extraction('Only ends with**') is None
    assert naive_title_extraction('#') == ''  # Just hash, no title
    assert naive_title_extraction('****') == ''  # Just asterisks
    
    # Test with whitespace
    assert naive_title_extraction('  # Title with spaces  ') == 'Title with spaces'
    assert naive_title_extraction('**  Spaced Bold  **') == 'Spaced Bold'
    
    # Test multiline (should only process first line)
    multiline_text = '''# First Line Title
    Second line content
    Third line content'''
    assert naive_title_extraction(multiline_text) == 'First Line Title'
    
    # Test empty string
    assert naive_title_extraction('') is None
    assert naive_title_extraction('   ') is None