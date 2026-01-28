# tests/test_annotators.py
"""Tests for annotation system."""

import pytest
from uuid import uuid4

from llm_archive.extractors import ChatGPTExtractor
from llm_archive.builders import TreeBuilder, ExchangeBuilder
from llm_archive.annotators import (
    Annotator, AnnotationManager,
    WikiLinkAnnotator, CodeBlockAnnotator, LatexAnnotator, ContinuationAnnotator,
)
from llm_archive.annotators.features import ExchangeTypeAnnotator
from llm_archive.models import Annotation, Message, ContentPart


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
    """Tests for creating custom annotators."""
    
    def test_custom_annotator_interface(self, db_session):
        """Test that custom annotators work correctly."""
        
        class TopicAnnotator(Annotator):
            """Custom annotator that tags exchanges with topics."""
            ANNOTATION_TYPE = 'tag'
            ENTITY_TYPE = 'exchange'
            SOURCE = 'custom'
            VERSION = '1.0'
            
            KEYWORDS = {
                'python': ['python', 'def ', 'import '],
                'javascript': ['javascript', 'function', 'const '],
                'database': ['sql', 'database', 'query'],
            }
            
            def compute(self) -> int:
                # In a real implementation, would query exchanges
                # For test, just verify the interface works
                count = 0
                test_id = uuid4()
                
                for topic, keywords in self.KEYWORDS.items():
                    if self.add_annotation(
                        entity_id=test_id,
                        value=topic,
                        key='topic',
                        confidence=0.8,
                        data={'keywords_matched': keywords},
                    ):
                        count += 1
                
                return count
        
        manager = AnnotationManager(db_session)
        manager.register(TopicAnnotator)
        results = manager.run_all()
        
        assert results['TopicAnnotator'] == 3  # 3 topics
        
        annotations = db_session.query(Annotation).filter(
            Annotation.annotation_key == 'topic'
        ).all()
        
        assert len(annotations) == 3
