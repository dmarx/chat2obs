# tests/unit/test_annotation_models.py
"""Tests for the annotation model factory.

Verifies that all 16 annotation ORM models are correctly generated
with proper table names, columns, constraints, and FK references.
"""

import pytest

from llm_archive.annotations.core import EntityType, ValueType
from llm_archive.models.annotations import (
    get_annotation_model,
    get_all_annotation_models,
    _ENTITY_CONFIG,
    ContentPartAnnotationFlag,
    ContentPartAnnotationString,
    PromptResponseAnnotationFlag,
    PromptResponseAnnotationString,
)
from llm_archive.models.raw import Base


# ============================================================
# Factory Completeness
# ============================================================

class TestAnnotationModelFactory:
    """Verify the factory generates all expected models."""

    def test_generates_16_models(self):
        models = get_all_annotation_models()
        assert len(models) == 16

    def test_all_entity_value_combinations_exist(self):
        for et in EntityType:
            for vt in ValueType:
                model = get_annotation_model(et, vt)
                assert model is not None
                assert issubclass(model, Base)

    def test_each_entity_type_has_config(self):
        for et in EntityType:
            assert et in _ENTITY_CONFIG


# ============================================================
# Table Naming
# ============================================================

class TestAnnotationModelTableNames:
    """Verify table names follow the convention."""

    @pytest.mark.parametrize("et,vt,expected", [
        (EntityType.CONTENT_PART, ValueType.FLAG, "content_part_annotations_flag"),
        (EntityType.CONTENT_PART, ValueType.STRING, "content_part_annotations_string"),
        (EntityType.MESSAGE, ValueType.NUMERIC, "message_annotations_numeric"),
        (EntityType.PROMPT_RESPONSE, ValueType.JSON, "prompt_response_annotations_json"),
        (EntityType.DIALOGUE, ValueType.FLAG, "dialogue_annotations_flag"),
    ])
    def test_table_name(self, et, vt, expected):
        model = get_annotation_model(et, vt)
        assert model.__tablename__ == expected

    def test_all_tables_in_derived_schema(self):
        for model in get_all_annotation_models():
            schema = model.__table__.schema
            assert schema == "derived", f"{model.__name__} has schema={schema}"


# ============================================================
# Class Naming
# ============================================================

class TestAnnotationModelClassNames:
    """Verify generated class names are PascalCase."""

    @pytest.mark.parametrize("et,vt,expected", [
        (EntityType.CONTENT_PART, ValueType.FLAG, "ContentPartAnnotationFlag"),
        (EntityType.MESSAGE, ValueType.STRING, "MessageAnnotationString"),
        (EntityType.PROMPT_RESPONSE, ValueType.NUMERIC, "PromptResponseAnnotationNumeric"),
        (EntityType.DIALOGUE, ValueType.JSON, "DialogueAnnotationJson"),
    ])
    def test_class_name(self, et, vt, expected):
        model = get_annotation_model(et, vt)
        assert model.__name__ == expected


# ============================================================
# Column Structure
# ============================================================

class TestAnnotationModelColumns:
    """Verify column presence varies correctly by value type."""

    def _column_names(self, model) -> set[str]:
        return {c.name for c in model.__table__.columns}

    def test_all_models_have_common_columns(self):
        common = {"id", "entity_id", "annotation_key", "confidence",
                  "reason", "source", "source_version", "created_at"}
        for model in get_all_annotation_models():
            cols = self._column_names(model)
            missing = common - cols
            assert not missing, f"{model.__name__} missing columns: {missing}"

    def test_flag_model_has_no_annotation_value(self):
        model = get_annotation_model(EntityType.CONTENT_PART, ValueType.FLAG)
        assert "annotation_value" not in self._column_names(model)

    @pytest.mark.parametrize("vt", [ValueType.STRING, ValueType.NUMERIC, ValueType.JSON])
    def test_valued_models_have_annotation_value(self, vt):
        model = get_annotation_model(EntityType.CONTENT_PART, vt)
        assert "annotation_value" in self._column_names(model)

    def test_entity_id_is_not_nullable(self):
        for model in get_all_annotation_models():
            col = model.__table__.c.entity_id
            assert not col.nullable, f"{model.__name__}.entity_id should not be nullable"


# ============================================================
# Foreign Keys
# ============================================================

class TestAnnotationModelForeignKeys:
    """Verify FK references point to the correct entity tables."""

    def _get_fk_target(self, model) -> str:
        col = model.__table__.c.entity_id
        fk = list(col.foreign_keys)[0]
        return str(fk.target_fullname)

    @pytest.mark.parametrize("et,expected_target", [
        (EntityType.CONTENT_PART, "raw.content_parts.id"),
        (EntityType.MESSAGE, "raw.messages.id"),
        (EntityType.PROMPT_RESPONSE, "derived.prompt_responses.id"),
        (EntityType.DIALOGUE, "raw.dialogues.id"),
    ])
    def test_fk_target(self, et, expected_target):
        # Check all 4 value types for this entity type
        for vt in ValueType:
            model = get_annotation_model(et, vt)
            target = self._get_fk_target(model)
            assert target == expected_target, (
                f"{model.__name__} FK target is {target}, expected {expected_target}"
            )


# ============================================================
# Unique Constraints
# ============================================================

class TestAnnotationModelConstraints:
    """Verify unique constraints vary by value type."""

    def _unique_columns(self, model) -> list[tuple[str, ...]]:
        """Extract unique constraint column sets."""
        uniques = []
        for constraint in model.__table__.constraints:
            if hasattr(constraint, 'columns') and constraint.__class__.__name__ == 'UniqueConstraint':
                cols = tuple(c.name for c in constraint.columns)
                uniques.append(cols)
        return uniques

    def test_flag_unique_on_entity_and_key(self):
        model = get_annotation_model(EntityType.CONTENT_PART, ValueType.FLAG)
        uniques = self._unique_columns(model)
        assert ("entity_id", "annotation_key") in uniques

    def test_string_unique_on_entity_key_value(self):
        model = get_annotation_model(EntityType.CONTENT_PART, ValueType.STRING)
        uniques = self._unique_columns(model)
        assert ("entity_id", "annotation_key", "annotation_value") in uniques

    def test_numeric_unique_on_entity_key_value(self):
        model = get_annotation_model(EntityType.PROMPT_RESPONSE, ValueType.NUMERIC)
        uniques = self._unique_columns(model)
        assert ("entity_id", "annotation_key", "annotation_value") in uniques

    def test_json_unique_on_entity_and_key(self):
        model = get_annotation_model(EntityType.DIALOGUE, ValueType.JSON)
        uniques = self._unique_columns(model)
        assert ("entity_id", "annotation_key") in uniques


# ============================================================
# Convenience Aliases
# ============================================================

class TestConvenienceAliases:
    """Verify module-level aliases resolve to the right models."""

    def test_content_part_flag_alias(self):
        assert ContentPartAnnotationFlag is get_annotation_model(
            EntityType.CONTENT_PART, ValueType.FLAG
        )

    def test_content_part_string_alias(self):
        assert ContentPartAnnotationString is get_annotation_model(
            EntityType.CONTENT_PART, ValueType.STRING
        )

    def test_prompt_response_flag_alias(self):
        assert PromptResponseAnnotationFlag is get_annotation_model(
            EntityType.PROMPT_RESPONSE, ValueType.FLAG
        )

    def test_prompt_response_string_alias(self):
        assert PromptResponseAnnotationString is get_annotation_model(
            EntityType.PROMPT_RESPONSE, ValueType.STRING
        )


# ============================================================
# Extensibility
# ============================================================

class TestAnnotationModelExtensibility:
    """Verify adding entity types only requires config changes."""

    def test_entity_config_covers_all_entity_types(self):
        """Every EntityType has an FK target configured."""
        for et in EntityType:
            assert et in _ENTITY_CONFIG, f"Missing config for {et.value}"
