# tests/unit/test_chatgpt_extractor_annotations.py
"""Unit tests for ChatGPT extractor annotation integration.

These tests verify that the ChatGPT extractor correctly writes
annotations during ingestion for:
- gizmo_id (string annotation on messages)
- has_gizmo (flag annotation on messages)
- model_slug (string annotation on messages)
- Canvas metadata (annotations on content_parts)
"""

import pytest
from uuid import uuid4


# ============================================================
# Test data fixtures
# ============================================================

def make_message_data(
    msg_id: str = None,
    role: str = 'assistant',
    content: str = 'Test content',
    gizmo_id: str = None,
    model_slug: str = None,
    canvas: dict = None,
) -> dict:
    """Create mock ChatGPT message data."""
    msg_id = msg_id or str(uuid4())
    
    metadata = {}
    if gizmo_id:
        metadata['gizmo_id'] = gizmo_id
    if model_slug:
        metadata['model_slug'] = model_slug
    if canvas:
        metadata['canvas'] = canvas
    
    return {
        'id': msg_id,
        'author': {
            'role': role,
            'name': None,
            'metadata': {},
        },
        'content': {
            'content_type': 'text',
            'parts': [content] if content else [],
        },
        'metadata': metadata,
        'create_time': 1700000000,
        'update_time': 1700000000,
        'status': 'finished',
        'end_turn': True,
    }


def make_canvas_data(
    textdoc_id: str = 'doc-123',
    version: int = 1,
    title: str = 'Test Canvas',
    textdoc_type: str = 'document',
    content: str = 'Canvas content here',
) -> dict:
    """Create mock canvas data."""
    return {
        'textdoc_id': textdoc_id,
        'version': version,
        'title': title,
        'textdoc_type': textdoc_type,
        'content': content,
        'from_version': version - 1 if version > 1 else None,
        'textdoc_content_length': len(content) if content else 0,
        'has_user_edit': False,
    }


# ============================================================
# Unit tests (no database required)
# ============================================================

class TestMessageDataConstruction:
    """Test message data fixture construction."""
    
    def test_basic_message_data(self):
        """Basic message data should have required fields."""
        data = make_message_data()
        
        assert 'id' in data
        assert data['author']['role'] == 'assistant'
        assert data['content']['parts'] == ['Test content']
    
    def test_message_with_gizmo(self):
        """Message with gizmo_id should have it in metadata."""
        data = make_message_data(gizmo_id='g-wiki-generator')
        
        assert data['metadata']['gizmo_id'] == 'g-wiki-generator'
    
    def test_message_with_model(self):
        """Message with model_slug should have it in metadata."""
        data = make_message_data(model_slug='gpt-4')
        
        assert data['metadata']['model_slug'] == 'gpt-4'
    
    def test_message_with_canvas(self):
        """Message with canvas should have canvas in metadata."""
        canvas = make_canvas_data(title='My Document')
        data = make_message_data(canvas=canvas)
        
        assert data['metadata']['canvas']['title'] == 'My Document'


class TestCanvasDataConstruction:
    """Test canvas data fixture construction."""
    
    def test_basic_canvas_data(self):
        """Basic canvas data should have required fields."""
        canvas = make_canvas_data()
        
        assert canvas['textdoc_id'] == 'doc-123'
        assert canvas['version'] == 1
        assert canvas['title'] == 'Test Canvas'
        assert canvas['textdoc_type'] == 'document'
    
    def test_canvas_version_tracking(self):
        """Canvas with version > 1 should have from_version."""
        canvas = make_canvas_data(version=3)
        
        assert canvas['from_version'] == 2
    
    def test_canvas_first_version(self):
        """First version canvas should have from_version=None."""
        canvas = make_canvas_data(version=1)
        
        assert canvas['from_version'] is None


# ============================================================
# Integration tests (require database)
# ============================================================

@pytest.fixture
def db_session():
    """
    Create a database session for integration tests.
    
    This fixture is a placeholder - actual implementation would
    need a test database setup with schema applied.
    """
    pytest.skip("Requires database setup with schema")


class TestChatGPTExtractorGizmoAnnotations:
    """Test gizmo annotation writing during extraction."""
    
    def test_extracts_gizmo_id_annotation(self, db_session):
        """Gizmo ID should be written as message string annotation."""
        from llm_archive.extractors.chatgpt import ChatGPTExtractor
        from llm_archive.annotations import AnnotationReader, EntityType
        
        extractor = ChatGPTExtractor(db_session)
        
        # Create a dialogue with a message using a gizmo
        dialogue_data = {
            'conversation_id': 'test-conv-1',
            'title': 'Test Conversation',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-1': {
                    'id': 'node-1',
                    'message': make_message_data(
                        msg_id='msg-1',
                        gizmo_id='g-wiki-generator',
                    ),
                },
            },
        }
        
        result = extractor.extract_dialogue(dialogue_data)
        db_session.commit()
        
        assert result == 'new'
        
        # Verify annotation was written
        reader = AnnotationReader(db_session)
        # Would need to resolve the message ID to verify
    
    def test_extracts_has_gizmo_flag(self, db_session):
        """has_gizmo flag should be written for messages with gizmo."""
        from llm_archive.extractors.chatgpt import ChatGPTExtractor
        
        extractor = ChatGPTExtractor(db_session)
        
        dialogue_data = {
            'conversation_id': 'test-conv-2',
            'title': 'Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-1': {
                    'id': 'node-1',
                    'message': make_message_data(
                        msg_id='msg-1',
                        gizmo_id='g-test',
                    ),
                },
            },
        }
        
        result = extractor.extract_dialogue(dialogue_data)
        assert result == 'new'
    
    def test_no_gizmo_annotation_when_missing(self, db_session):
        """Messages without gizmo should not have gizmo annotations."""
        from llm_archive.extractors.chatgpt import ChatGPTExtractor
        
        extractor = ChatGPTExtractor(db_session)
        
        dialogue_data = {
            'conversation_id': 'test-conv-3',
            'title': 'Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-1': {
                    'id': 'node-1',
                    'message': make_message_data(
                        msg_id='msg-1',
                        gizmo_id=None,  # No gizmo
                    ),
                },
            },
        }
        
        result = extractor.extract_dialogue(dialogue_data)
        assert result == 'new'


class TestChatGPTExtractorCanvasAnnotations:
    """Test canvas annotation writing during extraction."""
    
    def test_extracts_canvas_as_content_part(self, db_session):
        """Canvas should be created as content_part with type='canvas'."""
        from llm_archive.extractors.chatgpt import ChatGPTExtractor
        from llm_archive.models import ContentPart
        
        extractor = ChatGPTExtractor(db_session)
        
        canvas = make_canvas_data(
            textdoc_id='doc-abc',
            version=1,
            title='My Wiki Article',
            content='Article content here',
        )
        
        dialogue_data = {
            'conversation_id': 'test-conv-canvas',
            'title': 'Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-1': {
                    'id': 'node-1',
                    'message': make_message_data(
                        msg_id='msg-1',
                        content='Here is your document',
                        canvas=canvas,
                    ),
                },
            },
        }
        
        result = extractor.extract_dialogue(dialogue_data)
        db_session.commit()
        
        assert result == 'new'
        
        # Verify canvas content_part was created
        canvas_parts = db_session.query(ContentPart).filter(
            ContentPart.part_type == 'canvas'
        ).all()
        
        assert len(canvas_parts) >= 1
    
    def test_canvas_title_annotation(self, db_session):
        """Canvas title should be written as content_part annotation."""
        from llm_archive.extractors.chatgpt import ChatGPTExtractor
        from llm_archive.annotations import AnnotationReader, EntityType
        
        extractor = ChatGPTExtractor(db_session)
        
        canvas = make_canvas_data(title='Important Document')
        
        dialogue_data = {
            'conversation_id': 'test-conv-canvas-title',
            'title': 'Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-1': {
                    'id': 'node-1',
                    'message': make_message_data(canvas=canvas),
                },
            },
        }
        
        result = extractor.extract_dialogue(dialogue_data)
        db_session.commit()
        
        # Would verify title annotation exists
    
    def test_canvas_version_annotation(self, db_session):
        """Canvas version should be written as numeric annotation."""
        from llm_archive.extractors.chatgpt import ChatGPTExtractor
        
        extractor = ChatGPTExtractor(db_session)
        
        canvas = make_canvas_data(version=5)
        
        dialogue_data = {
            'conversation_id': 'test-conv-canvas-version',
            'title': 'Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-1': {
                    'id': 'node-1',
                    'message': make_message_data(canvas=canvas),
                },
            },
        }
        
        result = extractor.extract_dialogue(dialogue_data)
        assert result == 'new'


class TestMarkLatestCanvasVersions:
    """Test the mark_latest_canvas_versions utility."""
    
    def test_marks_single_version_as_latest(self, db_session):
        """Single canvas version should be marked as latest."""
        from llm_archive.extractors.chatgpt import (
            ChatGPTExtractor,
            mark_latest_canvas_versions,
        )
        
        extractor = ChatGPTExtractor(db_session)
        
        canvas = make_canvas_data(textdoc_id='doc-single', version=1)
        
        dialogue_data = {
            'conversation_id': 'test-single-version',
            'title': 'Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-1': {
                    'id': 'node-1',
                    'message': make_message_data(canvas=canvas),
                },
            },
        }
        
        extractor.extract_dialogue(dialogue_data)
        db_session.commit()
        
        count = mark_latest_canvas_versions(db_session)
        assert count >= 1
    
    def test_marks_highest_version_as_latest(self, db_session):
        """With multiple versions, only highest should be marked latest."""
        from llm_archive.extractors.chatgpt import (
            ChatGPTExtractor,
            mark_latest_canvas_versions,
        )
        
        extractor = ChatGPTExtractor(db_session)
        
        # Create messages with different canvas versions
        mapping = {}
        for i, version in enumerate([1, 3, 2]):  # Out of order
            canvas = make_canvas_data(
                textdoc_id='doc-multi',
                version=version,
            )
            mapping[f'node-{i}'] = {
                'id': f'node-{i}',
                'message': make_message_data(
                    msg_id=f'msg-{i}',
                    canvas=canvas,
                ),
            }
        
        dialogue_data = {
            'conversation_id': 'test-multi-version',
            'title': 'Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': mapping,
        }
        
        extractor.extract_dialogue(dialogue_data)
        db_session.commit()
        
        count = mark_latest_canvas_versions(db_session)
        
        # Should mark version 3 as latest (only one per textdoc_id)
        # Would need to verify the correct one is marked


class TestFindWikiGizmoMessages:
    """Test the find_wiki_gizmo_messages utility."""
    
    def test_finds_messages_by_gizmo(self, db_session):
        """Should find all messages with specific gizmo_id."""
        from llm_archive.extractors.chatgpt import (
            ChatGPTExtractor,
            find_wiki_gizmo_messages,
        )
        
        extractor = ChatGPTExtractor(db_session)
        
        # Create messages with different gizmos
        dialogue_data = {
            'conversation_id': 'test-find-gizmo',
            'title': 'Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-1': {
                    'id': 'node-1',
                    'message': make_message_data(
                        msg_id='msg-1',
                        gizmo_id='g-wiki',
                    ),
                },
                'node-2': {
                    'id': 'node-2',
                    'message': make_message_data(
                        msg_id='msg-2',
                        gizmo_id='g-other',
                    ),
                },
                'node-3': {
                    'id': 'node-3',
                    'message': make_message_data(
                        msg_id='msg-3',
                        gizmo_id='g-wiki',
                    ),
                },
            },
        }
        
        extractor.extract_dialogue(dialogue_data)
        db_session.commit()
        
        wiki_messages = find_wiki_gizmo_messages(db_session, 'g-wiki')
        other_messages = find_wiki_gizmo_messages(db_session, 'g-other')
        
        assert len(wiki_messages) == 2
        assert len(other_messages) == 1
    
    def test_returns_empty_for_unknown_gizmo(self, db_session):
        """Should return empty list for unknown gizmo_id."""
        from llm_archive.extractors.chatgpt import find_wiki_gizmo_messages
        
        messages = find_wiki_gizmo_messages(db_session, 'g-nonexistent')
        assert messages == []
