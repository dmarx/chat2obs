# llm_archive/annotators/base.py
"""
Base annotator class with cursor management and runtime tracking.

This module provides the foundation for all annotators, handling:
- Cursor-based incremental processing
- Runtime tracking
- Standard annotation workflow
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator
from uuid import UUID

from loguru import logger
from sqlalchemy.orm import Session

from llm_archive.annotations.core import (
    AnnotationResult,
    AnnotationWriter,
    AnnotationReader,
    EntityType,
)
from llm_archive.annotations.cursor import CursorManager, AnnotatorCursor


class BaseAnnotator(ABC):
    """
    Base class for all annotators with cursor management and runtime tracking.
    
    Subclasses must implement:
    - annotate(): Core annotation logic
    - _iter_entities(): Iterator over entities to process
    
    The base class handles:
    - Cursor management (get/update)
    - Runtime tracking
    - Standard compute() workflow
    """
    
    # Subclass must define
    ENTITY_TYPE: EntityType = None
    ANNOTATION_KEY: str = None
    VERSION: str = '1.0'
    PRIORITY: int = 50
    SOURCE: str = 'heuristic'
    
    def __init__(self, session: Session):
        self.session = session
        self.writer = AnnotationWriter(session)
        self.reader = AnnotationReader(session)
        self.cursor_manager = CursorManager(session)
        
        # Validate required class attributes
        if self.ENTITY_TYPE is None:
            raise ValueError(f"{self.__class__.__name__} must define ENTITY_TYPE")
        if self.ANNOTATION_KEY is None:
            raise ValueError(f"{self.__class__.__name__} must define ANNOTATION_KEY")
    
    def compute(self) -> dict[str, int | float]:
        """
        Run annotation with cursor tracking and runtime measurement.
        
        Returns:
            Dict with stats:
            - entities_processed: Number of entities processed in this run
            - annotations_created: Number of annotations created in this run
            - runtime_seconds: Runtime for this run
            - cumulative_runtime_seconds: Total runtime across all runs
        """
        # Start timing
        start_time = time.time()
        
        # Get cursor
        cursor = self._get_cursor()
        
        # Track stats for this run
        entities_processed = 0
        annotations_created = 0
        latest_created_at = cursor.high_water_mark
        
        # Process entities
        for entity_data in self._iter_entities_after(cursor.high_water_mark):
            # Run annotation logic
            results = self.annotate(entity_data)
            
            # Write results
            for result in results:
                if self._write_result(entity_data, result):
                    annotations_created += 1
            
            entities_processed += 1
            
            # Track latest timestamp
            if hasattr(entity_data, 'created_at') and entity_data.created_at:
                if entity_data.created_at > latest_created_at:
                    latest_created_at = entity_data.created_at
        
        # Calculate runtime
        runtime_seconds = time.time() - start_time
        
        # Update cursor
        self.cursor_manager.update_cursor(
            cursor=cursor,
            entities_processed=entities_processed,
            annotations_created=annotations_created,
            new_high_water_mark=latest_created_at,
            runtime_seconds=runtime_seconds,
        )
        
        return {
            'entities_processed': entities_processed,
            'annotations_created': annotations_created,
            'runtime_seconds': runtime_seconds,
            'cumulative_runtime_seconds': cursor.cumulative_runtime_seconds + runtime_seconds,
        }
    
    def _get_cursor(self) -> AnnotatorCursor:
        """Get or create cursor for this annotator."""
        return self.cursor_manager.get_cursor(
            annotator_name=self.__class__.__name__,
            annotator_version=self.VERSION,
            entity_type=self.ENTITY_TYPE,
        )
    
    @abstractmethod
    def _iter_entities_after(self, high_water_mark: datetime) -> Iterator:
        """
        Iterate over entities created after the high-water mark.
        
        Must be implemented by subclass.
        
        Args:
            high_water_mark: Only return entities created after this timestamp
            
        Yields:
            Entity data objects
        """
        pass
    
    @abstractmethod
    def annotate(self, entity_data) -> list[AnnotationResult]:
        """
        Run annotation logic on a single entity.
        
        Must be implemented by subclass.
        
        Args:
            entity_data: Entity-specific data object
            
        Returns:
            List of AnnotationResult objects
        """
        pass
    
    @abstractmethod
    def _write_result(self, entity_data, result: AnnotationResult) -> bool:
        """
        Write annotation result to database.
        
        Must be implemented by subclass to extract entity_id from entity_data.
        
        Args:
            entity_data: Entity-specific data object
            result: Annotation result to write
            
        Returns:
            True if annotation was created, False if it already existed
        """
        pass
