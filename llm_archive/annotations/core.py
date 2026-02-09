# llm_archive/annotations/core.py
"""Core annotation infrastructure for typed annotation tables.

Provides:
- EntityType / ValueType enums
- AnnotationResult dataclass (returned by annotator logic)
- AnnotationWriter: writes annotations via ORM models
- AnnotationReader: queries annotations via ORM models

All table routing is handled through the model registry in
llm_archive.models.annotations — no raw SQL string interpolation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from loguru import logger


# ============================================================
# Enums
# ============================================================

class EntityType(str, Enum):
    CONTENT_PART = 'content_part'
    MESSAGE = 'message'
    PROMPT_RESPONSE = 'prompt_response'
    DIALOGUE = 'dialogue'


class ValueType(str, Enum):
    FLAG = 'flag'
    STRING = 'string'
    NUMERIC = 'numeric'
    JSON = 'json'


# Single-value tables: (entity_id, annotation_key) is unique
SINGLE_VALUE_TYPES = {ValueType.FLAG, ValueType.JSON}


# ============================================================
# AnnotationResult (returned by annotators)
# ============================================================

@dataclass
class AnnotationResult:
    key: str
    value: Any = None
    value_type: ValueType = ValueType.STRING
    confidence: float | None = None
    reason: str | None = None
    source: str = 'heuristic'
    source_version: str | None = None

    def __eq__(self, other):
        if not isinstance(other, AnnotationResult):
            return NotImplemented
        return self.key == other.key and self.value == other.value and self.value_type == other.value_type

    def __hash__(self):
        value_hash = self.value
        if isinstance(self.value, dict):
            value_hash = tuple(sorted(self.value.items()))
        elif isinstance(self.value, list):
            value_hash = tuple(self.value)
        return hash((self.key, value_hash, self.value_type))

    def __repr__(self):
        if self.value_type == ValueType.FLAG:
            return f"AnnotationResult({self.key!r}, FLAG)"
        return f"AnnotationResult({self.key!r}, {self.value!r}, {self.value_type.value})"


# ============================================================
# Annotation Writer (ORM-based)
# ============================================================

def _get_model(entity_type: EntityType, value_type: ValueType):
    """Lazy import to avoid circular dependency."""
    from llm_archive.models.annotations import get_annotation_model
    return get_annotation_model(entity_type, value_type)


class AnnotationWriter:
    """Writes annotations to typed tables using ORM models.

    Uses PostgreSQL upsert (INSERT ... ON CONFLICT) for idempotency:
    - FLAG/JSON: ON CONFLICT (entity_id, key) → single value per key
    - STRING/NUMERIC: ON CONFLICT (entity_id, key, value) → multi-value
    """

    def __init__(self, session: Session):
        self.session = session
        self._counts: dict[str, int] = {}

    def write_flag(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        key: str,
        confidence: float | None = None,
        reason: str | None = None,
        source: str = 'heuristic',
        source_version: str | None = None,
    ) -> bool:
        model = _get_model(entity_type, ValueType.FLAG)
        values = {
            "entity_id": entity_id,
            "annotation_key": key,
            "confidence": confidence,
            "reason": reason,
            "source": source,
            "source_version": source_version,
        }
        stmt = (
            pg_insert(model)
            .values(**values)
            .on_conflict_do_nothing(
                index_elements=["entity_id", "annotation_key"],
            )
        )
        result = self.session.execute(stmt)
        created = result.rowcount > 0
        self._track(model.__tablename__, created)
        return created

    def write_string(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        key: str,
        value: str,
        confidence: float | None = None,
        reason: str | None = None,
        source: str = 'heuristic',
        source_version: str | None = None,
    ) -> bool:
        model = _get_model(entity_type, ValueType.STRING)
        values = {
            "entity_id": entity_id,
            "annotation_key": key,
            "annotation_value": value,
            "confidence": confidence,
            "reason": reason,
            "source": source,
            "source_version": source_version,
        }
        stmt = (
            pg_insert(model)
            .values(**values)
            .on_conflict_do_nothing(
                index_elements=["entity_id", "annotation_key", "annotation_value"],
            )
        )
        result = self.session.execute(stmt)
        created = result.rowcount > 0
        self._track(model.__tablename__, created)
        return created

    def write_numeric(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        key: str,
        value: float,
        confidence: float | None = None,
        reason: str | None = None,
        source: str = 'heuristic',
        source_version: str | None = None,
    ) -> bool:
        model = _get_model(entity_type, ValueType.NUMERIC)
        values = {
            "entity_id": entity_id,
            "annotation_key": key,
            "annotation_value": value,
            "confidence": confidence,
            "reason": reason,
            "source": source,
            "source_version": source_version,
        }
        stmt = (
            pg_insert(model)
            .values(**values)
            .on_conflict_do_nothing(
                index_elements=["entity_id", "annotation_key", "annotation_value"],
            )
        )
        result = self.session.execute(stmt)
        created = result.rowcount > 0
        self._track(model.__tablename__, created)
        return created

    def write_json(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        key: str,
        value: Any,
        confidence: float | None = None,
        reason: str | None = None,
        source: str = 'heuristic',
        source_version: str | None = None,
    ) -> bool:
        model = _get_model(entity_type, ValueType.JSON)
        values = {
            "entity_id": entity_id,
            "annotation_key": key,
            "annotation_value": value,
            "confidence": confidence,
            "reason": reason,
            "source": source,
            "source_version": source_version,
        }
        stmt = (
            pg_insert(model)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["entity_id", "annotation_key"],
                set_={
                    "annotation_value": value,
                    "confidence": confidence,
                    "reason": reason,
                    "source": source,
                    "source_version": source_version,
                },
            )
        )
        result = self.session.execute(stmt)
        created = result.rowcount > 0
        self._track(model.__tablename__, created)
        return created

    def write(self, entity_type, entity_id, result):
        """Dispatch to the appropriate typed writer."""
        if result.value_type == ValueType.FLAG:
            return self.write_flag(entity_type, entity_id, result.key, result.confidence, result.reason, result.source, result.source_version)
        if result.value_type == ValueType.STRING:
            return self.write_string(entity_type, entity_id, result.key, str(result.value), result.confidence, result.reason, result.source, result.source_version)
        if result.value_type == ValueType.NUMERIC:
            return self.write_numeric(entity_type, entity_id, result.key, float(result.value), result.confidence, result.reason, result.source, result.source_version)
        if result.value_type == ValueType.JSON:
            return self.write_json(entity_type, entity_id, result.key, result.value, result.confidence, result.reason, result.source, result.source_version)
        raise ValueError(f"Unknown value type: {result.value_type}")

    def _track(self, table: str, created: bool) -> None:
        if table not in self._counts:
            self._counts[table] = 0
        if created:
            self._counts[table] += 1

    @property
    def counts(self):
        return self._counts.copy()


# ============================================================
# Annotation Reader (ORM-based)
# ============================================================

class AnnotationReader:
    """Reads annotations from typed tables using ORM queries."""

    def __init__(self, session: Session):
        self.session = session

    def has_flag(self, entity_type: EntityType, entity_id: UUID, key: str) -> bool:
        model = _get_model(entity_type, ValueType.FLAG)
        return (
            self.session.query(model.id)
            .filter(model.entity_id == entity_id, model.annotation_key == key)
            .first()
        ) is not None

    def get_string(self, entity_type: EntityType, entity_id: UUID, key: str) -> list[str]:
        model = _get_model(entity_type, ValueType.STRING)
        rows = (
            self.session.query(model.annotation_value)
            .filter(model.entity_id == entity_id, model.annotation_key == key)
            .all()
        )
        return [row[0] for row in rows]

    def get_string_single(self, entity_type: EntityType, entity_id: UUID, key: str) -> str | None:
        values = self.get_string(entity_type, entity_id, key)
        return values[0] if values else None

    def get_numeric(self, entity_type: EntityType, entity_id: UUID, key: str) -> list[float]:
        model = _get_model(entity_type, ValueType.NUMERIC)
        rows = (
            self.session.query(model.annotation_value)
            .filter(model.entity_id == entity_id, model.annotation_key == key)
            .all()
        )
        return [float(row[0]) for row in rows]

    def get_json(self, entity_type: EntityType, entity_id: UUID, key: str) -> dict | list | None:
        model = _get_model(entity_type, ValueType.JSON)
        row = (
            self.session.query(model.annotation_value)
            .filter(model.entity_id == entity_id, model.annotation_key == key)
            .first()
        )
        return row[0] if row else None

    def has_annotation_key(self, entity_type: EntityType, entity_id: UUID, key: str) -> bool:
        for vt in ValueType:
            model = _get_model(entity_type, vt)
            hit = (
                self.session.query(model.id)
                .filter(model.entity_id == entity_id, model.annotation_key == key)
                .first()
            )
            if hit is not None:
                return True
        return False

    def find_entities_with_flag(self, entity_type: EntityType, key: str) -> set[UUID]:
        model = _get_model(entity_type, ValueType.FLAG)
        rows = (
            self.session.query(model.entity_id)
            .filter(model.annotation_key == key)
            .all()
        )
        return {row[0] for row in rows}

    def find_entities_with_string(
        self, entity_type: EntityType, key: str, value: str | None = None,
    ) -> set[UUID]:
        model = _get_model(entity_type, ValueType.STRING)
        query = (
            self.session.query(model.entity_id)
            .filter(model.annotation_key == key)
        )
        if value is not None:
            query = query.filter(model.annotation_value == value)
        rows = query.all()
        return {row[0] for row in rows}

    def get_all_keys(self, entity_type: EntityType, entity_id: UUID) -> set[str]:
        """Return the set of annotation keys present for an entity (any value type)."""
        keys: set[str] = set()
        for vt in ValueType:
            model = _get_model(entity_type, vt)
            rows = (
                self.session.query(model.annotation_key)
                .filter(model.entity_id == entity_id)
                .distinct()
                .all()
            )
            keys.update(row[0] for row in rows)
        return keys
