# tests/unit/test_models.py
"""Unit tests for SQLAlchemy models - no database required."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from llm_archive.models import (
    Dialogue,
    Message,
    ContentPart,
)


class TestDialogueModel:
    """Tests for Dialogue model instantiation."""
    
    def test_create_dialogue_instance(self):
        """Test creating a Dialogue instance."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='conv-001',
            title='Test Conversation',
            source_json={'test': True},
        )
        
        assert dialogue.source == 'chatgpt'
        assert dialogue.source_id == 'conv-001'
        assert dialogue.title == 'Test Conversation'
        assert dialogue.source_json == {'test': True}
    
    def test_dialogue_with_timestamps(self):
        """Test Dialogue with timestamp fields."""
        now = datetime.now(timezone.utc)
        dialogue = Dialogue(
            source='claude',
            source_id='conv-002',
            created_at=now,
            updated_at=now,
            source_json={},
        )
        
        assert dialogue.created_at == now
        assert dialogue.updated_at == now
    
    def test_dialogue_minimal_fields(self):
        """Test Dialogue with only required fields."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='conv-003',
            source_json={},
        )
        
        assert dialogue.source == 'chatgpt'
        assert dialogue.source_id == 'conv-003'
        assert dialogue.title is None
        assert dialogue.created_at is None


class TestMessageModel:
    """Tests for Message model instantiation."""
    
    def test_create_message_instance(self):
        """Test creating a Message instance."""
        dialogue_id = uuid4()
        message = Message(
            dialogue_id=dialogue_id,
            source_id='msg-001',
            role='user',
            source_json={'content': 'Hello'},
        )
        
        assert message.dialogue_id == dialogue_id
        assert message.source_id == 'msg-001'
        assert message.role == 'user'
        assert message.source_json == {'content': 'Hello'}
    
    def test_message_with_parent(self):
        """Test Message with parent reference."""
        dialogue_id = uuid4()
        parent_id = uuid4()
        
        message = Message(
            dialogue_id=dialogue_id,
            source_id='msg-002',
            role='assistant',
            parent_id=parent_id,
            source_json={},
        )
        
        assert message.parent_id == parent_id
    
    def test_message_with_author(self):
        """Test Message with author fields."""
        message = Message(
            dialogue_id=uuid4(),
            source_id='msg-003',
            role='user',
            author_id='user-123',
            author_name='John Doe',
            source_json={},
        )
        
        assert message.author_id == 'user-123'
        assert message.author_name == 'John Doe'
    
    def test_message_with_content_hash(self):
        """Test Message with content hash for change detection."""
        message = Message(
            dialogue_id=uuid4(),
            source_id='msg-004',
            role='user',
            content_hash='a' * 64,  # SHA-256 hash
            source_json={},
        )
        
        assert message.content_hash == 'a' * 64
    
    def test_message_with_deleted_at(self):
        """Test Message with soft delete timestamp."""
        now = datetime.now(timezone.utc)
        message = Message(
            dialogue_id=uuid4(),
            source_id='msg-005',
            role='user',
            deleted_at=now,
            source_json={},
        )
        
        assert message.deleted_at == now
    
    def test_message_not_deleted_by_default(self):
        """Test that deleted_at is None by default."""
        message = Message(
            dialogue_id=uuid4(),
            source_id='msg-006',
            role='user',
            source_json={},
        )
        
        assert message.deleted_at is None


class TestContentPartModel:
    """Tests for ContentPart model instantiation."""
    
    def test_create_text_content_part(self):
        """Test creating a text ContentPart."""
        message_id = uuid4()
        part = ContentPart(
            message_id=message_id,
            sequence=0,
            part_type='text',
            text_content='Hello, world!',
            source_json={'type': 'text'},
        )
        
        assert part.message_id == message_id
        assert part.sequence == 0
        assert part.part_type == 'text'
        assert part.text_content == 'Hello, world!'
    
    def test_create_code_content_part(self):
        """Test creating a code ContentPart with language."""
        part = ContentPart(
            message_id=uuid4(),
            sequence=1,
            part_type='code',
            text_content='print("hello")',
            language='python',
            source_json={'type': 'code', 'language': 'python'},
        )
        
        assert part.part_type == 'code'
        assert part.language == 'python'
        assert part.text_content == 'print("hello")'
    
    def test_create_image_content_part(self):
        """Test creating an image ContentPart with media type and URL."""
        part = ContentPart(
            message_id=uuid4(),
            sequence=0,
            part_type='image',
            media_type='image/png',
            url='https://example.com/image.png',
            source_json={'type': 'image'},
        )
        
        assert part.part_type == 'image'
        assert part.media_type == 'image/png'
        assert part.url == 'https://example.com/image.png'
    
    def test_create_tool_use_content_part(self):
        """Test creating a tool_use ContentPart."""
        part = ContentPart(
            message_id=uuid4(),
            sequence=0,
            part_type='tool_use',
            tool_name='web_search',
            tool_use_id='tool-123',
            tool_input={'query': 'test search'},
            source_json={'type': 'tool_use'},
        )
        
        assert part.part_type == 'tool_use'
        assert part.tool_name == 'web_search'
        assert part.tool_use_id == 'tool-123'
        assert part.tool_input == {'query': 'test search'}
    
    def test_create_tool_result_content_part(self):
        """Test creating a tool_result ContentPart."""
        part = ContentPart(
            message_id=uuid4(),
            sequence=1,
            part_type='tool_result',
            tool_use_id='tool-123',
            text_content='Search results: ...',
            is_error=False,
            source_json={'type': 'tool_result'},
        )
        
        assert part.part_type == 'tool_result'
        assert part.tool_use_id == 'tool-123'
        assert part.is_error is False


class TestModelTableNames:
    """Tests for model table name configuration."""
    
    def test_dialogue_table_name(self):
        """Test Dialogue uses raw schema."""
        assert Dialogue.__tablename__ == 'dialogues'
        assert Dialogue.__table__.schema == 'raw'
    
    def test_message_table_name(self):
        """Test Message uses raw schema."""
        assert Message.__tablename__ == 'messages'
        assert Message.__table__.schema == 'raw'
    
    def test_content_part_table_name(self):
        """Test ContentPart uses raw schema."""
        assert ContentPart.__tablename__ == 'content_parts'
        assert ContentPart.__table__.schema == 'raw'
    
