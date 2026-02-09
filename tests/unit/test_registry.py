# tests/unit/test_registry.py
"""Unit tests for AnnotatorRegistry."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from llm_archive.annotations.core import AnnotationResult, EntityType, ValueType
from llm_archive.annotators.base import BaseAnnotator
from llm_archive.annotators.registry import AnnotatorRegistry, get_default_registry


# ============================================================
# Stubs
# ============================================================

class HighPriorityAnnotator(BaseAnnotator):
    ENTITY_TYPE = EntityType.CONTENT_PART
    ANNOTATION_KEY = "high"
    PRIORITY = 90
    VERSION = "1.0"

    def _iter_entities_after(self, after):
        return iter([])

    def _entity_id(self, data):
        return uuid4()

    def _created_at(self, data):
        return None

    def annotate(self, data):
        return []


class LowPriorityAnnotator(BaseAnnotator):
    ENTITY_TYPE = EntityType.MESSAGE
    ANNOTATION_KEY = "low"
    PRIORITY = 10
    VERSION = "1.0"

    def _iter_entities_after(self, after):
        return iter([])

    def _entity_id(self, data):
        return uuid4()

    def _created_at(self, data):
        return None

    def annotate(self, data):
        return []


class MediumPriorityAnnotator(BaseAnnotator):
    ENTITY_TYPE = EntityType.PROMPT_RESPONSE
    ANNOTATION_KEY = "med"
    PRIORITY = 50
    VERSION = "1.0"

    def _iter_entities_after(self, after):
        return iter([])

    def _entity_id(self, data):
        return uuid4()

    def _created_at(self, data):
        return None

    def annotate(self, data):
        return []


# ============================================================
# Tests
# ============================================================

class TestRegistryRegistration:
    """Test registration mechanics."""

    def test_register_single(self):
        reg = AnnotatorRegistry()
        reg.register(HighPriorityAnnotator)
        assert reg.get("HighPriorityAnnotator") is HighPriorityAnnotator

    def test_register_many(self):
        reg = AnnotatorRegistry()
        reg.register_many([HighPriorityAnnotator, LowPriorityAnnotator])
        assert len(reg.list_annotators()) == 2

    def test_unregister(self):
        reg = AnnotatorRegistry()
        reg.register(HighPriorityAnnotator)
        reg.unregister("HighPriorityAnnotator")
        assert reg.get("HighPriorityAnnotator") is None

    def test_get_returns_none_for_missing(self):
        reg = AnnotatorRegistry()
        assert reg.get("NonExistent") is None


class TestRegistryOrdering:
    """Test priority-based ordering."""

    def test_list_sorted_by_priority_descending(self):
        reg = AnnotatorRegistry()
        reg.register_many([
            LowPriorityAnnotator,
            HighPriorityAnnotator,
            MediumPriorityAnnotator,
        ])

        ordered = reg.list_annotators()
        priorities = [cls.PRIORITY for cls in ordered]
        assert priorities == sorted(priorities, reverse=True)
        assert priorities == [90, 50, 10]


class TestRegistryExecution:
    """Test run_all and run_one."""

    def test_run_one_raises_for_unknown(self):
        reg = AnnotatorRegistry()
        session = MagicMock()
        with pytest.raises(KeyError, match="NotRegistered"):
            reg.run_one("NotRegistered", session)


class TestDefaultRegistry:
    """Test the default registry factory."""

    def test_default_registry_has_builtins(self):
        reg = get_default_registry()
        names = [cls.__name__ for cls in reg.list_annotators()]

        assert "CodeBlockAnnotator" in names
        assert "WikiCandidateAnnotator" in names
        assert "NaiveTitleAnnotator" in names

    def test_default_registry_sorted_by_priority(self):
        reg = get_default_registry()
        annotators = reg.list_annotators()
        priorities = [cls.PRIORITY for cls in annotators]
        assert priorities == sorted(priorities, reverse=True)
