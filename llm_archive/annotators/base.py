# llm_archive/annotators/base.py
"""Abstract base class for all annotators with cursor-based incremental processing.

Provides:
- Cursor creation / retrieval / update
- Incremental entity iteration (only entities newer than high_water_mark)
- Cumulative statistics (entities_processed, annotations_created, runtime)
- Consistent logging

Subclass hierarchy:
    BaseAnnotator (this file)
    ├── ContentPartAnnotator   (content_part.py)
    │   ├── CodeBlockAnnotator
    │   └── ...
    └── PromptResponseAnnotator (prompt_response.py)
        ├── WikiCandidateAnnotator
        └── ...
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Generic, Iterator, TypeVar
from uuid import UUID

from loguru import logger
from sqlalchemy.orm import Session

from llm_archive.annotations.core import (
    AnnotationResult,
    AnnotationWriter,
    EntityType,
    ValueType,
)
from llm_archive.models.derived import AnnotatorCursor

# Type variable for the dataclass each annotator family passes around.
EntityDataT = TypeVar("EntityDataT")

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class BaseAnnotator(ABC, Generic[EntityDataT]):
    """Abstract base for all annotators.

    Concrete subclasses must define:
        ENTITY_TYPE, ANNOTATION_KEY, and implement
        _iter_entities_after(), _entity_id(), _created_at(), annotate().

    Class attributes (override in subclass):
        ENTITY_TYPE      – EntityType enum member
        ANNOTATION_KEY   – primary annotation key produced
        VALUE_TYPE       – default ValueType for results
        PRIORITY         – higher runs first (descending sort)
        VERSION          – bump to force reprocessing
        SOURCE           – e.g. 'heuristic', 'model', 'ingestion'
    """

    # -- metadata (subclass must set ENTITY_TYPE and ANNOTATION_KEY) ------
    ENTITY_TYPE: EntityType = None          # type: ignore[assignment]
    ANNOTATION_KEY: str = ""
    VALUE_TYPE: ValueType = ValueType.STRING
    PRIORITY: int = 50
    VERSION: str = "1.0"
    SOURCE: str = "heuristic"

    def __init__(self, session: Session) -> None:
        self.session = session
        self.writer = AnnotationWriter(session)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute(self) -> int:
        """Run annotation with cursor-based incremental processing.

        Returns the number of annotations created this run.
        """
        start = time.monotonic()
        cursor = self._get_or_create_cursor()

        logger.info(
            "{name} v{ver} starting  hwm={hwm}  cumulative_processed={p}",
            name=self.__class__.__name__,
            ver=self.VERSION,
            hwm=cursor.high_water_mark,
            p=cursor.entities_processed,
        )

        annotations_created = 0
        entities_processed = 0
        latest_created_at = cursor.high_water_mark

        for data in self._iter_entities_after(cursor.high_water_mark):
            entity_id = self._entity_id(data)
            created_at = self._created_at(data)

            results = self.annotate(data)

            for result in results:
                if self._write_result(entity_id, result):
                    annotations_created += 1

            entities_processed += 1

            if created_at and created_at > latest_created_at:
                latest_created_at = created_at

        elapsed = time.monotonic() - start
        self._update_cursor(
            cursor,
            entities_processed=entities_processed,
            annotations_created=annotations_created,
            new_high_water_mark=latest_created_at,
            elapsed_seconds=elapsed,
        )

        logger.info(
            "{name} v{ver} finished  processed={p} annotations={a} elapsed={e:.2f}s",
            name=self.__class__.__name__,
            ver=self.VERSION,
            p=entities_processed,
            a=annotations_created,
            e=elapsed,
        )
        return annotations_created

    # ------------------------------------------------------------------
    # Cursor management
    # ------------------------------------------------------------------

    def _get_or_create_cursor(self) -> AnnotatorCursor:
        """Retrieve or create cursor for this annotator + version + entity_type."""
        cursor = (
            self.session.query(AnnotatorCursor)
            .filter_by(
                annotator_name=self.__class__.__name__,
                annotator_version=self.VERSION,
                entity_type=self.ENTITY_TYPE.value,
            )
            .one_or_none()
        )
        if cursor is not None:
            return cursor

        cursor = AnnotatorCursor(
            annotator_name=self.__class__.__name__,
            annotator_version=self.VERSION,
            entity_type=self.ENTITY_TYPE.value,
            high_water_mark=_EPOCH,
            entities_processed=0,
            annotations_created=0,
            cumulative_runtime_seconds=0.0,
        )
        self.session.add(cursor)
        self.session.flush()
        logger.debug("Created new cursor for {}", self.__class__.__name__)
        return cursor

    def _update_cursor(
        self,
        cursor: AnnotatorCursor,
        *,
        entities_processed: int,
        annotations_created: int,
        new_high_water_mark: datetime,
        elapsed_seconds: float,
    ) -> None:
        """Advance cursor state after a run."""
        cursor.high_water_mark = new_high_water_mark
        cursor.entities_processed += entities_processed
        cursor.annotations_created += annotations_created
        cursor.cumulative_runtime_seconds += elapsed_seconds
        cursor.updated_at = datetime.now(timezone.utc)
        self.session.flush()

    # ------------------------------------------------------------------
    # Result writing (delegates to AnnotationWriter)
    # ------------------------------------------------------------------

    def _write_result(self, entity_id: UUID, result: AnnotationResult) -> bool:
        """Write a single annotation result."""
        value_type = result.value_type or self.VALUE_TYPE

        if value_type == ValueType.FLAG:
            return self.writer.write_flag(
                entity_type=self.ENTITY_TYPE,
                entity_id=entity_id,
                key=result.key,
                confidence=result.confidence,
                reason=result.reason,
                source=result.source or self.SOURCE,
                source_version=result.source_version or self.VERSION,
            )
        if value_type == ValueType.STRING:
            return self.writer.write_string(
                entity_type=self.ENTITY_TYPE,
                entity_id=entity_id,
                key=result.key,
                value=str(result.value),
                confidence=result.confidence,
                reason=result.reason,
                source=result.source or self.SOURCE,
                source_version=result.source_version or self.VERSION,
            )
        if value_type == ValueType.NUMERIC:
            return self.writer.write_numeric(
                entity_type=self.ENTITY_TYPE,
                entity_id=entity_id,
                key=result.key,
                value=float(result.value),
                confidence=result.confidence,
                reason=result.reason,
                source=result.source or self.SOURCE,
                source_version=result.source_version or self.VERSION,
            )
        if value_type == ValueType.JSON:
            return self.writer.write_json(
                entity_type=self.ENTITY_TYPE,
                entity_id=entity_id,
                key=result.key,
                value=result.value,
                confidence=result.confidence,
                reason=result.reason,
                source=result.source or self.SOURCE,
                source_version=result.source_version or self.VERSION,
            )
        return False

    # ------------------------------------------------------------------
    # Abstract interface — concrete annotators must implement
    # ------------------------------------------------------------------

    @abstractmethod
    def _iter_entities_after(self, after: datetime) -> Iterator[EntityDataT]:
        """Yield entities whose created_at > *after*, ordered by created_at."""
        ...

    @abstractmethod
    def _entity_id(self, data: EntityDataT) -> UUID:
        """Extract the primary-key UUID from entity data."""
        ...

    @abstractmethod
    def _created_at(self, data: EntityDataT) -> datetime | None:
        """Extract the created_at timestamp from entity data."""
        ...

    @abstractmethod
    def annotate(self, data: EntityDataT) -> list[AnnotationResult]:
        """Produce annotations for a single entity.

        Returns an empty list when no annotation applies.
        """
        ...
