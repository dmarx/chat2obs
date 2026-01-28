# llm_archive/annotators/base.py
"""Base annotation infrastructure."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func as sql_func
from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import Annotation
from llm_archive.models.derived import AnnotatorCursor


class Annotator(ABC):
    """
    Base class for annotation generators.
    
    Annotators analyze entities and produce annotations stored in
    the derived.annotations table.
    
    Supports incremental processing via cursor tracking:
    - Each annotator+version tracks a "high water mark" (cursor)
    - Only entities created after the cursor are processed
    - Bump VERSION to force reprocessing all entities
    
    Subclass and implement:
    - ANNOTATION_TYPE: Type of annotation ('tag', 'title', 'feature', etc.)
    - ENTITY_TYPE: Target entity type ('message', 'exchange', 'dialogue')
    - SOURCE: Provenance ('heuristic', 'model', 'manual')
    - VERSION: Version string - bump this to reprocess all entities
    - compute(): Main logic to generate annotations
    """
    
    # Override in subclass
    ANNOTATION_TYPE: str = None
    ENTITY_TYPE: str = None
    SOURCE: str = 'heuristic'
    VERSION: str = '1.0'
    
    def __init__(self, session: Session):
        self.session = session
        self._cursor: AnnotatorCursor | None = None
        self._max_created_at: datetime | None = None
        self._entities_processed: int = 0
        self._annotations_created: int = 0
    
    @property
    def name(self) -> str:
        """Annotator name for cursor tracking."""
        return self.__class__.__name__
    
    def get_cursor(self) -> datetime | None:
        """
        Get the high water mark for this annotator version.
        
        Returns the timestamp of the last processed entity, or None if
        this annotator version hasn't run before.
        """
        cursor = (
            self.session.query(AnnotatorCursor)
            .filter(AnnotatorCursor.annotator_name == self.name)
            .filter(AnnotatorCursor.annotator_version == self.VERSION)
            .filter(AnnotatorCursor.entity_type == self.ENTITY_TYPE)
            .first()
        )
        
        self._cursor = cursor
        return cursor.high_water_mark if cursor else None
    
    def update_cursor(self, high_water_mark: datetime, entities_processed: int, annotations_created: int):
        """
        Update the cursor position after processing.
        
        Args:
            high_water_mark: The max created_at timestamp seen
            entities_processed: Number of entities processed in this run
            annotations_created: Number of annotations created in this run
        """
        if self._cursor:
            # Update existing cursor
            self._cursor.high_water_mark = high_water_mark
            self._cursor.entities_processed += entities_processed
            self._cursor.annotations_created += annotations_created
            self._cursor.updated_at = datetime.now(timezone.utc)
        else:
            # Create new cursor
            cursor = AnnotatorCursor(
                annotator_name=self.name,
                annotator_version=self.VERSION,
                entity_type=self.ENTITY_TYPE,
                high_water_mark=high_water_mark,
                entities_processed=entities_processed,
                annotations_created=annotations_created,
            )
            self.session.add(cursor)
    
    def track_entity(self, created_at: datetime | None):
        """Track an entity being processed for cursor update."""
        self._entities_processed += 1
        if created_at and (self._max_created_at is None or created_at > self._max_created_at):
            self._max_created_at = created_at
    
    def finalize_cursor(self):
        """Finalize cursor update after processing."""
        if self._max_created_at:
            self.update_cursor(
                high_water_mark=self._max_created_at,
                entities_processed=self._entities_processed,
                annotations_created=self._annotations_created,
            )
    
    @abstractmethod
    def compute(self) -> int:
        """
        Compute and persist annotations.
        
        Implementations should:
        1. Call get_cursor() to get the high water mark
        2. Query only entities with created_at > cursor (or all if cursor is None)
        3. Call track_entity(created_at) for each entity processed
        4. Call add_annotation() for each annotation
        5. Call finalize_cursor() at the end
        
        Returns count of annotations created/updated.
        """
        pass
    
    def add_annotation(
        self,
        entity_id: UUID,
        value: str,
        key: str | None = None,
        confidence: float | None = None,
        data: dict | None = None,
    ) -> bool:
        """
        Add or update an annotation.
        
        Args:
            entity_id: Target entity UUID
            value: Annotation value (required)
            key: Optional sub-key for namespacing
            confidence: Optional confidence score (0.0-1.0)
            data: Optional additional structured data
        
        Returns:
            True if a new annotation was created, False if existing.
        """
        # Check for existing active annotation
        existing = (
            self.session.query(Annotation)
            .filter(Annotation.entity_type == self.ENTITY_TYPE)
            .filter(Annotation.entity_id == entity_id)
            .filter(Annotation.annotation_type == self.ANNOTATION_TYPE)
            .filter(Annotation.annotation_key == key if key else Annotation.annotation_key.is_(None))
            .filter(Annotation.annotation_value == value)
            .filter(Annotation.superseded_at.is_(None))
            .first()
        )
        
        if existing:
            # Update if confidence changed significantly
            if confidence is not None and existing.confidence != confidence:
                if abs((existing.confidence or 0) - confidence) > 0.01:
                    existing.confidence = confidence
                    existing.annotation_data = data
            return False
        
        # Create new annotation
        annotation = Annotation(
            entity_type=self.ENTITY_TYPE,
            entity_id=entity_id,
            annotation_type=self.ANNOTATION_TYPE,
            annotation_key=key,
            annotation_value=value,
            annotation_data=data,
            confidence=confidence,
            source=self.SOURCE,
            source_version=self.VERSION,
        )
        self.session.add(annotation)
        self._annotations_created += 1
        return True
    
    def supersede_annotation(
        self,
        entity_id: UUID,
        value: str,
        key: str | None = None,
        new_annotation_id: UUID | None = None,
    ):
        """Mark an existing annotation as superseded."""
        existing = (
            self.session.query(Annotation)
            .filter(Annotation.entity_type == self.ENTITY_TYPE)
            .filter(Annotation.entity_id == entity_id)
            .filter(Annotation.annotation_type == self.ANNOTATION_TYPE)
            .filter(Annotation.annotation_key == key if key else Annotation.annotation_key.is_(None))
            .filter(Annotation.annotation_value == value)
            .filter(Annotation.superseded_at.is_(None))
            .first()
        )
        
        if existing:
            existing.superseded_at = datetime.now(timezone.utc)
            existing.superseded_by = new_annotation_id


class AnnotationManager:
    """
    Manages annotation operations and annotator execution.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.annotators: list[Annotator] = []
    
    def register(self, annotator_class: type[Annotator]):
        """Register an annotator class."""
        annotator = annotator_class(self.session)
        self.annotators.append(annotator)
    
    def run_all(self) -> dict[str, int]:
        """Run all registered annotators."""
        results = {}
        
        for annotator in self.annotators:
            name = annotator.__class__.__name__
            try:
                count = annotator.compute()
                results[name] = count
                logger.info(f"{name}: {count} annotations")
            except Exception as e:
                logger.error(f"{name} failed: {e}")
                results[name] = -1
                self.session.rollback()
        
        self.session.commit()
        return results
    
    def get_annotations(
        self,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        annotation_type: str | None = None,
        active_only: bool = True,
    ) -> list[Annotation]:
        """Query annotations with filters."""
        query = self.session.query(Annotation)
        
        if entity_type:
            query = query.filter(Annotation.entity_type == entity_type)
        if entity_id:
            query = query.filter(Annotation.entity_id == entity_id)
        if annotation_type:
            query = query.filter(Annotation.annotation_type == annotation_type)
        if active_only:
            query = query.filter(Annotation.superseded_at.is_(None))
        
        return query.all()
    
    def get_entity_annotations(self, entity_type: str, entity_id: UUID) -> dict[str, Any]:
        """Get all active annotations for an entity as a dict."""
        annotations = self.get_annotations(entity_type=entity_type, entity_id=entity_id)
        
        result = {}
        for ann in annotations:
            key_parts = [ann.annotation_type]
            if ann.annotation_key:
                key_parts.append(ann.annotation_key)
            key_parts.append(ann.annotation_value)
            key = ':'.join(key_parts)
            
            result[key] = {
                'confidence': ann.confidence,
                'source': ann.source,
                'data': ann.annotation_data,
            }
        
        return result
    
    def get_tags(self, entity_type: str, entity_id: UUID) -> list[str]:
        """Get tag values for an entity."""
        annotations = self.get_annotations(
            entity_type=entity_type, 
            entity_id=entity_id,
            annotation_type='tag',
        )
        return [ann.annotation_value for ann in annotations]
    
    def get_title(self, entity_type: str, entity_id: UUID) -> str | None:
        """Get title annotation for an entity."""
        annotations = self.get_annotations(
            entity_type=entity_type,
            entity_id=entity_id,
            annotation_type='title',
        )
        return annotations[0].annotation_value if annotations else None
    
    def clear_annotations(
        self,
        entity_type: str | None = None,
        annotation_type: str | None = None,
        source: str | None = None,
    ):
        """Clear annotations matching filters (hard delete)."""
        query = self.session.query(Annotation)
        
        if entity_type:
            query = query.filter(Annotation.entity_type == entity_type)
        if annotation_type:
            query = query.filter(Annotation.annotation_type == annotation_type)
        if source:
            query = query.filter(Annotation.source == source)
        
        count = query.delete()
        logger.info(f"Deleted {count} annotations")
        return count