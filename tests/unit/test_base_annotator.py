# tests/unit/test_base_annotator.py
"""Unit tests for BaseAnnotator cursor-based incremental processing.

These tests verify the cursor lifecycle (create, read, update) and the
compute() orchestration without requiring a live database.  We use a
concrete stub annotator and mock the session/database interaction.
"""

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4

import pytest

from llm_archive.annotations.core import AnnotationResult, EntityType, ValueType
from llm_archive.annotators.base import BaseAnnotator, _EPOCH
from llm_archive.models.derived import AnnotatorCursor


# ============================================================
# Concrete stub for testing
# ============================================================

class StubAnnotator(BaseAnnotator):
    """Minimal concrete annotator for testing BaseAnnotator mechanics."""

    ENTITY_TYPE = EntityType.CONTENT_PART
    ANNOTATION_KEY = "stub"
    VALUE_TYPE = ValueType.FLAG
    PRIORITY = 50
    VERSION = "1.0"
    SOURCE = "test"

    def __init__(self, session, entities=None):
        super().__init__(session)
        self._entities = entities or []

    def _iter_entities_after(self, after):
        for entity in self._entities:
            if entity["created_at"] > after:
                yield entity

    def _entity_id(self, data):
        return data["id"]

    def _created_at(self, data):
        return data["created_at"]

    def annotate(self, data):
        if data.get("should_annotate", True):
            return [AnnotationResult(key="stub", value_type=ValueType.FLAG)]
        return []


# ============================================================
# Fixtures
# ============================================================

def _make_entity(created_at: datetime, should_annotate: bool = True):
    return {
        "id": uuid4(),
        "created_at": created_at,
        "should_annotate": should_annotate,
    }


def _make_cursor(
    name: str = "StubAnnotator",
    version: str = "1.0",
    hwm: datetime | None = None,
) -> AnnotatorCursor:
    c = AnnotatorCursor()
    c.annotator_name = name
    c.annotator_version = version
    c.entity_type = EntityType.CONTENT_PART.value
    c.high_water_mark = hwm or _EPOCH
    c.entities_processed = 0
    c.annotations_created = 0
    c.cumulative_runtime_seconds = 0.0
    c.updated_at = datetime.now(timezone.utc)
    return c


# ============================================================
# Tests
# ============================================================

class TestBaseAnnotatorCursorCreation:
    """Test cursor creation on first run."""

    def test_creates_cursor_when_none_exists(self):
        """First call to _get_or_create_cursor creates a new cursor."""
        session = MagicMock()
        query_mock = MagicMock()
        query_mock.filter_by.return_value.one_or_none.return_value = None
        session.query.return_value = query_mock

        annotator = StubAnnotator(session)
        cursor = annotator._get_or_create_cursor()

        session.add.assert_called_once()
        added = session.add.call_args[0][0]
        assert isinstance(added, AnnotatorCursor)
        assert added.annotator_name == "StubAnnotator"
        assert added.annotator_version == "1.0"
        assert added.high_water_mark == _EPOCH

    def test_returns_existing_cursor(self):
        """Returns existing cursor if one matches."""
        existing = _make_cursor(hwm=datetime(2024, 6, 1, tzinfo=timezone.utc))
        session = MagicMock()
        session.query.return_value.filter_by.return_value.one_or_none.return_value = existing

        annotator = StubAnnotator(session)
        cursor = annotator._get_or_create_cursor()

        assert cursor is existing
        session.add.assert_not_called()


class TestBaseAnnotatorCursorUpdate:
    """Test cursor update after processing."""

    def test_update_advances_hwm(self):
        cursor = _make_cursor()
        session = MagicMock()

        annotator = StubAnnotator(session)
        new_hwm = datetime(2025, 1, 1, tzinfo=timezone.utc)

        annotator._update_cursor(
            cursor,
            entities_processed=10,
            annotations_created=5,
            new_high_water_mark=new_hwm,
            elapsed_seconds=1.23,
        )

        assert cursor.high_water_mark == new_hwm
        assert cursor.entities_processed == 10
        assert cursor.annotations_created == 5
        assert cursor.cumulative_runtime_seconds == pytest.approx(1.23, abs=0.01)

    def test_update_accumulates_stats(self):
        """Stats are cumulative across runs."""
        cursor = _make_cursor()
        cursor.entities_processed = 100
        cursor.annotations_created = 50
        cursor.cumulative_runtime_seconds = 10.0
        session = MagicMock()
        annotator = StubAnnotator(session)

        annotator._update_cursor(
            cursor,
            entities_processed=20,
            annotations_created=8,
            new_high_water_mark=datetime(2025, 1, 1, tzinfo=timezone.utc),
            elapsed_seconds=2.5,
        )

        assert cursor.entities_processed == 120
        assert cursor.annotations_created == 58
        assert cursor.cumulative_runtime_seconds == pytest.approx(12.5, abs=0.01)


class TestBaseAnnotatorCompute:
    """Test the compute() orchestration."""

    def test_compute_processes_entities_after_hwm(self):
        """Only entities newer than HWM are processed."""
        t1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2024, 6, 1, tzinfo=timezone.utc)
        t3 = datetime(2024, 12, 1, tzinfo=timezone.utc)

        entities = [
            _make_entity(t1),
            _make_entity(t2),
            _make_entity(t3),
        ]

        existing_cursor = _make_cursor(hwm=t2)

        session = MagicMock()
        session.query.return_value.filter_by.return_value.one_or_none.return_value = existing_cursor

        annotator = StubAnnotator(session, entities=entities)
        # Mock _write_result to return True
        annotator._write_result = MagicMock(return_value=True)

        count = annotator.compute()

        # Only t3 entity is after hwm=t2
        assert count == 1
        assert annotator._write_result.call_count == 1

    def test_compute_updates_hwm_to_latest(self):
        """HWM advances to the latest entity's created_at."""
        t1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2024, 6, 1, tzinfo=timezone.utc)

        entities = [_make_entity(t1), _make_entity(t2)]
        cursor = _make_cursor()  # hwm=epoch

        session = MagicMock()
        session.query.return_value.filter_by.return_value.one_or_none.return_value = cursor

        annotator = StubAnnotator(session, entities=entities)
        annotator._write_result = MagicMock(return_value=True)

        annotator.compute()

        assert cursor.high_water_mark == t2

    def test_compute_returns_annotation_count(self):
        """compute() returns number of annotations created."""
        entities = [
            _make_entity(datetime(2024, 1, 1, tzinfo=timezone.utc)),
            _make_entity(datetime(2024, 2, 1, tzinfo=timezone.utc), should_annotate=False),
            _make_entity(datetime(2024, 3, 1, tzinfo=timezone.utc)),
        ]
        cursor = _make_cursor()

        session = MagicMock()
        session.query.return_value.filter_by.return_value.one_or_none.return_value = cursor

        annotator = StubAnnotator(session, entities=entities)
        annotator._write_result = MagicMock(return_value=True)

        count = annotator.compute()

        # 2 entities annotate, 1 does not
        assert count == 2

    def test_compute_tracks_runtime(self):
        """cumulative_runtime_seconds increases after compute()."""
        cursor = _make_cursor()

        session = MagicMock()
        session.query.return_value.filter_by.return_value.one_or_none.return_value = cursor

        annotator = StubAnnotator(session, entities=[])
        annotator.compute()

        assert cursor.cumulative_runtime_seconds > 0

    def test_compute_noop_when_no_new_entities(self):
        """compute() returns 0 and HWM unchanged when nothing new."""
        hwm = datetime(2025, 1, 1, tzinfo=timezone.utc)
        cursor = _make_cursor(hwm=hwm)

        session = MagicMock()
        session.query.return_value.filter_by.return_value.one_or_none.return_value = cursor

        annotator = StubAnnotator(session, entities=[])
        count = annotator.compute()

        assert count == 0
        assert cursor.high_water_mark == hwm


class TestBaseAnnotatorVersioning:
    """Test that version changes create separate cursors."""

    def test_different_versions_get_different_cursors(self):
        """Changing VERSION should query for a new cursor key."""
        session = MagicMock()
        session.query.return_value.filter_by.return_value.one_or_none.return_value = None

        class V1(StubAnnotator):
            VERSION = "1.0"

        class V2(StubAnnotator):
            VERSION = "2.0"

        v1 = V1(session)
        v1._get_or_create_cursor()
        call1_kwargs = session.query.return_value.filter_by.call_args

        v2 = V2(session)
        v2._get_or_create_cursor()
        call2_kwargs = session.query.return_value.filter_by.call_args

        # The filter_by calls should differ in annotator_version
        assert call1_kwargs != call2_kwargs


class TestBaseAnnotatorWriteResult:
    """Test _write_result dispatch."""

    def test_dispatches_flag(self):
        session = MagicMock()
        annotator = StubAnnotator(session)
        annotator.writer = MagicMock()
        annotator.writer.write_flag.return_value = True

        result = AnnotationResult(key="test", value_type=ValueType.FLAG)
        written = annotator._write_result(uuid4(), result)

        assert written is True
        annotator.writer.write_flag.assert_called_once()

    def test_dispatches_string(self):
        session = MagicMock()
        annotator = StubAnnotator(session)
        annotator.writer = MagicMock()
        annotator.writer.write_string.return_value = True

        result = AnnotationResult(key="test", value="hello", value_type=ValueType.STRING)
        written = annotator._write_result(uuid4(), result)

        assert written is True
        annotator.writer.write_string.assert_called_once()

    def test_dispatches_numeric(self):
        session = MagicMock()
        annotator = StubAnnotator(session)
        annotator.writer = MagicMock()
        annotator.writer.write_numeric.return_value = True

        result = AnnotationResult(key="test", value=42, value_type=ValueType.NUMERIC)
        written = annotator._write_result(uuid4(), result)

        assert written is True
        annotator.writer.write_numeric.assert_called_once()

    def test_dispatches_json(self):
        session = MagicMock()
        annotator = StubAnnotator(session)
        annotator.writer = MagicMock()
        annotator.writer.write_json.return_value = True

        result = AnnotationResult(key="test", value={"a": 1}, value_type=ValueType.JSON)
        written = annotator._write_result(uuid4(), result)

        assert written is True
        annotator.writer.write_json.assert_called_once()
