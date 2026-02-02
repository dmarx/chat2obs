# llm_archive/annotators/base.py
"""Base annotation infrastructure with modular, extensible design."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterator
from uuid import UUID

from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import Annotation
from llm_archive.models.derived import AnnotatorCursor


# ============================================================
# Annotation Result
# ============================================================

@dataclass
class AnnotationResult:
    """Result from annotation logic - what to annotate."""
    value: str
    key: str | None = None
    confidence: float | None = None
    data: dict | None = None


# ============================================================
# Base Annotator
# ============================================================

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
        """Update the cursor position after processing."""
        if self._cursor:
            self._cursor.high_water_mark = high_water_mark
            self._cursor.entities_processed += entities_processed
            self._cursor.annotations_created += annotations_created
            self._cursor.updated_at = datetime.now(timezone.utc)
        else:
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
        
        Returns True if a new annotation was created, False if existing.
        """
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
            if confidence is not None and existing.confidence != confidence:
                if abs((existing.confidence or 0) - confidence) > 0.01:
                    existing.confidence = confidence
                    existing.annotation_data = data
            return False
        
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
    
    def add_result(self, entity_id: UUID, result: AnnotationResult) -> bool:
        """Add annotation from an AnnotationResult."""
        return self.add_annotation(
            entity_id=entity_id,
            value=result.value,
            key=result.key,
            confidence=result.confidence,
            data=result.data,
        )
    
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


# ============================================================
# Message Text Annotator
# ============================================================

@dataclass
class MessageTextData:
    """Data passed to message annotation logic."""
    message_id: UUID
    text: str
    created_at: datetime | None
    role: str | None = None


class MessageTextAnnotator(Annotator):
    """
    Base class for annotating messages based on text content.
    
    Handles:
    - Querying ContentPart joined to Message
    - Grouping text parts by message
    - Cursor filtering
    - Entity iteration
    
    Subclass and implement:
    - annotate(data: MessageTextData) -> list[AnnotationResult]
    
    Optionally override:
    - ROLE_FILTER: Limit to 'user' or 'assistant' (None = all)
    """
    
    ENTITY_TYPE = 'message'
    ROLE_FILTER: str | None = None  # 'user', 'assistant', or None
    
    def compute(self) -> int:
        """Run annotation over all matching messages."""
        count = 0
        
        for data in self._iter_messages():
            self.track_entity(data.created_at)
            
            results = self.annotate(data)
            for result in results:
                if self.add_result(data.message_id, result):
                    count += 1
        
        self.finalize_cursor()
        return count
    
    def _iter_messages(self) -> Iterator[MessageTextData]:
        """Iterate over messages with grouped text content."""
        from llm_archive.models import Message, ContentPart
        
        cursor = self.get_cursor()
        
        query = (
            self.session.query(
                ContentPart.message_id,
                ContentPart.text_content,
                Message.created_at,
                Message.role,
            )
            .join(Message)
            .filter(Message.deleted_at.is_(None))
            .filter(ContentPart.part_type == 'text')
            .filter(ContentPart.text_content.isnot(None))
        )
        
        if self.ROLE_FILTER:
            query = query.filter(Message.role == self.ROLE_FILTER)
        
        if cursor:
            query = query.filter(Message.created_at > cursor)
        
        # Group by message
        message_data: dict[UUID, dict] = {}
        for msg_id, text, created_at, role in query.all():
            if msg_id not in message_data:
                message_data[msg_id] = {
                    'texts': [],
                    'created_at': created_at,
                    'role': role,
                }
            message_data[msg_id]['texts'].append(text)
        
        for msg_id, data in message_data.items():
            yield MessageTextData(
                message_id=msg_id,
                text='\n'.join(data['texts']),
                created_at=data['created_at'],
                role=data['role'],
            )
    
    @abstractmethod
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        """
        Analyze message text and return annotations to create.
        
        Args:
            data: Message data including id, combined text, timestamp, role
            
        Returns:
            List of AnnotationResult objects (empty list if no match)
        """
        pass


# ============================================================
# Exchange Annotator
# ============================================================

@dataclass
class ExchangeData:
    """Data passed to exchange annotation logic."""
    exchange_id: UUID
    user_text: str | None
    assistant_text: str | None
    user_word_count: int | None
    assistant_word_count: int | None
    created_at: datetime | None


class ExchangeAnnotator(Annotator):
    """
    Base class for annotating exchanges.
    
    Handles:
    - Querying Exchange joined to ExchangeContent
    - Cursor filtering
    - Entity iteration
    
    Subclass and implement:
    - annotate(data: ExchangeData) -> list[AnnotationResult]
    """
    
    ENTITY_TYPE = 'exchange'
    
    def compute(self) -> int:
        """Run annotation over all exchanges."""
        count = 0
        
        for data in self._iter_exchanges():
            self.track_entity(data.created_at)
            
            results = self.annotate(data)
            for result in results:
                if self.add_result(data.exchange_id, result):
                    count += 1
        
        self.finalize_cursor()
        return count
    
    def _iter_exchanges(self) -> Iterator[ExchangeData]:
        """Iterate over exchanges with content."""
        from llm_archive.models import Exchange, ExchangeContent
        
        cursor = self.get_cursor()
        
        query = (
            self.session.query(Exchange, ExchangeContent)
            .join(ExchangeContent)
        )
        
        if cursor:
            query = query.filter(Exchange.created_at > cursor)
        
        for exchange, content in query.all():
            yield ExchangeData(
                exchange_id=exchange.id,
                user_text=content.user_text,
                assistant_text=content.assistant_text,
                user_word_count=content.user_word_count,
                assistant_word_count=content.assistant_word_count,
                created_at=exchange.created_at,
            )
    
    @abstractmethod
    def annotate(self, data: ExchangeData) -> list[AnnotationResult]:
        """
        Analyze exchange and return annotations to create.
        
        Args:
            data: Exchange data including texts and word counts
            
        Returns:
            List of AnnotationResult objects (empty list if no match)
        """
        pass


# ============================================================
# Dialogue Annotator
# ============================================================

@dataclass
class DialogueData:
    """Data passed to dialogue annotation logic."""
    dialogue_id: UUID
    source: str
    title: str | None
    exchange_count: int
    message_count: int
    user_message_count: int
    assistant_message_count: int
    user_texts: list[str]
    assistant_texts: list[str]
    user_word_counts: list[int]
    assistant_word_counts: list[int]
    created_at: datetime | None
    first_user_text: str | None = None
    first_assistant_text: str | None = None


class DialogueAnnotator(Annotator):
    """
    Base class for annotating dialogues with aggregate statistics.
    
    Handles:
    - Querying Dialogue with related exchanges and content
    - Computing aggregate statistics across the dialogue
    - Cursor filtering
    - Entity iteration
    
    Subclass and implement:
    - annotate(data: DialogueData) -> list[AnnotationResult]
    """
    
    ENTITY_TYPE = 'dialogue'
    
    def compute(self) -> int:
        """Run annotation over all dialogues."""
        count = 0
        
        for data in self._iter_dialogues():
            self.track_entity(data.created_at)
            
            results = self.annotate(data)
            for result in results:
                if self.add_result(data.dialogue_id, result):
                    count += 1
        
        self.finalize_cursor()
        return count
    
    def _iter_dialogues(self) -> Iterator[DialogueData]:
        """Iterate over dialogues with aggregate content."""
        from llm_archive.models import Dialogue, Exchange, ExchangeContent
        
        cursor = self.get_cursor()
        
        # Get dialogues
        query = self.session.query(Dialogue)
        if cursor:
            query = query.filter(Dialogue.created_at > cursor)
        
        for dialogue in query.all():
            # Get exchange content for this dialogue
            exchange_content = (
                self.session.query(Exchange, ExchangeContent)
                .join(ExchangeContent)
                .filter(Exchange.dialogue_id == dialogue.id)
                .order_by(Exchange.started_at)
                .all()
            )
            
            user_texts = []
            assistant_texts = []
            user_word_counts = []
            assistant_word_counts = []
            user_message_count = 0
            assistant_message_count = 0
            
            for exchange, content in exchange_content:
                if content.user_text:
                    user_texts.append(content.user_text)
                if content.assistant_text:
                    assistant_texts.append(content.assistant_text)
                if content.user_word_count:
                    user_word_counts.append(content.user_word_count)
                if content.assistant_word_count:
                    assistant_word_counts.append(content.assistant_word_count)
                user_message_count += exchange.user_message_count
                assistant_message_count += exchange.assistant_message_count
            
            yield DialogueData(
                dialogue_id=dialogue.id,
                source=dialogue.source,
                title=dialogue.title,
                exchange_count=len(exchange_content),
                message_count=user_message_count + assistant_message_count,
                user_message_count=user_message_count,
                assistant_message_count=assistant_message_count,
                user_texts=user_texts,
                assistant_texts=assistant_texts,
                user_word_counts=user_word_counts,
                assistant_word_counts=assistant_word_counts,
                created_at=dialogue.created_at,
                first_user_text=user_texts[0] if user_texts else None,
                first_assistant_text=assistant_texts[0] if assistant_texts else None,
            )
    
    @abstractmethod
    def annotate(self, data: DialogueData) -> list[AnnotationResult]:
        """
        Analyze dialogue and return annotations to create.
        
        Args:
            data: Dialogue data including texts and aggregate stats
            
        Returns:
            List of AnnotationResult objects (empty list if no match)
        """
        pass


# ============================================================
# Annotation Manager
# ============================================================

class AnnotationManager:
    """Manages annotation operations and annotator execution."""
    
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