# tests/integration/test_annotations.py
"""Integration tests for typed annotation system."""

import pytest
from uuid import uuid4

from llm_archive.annotations import (
    AnnotationWriter,
    AnnotationReader,
    EntityType,
    ValueType,
    AnnotationResult,
)
from llm_archive.extractors.chatgpt import ChatGPTExtractor
from llm_archive.builders.prompt_response import PromptResponseBuilder
from llm_archive.annotators.prompt_response import (
    WikiCandidateAnnotator,
    NaiveTitleAnnotator,
)
from llm_archive.models import Message, PromptResponse


class TestAnnotationWriterIntegration:
    """Integration tests for AnnotationWriter."""
    
    def test_write_flag_creates_record(self, clean_db_session, chatgpt_simple_conversation):
        """Writing a flag creates a record in flag table."""
        # Get a real message ID
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        message = clean_db_session.query(Message).first()
        
        writer = AnnotationWriter(clean_db_session)
        result = writer.write_flag(
            entity_type=EntityType.MESSAGE,
            entity_id=message.id,
            key='test_flag',
            source='test',
        )
        clean_db_session.commit()
        
        assert result is True
        
        # Verify record exists
        reader = AnnotationReader(clean_db_session)
        assert reader.has_flag(EntityType.MESSAGE, message.id, 'test_flag')
    
    def test_write_string_creates_record(self, clean_db_session, chatgpt_simple_conversation):
        """Writing a string creates a record in string table."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        message = clean_db_session.query(Message).first()
        
        writer = AnnotationWriter(clean_db_session)
        result = writer.write_string(
            entity_type=EntityType.MESSAGE,
            entity_id=message.id,
            key='category',
            value='greeting',
            source='test',
        )
        clean_db_session.commit()
        
        assert result is True
        
        reader = AnnotationReader(clean_db_session)
        values = reader.get_string(EntityType.MESSAGE, message.id, 'category')
        assert 'greeting' in values
    
    def test_write_numeric_creates_record(self, clean_db_session, chatgpt_simple_conversation):
        """Writing a numeric creates a record in numeric table."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        message = clean_db_session.query(Message).first()
        
        writer = AnnotationWriter(clean_db_session)
        result = writer.write_numeric(
            entity_type=EntityType.MESSAGE,
            entity_id=message.id,
            key='word_count',
            value=42,
            source='test',
        )
        clean_db_session.commit()
        
        assert result is True
        
        reader = AnnotationReader(clean_db_session)
        values = reader.get_numeric(EntityType.MESSAGE, message.id, 'word_count')
        assert 42 in values
    
    def test_write_json_creates_record(self, clean_db_session, chatgpt_simple_conversation):
        """Writing JSON creates a record in json table."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        message = clean_db_session.query(Message).first()
        
        writer = AnnotationWriter(clean_db_session)
        result = writer.write_json(
            entity_type=EntityType.MESSAGE,
            entity_id=message.id,
            key='metadata',
            value={'tags': ['test', 'example'], 'score': 0.95},
            source='test',
        )
        clean_db_session.commit()
        
        assert result is True
        
        reader = AnnotationReader(clean_db_session)
        value = reader.get_json(EntityType.MESSAGE, message.id, 'metadata')
        assert value == {'tags': ['test', 'example'], 'score': 0.95}
    
    def test_write_duplicate_flag_returns_false(self, clean_db_session, chatgpt_simple_conversation):
        """Writing duplicate flag returns False (no new record)."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        message = clean_db_session.query(Message).first()
        
        writer = AnnotationWriter(clean_db_session)
        
        # First write succeeds
        result1 = writer.write_flag(
            entity_type=EntityType.MESSAGE,
            entity_id=message.id,
            key='test_flag',
            source='test',
        )
        clean_db_session.commit()
        assert result1 is True
        
        # Duplicate returns False
        result2 = writer.write_flag(
            entity_type=EntityType.MESSAGE,
            entity_id=message.id,
            key='test_flag',
            source='test',
        )
        assert result2 is False
    
    def test_write_multi_value_string(self, clean_db_session, chatgpt_simple_conversation):
        """Can write multiple values for same string key."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        message = clean_db_session.query(Message).first()
        
        writer = AnnotationWriter(clean_db_session)
        writer.write_string(
            entity_type=EntityType.MESSAGE,
            entity_id=message.id,
            key='tag',
            value='coding',
            source='test',
        )
        writer.write_string(
            entity_type=EntityType.MESSAGE,
            entity_id=message.id,
            key='tag',
            value='python',
            source='test',
        )
        clean_db_session.commit()
        
        reader = AnnotationReader(clean_db_session)
        values = reader.get_string(EntityType.MESSAGE, message.id, 'tag')
        assert set(values) == {'coding', 'python'}
    
    def test_write_from_annotation_result(self, clean_db_session, chatgpt_simple_conversation):
        """Can write from AnnotationResult object."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        message = clean_db_session.query(Message).first()
        
        result = AnnotationResult(
            key='exchange_type',
            value='wiki_article',
            value_type=ValueType.STRING,
            confidence=0.9,
            reason='wiki_links_detected',
        )
        
        writer = AnnotationWriter(clean_db_session)
        written = writer.write(EntityType.MESSAGE, message.id, result)
        clean_db_session.commit()
        
        assert written is True
        
        reader = AnnotationReader(clean_db_session)
        values = reader.get_string(EntityType.MESSAGE, message.id, 'exchange_type')
        assert 'wiki_article' in values


class TestAnnotationReaderIntegration:
    """Integration tests for AnnotationReader."""
    
    def test_find_entities_with_flag(self, clean_db_session, chatgpt_simple_conversation):
        """Can find all entities with a specific flag."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        messages = clean_db_session.query(Message).all()
        assert len(messages) >= 2
        
        writer = AnnotationWriter(clean_db_session)
        
        # Flag first two messages with 'has_code'
        writer.write_flag(EntityType.MESSAGE, messages[0].id, 'has_code', source='test')
        writer.write_flag(EntityType.MESSAGE, messages[1].id, 'has_code', source='test')
        
        # Flag third message with something else (if exists)
        if len(messages) > 2:
            writer.write_flag(EntityType.MESSAGE, messages[2].id, 'has_attachment', source='test')
        
        clean_db_session.commit()
        
        reader = AnnotationReader(clean_db_session)
        results = reader.find_entities_with_flag(EntityType.MESSAGE, 'has_code')
        
        assert messages[0].id in results
        assert messages[1].id in results
        if len(messages) > 2:
            assert messages[2].id not in results
    
    def test_find_entities_with_string_value(self, clean_db_session, chatgpt_simple_conversation):
        """Can find entities with specific string value."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        messages = clean_db_session.query(Message).all()
        
        writer = AnnotationWriter(clean_db_session)
        writer.write_string(EntityType.MESSAGE, messages[0].id, 'topic', 'coding', source='test')
        writer.write_string(EntityType.MESSAGE, messages[1].id, 'topic', 'general', source='test')
        clean_db_session.commit()
        
        reader = AnnotationReader(clean_db_session)
        
        # Find by specific value
        coding_results = reader.find_entities_with_string(EntityType.MESSAGE, 'topic', 'coding')
        assert messages[0].id in coding_results
        assert messages[1].id not in coding_results
        
        # Find by key only (any value)
        all_results = reader.find_entities_with_string(EntityType.MESSAGE, 'topic', None)
        assert messages[0].id in all_results
        assert messages[1].id in all_results
    
    def test_get_all_keys(self, clean_db_session, chatgpt_simple_conversation):
        """Can get all annotations for an entity."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        message = clean_db_session.query(Message).first()
        
        writer = AnnotationWriter(clean_db_session)
        writer.write_flag(EntityType.MESSAGE, message.id, 'has_code', source='test')
        writer.write_string(EntityType.MESSAGE, message.id, 'language', 'python', source='test')
        writer.write_numeric(EntityType.MESSAGE, message.id, 'line_count', 50, source='test')
        clean_db_session.commit()
        
        reader = AnnotationReader(clean_db_session)
        all_keys = reader.get_all_keys(EntityType.MESSAGE, message.id)
        
        assert 'has_code' in all_keys
        assert 'language' in all_keys
        assert 'line_count' in all_keys


class TestPromptResponseAnnotatorIntegration:
    """Integration tests for prompt-response annotators."""
    
    @pytest.fixture
    def wiki_conversation(self):
        """Conversation with wiki-style content."""
        return {
            'conversation_id': 'conv-wiki',
            'title': 'Wiki Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-user': {
                    'id': 'node-user',
                    'message': {
                        'id': 'msg-user',
                        'author': {'role': 'user'},
                        'content': {'parts': ['Write about cats']},
                        'create_time': 1700000000,
                    },
                    'parent': None,
                },
                'node-asst': {
                    'id': 'node-asst',
                    'message': {
                        'id': 'msg-asst',
                        'author': {'role': 'assistant'},
                        'content': {'parts': [
                            '# The Domestic Cat\n\n'
                            '[[Cats]] are [[mammals]] that belong to the family [[Felidae]]. '
                            'They are known for their [[hunting]] abilities.'
                        ]},
                        'create_time': 1700000001,
                    },
                    'parent': 'node-user',
                },
            },
        }
    
    def test_wiki_candidate_annotator_end_to_end(self, clean_db_session, wiki_conversation):
        """Test WikiCandidateAnnotator with real database."""
        # Import and build
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(wiki_conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        builder.build_all()
        clean_db_session.commit()
        
        # Run annotator
        annotator = WikiCandidateAnnotator(clean_db_session)
        count = annotator.compute()
        clean_db_session.commit()
        
        assert count > 0
        
        # Verify annotations exist
        reader = AnnotationReader(clean_db_session)
        pr = clean_db_session.query(PromptResponse).first()
        
        values = reader.get_string(EntityType.PROMPT_RESPONSE, pr.id, 'exchange_type')
        assert 'wiki_article' in values
        
        counts = reader.get_numeric(EntityType.PROMPT_RESPONSE, pr.id, 'wiki_link_count')
        assert len(counts) > 0
        assert counts[0] >= 4  # At least 4 wiki links in our test data
    
    def test_naive_title_annotator_end_to_end(self, clean_db_session, wiki_conversation):
        """Test NaiveTitleAnnotator with real database."""
        # Import and build
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(wiki_conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        builder.build_all()
        clean_db_session.commit()
        
        # Run wiki candidate annotator first (prerequisite)
        wiki_annotator = WikiCandidateAnnotator(clean_db_session)
        wiki_annotator.compute()
        clean_db_session.commit()
        
        # Run title annotator
        title_annotator = NaiveTitleAnnotator(clean_db_session)
        count = title_annotator.compute()
        clean_db_session.commit()
        
        assert count > 0
        
        # Verify title was extracted
        reader = AnnotationReader(clean_db_session)
        pr = clean_db_session.query(PromptResponse).first()
        
        values = reader.get_string(EntityType.PROMPT_RESPONSE, pr.id, 'proposed_title')
        assert 'The Domestic Cat' in values
    
    def test_annotator_prerequisite_filtering(self, clean_db_session, chatgpt_simple_conversation):
        """Test that NaiveTitleAnnotator respects REQUIRES_STRINGS."""
        # Import conversation that won't be marked as wiki
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        builder.build_all()
        clean_db_session.commit()
        
        # Skip wiki annotator - no wiki_article annotations will exist
        
        # Run title annotator
        title_annotator = NaiveTitleAnnotator(clean_db_session)
        count = title_annotator.compute()
        clean_db_session.commit()
        
        # Should process nothing because prerequisite not met
        assert count == 0


class TestGizmoAnnotationIntegration:
    """Integration tests for gizmo annotation writing during extraction."""
    
    def test_gizmo_annotation_written_during_extraction(self, clean_db_session):
        """Test that gizmo_id is written as annotation during extraction."""
        conversation = {
            'conversation_id': 'conv-gizmo',
            'title': 'Gizmo Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-1': {
                    'id': 'node-1',
                    'message': {
                        'id': 'msg-1',
                        'author': {'role': 'assistant'},
                        'content': {'parts': ['Response from custom GPT']},
                        'metadata': {
                            'gizmo_id': 'g-wiki-generator',
                            'model_slug': 'gpt-4',
                        },
                        'create_time': 1700000000,
                    },
                    'parent': None,
                },
            },
        }
        
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conversation)
        clean_db_session.commit()
        
        message = clean_db_session.query(Message).first()
        reader = AnnotationReader(clean_db_session)
        
        # Check gizmo_id annotation
        gizmo_values = reader.get_string(EntityType.MESSAGE, message.id, 'gizmo_id')
        assert 'g-wiki-generator' in gizmo_values
        
        # Check has_gizmo flag
        assert reader.has_flag(EntityType.MESSAGE, message.id, 'has_gizmo')
        
        # Check model_slug annotation
        model_values = reader.get_string(EntityType.MESSAGE, message.id, 'model_slug')
        assert 'gpt-4' in model_values
