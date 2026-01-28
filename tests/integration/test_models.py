# tests/integration/test_models.py
"""Integration tests for SQLAlchemy models with database."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from llm_archive.models import (
    Dialogue, Message, ContentPart,
    DialogueTree, MessagePath, LinearSequence,
    Exchange, ExchangeContent, Annotation,
)


class TestRawModels:
    """Tests for raw schema models with database persistence."""
    
    def test_create_dialogue(self, db_session):
        """Test creating and persisting a dialogue."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='test-001',
            title='Test Dialogue',
            created_at=datetime.now(timezone.utc),
            source_json={'test': True},
        )
        db_session.add(dialogue)
        db_session.flush()
        
        assert dialogue.id is not None
        assert dialogue.source == 'chatgpt'
    
    def test_create_message_with_parent(self, db_session):
        """Test creating messages with parent relationship."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='test-002',
            source_json={'conversation_id': 'test-002'},
        )
        db_session.add(dialogue)
        db_session.flush()
        
        msg1 = Message(
            dialogue_id=dialogue.id,
            source_id='msg-001',
            role='user',
            source_json={'id': 'msg-001', 'role': 'user'},
        )
        db_session.add(msg1)
        db_session.flush()
        
        msg2 = Message(
            dialogue_id=dialogue.id,
            source_id='msg-002',
            role='assistant',
            parent_id=msg1.id,
            source_json={'id': 'msg-002', 'role': 'assistant'},
        )
        db_session.add(msg2)
        db_session.flush()
        
        assert msg2.parent_id == msg1.id
    
    def test_create_content_part(self, db_session):
        """Test creating content parts."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='test-003',
            source_json={},
        )
        db_session.add(dialogue)
        db_session.flush()
        
        message = Message(
            dialogue_id=dialogue.id,
            source_id='msg-003',
            role='assistant',
            source_json={'id': 'msg-003'},
        )
        db_session.add(message)
        db_session.flush()
        
        part = ContentPart(
            message_id=message.id,
            sequence=0,
            part_type='text',
            text_content='Hello world',
            source_json={'type': 'text'},
        )
        db_session.add(part)
        db_session.flush()
        
        assert part.id is not None
        assert part.message_id == message.id
    
    def test_dialogue_messages_relationship(self, db_session):
        """Test dialogue to messages relationship."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='test-004',
            source_json={},
        )
        db_session.add(dialogue)
        db_session.flush()
        
        msg1 = Message(
            dialogue_id=dialogue.id,
            source_id='m1',
            role='user',
            source_json={},
        )
        msg2 = Message(
            dialogue_id=dialogue.id,
            source_id='m2',
            role='assistant',
            source_json={},
        )
        db_session.add_all([msg1, msg2])
        db_session.flush()
        
        # Refresh to load relationship
        db_session.refresh(dialogue)
        
        assert len(dialogue.messages) == 2


class TestDerivedModels:
    """Tests for derived schema models with database persistence."""
    
    def test_create_dialogue_tree(self, db_session):
        """Test creating a dialogue tree."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='test-005',
            source_json={},
        )
        db_session.add(dialogue)
        db_session.flush()
        
        tree = DialogueTree(
            dialogue_id=dialogue.id,
            total_nodes=5,
            max_depth=4,
            branch_count=0,
            leaf_count=1,
        )
        db_session.add(tree)
        db_session.flush()
        
        assert tree.dialogue_id == dialogue.id
    
    def test_create_exchange(self, db_session):
        """Test creating an exchange."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='test-006',
            source_json={},
        )
        db_session.add(dialogue)
        db_session.flush()
        
        msg1 = Message(
            dialogue_id=dialogue.id,
            source_id='m1',
            role='user',
            source_json={},
        )
        msg2 = Message(
            dialogue_id=dialogue.id,
            source_id='m2',
            role='assistant',
            source_json={},
        )
        db_session.add_all([msg1, msg2])
        db_session.flush()
        
        exchange = Exchange(
            dialogue_id=dialogue.id,
            first_message_id=msg1.id,
            last_message_id=msg2.id,
            message_count=2,
            user_message_count=1,
            assistant_message_count=1,
        )
        db_session.add(exchange)
        db_session.flush()
        
        assert exchange.id is not None
    
    def test_exchange_content_relationship(self, db_session):
        """Test exchange to content relationship."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='test-007',
            source_json={},
        )
        db_session.add(dialogue)
        db_session.flush()
        
        msg1 = Message(
            dialogue_id=dialogue.id,
            source_id='m1',
            role='user',
            source_json={},
        )
        msg2 = Message(
            dialogue_id=dialogue.id,
            source_id='m2',
            role='assistant',
            source_json={},
        )
        db_session.add_all([msg1, msg2])
        db_session.flush()
        
        exchange = Exchange(
            dialogue_id=dialogue.id,
            first_message_id=msg1.id,
            last_message_id=msg2.id,
            message_count=2,
            user_message_count=1,
            assistant_message_count=1,
        )
        db_session.add(exchange)
        db_session.flush()
        
        content = ExchangeContent(
            exchange_id=exchange.id,
            user_text='Hello',
            assistant_text='Hi there',
            total_word_count=3,
        )
        db_session.add(content)
        db_session.flush()
        
        # Test relationship
        db_session.refresh(exchange)
        assert exchange.content is not None
        assert exchange.content.user_text == 'Hello'
    
    def test_create_annotation(self, db_session):
        """Test creating an annotation."""
        entity_id = uuid4()
        
        annotation = Annotation(
            entity_type='exchange',
            entity_id=entity_id,
            annotation_type='tag',
            annotation_value='coding',
            source='manual',
        )
        db_session.add(annotation)
        db_session.flush()
        
        assert annotation.id is not None
        assert annotation.superseded_at is None
    
    def test_annotation_with_data(self, db_session):
        """Test annotation with JSONB data."""
        entity_id = uuid4()
        
        annotation = Annotation(
            entity_type='message',
            entity_id=entity_id,
            annotation_type='feature',
            annotation_value='has_code_blocks',
            annotation_data={'count': 3, 'languages': ['python', 'sql']},
            source='heuristic',
        )
        db_session.add(annotation)
        db_session.flush()
        
        db_session.refresh(annotation)
        assert annotation.annotation_data['count'] == 3
        assert 'python' in annotation.annotation_data['languages']


class TestCascadeDeletes:
    """Tests for cascade delete behavior."""
    
    def test_delete_dialogue_cascades_to_messages(self, db_session):
        """Test that deleting dialogue deletes messages."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='test-cascade-001',
            source_json={},
        )
        db_session.add(dialogue)
        db_session.flush()
        
        msg = Message(
            dialogue_id=dialogue.id,
            source_id='m1',
            role='user',
            source_json={},
        )
        db_session.add(msg)
        db_session.flush()
        
        dialogue_id = dialogue.id
        
        # Delete dialogue
        db_session.delete(dialogue)
        db_session.flush()
        
        # Message should be gone
        remaining = db_session.query(Message).filter(
            Message.dialogue_id == dialogue_id
        ).count()
        assert remaining == 0
    
    def test_delete_message_cascades_to_content(self, db_session):
        """Test that deleting message deletes content parts."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='test-cascade-002',
            source_json={},
        )
        db_session.add(dialogue)
        db_session.flush()
        
        msg = Message(
            dialogue_id=dialogue.id,
            source_id='m1',
            role='user',
            source_json={},
        )
        db_session.add(msg)
        db_session.flush()
        
        part = ContentPart(
            message_id=msg.id,
            sequence=0,
            part_type='text',
            text_content='Hello',
            source_json={},
        )
        db_session.add(part)
        db_session.flush()
        
        msg_id = msg.id
        
        # Delete message
        db_session.delete(msg)
        db_session.flush()
        
        # Content part should be gone
        remaining = db_session.query(ContentPart).filter(
            ContentPart.message_id == msg_id
        ).count()
        assert remaining == 0
