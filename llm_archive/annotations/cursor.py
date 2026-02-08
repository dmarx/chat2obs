# llm_archive/annotations/cursor.py
"""
Cursor management for incremental annotation processing.

Tracks the high-water mark (last processed timestamp) and statistics
for each annotator version, including cumulative runtime.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from llm_archive.annotations.core import EntityType


@dataclass
class AnnotatorCursor:
    """
    Cursor tracking state for an annotator version.
    
    Each unique (annotator_name, annotator_version, entity_type) 
    combination gets its own cursor.
    """
    
    id: UUID
    annotator_name: str
    annotator_version: str
    entity_type: str
    high_water_mark: datetime
    entities_processed: int
    annotations_created: int
    cumulative_runtime_seconds: float
    updated_at: datetime


class CursorManager:
    """
    Manages annotator cursors for incremental processing.
    
    Provides methods to:
    - Get or create cursors
    - Update cursor state after processing
    - Track cumulative runtime across runs
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_cursor(
        self,
        annotator_name: str,
        annotator_version: str,
        entity_type: EntityType | str,
    ) -> AnnotatorCursor:
        """
        Get or create cursor for an annotator version.
        
        If no cursor exists, creates one with high_water_mark set to epoch.
        
        Args:
            annotator_name: Name of the annotator class
            annotator_version: Version string from annotator
            entity_type: Entity type being processed
            
        Returns:
            AnnotatorCursor with current state
        """
        if isinstance(entity_type, EntityType):
            entity_type = entity_type.value
        
        # Try to get existing cursor
        result = self.session.execute(
            text("""
                SELECT 
                    id,
                    annotator_name,
                    annotator_version,
                    entity_type,
                    high_water_mark,
                    entities_processed,
                    annotations_created,
                    COALESCE(cumulative_runtime_seconds, 0.0) as cumulative_runtime_seconds,
                    updated_at
                FROM derived.annotator_cursors
                WHERE annotator_name = :name
                  AND annotator_version = :version
                  AND entity_type = :entity_type
            """),
            {
                'name': annotator_name,
                'version': annotator_version,
                'entity_type': entity_type,
            }
        ).fetchone()
        
        if result:
            return AnnotatorCursor(
                id=result.id,
                annotator_name=result.annotator_name,
                annotator_version=result.annotator_version,
                entity_type=result.entity_type,
                high_water_mark=result.high_water_mark,
                entities_processed=result.entities_processed,
                annotations_created=result.annotations_created,
                cumulative_runtime_seconds=result.cumulative_runtime_seconds,
                updated_at=result.updated_at,
            )
        
        # Create new cursor at epoch
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        
        result = self.session.execute(
            text("""
                INSERT INTO derived.annotator_cursors
                    (annotator_name, annotator_version, entity_type, high_water_mark,
                     entities_processed, annotations_created, cumulative_runtime_seconds)
                VALUES 
                    (:name, :version, :entity_type, :high_water_mark, 0, 0, 0.0)
                RETURNING id, updated_at
            """),
            {
                'name': annotator_name,
                'version': annotator_version,
                'entity_type': entity_type,
                'high_water_mark': epoch,
            }
        )
        row = result.fetchone()
        
        logger.info(
            f"Created cursor for {annotator_name} v{annotator_version} ({entity_type})"
        )
        
        return AnnotatorCursor(
            id=row.id,
            annotator_name=annotator_name,
            annotator_version=annotator_version,
            entity_type=entity_type,
            high_water_mark=epoch,
            entities_processed=0,
            annotations_created=0,
            cumulative_runtime_seconds=0.0,
            updated_at=row.updated_at,
        )
    
    def update_cursor(
        self,
        cursor: AnnotatorCursor,
        entities_processed: int,
        annotations_created: int,
        new_high_water_mark: datetime,
        runtime_seconds: float,
    ) -> None:
        """
        Update cursor with new processing stats.
        
        Args:
            cursor: Existing cursor to update
            entities_processed: Number of entities processed in this run
            annotations_created: Number of annotations created in this run
            new_high_water_mark: New timestamp high-water mark
            runtime_seconds: Runtime for this processing run in seconds
        """
        # Calculate new cumulative values
        new_entities_total = cursor.entities_processed + entities_processed
        new_annotations_total = cursor.annotations_created + annotations_created
        new_runtime_total = cursor.cumulative_runtime_seconds + runtime_seconds
        
        self.session.execute(
            text("""
                UPDATE derived.annotator_cursors
                SET high_water_mark = :high_water_mark,
                    entities_processed = :entities_processed,
                    annotations_created = :annotations_created,
                    cumulative_runtime_seconds = :cumulative_runtime_seconds,
                    updated_at = now()
                WHERE id = :cursor_id
            """),
            {
                'cursor_id': cursor.id,
                'high_water_mark': new_high_water_mark,
                'entities_processed': new_entities_total,
                'annotations_created': new_annotations_total,
                'cumulative_runtime_seconds': new_runtime_total,
            }
        )
        
        logger.info(
            f"Updated cursor for {cursor.annotator_name} v{cursor.annotator_version}: "
            f"+{entities_processed} entities, +{annotations_created} annotations, "
            f"+{runtime_seconds:.2f}s (total: {new_runtime_total:.2f}s)"
        )
    
    def clear_cursor(
        self,
        annotator_name: str,
        annotator_version: str,
        entity_type: EntityType | str,
    ) -> None:
        """
        Delete a cursor, forcing full reprocessing on next run.
        
        Args:
            annotator_name: Name of the annotator class
            annotator_version: Version string from annotator
            entity_type: Entity type being processed
        """
        if isinstance(entity_type, EntityType):
            entity_type = entity_type.value
        
        self.session.execute(
            text("""
                DELETE FROM derived.annotator_cursors
                WHERE annotator_name = :name
                  AND annotator_version = :version
                  AND entity_type = :entity_type
            """),
            {
                'name': annotator_name,
                'version': annotator_version,
                'entity_type': entity_type,
            }
        )
        
        logger.info(
            f"Cleared cursor for {annotator_name} v{annotator_version} ({entity_type})"
        )
    
    def get_all_cursors(self) -> list[AnnotatorCursor]:
        """
        Get all cursors for diagnostics/monitoring.
        
        Returns:
            List of all AnnotatorCursor objects
        """
        result = self.session.execute(
            text("""
                SELECT 
                    id,
                    annotator_name,
                    annotator_version,
                    entity_type,
                    high_water_mark,
                    entities_processed,
                    annotations_created,
                    COALESCE(cumulative_runtime_seconds, 0.0) as cumulative_runtime_seconds,
                    updated_at
                FROM derived.annotator_cursors
                ORDER BY cumulative_runtime_seconds DESC
            """)
        ).fetchall()
        
        return [
            AnnotatorCursor(
                id=row.id,
                annotator_name=row.annotator_name,
                annotator_version=row.annotator_version,
                entity_type=row.entity_type,
                high_water_mark=row.high_water_mark,
                entities_processed=row.entities_processed,
                annotations_created=row.annotations_created,
                cumulative_runtime_seconds=row.cumulative_runtime_seconds,
                updated_at=row.updated_at,
            )
            for row in result
        ]
