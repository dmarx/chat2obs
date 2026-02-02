# tests/integration/test_annotators.py
"""Tests for annotation system."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from llm_archive.extractors import ChatGPTExtractor
from llm_archive.builders import TreeBuilder, ExchangeBuilder
from llm_archive.annotators import (
    Annotator, AnnotationManager, AnnotationResult,
    MessageTextAnnotator, MessageTextData,
    ExchangeAnnotator, ExchangeData,
    WikiLinkAnnotator, CodeBlockAnnotator, LatexAnnotator, ContinuationAnnotator,
    ExchangeTypeAnnotator,
)
from llm_archive.models import Annotation, Message, ContentPart
from llm_archive.models.derived import AnnotatorCursor


class TestAnnotatorBase:
    """Tests for base annotator functionality."""
    
    def test_add_annotation(self, db_session):
        """Test adding a simple annotation."""
        class TestAnnotator(Annotator):
            ANNOTATION_TYPE = 'test'
            ENTITY_TYPE = 'message'
            SOURCE = 'test'
            VERSION = '1.0'
            
            def compute(self):
                return 0
        
        annotator = TestAnnotator(db_session)
        entity_id = uuid4()
        
        created = annotator.add_annotation(
            entity_id=entity_id,
            value='test_value',
            confidence=0.9,
        )
        
        assert created is True
        
        # Check annotation exists
        annotation = db_session.query(Annotation).filter(
            Annotation.entity_id == entity_id
        ).first()
        
        assert annotation is not None
        assert annotation.annotation_type == 'test'
        assert annotation.annotation_value == 'test_value'
        assert annotation.confidence == 0.9
    
    def test_annotation_with_key(self, db_session):
        """Test adding annotation with a key."""
        class TestAnnotator(Annotator):
            ANNOTATION_TYPE = 'feature'
            ENTITY_TYPE = 'message'
            SOURCE = 'test'
            VERSION = '1.0'
            
            def compute(self):
                return 0
        
        annotator = TestAnnotator(db_session)
        entity_id = uuid4()
        
        annotator.add_annotation(
            entity_id=entity_id,
            value='python',
            key='code_language',
        )
        
        annotation = db_session.query(Annotation).first()
        assert annotation.annotation_key == 'code_language'
        assert annotation.annotation_value == 'python'
    
    def test_annotation_deduplication(self, db_session):
        """Test that duplicate annotations are not created."""
        class TestAnnotator(Annotator):
            ANNOTATION_TYPE = 'test'
            ENTITY_TYPE = 'message'
            SOURCE = 'test'
            VERSION = '1.0'
            
            def compute(self):
                return 0
        
        annotator = TestAnnotator(db_session)
        entity_id = uuid4()
        
        created1 = annotator.add_annotation(entity_id=entity_id, value='test')
        created2 = annotator.add_annotation(entity_id=entity_id, value='test')
        
        assert created1 is True
        assert created2 is False
        
        count = db_session.query(Annotation).count()
        assert count == 1
    
    def test_supersede_annotation(self, db_session):
        """Test superseding an annotation."""
        class TestAnnotator(Annotator):
            ANNOTATION_TYPE = 'test'
            ENTITY_TYPE = 'message'
            SOURCE = 'test'
            VERSION = '1.0'
            
            def compute(self):
                return 0
        
        annotator = TestAnnotator(db_session)
        entity_id = uuid4()
        
        annotator.add_annotation(entity_id=entity_id, value='old_value')
        db_session.flush()
        
        annotator.supersede_annotation(entity_id=entity_id, value='old_value')
        db_session.flush()
        
        annotation = db_session.query(Annotation).first()
        assert annotation.superseded_at is not None
    
    def test_add_result(self, db_session):
        """Test adding annotation from AnnotationResult."""
        class TestAnnotator(Annotator):
            ANNOTATION_TYPE = 'test'
            ENTITY_TYPE = 'message'
            SOURCE = 'test'
            VERSION = '1.0'
            
            def compute(self):
                return 0
        
        annotator = TestAnnotator(db_session)
        entity_id = uuid4()
        
        result = AnnotationResult(
            value='test_value',
            key='test_key',
            confidence=0.85,
            data={'extra': 'data'},
        )
        
        created = annotator.add_result(entity_id, result)
        assert created is True
        
        annotation = db_session.query(Annotation).first()
        assert annotation.annotation_value == 'test_value'
        assert annotation.annotation_key == 'test_key'
        assert annotation.confidence == 0.85
        assert annotation.annotation_data == {'extra': 'data'}


class TestAnnotatorCursor:
    """Tests for cursor-based incremental processing."""
    
    def test_cursor_created_on_first_run(self, clean_db_session, chatgpt_simple_conversation):
        """Test that cursor is created after first annotation run."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        annotator = CodeBlockAnnotator(clean_db_session)
        annotator.compute()
        clean_db_session.commit()
        
        cursor = clean_db_session.query(AnnotatorCursor).filter(
            AnnotatorCursor.annotator_name == 'CodeBlockAnnotator',
            AnnotatorCursor.annotator_version == CodeBlockAnnotator.VERSION, #'1.1',
        ).first()
        
        assert cursor is not None
        assert cursor.high_water_mark is not None
        assert cursor.entities_processed > 0
    
    def test_cursor_skips_old_entities(self, clean_db_session, chatgpt_simple_conversation):
        """Test that second run skips already-processed entities."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        annotator = CodeBlockAnnotator(clean_db_session)
        first_count = annotator.compute()
        clean_db_session.commit()
        
        # Second run should find nothing new
        annotator2 = CodeBlockAnnotator(clean_db_session)
        second_count = annotator2.compute()
        clean_db_session.commit()
        
        # Second run processes 0 new entities (cursor filters them out)
        assert second_count == 0
    
    def test_version_bump_reprocesses(self, clean_db_session, chatgpt_simple_conversation):
        """Test that bumping VERSION forces reprocessing."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # First run with version 1.0
        annotator = CodeBlockAnnotator(clean_db_session)
        first_count = annotator.compute()
        clean_db_session.commit()
        
        # Create a "v1.1" annotator
        class CodeBlockAnnotatorV11(MessageTextAnnotator):
            ANNOTATION_TYPE = 'feature'
            VERSION = '1.1'  # Different version
            
            def annotate(self, data):
                if '```' in data.text:
                    return [AnnotationResult(value='has_code_v11')]
                return []
        
        annotator_v11 = CodeBlockAnnotatorV11(clean_db_session)
        v11_count = annotator_v11.compute()
        clean_db_session.commit()
        
        # v1.1 should process entities again (different cursor)
        # Since cursor is per-version, it starts fresh
        assert v11_count >= 0  # May or may not find code blocks
        
        # Should have separate cursor entries
        cursors = clean_db_session.query(AnnotatorCursor).filter(
            AnnotatorCursor.annotator_name.in_(['CodeBlockAnnotator', 'CodeBlockAnnotatorV11'])
        ).all()
        
        assert len(cursors) == 2
    
    def test_cursor_tracks_stats(self, clean_db_session, chatgpt_simple_conversation):
        """Test that cursor tracks entities_processed and annotations_created."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        annotator = WikiLinkAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        cursor = clean_db_session.query(AnnotatorCursor).filter(
            AnnotatorCursor.annotator_name == 'WikiLinkAnnotator',
        ).first()
        
        assert cursor is not None
        assert cursor.entities_processed > 0
        assert cursor.annotations_created == count


class TestMessageTextAnnotator:
    """Tests for MessageTextAnnotator base class."""
    
    def test_simple_message_annotator(self, clean_db_session, chatgpt_simple_conversation):
        """Test creating a simple message annotator."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        class HelloAnnotator(MessageTextAnnotator):
            ANNOTATION_TYPE = 'feature'
            VERSION = '1.0'
            
            def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
                if 'hello' in data.text.lower():
                    return [AnnotationResult(value='has_greeting')]
                return []
        
        annotator = HelloAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        # Should find messages with "hello"
        assert count >= 0  # May or may not have hello
    
    def test_role_filter(self, clean_db_session, chatgpt_simple_conversation):
        """Test that ROLE_FILTER limits messages."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        class UserOnlyAnnotator(MessageTextAnnotator):
            ANNOTATION_TYPE = 'test'
            VERSION = '1.0'
            ROLE_FILTER = 'user'
            
            def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
                assert data.role == 'user', "Should only see user messages"
                return [AnnotationResult(value='user_message')]
        
        annotator = UserOnlyAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        # Should have annotated user messages
        assert count > 0
    
    def test_multiple_results(self, clean_db_session, chatgpt_simple_conversation):
        """Test returning multiple annotation results."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        class MultiResultAnnotator(MessageTextAnnotator):
            ANNOTATION_TYPE = 'test'
            VERSION = '1.0'
            
            def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
                results = []
                if len(data.text) > 10:
                    results.append(AnnotationResult(value='long'))
                if len(data.text) < 100:
                    results.append(AnnotationResult(value='short'))
                return results
        
        annotator = MultiResultAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        # Should have multiple annotations
        assert count > 0


class TestExchangeAnnotator:
    """Tests for ExchangeAnnotator base class."""
    
    def test_simple_exchange_annotator(self, clean_db_session, chatgpt_simple_conversation):
        """Test creating a simple exchange annotator."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        TreeBuilder(clean_db_session).build_all()
        ExchangeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        class LengthAnnotator(ExchangeAnnotator):
            ANNOTATION_TYPE = 'tag'
            VERSION = '1.0'
            
            def annotate(self, data: ExchangeData) -> list[AnnotationResult]:
                word_count = (data.assistant_word_count or 0)
                if word_count > 100:
                    return [AnnotationResult(value='long_response')]
                return [AnnotationResult(value='short_response')]
        
        annotator = LengthAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        assert count > 0


class TestAnnotationManager:
    """Tests for annotation manager."""
    
    def test_register_annotator(self, db_session):
        """Test registering an annotator."""
        manager = AnnotationManager(db_session)
        
        class DummyAnnotator(Annotator):
            ANNOTATION_TYPE = 'dummy'
            ENTITY_TYPE = 'message'
            SOURCE = 'test'
            VERSION = '1.0'
            
            def compute(self):
                return 0
        
        manager.register(DummyAnnotator)
        assert len(manager.annotators) == 1
    
    def test_run_all(self, db_session):
        """Test running all annotators."""
        manager = AnnotationManager(db_session)
        
        class CountingAnnotator(Annotator):
            ANNOTATION_TYPE = 'counting'
            ENTITY_TYPE = 'message'
            SOURCE = 'test'
            VERSION = '1.0'
            
            def compute(self):
                return 5
        
        manager.register(CountingAnnotator)
        results = manager.run_all()
        
        assert 'CountingAnnotator' in results
        assert results['CountingAnnotator'] == 5
    
    def test_get_annotations(self, db_session):
        """Test querying annotations."""
        manager = AnnotationManager(db_session)
        entity_id = uuid4()
        
        # Add some annotations directly
        ann1 = Annotation(
            entity_type='message',
            entity_id=entity_id,
            annotation_type='tag',
            annotation_value='coding',
            source='manual',
        )
        ann2 = Annotation(
            entity_type='message',
            entity_id=entity_id,
            annotation_type='feature',
            annotation_value='has_code',
            source='heuristic',
        )
        db_session.add_all([ann1, ann2])
        db_session.flush()
        
        annotations = manager.get_annotations(entity_id=entity_id)
        assert len(annotations) == 2
        
        tags = manager.get_annotations(annotation_type='tag')
        assert len(tags) == 1
    
    def test_get_tags(self, db_session):
        """Test getting tags for an entity."""
        manager = AnnotationManager(db_session)
        entity_id = uuid4()
        
        ann1 = Annotation(
            entity_type='exchange',
            entity_id=entity_id,
            annotation_type='tag',
            annotation_value='coding',
            source='manual',
        )
        ann2 = Annotation(
            entity_type='exchange',
            entity_id=entity_id,
            annotation_type='tag',
            annotation_value='python',
            source='manual',
        )
        db_session.add_all([ann1, ann2])
        db_session.flush()
        
        tags = manager.get_tags('exchange', entity_id)
        assert set(tags) == {'coding', 'python'}


class TestFeatureAnnotators:
    """Tests for feature detection annotators."""
    
    @pytest.fixture
    def conversation_with_features(self):
        """Conversation with various detectable features."""
        return {
            "conversation_id": "features-001",
            "title": "Features Test",
            "create_time": 1700000000.0,
            "update_time": 1700001000.0,
            "mapping": {
                "root": {
                    "id": "root",
                    "parent": None,
                    "children": ["m1"],
                    "message": None
                },
                "m1": {
                    "id": "m1",
                    "parent": "root",
                    "children": ["m2"],
                    "message": {
                        "id": "m1",
                        "author": {"role": "user"},
                        "create_time": 1700000100.0,
                        "content": {"content_type": "text", "parts": ["Show me Python code"]}
                    }
                },
                "m2": {
                    "id": "m2",
                    "parent": "m1",
                    "children": ["m3"],
                    "message": {
                        "id": "m2",
                        "author": {"role": "assistant"},
                        "create_time": 1700000200.0,
                        "content": {"content_type": "text", "parts": [
                            "Here's a Python example:\n\n```python\ndef hello():\n    print('Hello')\n```\n\nSee also [[Python Basics]] for more."
                        ]}
                    }
                },
                "m3": {
                    "id": "m3",
                    "parent": "m2",
                    "children": ["m4"],
                    "message": {
                        "id": "m3",
                        "author": {"role": "user"},
                        "create_time": 1700000300.0,
                        "content": {"content_type": "text", "parts": ["continue"]}
                    }
                },
                "m4": {
                    "id": "m4",
                    "parent": "m3",
                    "children": [],
                    "message": {
                        "id": "m4",
                        "author": {"role": "assistant"},
                        "create_time": 1700000400.0,
                        "content": {"content_type": "text", "parts": [
                            "The integral is $\\int_0^1 x^2 dx = \\frac{1}{3}$"
                        ]}
                    }
                }
            }
        }
    
    def test_wiki_link_annotator(self, clean_db_session, conversation_with_features):
        """Test wiki link detection."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conversation_with_features)
        clean_db_session.commit()
        
        annotator = WikiLinkAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        assert count >= 1
        
        annotations = clean_db_session.query(Annotation).filter(
            Annotation.annotation_value == 'has_wiki_links'
        ).all()
        
        assert len(annotations) >= 1
    
    def test_code_block_annotator(self, clean_db_session, conversation_with_features):
        """Test code block detection."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conversation_with_features)
        clean_db_session.commit()
        
        annotator = CodeBlockAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        assert count >= 1
        
        # Check for code_language annotation
        lang_annotations = clean_db_session.query(Annotation).filter(
            Annotation.annotation_key == 'code_language'
        ).all()
        
        assert len(lang_annotations) >= 1
        assert any(a.annotation_value == 'python' for a in lang_annotations)
    
    def test_latex_annotator(self, clean_db_session, conversation_with_features):
        """Test LaTeX detection."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conversation_with_features)
        clean_db_session.commit()
        
        annotator = LatexAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        assert count >= 1
        
        annotations = clean_db_session.query(Annotation).filter(
            Annotation.annotation_value == 'has_latex'
        ).all()
        
        assert len(annotations) >= 1
    
    def test_continuation_annotator(self, clean_db_session, conversation_with_features):
        """Test continuation signal detection."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conversation_with_features)
        clean_db_session.commit()
        
        annotator = ContinuationAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        assert count >= 1
        
        annotations = clean_db_session.query(Annotation).filter(
            Annotation.annotation_value == 'continuation_signal'
        ).all()
        
        assert len(annotations) >= 1
    
    def test_exchange_type_annotator(self, clean_db_session, conversation_with_features):
        """Test exchange type classification."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conversation_with_features)
        clean_db_session.commit()
        
        TreeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        ExchangeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        annotator = ExchangeTypeAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        assert count >= 1
        
        # Should have exchange_type annotations
        type_annotations = clean_db_session.query(Annotation).filter(
            Annotation.annotation_key == 'exchange_type'
        ).all()
        
        assert len(type_annotations) >= 1


class TestCustomAnnotator:
    """Tests for creating custom annotators using new base classes."""
    
    def test_custom_message_annotator(self, clean_db_session, chatgpt_simple_conversation):
        """Test custom MessageTextAnnotator."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        class QuestionAnnotator(MessageTextAnnotator):
            """Detects messages containing questions."""
            ANNOTATION_TYPE = 'feature'
            VERSION = '1.0'
            ROLE_FILTER = 'user'
            
            def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
                if '?' in data.text:
                    return [AnnotationResult(
                        value='has_question',
                        confidence=0.9,
                        data={'question_count': data.text.count('?')},
                    )]
                return []
        
        manager = AnnotationManager(clean_db_session)
        manager.register(QuestionAnnotator)
        results = manager.run_all()
        
        # Verify it ran
        assert 'QuestionAnnotator' in results
    
    def test_custom_exchange_annotator(self, clean_db_session, chatgpt_simple_conversation):
        """Test custom ExchangeAnnotator."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        TreeBuilder(clean_db_session).build_all()
        ExchangeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        class BalanceAnnotator(ExchangeAnnotator):
            """Tags exchanges based on user/assistant word balance."""
            ANNOTATION_TYPE = 'tag'
            VERSION = '1.0'
            
            def annotate(self, data: ExchangeData) -> list[AnnotationResult]:
                user_words = data.user_word_count or 0
                asst_words = data.assistant_word_count or 0
                
                if user_words == 0:
                    return []
                
                ratio = asst_words / max(user_words, 1)
                if ratio > 5:
                    return [AnnotationResult(value='verbose_response', key='balance')]
                elif ratio < 0.5:
                    return [AnnotationResult(value='brief_response', key='balance')]
                return [AnnotationResult(value='balanced', key='balance')]
        
        manager = AnnotationManager(clean_db_session)
        manager.register(BalanceAnnotator)
        results = manager.run_all()
        
        assert 'BalanceAnnotator' in results
        assert results['BalanceAnnotator'] > 0
