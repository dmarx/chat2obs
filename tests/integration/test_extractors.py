# tests/integration/test_extractors.py
"""Tests for conversation extractors."""

import pytest
from uuid import UUID

from llm_archive.extractors import ChatGPTExtractor, ClaudeExtractor
from llm_archive.models import Dialogue, Message, ContentPart


class TestChatGPTExtractor:
    """Tests for ChatGPT extractor."""
    
    def test_extract_simple_conversation(self, db_session, chatgpt_simple_conversation):
        """Test extracting a simple linear conversation."""
        extractor = ChatGPTExtractor(db_session)
        result = extractor.extract_dialogue(chatgpt_simple_conversation)
        
        assert result == 'new'
        
        # Check dialogue was created
        dialogue = db_session.query(Dialogue).filter(
            Dialogue.source_id == "conv-simple-001"
        ).first()
        
        assert dialogue is not None
        assert dialogue.source == 'chatgpt'
        assert dialogue.title == "Simple Test Conversation"
    
    def test_extract_messages(self, db_session, chatgpt_simple_conversation):
        """Test that messages are extracted correctly."""
        extractor = ChatGPTExtractor(db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        
        dialogue = db_session.query(Dialogue).filter(
            Dialogue.source_id == "conv-simple-001"
        ).first()
        
        messages = db_session.query(Message).filter(
            Message.dialogue_id == dialogue.id
        ).all()
        
        # Should have 4 messages (excluding root node which has no message)
        assert len(messages) == 4
        
        # Check roles
        roles = sorted([m.role for m in messages])
        assert roles == ['assistant', 'assistant', 'user', 'user']
    
    def test_extract_content_parts(self, db_session, chatgpt_simple_conversation):
        """Test that content parts are extracted."""
        extractor = ChatGPTExtractor(db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        
        # Get a user message
        message = db_session.query(Message).filter(
            Message.role == 'user'
        ).first()
        
        parts = db_session.query(ContentPart).filter(
            ContentPart.message_id == message.id
        ).all()
        
        assert len(parts) >= 1
        assert parts[0].part_type == 'text'
        assert parts[0].text_content is not None
    
    def test_extract_branched_conversation(self, db_session, chatgpt_branched_conversation):
        """Test extracting a conversation with branches."""
        extractor = ChatGPTExtractor(db_session)
        result = extractor.extract_dialogue(chatgpt_branched_conversation)
        
        assert result == 'new'
        
        dialogue = db_session.query(Dialogue).filter(
            Dialogue.source_id == "conv-branched-001"
        ).first()
        
        messages = db_session.query(Message).filter(
            Message.dialogue_id == dialogue.id
        ).all()
        
        # Should have 5 messages (including both branches)
        assert len(messages) == 5
        
        # Check for branch point (message with multiple children)
        user_msg = db_session.query(Message).filter(
            Message.dialogue_id == dialogue.id,
            Message.role == 'user'
        ).first()
        
        # Count children
        children = db_session.query(Message).filter(
            Message.parent_id == user_msg.id
        ).all()
        
        # First user message should have 2 children (regeneration)
        assert len(children) == 2
    
    def test_extract_code_content(self, db_session, chatgpt_conversation_with_code):
        """Test extracting code execution content with language."""
        extractor = ChatGPTExtractor(db_session)
        extractor.extract_dialogue(chatgpt_conversation_with_code)
        
        dialogue = db_session.query(Dialogue).filter(
            Dialogue.source_id == "conv-code-001"
        ).first()
        
        assert dialogue is not None
        
        # Check for code content part with language
        code_parts = db_session.query(ContentPart).filter(
            ContentPart.part_type == 'code'
        ).all()
        
        assert len(code_parts) >= 1
        
        code_part = code_parts[0]
        assert code_part.language == 'python'
        assert 'fibonacci' in code_part.text_content
    
    def test_extract_image_content(self, db_session, chatgpt_conversation_with_image):
        """Test extracting image content with media type and URL."""
        extractor = ChatGPTExtractor(db_session)
        extractor.extract_dialogue(chatgpt_conversation_with_image)
        
        dialogue = db_session.query(Dialogue).filter(
            Dialogue.source_id == "conv-image-001"
        ).first()
        
        assert dialogue is not None
        
        # Check for image content part
        image_parts = db_session.query(ContentPart).filter(
            ContentPart.part_type == 'image'
        ).all()
        
        assert len(image_parts) >= 1
        
        image_part = image_parts[0]
        assert image_part.media_type == 'image/png'
        assert image_part.url is not None
        assert 'dalle-gen-abc123' in image_part.url or 'example.com' in image_part.url
    
    def test_missing_conversation_id(self, db_session):
        """Test handling of conversation without ID."""
        extractor = ChatGPTExtractor(db_session)
        result = extractor.extract_dialogue({"title": "No ID"})
        
        assert result is None
    
    def test_extract_all(self, db_session, chatgpt_conversations):
        """Test extracting multiple conversations."""
        extractor = ChatGPTExtractor(db_session)
        counts = extractor.extract_all(chatgpt_conversations)
        
        assert counts['dialogues_new'] == 3
        assert counts['failed'] == 0


class TestClaudeExtractor:
    """Tests for Claude extractor."""
    
    def test_extract_simple_conversation(self, db_session, claude_simple_conversation):
        """Test extracting a simple Claude conversation."""
        extractor = ClaudeExtractor(db_session)
        result = extractor.extract_dialogue(claude_simple_conversation)
        
        assert result == 'new'
        
        dialogue = db_session.query(Dialogue).filter(
            Dialogue.source_id == "claude-conv-001"
        ).first()
        
        assert dialogue is not None
        assert dialogue.source == 'claude'
        assert dialogue.title == "Claude Test Conversation"
    
    def test_extract_messages_linear(self, db_session, claude_simple_conversation):
        """Test that Claude messages form a linear chain."""
        extractor = ClaudeExtractor(db_session)
        extractor.extract_dialogue(claude_simple_conversation)
        
        dialogue = db_session.query(Dialogue).filter(
            Dialogue.source_id == "claude-conv-001"
        ).first()
        
        messages = db_session.query(Message).filter(
            Message.dialogue_id == dialogue.id
        ).order_by(Message.created_at).all()
        
        assert len(messages) == 4
        
        # Check linear structure
        for i in range(1, len(messages)):
            assert messages[i].parent_id == messages[i-1].id
    
    def test_role_normalization(self, db_session, claude_simple_conversation):
        """Test that 'human' role is normalized to 'user'."""
        extractor = ClaudeExtractor(db_session)
        extractor.extract_dialogue(claude_simple_conversation)
        
        messages = db_session.query(Message).all()
        roles = set(m.role for m in messages)
        
        assert 'human' not in roles
        assert 'user' in roles
        assert 'assistant' in roles
    
    def test_extract_thinking_blocks(self, db_session, claude_conversation_with_thinking):
        """Test extracting thinking content."""
        extractor = ClaudeExtractor(db_session)
        extractor.extract_dialogue(claude_conversation_with_thinking)
        
        # Check for thinking content part
        thinking_parts = db_session.query(ContentPart).filter(
            ContentPart.part_type == 'thinking'
        ).all()
        
        assert len(thinking_parts) >= 1
        assert thinking_parts[0].text_content is not None
    
    def test_extract_tool_use(self, db_session, claude_conversation_with_tool_use):
        """Test extracting tool use content with all fields."""
        extractor = ClaudeExtractor(db_session)
        extractor.extract_dialogue(claude_conversation_with_tool_use)
        
        tool_use_parts = db_session.query(ContentPart).filter(
            ContentPart.part_type == 'tool_use'
        ).all()
        
        assert len(tool_use_parts) >= 1
        
        # Verify tool use fields are extracted
        tool_use = tool_use_parts[0]
        assert tool_use.tool_name == 'web_search'
        assert tool_use.tool_use_id == 'tool-001'
        assert tool_use.tool_input == {'query': 'recent AI news 2024'}
        assert tool_use.text_content == 'recent AI news 2024'  # Extracted from input.query
    
    def test_extract_tool_result(self, db_session, claude_conversation_with_tool_use):
        """Test extracting tool result content with linked tool_use_id."""
        extractor = ClaudeExtractor(db_session)
        extractor.extract_dialogue(claude_conversation_with_tool_use)
        
        tool_result_parts = db_session.query(ContentPart).filter(
            ContentPart.part_type == 'tool_result'
        ).all()
        
        assert len(tool_result_parts) >= 1
        
        # Verify tool result fields
        tool_result = tool_result_parts[0]
        assert tool_result.tool_use_id == 'tool-001'  # Links back to tool_use
        assert tool_result.text_content == 'AI advances in 2024 include...'
    
    def test_missing_uuid(self, db_session):
        """Test handling of conversation without UUID."""
        extractor = ClaudeExtractor(db_session)
        result = extractor.extract_dialogue({"name": "No UUID"})
        
        assert result is None
    
    def test_extract_all(self, db_session, claude_conversations):
        """Test extracting multiple Claude conversations."""
        extractor = ClaudeExtractor(db_session)
        counts = extractor.extract_all(claude_conversations)
        
        assert counts['dialogues_new'] == 3
        assert counts['failed'] == 0


class TestExtractorTimestamps:
    """Tests for timestamp parsing."""
    
    def test_chatgpt_epoch_timestamps(self, db_session, chatgpt_simple_conversation):
        """Test parsing ChatGPT epoch timestamps."""
        extractor = ChatGPTExtractor(db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        
        dialogue = db_session.query(Dialogue).first()
        
        assert dialogue.created_at is not None
        assert dialogue.updated_at is not None
        assert dialogue.created_at.tzinfo is not None  # Timezone aware
    
    def test_claude_iso_timestamps(self, db_session, claude_simple_conversation):
        """Test parsing Claude ISO timestamps."""
        extractor = ClaudeExtractor(db_session)
        extractor.extract_dialogue(claude_simple_conversation)
        
        dialogue = db_session.query(Dialogue).first()
        
        assert dialogue.created_at is not None
        assert dialogue.updated_at is not None
        assert dialogue.created_at.tzinfo is not None  # Timezone aware
