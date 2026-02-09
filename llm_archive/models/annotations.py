# llm_archive/models/annotations.py
"""Factory-generated ORM models for typed annotation tables.

Each (entity_type, value_type) pair gets its own table:
    derived.{entity}_annotations_{value_type}

This module generates all 16 models (4 entity types × 4 value types)
and provides a registry for lookup:

    from llm_archive.models.annotations import get_annotation_model
    model = get_annotation_model(EntityType.CONTENT_PART, ValueType.FLAG)
    session.query(model).filter(model.annotation_key == 'has_code_block')

Adding a new entity type only requires adding an entry to _ENTITY_CONFIG.
"""

from __future__ import annotations

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Index, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from llm_archive.annotations.core import EntityType, ValueType
from llm_archive.models.raw import Base


# ------------------------------------------------------------------
# Entity configuration: maps EntityType → FK target string
# ------------------------------------------------------------------

_ENTITY_CONFIG: dict[EntityType, str] = {
    EntityType.CONTENT_PART:    "raw.content_parts.id",
    EntityType.MESSAGE:         "raw.messages.id",
    EntityType.PROMPT_RESPONSE: "derived.prompt_responses.id",
    EntityType.DIALOGUE:        "raw.dialogues.id",
}


# ------------------------------------------------------------------
# Shared columns present on every annotation table
# ------------------------------------------------------------------

def _common_columns(entity_fk: str) -> dict:
    return {
        "id": Column(
            PG_UUID(as_uuid=True), primary_key=True,
            server_default=func.gen_random_uuid(),
        ),
        "entity_id": Column(
            PG_UUID(as_uuid=True),
            ForeignKey(entity_fk, ondelete="CASCADE"),
            nullable=False,
        ),
        "annotation_key": Column(String, nullable=False),
        "confidence": Column(Float),
        "reason": Column(Text),
        "source": Column(String, nullable=False),
        "source_version": Column(String),
        "created_at": Column(DateTime(timezone=True), server_default=func.now()),
    }


# ------------------------------------------------------------------
# Value-type-specific columns and constraints
# ------------------------------------------------------------------

def _value_columns_and_args(
    entity_type: EntityType,
    value_type: ValueType,
) -> tuple[dict, tuple]:
    """Return (extra_columns, __table_args__) for a value type."""
    prefix = entity_type.value.replace("_", "")[:6]  # short prefix for index names

    if value_type == ValueType.FLAG:
        return {}, (
            UniqueConstraint("entity_id", "annotation_key"),
            Index(f"ix_{prefix}_ann_flag_key", "annotation_key"),
            Index(f"ix_{prefix}_ann_flag_eid", "entity_id"),
            {"schema": "derived"},
        )

    if value_type == ValueType.STRING:
        return {"annotation_value": Column(String, nullable=False)}, (
            UniqueConstraint("entity_id", "annotation_key", "annotation_value"),
            Index(f"ix_{prefix}_ann_str_key", "annotation_key"),
            Index(f"ix_{prefix}_ann_str_kv", "annotation_key", "annotation_value"),
            Index(f"ix_{prefix}_ann_str_eid", "entity_id"),
            {"schema": "derived"},
        )

    if value_type == ValueType.NUMERIC:
        return {"annotation_value": Column(Float, nullable=False)}, (
            UniqueConstraint("entity_id", "annotation_key", "annotation_value"),
            Index(f"ix_{prefix}_ann_num_key", "annotation_key"),
            Index(f"ix_{prefix}_ann_num_eid", "entity_id"),
            {"schema": "derived"},
        )

    if value_type == ValueType.JSON:
        return {"annotation_value": Column(JSONB, nullable=False)}, (
            UniqueConstraint("entity_id", "annotation_key"),
            Index(f"ix_{prefix}_ann_json_key", "annotation_key"),
            Index(f"ix_{prefix}_ann_json_eid", "entity_id"),
            {"schema": "derived"},
        )

    raise ValueError(f"Unknown value type: {value_type}")


# ------------------------------------------------------------------
# Model factory
# ------------------------------------------------------------------

def _class_name(entity_type: EntityType, value_type: ValueType) -> str:
    """Generate a PascalCase class name: e.g. ContentPartAnnotationFlag."""
    entity_pascal = entity_type.value.replace("_", " ").title().replace(" ", "")
    value_pascal = value_type.value.title()
    return f"{entity_pascal}Annotation{value_pascal}"


def _make_annotation_model(
    entity_type: EntityType,
    value_type: ValueType,
) -> type:
    """Generate an ORM model class for one annotation table."""
    entity_fk = _ENTITY_CONFIG[entity_type]
    table_name = f"{entity_type.value}_annotations_{value_type.value}"

    columns = _common_columns(entity_fk)
    extra_columns, table_args = _value_columns_and_args(entity_type, value_type)
    columns.update(extra_columns)

    attrs = {
        "__tablename__": table_name,
        "__table_args__": table_args,
        **columns,
    }

    cls = type(_class_name(entity_type, value_type), (Base,), attrs)
    return cls


# ------------------------------------------------------------------
# Registry: generated once at import time
# ------------------------------------------------------------------

_ANNOTATION_MODELS: dict[EntityType, dict[ValueType, type]] = {}

for _et in EntityType:
    _ANNOTATION_MODELS[_et] = {}
    for _vt in ValueType:
        _ANNOTATION_MODELS[_et][_vt] = _make_annotation_model(_et, _vt)


def get_annotation_model(entity_type: EntityType, value_type: ValueType) -> type:
    """Look up the ORM model for a (entity_type, value_type) pair."""
    return _ANNOTATION_MODELS[entity_type][value_type]


def get_all_annotation_models() -> list[type]:
    """Return all 16 annotation model classes (for schema creation)."""
    return [
        model
        for et_models in _ANNOTATION_MODELS.values()
        for model in et_models.values()
    ]


# ------------------------------------------------------------------
# Convenience aliases for the most commonly used models
# ------------------------------------------------------------------

ContentPartAnnotationFlag = _ANNOTATION_MODELS[EntityType.CONTENT_PART][ValueType.FLAG]
ContentPartAnnotationString = _ANNOTATION_MODELS[EntityType.CONTENT_PART][ValueType.STRING]
ContentPartAnnotationNumeric = _ANNOTATION_MODELS[EntityType.CONTENT_PART][ValueType.NUMERIC]
ContentPartAnnotationJson = _ANNOTATION_MODELS[EntityType.CONTENT_PART][ValueType.JSON]

MessageAnnotationFlag = _ANNOTATION_MODELS[EntityType.MESSAGE][ValueType.FLAG]
MessageAnnotationString = _ANNOTATION_MODELS[EntityType.MESSAGE][ValueType.STRING]

PromptResponseAnnotationFlag = _ANNOTATION_MODELS[EntityType.PROMPT_RESPONSE][ValueType.FLAG]
PromptResponseAnnotationString = _ANNOTATION_MODELS[EntityType.PROMPT_RESPONSE][ValueType.STRING]
PromptResponseAnnotationNumeric = _ANNOTATION_MODELS[EntityType.PROMPT_RESPONSE][ValueType.NUMERIC]
PromptResponseAnnotationJson = _ANNOTATION_MODELS[EntityType.PROMPT_RESPONSE][ValueType.JSON]

DialogueAnnotationFlag = _ANNOTATION_MODELS[EntityType.DIALOGUE][ValueType.FLAG]
DialogueAnnotationString = _ANNOTATION_MODELS[EntityType.DIALOGUE][ValueType.STRING]
