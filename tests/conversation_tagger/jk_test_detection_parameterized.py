# tests/conversation_tagger/test_detection_consistent.py
"""
Consistent test pattern using centralized test data.
"""

import pytest
from conversation_tagger import create_default_tagger
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.detection import *

# Import all test data from centralized module
from test_data import (
    get_simple_conversation_data,
    get_code_conversation_data,
    get_math_conversation_data,
    get_attachment_conversation_data,
    get_large_content_conversation_data,
    create_message_obj
)


class TestCodeDetection:
    """Test code detection using consistent data patterns."""
    
    @pytest.mark.parametrize("source,data", [
        ("oai", get_code_conversation_data()[0]),
        ("claude", get_code_conversation_data()[1])
    ])
    def test_has_code_blocks(self, source, data):
        """Test code block detection across sources."""
        tagger = create_default_tagger(source=source)
        result = tagger.tag_conversation(data)
        
        # Should detect code blocks
        has_code = any(exchange.has_annotation('has_code_blocks') 
                      for exchange in result.exchanges)
        assert has_code, f"Code blocks not detected for {source}"
        
        # Verify actual content contains code
        all_text = result.get_all_user_text() + result.get_all_assistant_text()
        assert '```' in all_text
        assert 'def hello' in all_text

    @pytest.mark.parametrize("source,data", [
        ("oai", get_code_conversation_data()[0]),
        ("claude", get_code_conversation_data()[1])
    ])
    def test_first_user_has_code_patterns(self, source, data):
        """Test first user code pattern detection."""
        tagger = create_default_tagger(source=source)
        result = tagger.tag_conversation(data)
        
        # Should detect code patterns in first user message
        has_first_user_code = any(exchange.has_annotation('first_user_has_code_patterns')
                                 for exchange in result.exchanges)
        assert has_first_user_code, f"First user code patterns not detected for {source}"

    @pytest.mark.parametrize("source", ["oai", "claude"])
    def test_has_script_headers(self, source):
        """Test script header detection using message helper."""
        script_text = '#!/bin/bash\necho "hello world"'
        message_obj = create_message_obj(source, 'user', script_text)
        exchange = Exchange.create('test', [message_obj])
        
        assert has_script_headers(exchange) == True

    @pytest.mark.parametrize("source", ["oai", "claude"])
    def test_has_code_structure_patterns(self, source):
        """Test code structure pattern detection."""
        code_text = 'def calculate(x, y):\n    if x > 0:\n        return x + y\n    return 0'
        message_obj = create_message_obj(source, 'user', code_text)
        exchange = Exchange.create('test', [message_obj])
        
        assert has_code_structure_patterns(exchange) == True


class TestMathDetection:
    """Test mathematical content detection using consistent patterns."""
    
    @pytest.mark.parametrize("source,data", [
        ("oai", get_math_conversation_data()[0]),
        ("claude", get_math_conversation_data()[1])
    ])
    def test_has_latex_math(self, source, data):
        """Test LaTeX math detection across sources."""
        tagger = create_default_tagger(source=source)
        result = tagger.tag_conversation(data)
        
        # Should detect LaTeX math
        has_math = any(exchange.has_annotation('has_latex_math') 
                      for exchange in result.exchanges)
        assert has_math, f"LaTeX math not detected for {source}"
        
        # Verify actual content contains math
        all_text = result.get_all_assistant_text()
        assert '$$' in all_text
        assert '\\frac' in all_text

    @pytest.mark.parametrize("source,pattern", [
        ("oai", '\\int_{0}^{\\infty} e^{-x} dx = 1'),
        ("claude", '\\int_{0}^{\\infty} e^{-x} dx = 1'),
        ("oai", 'The derivative is \\frac{dy}{dx}'),
        ("claude", 'The derivative is \\frac{dy}{dx}'),
        ("oai", 'Greek letters: \\alpha, \\beta, \\gamma'),
        ("claude", 'Greek letters: \\alpha, \\beta, \\gamma')
    ])
    def test_latex_patterns(self, source, pattern):
        """Test various LaTeX patterns using message helper."""
        message_obj = create_message_obj(source, 'assistant', pattern)
        exchange = Exchange.create('test', [message_obj])
        
        assert has_latex_math(exchange) == True, f"LaTeX pattern not detected: {pattern}"


class TestAttachmentDetection:
    """Test attachment detection using consistent patterns."""
    
    @pytest.mark.parametrize("source,data", [
        ("oai", get_attachment_conversation_data()[0]),
        ("claude", get_attachment_conversation_data()[1])
    ])
    def test_first_user_has_attachments(self, source, data):
        """Test attachment detection across sources."""
        tagger = create_default_tagger(source=source)
        result = tagger.tag_conversation(data)
        
        # Should detect attachments
        has_attachments = any(exchange.has_annotation('first_user_has_attachments')
                             for exchange in result.exchanges)
        assert has_attachments, f"Attachments not detected for {source}"

    @pytest.mark.parametrize("source,data", [
        ("oai", get_attachment_conversation_data()[0]),
        ("claude", get_attachment_conversation_data()[1])
    ])
    def test_first_user_has_code_attachments(self, source, data):
        """Test code attachment detection across sources."""
        tagger = create_default_tagger(source=source)
        result = tagger.tag_conversation(data)
        
        # Should detect code attachments specifically
        has_code_attachments = any(exchange.has_annotation('first_user_has_code_attachments')
                                  for exchange in result.exchanges)
        assert has_code_attachments, f"Code attachments not detected for {source}"

    @pytest.mark.parametrize("source", ["oai", "claude"])
    def test_user_has_attachments_edge_cases(self, source):
        """Test attachment detection edge cases using message helper."""
        # Message with empty attachments
        if source == "oai":
            message_obj = create_message_obj(source, 'user', 'No files here', 
                                           metadata={'attachments': []})
        else:
            message_obj = create_message_obj(source, 'user', 'No files here',
                                           attachments=[], files=[])
        
        exchange = Exchange.create('test', [message_obj])
        assert user_has_attachments(exchange) == False


class TestContentSizeDetection:
    """Test content size detection using consistent patterns."""
    
    @pytest.mark.parametrize("source,data", [
        ("oai", get_large_content_conversation_data()[0]),
        ("claude", get_large_content_conversation_data()[1])
    ])
    def test_first_user_has_large_content(self, source, data):
        """Test large content detection across sources."""
        tagger = create_default_tagger(source=source)
        result = tagger.tag_conversation(data)
        
        # Should detect large content
        has_large_content = any(exchange.has_annotation('first_user_has_large_content')
                               for exchange in result.exchanges)
        assert has_large_content, f"Large content not detected for {source}"

    @pytest.mark.parametrize("source,threshold,text_size,expected", [
        ("oai", 1000, 1500, True),
        ("claude", 1000, 1500, True),
        ("oai", 1000, 500, False),
        ("claude", 1000, 500, False),
        ("oai", 2000, 2500, True),
        ("claude", 2000, 2500, True)
    ])
    def test_large_content_thresholds(self, source, threshold, text_size, expected):
        """Test large content detection with different thresholds."""
        large_text = 'x' * text_size
        message_obj = create_message_obj(source, 'user', large_text)
        exchange = Exchange.create('test', [message_obj])
        
        result = first_user_has_large_content(exchange, min_length=threshold)
        assert result == expected, f"Threshold test failed for {source}"


class TestWikiLinkDetection:
    """Test wiki link detection using consistent patterns."""
    
    @pytest.mark.parametrize("source,text,expected", [
        ("oai", 'See also: [[Machine Learning]] and [[Neural Networks]]', True),
        ("claude", 'See also: [[Machine Learning]] and [[Neural Networks]]', True),
        ("oai", 'Check out [[Python Programming]]', True),
        ("claude", 'Check out [[Python Programming]]', True),
        ("oai", 'No wiki links in this text', False),
        ("claude", 'No wiki links in this text', False),
        ("oai", 'Single bracket [not a wiki link]', False),
        ("claude", 'Single bracket [not a wiki link]', False)
    ])
    def test_has_wiki_links(self, source, text, expected):
        """Test wiki link detection patterns."""
        message_obj = create_message_obj(source, 'assistant', text)
        exchange = Exchange.create('test', [message_obj])
        
        assert has_wiki_links(exchange) == expected


class TestTitleExtraction:
    """Test title extraction using consistent patterns."""
    
    @pytest.mark.parametrize("source,text,expected", [
        ("oai", '# Introduction to Python\n\nPython is...', 'Introduction to Python'),
        ("claude", '# Introduction to Python\n\nPython is...', 'Introduction to Python'),
        ("oai", '## Advanced Topics\n\nThis section covers...', 'Advanced Topics'),
        ("claude", '## Advanced Topics\n\nThis section covers...', 'Advanced Topics'),
        ("oai", '**Machine Learning Basics**\n\nML is...', 'Machine Learning Basics'),
        ("claude", '**Machine Learning Basics**\n\nML is...', 'Machine Learning Basics'),
        ("oai", 'Regular text without title formatting', None),
        ("claude", 'Regular text without title formatting', None)
    ])
    def test_extract_proposed_title(self, source, text, expected):
        """Test title extraction patterns."""
        message_obj = create_message_obj(source, 'assistant', text)
        exchange = Exchange.create('test', [message_obj])
        
        result = extract_proposed_title(exchange)
        assert result == expected


class TestBasicIntegration:
    """Test basic integration using consistent patterns."""
    
    @pytest.mark.parametrize("source,data", [
        ("oai", get_simple_conversation_data()[0]),
        ("claude", get_simple_conversation_data()[1])
    ])
    def test_end_to_end_tagging(self, source, data):
        """Test complete tagging pipeline."""
        tagger = create_default_tagger(source=source)
        result = tagger.tag_conversation(data)
        
        # Basic structure checks
        assert result.exchange_count == 1
        assert result.total_message_count == 2
        
        # Should have some annotations applied
        exchange = result.exchanges[0]
        assert len(exchange.annotations) > 0
        
        # Text extraction should work
        user_text = result.get_all_user_text()
        assistant_text = result.get_all_assistant_text()
        assert 'Hello world' in user_text
        assert 'Hi there!' in assistant_text

    @pytest.mark.parametrize("source", ["oai", "claude"])
    def test_empty_conversation_handling(self, source):
        """Test empty conversation handling."""
        if source == "oai":
            empty_data = {
                'conversation_id': 'empty_oai',
                'title': 'Empty',
                'mapping': {}
            }
        else:
            empty_data = {
                'uuid': 'empty-claude',
                'name': 'Empty',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'account': {'uuid': 'account-uuid'},
                'chat_messages': []
            }
        
        tagger = create_default_tagger(source=source)
        result = tagger.tag_conversation(empty_data)
        
        assert result.exchange_count == 0
        assert result.total_message_count == 0

    @pytest.mark.parametrize("source", ["oai", "claude"])
    def test_custom_rule_addition(self, source):
        """Test adding custom rules works consistently."""
        tagger = create_default_tagger(source=source)
        
        def custom_rule(exchange):
            return {'custom_annotation': True, 'message_count': len(exchange.messages)}
        
        tagger.add_exchange_rule('custom', custom_rule)
        
        # Use message helper for consistency
        message_obj = create_message_obj(source, 'user', 'Test message')
        
        # Create minimal conversation data
        if source == "oai":
            data = {
                'conversation_id': 'custom_test',
                'title': 'Custom Test',
                'mapping': {
                    'msg1': {'message': message_obj.data}
                }
            }
        else:
            data = {
                'uuid': 'custom-test',
                'name': 'Custom Test',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'account': {'uuid': 'account-uuid'},
                'chat_messages': [message_obj.data]
            }
        
        result = tagger.tag_conversation(data)
        exchange = result.exchanges[0]
        
        assert exchange.has_annotation('custom_annotation')
        assert exchange.get_annotation('custom_annotation') == True
        assert exchange.get_annotation('message_count') == 1