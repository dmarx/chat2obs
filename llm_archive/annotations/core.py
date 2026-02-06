# llm_archive/annotations/core.py
"""
Core annotation infrastructure for typed annotation tables.

This module provides:
- Enum types for annotation value types and entity types
- AnnotationWriter for inserting annotations during ingestion/processing
- Base classes for annotators that iterate over entities

The schema uses separate tables per (entity_type, value_type) combination:
- derived.{entity}_annotations_{value_type}
- e.g., derived.message_annotations_string, derived.prompt_response_annotations_flag
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger


# ============================================================
# Enums
# ============================================================

class EntityType(str, Enum):
    """Supported entity types for annotations."""
    CONTENT_PART = 'content_part'
    MESSAGE = 'message'
    PROMPT_RESPONSE = 'prompt_response'
    DIALOGUE = 'dialogue'


class ValueType(str, Enum):
    """Annotation value types."""
    FLAG = 'flag'       # Key presence = true, no value
    STRING = 'string'   # Text value
    NUMERIC = 'numeric' # Numeric value
    JSON = 'json'       # JSONB value


# ============================================================
# Annotation Result (returned by annotators)
# ============================================================

@dataclass
class AnnotationResult:
    """
    Result from annotation logic.
    
    For FLAG annotations: only key is required
    For STRING/NUMERIC/JSON: key and value are required
    """
    key: str
    value: Any = None  # None for flags, typed for others
    value_type: ValueType = ValueType.STRING  # Inferred if not specified
    confidence: float | None = None
    reason: str | None = None
    source: str = 'heuristic'
    source_version: str | None = None
    
    def __eq__(self, other: object) -> bool:
        """Equality check - compares key, value, and value_type."""
        if not isinstance(other, AnnotationResult):
            return NotImplemented
        return (
            self.key == other.key 
            and self.value == other.value 
            and self.value_type == other.value_type
        )
    
    def __hash__(self) -> int:
        """Hash based on key, value, and value_type."""
        # Convert value to a hashable form if it's a dict/list
        value_hash = self.value
        if isinstance(self.value, dict):
            value_hash = tuple(sorted(self.value.items()))
        elif isinstance(self.value, list):
            value_hash = tuple(self.value)
        return hash((self.key, value_hash, self.value_type))
    
    def __repr__(self) -> str:
        """Compact string representation."""
        if self.value_type == ValueType.FLAG:
            return f"AnnotationResult({self.key!r}, FLAG)"
        return f"AnnotationResult({self.key!r}, {self.value!r}, {self.value_type.value})"


# ============================================================
# Annotation Writer (for ingestion and annotators)
# ============================================================

class AnnotationWriter:
    """
    Writes annotations to the appropriate typed tables.
    
    Used by:
    - Extractors during ingestion (source='ingestion')
    - Annotators during processing (source='heuristic', 'model', etc.)
    
    Handles table routing based on entity_type and value_type.
    Uses upsert semantics (ON CONFLICT DO NOTHING for multi-value,
    ON CONFLICT DO UPDATE for single-value tables).
    """
    
    # Table name templates
    TABLE_TEMPLATE = "derived.{entity}_annotations_{value_type}"
    
    # Tables where (entity_id, key) is unique (single value per key)
    SINGLE_VALUE_TABLES = {ValueType.FLAG, ValueType.JSON}
    
    def __init__(self, session: Session):
        self.session = session
        self._counts: dict[str, int] = {}
    
    def _table_name(self, entity_type: EntityType, value_type: ValueType) -> str:
        """Get the table name for an entity/value type combination."""
        return self.TABLE_TEMPLATE.format(
            entity=entity_type.value,
            value_type=value_type.value,
        )
    
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
        """Write a flag annotation (key presence = true)."""
        table = self._table_name(entity_type, ValueType.FLAG)
        
        result = self.session.execute(
            text(f"""
                INSERT INTO {table} 
                    (entity_id, annotation_key, confidence, reason, source, source_version)
                VALUES 
                    (:entity_id, :key, :confidence, :reason, :source, :source_version)
                ON CONFLICT (entity_id, annotation_key) DO NOTHING
                RETURNING id
            """),
            {
                'entity_id': entity_id,
                'key': key,
                'confidence': confidence,
                'reason': reason,
                'source': source,
                'source_version': source_version,
            }
        )
        created = result.scalar() is not None
        self._track(table, created)
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
        """Write a string annotation."""
        table = self._table_name(entity_type, ValueType.STRING)
        
        result = self.session.execute(
            text(f"""
                INSERT INTO {table} 
                    (entity_id, annotation_key, annotation_value, confidence, reason, source, source_version)
                VALUES 
                    (:entity_id, :key, :value, :confidence, :reason, :source, :source_version)
                ON CONFLICT (entity_id, annotation_key, annotation_value) DO NOTHING
                RETURNING id
            """),
            {
                'entity_id': entity_id,
                'key': key,
                'value': value,
                'confidence': confidence,
                'reason': reason,
                'source': source,
                'source_version': source_version,
            }
        )
        created = result.scalar() is not None
        self._track(table, created)
        return created
    
    def write_numeric(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        key: str,
        value: float | int,
        confidence: float | None = None,
        reason: str | None = None,
        source: str = 'heuristic',
        source_version: str | None = None,
    ) -> bool:
        """Write a numeric annotation."""
        table = self._table_name(entity_type, ValueType.NUMERIC)
        
        result = self.session.execute(
            text(f"""
                INSERT INTO {table} 
                    (entity_id, annotation_key, annotation_value, confidence, reason, source, source_version)
                VALUES 
                    (:entity_id, :key, :value, :confidence, :reason, :source, :source_version)
                ON CONFLICT (entity_id, annotation_key, annotation_value) DO NOTHING
                RETURNING id
            """),
            {
                'entity_id': entity_id,
                'key': key,
                'value': value,
                'confidence': confidence,
                'reason': reason,
                'source': source,
                'source_version': source_version,
            }
        )
        created = result.scalar() is not None
        self._track(table, created)
        return created
    
    def write_json(
        self,
        entity_type: EntityType,
        entity_id: UUID,
        key: str,
        value: dict | list,
        confidence: float | None = None,
        reason: str | None = None,
        source: str = 'heuristic',
        source_version: str | None = None,
    ) -> bool:
        """Write a JSON annotation (single value per key, upserts)."""
        import json
        table = self._table_name(entity_type, ValueType.JSON)
        
        result = self.session.execute(
            text(f"""
                INSERT INTO {table} 
                    (entity_id, annotation_key, annotation_value, confidence, reason, source, source_version)
                VALUES 
                    (:entity_id, :key, CAST(:value AS jsonb), :confidence, :reason, :source, :source_version)
                ON CONFLICT (entity_id, annotation_key) DO UPDATE SET
                    annotation_value = EXCLUDED.annotation_value,
                    confidence = EXCLUDED.confidence,
                    reason = EXCLUDED.reason,
                    source = EXCLUDED.source,
                    source_version = EXCLUDED.source_version,
                    created_at = now()
                RETURNING id
            """),
            {
                'entity_id': entity_id,
                'key': key,
                'value': json.dumps(value),
                'confidence': confidence,
                'reason': reason,
                'source': source,
                'source_version': source_version,
            }
        )
        created = result.scalar() is not None
        self._track(table, created)
        return created
    
    def write(self, entity_type: EntityType, entity_id: UUID, result: AnnotationResult) -> bool:
        """
        Write an annotation from an AnnotationResult.
        
        Dispatches to the appropriate typed write method.
        """
        if result.value_type == ValueType.FLAG:
            return self.write_flag(
                entity_type=entity_type,
                entity_id=entity_id,
                key=result.key,
                confidence=result.confidence,
                reason=result.reason,
                source=result.source,
                source_version=result.source_version,
            )
        elif result.value_type == ValueType.STRING:
            return self.write_string(
                entity_type=entity_type,
                entity_id=entity_id,
                key=result.key,
                value=str(result.value),
                confidence=result.confidence,
                reason=result.reason,
                source=result.source,
                source_version=result.source_version,
            )
        elif result.value_type == ValueType.NUMERIC:
            return self.write_numeric(
                entity_type=entity_type,
                entity_id=entity_id,
                key=result.key,
                value=float(result.value),
                confidence=result.confidence,
                reason=result.reason,
                source=result.source,
                source_version=result.source_version,
            )
        elif result.value_type == ValueType.JSON:
            return self.write_json(
                entity_type=entity_type,
                entity_id=entity_id,
                key=result.key,
                value=result.value,
                confidence=result.confidence,
                reason=result.reason,
                source=result.source,
                source_version=result.source_version,
            )
        else:
            raise ValueError(f"Unknown value type: {result.value_type}")
    
    def _track(self, table: str, created: bool):
        """Track annotation counts."""
        if table not in self._counts:
            self._counts[table] = 0
        if created:
            self._counts[table] += 1
    
    @property
    def counts(self) -> dict[str, int]:
        """Get annotation counts by table."""
        return self._counts.copy()


# ============================================================
# Annotation Reader (for querying)
# ============================================================

class AnnotationReader:
    """
    Reads annotations from the typed tables.
    
    Provides methods for:
    - Checking if an annotation exists
    - Getting annotation values
    - Filtering entities by annotations
    """
    
    TABLE_TEMPLATE = "derived.{entity}_annotations_{value_type}"
    
    def __init__(self, session: Session):
        self.session = session
    
    def _table_name(self, entity_type: EntityType, value_type: ValueType) -> str:
        return self.TABLE_TEMPLATE.format(
            entity=entity_type.value,
            value_type=value_type.value,
        )
    
    def has_flag(self, entity_type: EntityType, entity_id: UUID, key: str) -> bool:
        """Check if entity has a flag annotation."""
        table = self._table_name(entity_type, ValueType.FLAG)
        result = self.session.execute(
            text(f"SELECT 1 FROM {table} WHERE entity_id = :id AND annotation_key = :key"),
            {'id': entity_id, 'key': key}
        )
        return result.scalar() is not None
    
    def get_string(self, entity_type: EntityType, entity_id: UUID, key: str) -> list[str]:
        """Get all string values for a key (multi-value)."""
        table = self._table_name(entity_type, ValueType.STRING)
        result = self.session.execute(
            text(f"SELECT annotation_value FROM {table} WHERE entity_id = :id AND annotation_key = :key"),
            {'id': entity_id, 'key': key}
        )
        return [row[0] for row in result]
    
    def get_string_single(self, entity_type: EntityType, entity_id: UUID, key: str) -> str | None:
        """Get single string value (returns first if multiple)."""
        values = self.get_string(entity_type, entity_id, key)
        return values[0] if values else None
    
    def get_numeric(self, entity_type: EntityType, entity_id: UUID, key: str) -> list[float]:
        """Get all numeric values for a key."""
        table = self._table_name(entity_type, ValueType.NUMERIC)
        result = self.session.execute(
            text(f"SELECT annotation_value FROM {table} WHERE entity_id = :id AND annotation_key = :key"),
            {'id': entity_id, 'key': key}
        )
        return [float(row[0]) for row in result]
    
    def get_json(self, entity_type: EntityType, entity_id: UUID, key: str) -> dict | list | None:
        """Get JSON value for a key (single value)."""
        table = self._table_name(entity_type, ValueType.JSON)
        result = self.session.execute(
            text(f"SELECT annotation_value FROM {table} WHERE entity_id = :id AND annotation_key = :key"),
            {'id': entity_id, 'key': key}
        )
        row = result.fetchone()
        return row[0] if row else None
    
    def get_all_keys(self, entity_type: EntityType, entity_id: UUID) -> dict[str, list[Any]]:
        """Get all annotations for an entity, grouped by key."""
        all_table = f"derived.{entity_type.value}_annotations_all"
        result = self.session.execute(
            text(f"SELECT annotation_key, annotation_value, value_type FROM {all_table} WHERE entity_id = :id"),
            {'id': entity_id}
        )
        
        annotations: dict[str, list[Any]] = {}
        for key, value, value_type in result:
            if key not in annotations:
                annotations[key] = []
            if value_type == 'flag':
                annotations[key].append(True)
            else:
                annotations[key].append(value)
        
        return annotations
    
    def find_entities_with_flag(self, entity_type: EntityType, key: str) -> list[UUID]:
        """Find all entity IDs that have a specific flag."""
        table = self._table_name(entity_type, ValueType.FLAG)
        result = self.session.execute(
            text(f"SELECT entity_id FROM {table} WHERE annotation_key = :key"),
            {'key': key}
        )
        return [row[0] for row in result]
    
    def find_entities_with_string(
        self, 
        entity_type: EntityType, 
        key: str, 
        value: str | None = None
    ) -> list[UUID]:
        """Find entity IDs with a string annotation (optionally matching value)."""
        table = self._table_name(entity_type, ValueType.STRING)
        if value is not None:
            result = self.session.execute(
                text(f"SELECT entity_id FROM {table} WHERE annotation_key = :key AND annotation_value = :value"),
                {'key': key, 'value': value}
            )
        else:
            result = self.session.execute(
                text(f"SELECT DISTINCT entity_id FROM {table} WHERE annotation_key = :key"),
                {'key': key}
            )
        return [row[0] for row in result]
