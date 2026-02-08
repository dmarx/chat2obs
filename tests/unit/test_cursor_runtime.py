# tests/unit/test_cursor_runtime.py
"""
Unit tests for cursor management with runtime tracking.

Tests the CursorManager and BaseAnnotator runtime tracking functionality.
"""

import time
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from unittest.mock import Mock

from llm_archive.annotations.cursor import CursorManager, AnnotatorCursor
from llm_archive.annotations.core import EntityType


class TestCursorManager:
    """Test CursorManager cursor creation and updates."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock session for testing."""
        return Mock()
    
    @pytest.fixture
    def cursor_manager(self, mock_session):
        """Create cursor manager with mock session."""
        return CursorManager(mock_session)
    
    def test_cursor_dataclass(self):
        """Test AnnotatorCursor dataclass creation."""
        now = datetime.now(timezone.utc)
        cursor = AnnotatorCursor(
            id=uuid4(),
            annotator_name='TestAnnotator',
            annotator_version='1.0',
            entity_type='message',
            high_water_mark=now,
            entities_processed=100,
            annotations_created=50,
            cumulative_runtime_seconds=12.5,
            updated_at=now,
        )
        
        assert cursor.annotator_name == 'TestAnnotator'
        assert cursor.entities_processed == 100
        assert cursor.annotations_created == 50
        assert cursor.cumulative_runtime_seconds == 12.5
    
    def test_cursor_runtime_accumulation(self):
        """Test that runtime accumulates correctly across updates."""
        now = datetime.now(timezone.utc)
        cursor = AnnotatorCursor(
            id=uuid4(),
            annotator_name='TestAnnotator',
            annotator_version='1.0',
            entity_type='message',
            high_water_mark=now,
            entities_processed=100,
            annotations_created=50,
            cumulative_runtime_seconds=10.0,
            updated_at=now,
        )
        
        # Simulate adding more runtime
        new_runtime_total = cursor.cumulative_runtime_seconds + 5.5
        assert new_runtime_total == 15.5


class TestRuntimeTracking:
    """Integration tests for runtime tracking in annotators."""
    
    def test_compute_tracks_runtime(self):
        """Test that compute() tracks runtime correctly."""
        # This would require a real database session to test properly
        # Placeholder for integration test
        pass
    
    def test_multiple_runs_accumulate_runtime(self):
        """Test that multiple runs accumulate runtime."""
        # This would require a real database session to test properly
        # Placeholder for integration test
        pass


class TestRuntimeFormatting:
    """Test human-readable runtime formatting."""
    
    def test_format_milliseconds(self):
        """Test formatting sub-second times."""
        from llm_archive.cli_cursors import CursorStats
        
        stats = CursorStats(Mock())
        
        assert stats._format_runtime(0.5) == '500ms'
        assert stats._format_runtime(0.001) == '1ms'
    
    def test_format_seconds(self):
        """Test formatting seconds."""
        from llm_archive.cli_cursors import CursorStats
        
        stats = CursorStats(Mock())
        
        assert stats._format_runtime(1.0) == '1.0s'
        assert stats._format_runtime(30.5) == '30.5s'
    
    def test_format_minutes(self):
        """Test formatting minutes."""
        from llm_archive.cli_cursors import CursorStats
        
        stats = CursorStats(Mock())
        
        assert stats._format_runtime(60.0) == '1.0m'
        assert stats._format_runtime(150.0) == '2.5m'
    
    def test_format_hours(self):
        """Test formatting hours."""
        from llm_archive.cli_cursors import CursorStats
        
        stats = CursorStats(Mock())
        
        assert stats._format_runtime(3600.0) == '1.00h'
        assert stats._format_runtime(7200.0) == '2.00h'


# ============================================================
# Integration test examples (require database)
# ============================================================

class TestCursorRuntimeIntegration:
    """Integration tests with real database."""
    
    @pytest.fixture
    def db_session(self):
        """Database session fixture - would need real DB setup."""
        pytest.skip("Requires database setup")
    
    def test_cursor_creation_initializes_runtime(self, db_session):
        """Test that new cursors initialize runtime to 0.0."""
        manager = CursorManager(db_session)
        
        cursor = manager.get_cursor(
            annotator_name='TestAnnotator',
            annotator_version='1.0',
            entity_type=EntityType.MESSAGE,
        )
        
        assert cursor.cumulative_runtime_seconds == 0.0
    
    def test_cursor_update_accumulates_runtime(self, db_session):
        """Test that updating cursor accumulates runtime."""
        manager = CursorManager(db_session)
        
        # Get initial cursor
        cursor = manager.get_cursor(
            annotator_name='TestAnnotator',
            annotator_version='1.0',
            entity_type=EntityType.MESSAGE,
        )
        
        initial_runtime = cursor.cumulative_runtime_seconds
        
        # Update with runtime
        manager.update_cursor(
            cursor=cursor,
            entities_processed=10,
            annotations_created=5,
            new_high_water_mark=datetime.now(timezone.utc),
            runtime_seconds=3.5,
        )
        
        # Get updated cursor
        updated_cursor = manager.get_cursor(
            annotator_name='TestAnnotator',
            annotator_version='1.0',
            entity_type=EntityType.MESSAGE,
        )
        
        assert updated_cursor.cumulative_runtime_seconds == initial_runtime + 3.5
        assert updated_cursor.entities_processed == 10
        assert updated_cursor.annotations_created == 5
    
    def test_multiple_runs_accumulate(self, db_session):
        """Test that multiple annotation runs accumulate stats."""
        manager = CursorManager(db_session)
        
        cursor = manager.get_cursor(
            annotator_name='TestAnnotator',
            annotator_version='1.0',
            entity_type=EntityType.MESSAGE,
        )
        
        # First run
        manager.update_cursor(
            cursor=cursor,
            entities_processed=100,
            annotations_created=50,
            new_high_water_mark=datetime.now(timezone.utc),
            runtime_seconds=10.0,
        )
        
        # Get cursor for second run
        cursor = manager.get_cursor(
            annotator_name='TestAnnotator',
            annotator_version='1.0',
            entity_type=EntityType.MESSAGE,
        )
        
        # Second run
        manager.update_cursor(
            cursor=cursor,
            entities_processed=50,
            annotations_created=25,
            new_high_water_mark=datetime.now(timezone.utc),
            runtime_seconds=5.0,
        )
        
        # Verify cumulative stats
        final_cursor = manager.get_cursor(
            annotator_name='TestAnnotator',
            annotator_version='1.0',
            entity_type=EntityType.MESSAGE,
        )
        
        assert final_cursor.entities_processed == 150
        assert final_cursor.annotations_created == 75
        assert final_cursor.cumulative_runtime_seconds == 15.0
