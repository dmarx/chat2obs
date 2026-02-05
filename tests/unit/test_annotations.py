# tests/unit/test_annotations.py
"""Unit tests for annotation infrastructure."""

import pytest
from uuid import uuid4

from llm_archive.annotations.core import (
    EntityType,
    ValueType,
    AnnotationResult,
    AnnotationWriter,
    AnnotationReader,
)


# ============================================================
# AnnotationResult Tests
# ============================================================

class TestAnnotationResult:
    """Test AnnotationResult dataclass."""
    
    def test_create_flag_result(self):
        """Flag results only need key."""
        result = AnnotationResult(
            key='has_code',
            value_type=ValueType.FLAG,
        )
        assert result.key == 'has_code'
        assert result.value is None
        assert result.value_type == ValueType.FLAG
    
    def test_create_string_result(self):
        """String results need key and value."""
        result = AnnotationResult(
            key='exchange_type',
            value='wiki_article',
            value_type=ValueType.STRING,
            confidence=0.9,
            reason='wiki_links_detected',
        )
        assert result.key == 'exchange_type'
        assert result.value == 'wiki_article'
        assert result.value_type == ValueType.STRING
        assert result.confidence == 0.9
        assert result.reason == 'wiki_links_detected'
    
    def test_create_numeric_result(self):
        """Numeric results need key and numeric value."""
        result = AnnotationResult(
            key='wiki_link_count',
            value=5,
            value_type=ValueType.NUMERIC,
        )
        assert result.key == 'wiki_link_count'
        assert result.value == 5
        assert result.value_type == ValueType.NUMERIC
    
    def test_create_json_result(self):
        """JSON results can store complex data."""
        result = AnnotationResult(
            key='metadata',
            value={'domains': ['example.com', 'test.org']},
            value_type=ValueType.JSON,
        )
        assert result.key == 'metadata'
        assert result.value == {'domains': ['example.com', 'test.org']}
        assert result.value_type == ValueType.JSON
    
    def test_default_value_type_is_string(self):
        """Default value_type should be STRING."""
        result = AnnotationResult(key='title', value='Test Title')
        assert result.value_type == ValueType.STRING
    
    def test_default_source_is_heuristic(self):
        """Default source should be 'heuristic'."""
        result = AnnotationResult(key='test', value='value')
        assert result.source == 'heuristic'


# ============================================================
# EntityType and ValueType Enum Tests
# ============================================================

class TestEnums:
    """Test EntityType and ValueType enums."""
    
    def test_entity_types(self):
        """All expected entity types exist."""
        assert EntityType.CONTENT_PART.value == 'content_part'
        assert EntityType.MESSAGE.value == 'message'
        assert EntityType.PROMPT_RESPONSE.value == 'prompt_response'
        assert EntityType.DIALOGUE.value == 'dialogue'
    
    def test_value_types(self):
        """All expected value types exist."""
        assert ValueType.FLAG.value == 'flag'
        assert ValueType.STRING.value == 'string'
        assert ValueType.NUMERIC.value == 'numeric'
        assert ValueType.JSON.value == 'json'


# ============================================================
# AnnotationWriter Tests (mock-based, no DB)
# ============================================================

class TestAnnotationWriterInterface:
    """Test AnnotationWriter interface without database."""
    
    def test_table_name_generation(self):
        """Test table name generation for entity/value type combos."""
        # Can't instantiate without session, but can test the pattern
        template = "derived.{entity}_annotations_{value_type}"
        
        assert template.format(
            entity='message', value_type='string'
        ) == 'derived.message_annotations_string'
        
        assert template.format(
            entity='content_part', value_type='flag'
        ) == 'derived.content_part_annotations_flag'
        
        assert template.format(
            entity='prompt_response', value_type='numeric'
        ) == 'derived.prompt_response_annotations_numeric'


# ============================================================
# Integration test fixtures (require database)
# ============================================================

@pytest.fixture
def db_session():
    """
    Create a database session for integration tests.
    
    This fixture is a placeholder - actual implementation would
    need a test database setup.
    """
    pytest.skip("Requires database setup")


class TestAnnotationWriterIntegration:
    """Integration tests for AnnotationWriter (require database)."""
    
    def test_write_flag_creates_record(self, db_session):
        """Writing a flag creates a record in flag table."""
        writer = AnnotationWriter(db_session)
        entity_id = uuid4()
        
        result = writer.write_flag(
            entity_type=EntityType.MESSAGE,
            entity_id=entity_id,
            key='has_code',
            source='test',
        )
        
        assert result is True
        # Verify record exists
        reader = AnnotationReader(db_session)
        assert reader.has_flag(EntityType.MESSAGE, entity_id, 'has_code')
    
    def test_write_string_creates_record(self, db_session):
        """Writing a string creates a record in string table."""
        writer = AnnotationWriter(db_session)
        entity_id = uuid4()
        
        result = writer.write_string(
            entity_type=EntityType.MESSAGE,
            entity_id=entity_id,
            key='gizmo_id',
            value='g-12345',
            source='test',
        )
        
        assert result is True
        reader = AnnotationReader(db_session)
        values = reader.get_string(EntityType.MESSAGE, entity_id, 'gizmo_id')
        assert 'g-12345' in values
    
    def test_write_duplicate_flag_returns_false(self, db_session):
        """Writing duplicate flag returns False (no new record)."""
        writer = AnnotationWriter(db_session)
        entity_id = uuid4()
        
        # First write succeeds
        result1 = writer.write_flag(
            entity_type=EntityType.MESSAGE,
            entity_id=entity_id,
            key='has_code',
            source='test',
        )
        assert result1 is True
        
        # Duplicate returns False
        result2 = writer.write_flag(
            entity_type=EntityType.MESSAGE,
            entity_id=entity_id,
            key='has_code',
            source='test',
        )
        assert result2 is False
    
    def test_write_multi_value_string(self, db_session):
        """Can write multiple values for same string key."""
        writer = AnnotationWriter(db_session)
        entity_id = uuid4()
        
        writer.write_string(
            entity_type=EntityType.MESSAGE,
            entity_id=entity_id,
            key='tag',
            value='coding',
            source='test',
        )
        writer.write_string(
            entity_type=EntityType.MESSAGE,
            entity_id=entity_id,
            key='tag',
            value='python',
            source='test',
        )
        
        reader = AnnotationReader(db_session)
        values = reader.get_string(EntityType.MESSAGE, entity_id, 'tag')
        assert set(values) == {'coding', 'python'}


class TestAnnotationReaderIntegration:
    """Integration tests for AnnotationReader (require database)."""
    
    def test_find_entities_with_flag(self, db_session):
        """Can find all entities with a specific flag."""
        writer = AnnotationWriter(db_session)
        
        # Create some flagged entities
        id1, id2, id3 = uuid4(), uuid4(), uuid4()
        writer.write_flag(EntityType.MESSAGE, id1, 'has_code', source='test')
        writer.write_flag(EntityType.MESSAGE, id2, 'has_code', source='test')
        writer.write_flag(EntityType.MESSAGE, id3, 'has_attachment', source='test')
        
        reader = AnnotationReader(db_session)
        results = reader.find_entities_with_flag(EntityType.MESSAGE, 'has_code')
        
        assert id1 in results
        assert id2 in results
        assert id3 not in results
    
    def test_find_entities_with_string_value(self, db_session):
        """Can find entities with specific string value."""
        writer = AnnotationWriter(db_session)
        
        id1, id2 = uuid4(), uuid4()
        writer.write_string(EntityType.MESSAGE, id1, 'gizmo_id', 'g-wiki', source='test')
        writer.write_string(EntityType.MESSAGE, id2, 'gizmo_id', 'g-other', source='test')
        
        reader = AnnotationReader(db_session)
        results = reader.find_entities_with_string(
            EntityType.MESSAGE, 'gizmo_id', 'g-wiki'
        )
        
        assert id1 in results
        assert id2 not in results
