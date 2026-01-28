# tests/unit/test_content_classification.py
"""Unit tests for content part classification logic."""

import pytest

from llm_archive.extractors.chatgpt import ChatGPTExtractor
from llm_archive.extractors.claude import ClaudeExtractor


class TestChatGPTClassifyContentPart:
    """Tests for ChatGPT content part classification."""
    
    @pytest.fixture
    def extractor(self, mock_session):
        """Create extractor with mock session."""
        return ChatGPTExtractor(mock_session)
    
    def test_classify_string_text(self, extractor):
        """Test classifying a plain string as text."""
        result = extractor._classify_content_part("Hello world")
        
        assert result['part_type'] == 'text'
        assert result['text_content'] == "Hello world"
        assert result['source_json'] == {'text': "Hello world"}
    
    def test_classify_dict_text(self, extractor):
        """Test classifying a dict with text."""
        part = {'text': 'Some text content'}
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'text'
        assert result['text_content'] == 'Some text content'
    
    def test_classify_image(self, extractor):
        """Test classifying image content."""
        part = {
            'content_type': 'image/png',
            'asset_pointer': 'file-service://abc123',
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'image'
        assert result['media_type'] == 'image/png'
        assert result['url'] == 'file-service://abc123'
    
    def test_classify_image_with_url(self, extractor):
        """Test classifying image with direct URL."""
        part = {
            'content_type': 'image/jpeg',
            'url': 'https://example.com/image.jpg',
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'image'
        assert result['media_type'] == 'image/jpeg'
        assert result['url'] == 'https://example.com/image.jpg'
    
    def test_classify_audio(self, extractor):
        """Test classifying audio content."""
        part = {
            'content_type': 'audio/mp3',
            'url': 'https://example.com/audio.mp3',
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'audio'
        assert result['media_type'] == 'audio/mp3'
        assert result['url'] == 'https://example.com/audio.mp3'
    
    def test_classify_video(self, extractor):
        """Test classifying video content."""
        part = {
            'content_type': 'video/mp4',
            'asset_pointer': 'file-service://video123',
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'video'
        assert result['media_type'] == 'video/mp4'
        assert result['url'] == 'file-service://video123'
    
    def test_classify_code(self, extractor):
        """Test classifying code content."""
        part = {
            'content_type': 'code',
            'language': 'python',
            'text': 'print("hello")',
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'code'
        assert result['language'] == 'python'
        assert result['text_content'] == 'print("hello")'
    
    def test_classify_code_by_language(self, extractor):
        """Test classifying code by presence of language field."""
        part = {
            'language': 'javascript',
            'code': 'console.log("hi")',
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'code'
        assert result['language'] == 'javascript'
    
    def test_classify_unknown_type(self, extractor):
        """Test classifying unknown content type."""
        part = {'content_type': 'exotic/type', 'data': 'something'}
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'exotic/type'
    
    def test_classify_non_dict(self, extractor):
        """Test classifying non-dict, non-string content."""
        result = extractor._classify_content_part(12345)
        
        assert result['part_type'] == 'unknown'
        assert result['source_json'] == {'raw': '12345'}


class TestClaudeClassifyContentPart:
    """Tests for Claude content part classification."""
    
    @pytest.fixture
    def extractor(self, mock_session):
        """Create extractor with mock session."""
        return ClaudeExtractor(mock_session)
    
    def test_classify_text(self, extractor):
        """Test classifying text content."""
        part = {'type': 'text', 'text': 'Hello from Claude'}
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'text'
        assert result['text_content'] == 'Hello from Claude'
    
    def test_classify_thinking(self, extractor):
        """Test classifying thinking content."""
        part = {'type': 'thinking', 'thinking': 'Let me consider this...'}
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'thinking'
        assert result['text_content'] == 'Let me consider this...'
    
    def test_classify_tool_use(self, extractor):
        """Test classifying tool_use content."""
        part = {
            'type': 'tool_use',
            'name': 'web_search',
            'id': 'tool-abc123',
            'input': {'query': 'climate change'},
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'tool_use'
        assert result['tool_name'] == 'web_search'
        assert result['tool_use_id'] == 'tool-abc123'
        assert result['tool_input'] == {'query': 'climate change'}
        assert result['text_content'] == 'climate change'  # Extracted from input.query
    
    def test_classify_tool_use_text_input(self, extractor):
        """Test classifying tool_use with text input."""
        part = {
            'type': 'tool_use',
            'name': 'code_executor',
            'id': 'tool-xyz',
            'input': {'text': 'print(1+1)'},
        }
        result = extractor._classify_content_part(part)
        
        assert result['tool_name'] == 'code_executor'
        assert result['text_content'] == 'print(1+1)'
    
    def test_classify_tool_result_string(self, extractor):
        """Test classifying tool_result with string content."""
        part = {
            'type': 'tool_result',
            'tool_use_id': 'tool-abc123',
            'content': 'Search results: AI news...',
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'tool_result'
        assert result['tool_use_id'] == 'tool-abc123'
        assert result['text_content'] == 'Search results: AI news...'
    
    def test_classify_tool_result_list(self, extractor):
        """Test classifying tool_result with list content."""
        part = {
            'type': 'tool_result',
            'tool_use_id': 'tool-abc123',
            'content': [
                {'text': 'First result'},
                {'text': 'Second result'},
            ],
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'tool_result'
        assert result['text_content'] == 'First result\nSecond result'
    
    def test_classify_tool_result_mixed_list(self, extractor):
        """Test classifying tool_result with mixed list content."""
        part = {
            'type': 'tool_result',
            'tool_use_id': 'tool-abc123',
            'content': [
                'Plain string',
                {'text': 'Dict with text'},
            ],
        }
        result = extractor._classify_content_part(part)
        
        assert result['text_content'] == 'Plain string\nDict with text'
    
    def test_classify_tool_result_error(self, extractor):
        """Test classifying tool_result with error flag."""
        part = {
            'type': 'tool_result',
            'tool_use_id': 'tool-abc123',
            'is_error': True,
            'content': 'Error: Something went wrong',
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'tool_result'
        assert result['is_error'] is True
    
    def test_classify_image(self, extractor):
        """Test classifying image content."""
        part = {
            'type': 'image',
            'media_type': 'image/png',
            'source': {'type': 'url', 'url': 'https://example.com/img.png'},
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'image'
        assert result['media_type'] == 'image/png'
        assert result['url'] == 'https://example.com/img.png'
    
    def test_classify_image_base64(self, extractor):
        """Test classifying base64 image (no URL)."""
        part = {
            'type': 'image',
            'media_type': 'image/jpeg',
            'source': {'type': 'base64', 'data': 'abc123...'},
        }
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'image'
        assert result['media_type'] == 'image/jpeg'
        assert 'url' not in result or result.get('url') is None
    
    def test_classify_unknown_type(self, extractor):
        """Test classifying unknown content type."""
        part = {'type': 'custom_widget', 'data': {'foo': 'bar'}}
        result = extractor._classify_content_part(part)
        
        assert result['part_type'] == 'custom_widget'
