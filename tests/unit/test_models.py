# tests/unit/test_models.py
"""Unit tests for SQLAlchemy models - no database required."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from llm_archive.models import (
    Dialogue, Message, ContentPart,
    DialogueTree, MessagePath, LinearSequence, SequenceMessage,
    Exchange, ExchangeMessage, SequenceExchange, ExchangeContent,
    Annotation, ContentHash,
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


class TestDerivedModels:
    """Tests for derived schema model instantiation."""
    
    def test_create_dialogue_tree(self):
        """Test creating a DialogueTree."""
        dialogue_id = uuid4()
        tree = DialogueTree(
            dialogue_id=dialogue_id,
            total_nodes=10,
            max_depth=5,
            branch_count=2,
            leaf_count=3,
        )
        
        assert tree.dialogue_id == dialogue_id
        assert tree.total_nodes == 10
        assert tree.max_depth == 5
        assert tree.branch_count == 2
        assert tree.leaf_count == 3
    
    def test_dialogue_tree_boolean_flags(self):
        """Test DialogueTree boolean flags."""
        tree = DialogueTree(
            dialogue_id=uuid4(),
            total_nodes=5,
            max_depth=4,
            branch_count=0,
            leaf_count=1,
            has_regenerations=True,
            has_edits=False,
        )
        
        assert tree.has_regenerations is True
        assert tree.has_edits is False
    
    def test_create_exchange(self):
        """Test creating an Exchange."""
        dialogue_id = uuid4()
        first_msg = uuid4()
        last_msg = uuid4()
        
        exchange = Exchange(
            dialogue_id=dialogue_id,
            first_message_id=first_msg,
            last_message_id=last_msg,
            message_count=3,
            user_message_count=1,
            assistant_message_count=2,
        )
        
        assert exchange.dialogue_id == dialogue_id
        assert exchange.first_message_id == first_msg
        assert exchange.last_message_id == last_msg
        assert exchange.message_count == 3
    
    def test_exchange_continuation_flag(self):
        """Test Exchange continuation flag."""
        exchange = Exchange(
            dialogue_id=uuid4(),
            first_message_id=uuid4(),
            last_message_id=uuid4(),
            message_count=4,
            user_message_count=2,
            assistant_message_count=2,
            is_continuation=True,
            merged_count=2,
        )
        
        assert exchange.is_continuation is True
        assert exchange.merged_count == 2
    
    def test_create_exchange_content(self):
        """Test creating ExchangeContent."""
        exchange_id = uuid4()
        content = ExchangeContent(
            exchange_id=exchange_id,
            user_text='What is Python?',
            assistant_text='Python is a programming language.',
            total_word_count=8,
        )
        
        assert content.exchange_id == exchange_id
        assert content.user_text == 'What is Python?'
        assert content.assistant_text == 'Python is a programming language.'
        assert content.total_word_count == 8


class TestAnnotationModel:
    """Tests for Annotation model instantiation."""
    
    def test_create_tag_annotation(self):
        """Test creating a tag annotation."""
        entity_id = uuid4()
        annotation = Annotation(
            entity_type='exchange',
            entity_id=entity_id,
            annotation_type='tag',
            annotation_value='coding',
            source='manual',
        )
        
        assert annotation.entity_type == 'exchange'
        assert annotation.entity_id == entity_id
        assert annotation.annotation_type == 'tag'
        assert annotation.annotation_value == 'coding'
        assert annotation.source == 'manual'
    
    def test_annotation_with_key(self):
        """Test annotation with key for namespacing."""
        annotation = Annotation(
            entity_type='message',
            entity_id=uuid4(),
            annotation_type='feature',
            annotation_key='code_language',
            annotation_value='python',
            source='heuristic',
        )
        
        assert annotation.annotation_key == 'code_language'
        assert annotation.annotation_value == 'python'
    
    def test_annotation_with_data(self):
        """Test annotation with JSONB data."""
        annotation = Annotation(
            entity_type='exchange',
            entity_id=uuid4(),
            annotation_type='feature',
            annotation_value='has_code',
            annotation_data={'languages': ['python', 'sql'], 'block_count': 3},
            source='heuristic',
        )
        
        assert annotation.annotation_data['languages'] == ['python', 'sql']
        assert annotation.annotation_data['block_count'] == 3
    
    def test_annotation_with_confidence(self):
        """Test annotation with confidence score."""
        annotation = Annotation(
            entity_type='exchange',
            entity_id=uuid4(),
            annotation_type='topic',
            annotation_value='machine_learning',
            confidence=0.85,
            source='llm',
        )
        
        assert annotation.confidence == 0.85


class TestContentHashModel:
    """Tests for ContentHash model instantiation."""
    
    def test_create_message_hash(self):
        """Test creating a message content hash."""
        entity_id = uuid4()
        hash_value = 'a' * 64  # SHA-256 is 64 hex chars
        
        content_hash = ContentHash(
            entity_type='message',
            entity_id=entity_id,
            hash_scope='full',
            normalization='none',
            hash_sha256=hash_value,
        )
        
        assert content_hash.entity_type == 'message'
        assert content_hash.entity_id == entity_id
        assert content_hash.hash_scope == 'full'
        assert content_hash.normalization == 'none'
        assert content_hash.hash_sha256 == hash_value
    
    def test_create_exchange_hash(self):
        """Test creating an exchange content hash."""
        content_hash = ContentHash(
            entity_type='exchange',
            entity_id=uuid4(),
            hash_scope='assistant',
            normalization='normalized',
            hash_sha256='b' * 64,
        )
        
        assert content_hash.entity_type == 'exchange'
        assert content_hash.hash_scope == 'assistant'
        assert content_hash.normalization == 'normalized'


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
    
    def test_exchange_table_name(self):
        """Test Exchange uses derived schema."""
        assert Exchange.__tablename__ == 'exchanges'
        assert Exchange.__table__.schema == 'derived'
    
    def test_annotation_table_name(self):
        """Test Annotation uses derived schema."""
        assert Annotation.__tablename__ == 'annotations'
        assert Annotation.__table__.schema == 'derived'
