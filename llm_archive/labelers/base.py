# llm_archive/labelers/base.py
"""Base labeling infrastructure."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import Label


class Labeler(ABC):
    """
    Base class for label generators.
    
    Labelers analyze entities and produce labels that are stored
    in the derived.labels table.
    """
    
    # Override in subclass
    LABEL_TYPE: str = None
    ENTITY_TYPE: str = None
    SOURCE: str = 'heuristic'
    VERSION: str = '1.0'
    
    def __init__(self, session: Session):
        self.session = session
    
    @abstractmethod
    def compute(self) -> int:
        """
        Compute and persist labels.
        Returns count of labels created/updated.
        """
        pass
    
    def add_label(
        self,
        entity_id: UUID,
        label_value: str,
        confidence: float | None = None,
        label_data: dict | None = None,
    ) -> bool:
        """
        Add or update a label.
        Returns True if a new label was created.
        """
        # Check for existing active label
        existing = (
            self.session.query(Label)
            .filter(Label.entity_type == self.ENTITY_TYPE)
            .filter(Label.entity_id == entity_id)
            .filter(Label.label_type == self.LABEL_TYPE)
            .filter(Label.label_value == label_value)
            .filter(Label.superseded_at.is_(None))
            .first()
        )
        
        if existing:
            # Update if confidence changed significantly
            if confidence is not None and existing.confidence != confidence:
                if abs((existing.confidence or 0) - confidence) > 0.01:
                    existing.confidence = confidence
                    existing.label_data = label_data
            return False
        
        # Create new label
        label = Label(
            entity_type=self.ENTITY_TYPE,
            entity_id=entity_id,
            label_type=self.LABEL_TYPE,
            label_value=label_value,
            label_data=label_data,
            confidence=confidence,
            source=self.SOURCE,
            source_version=self.VERSION,
        )
        self.session.add(label)
        return True
    
    def supersede_label(
        self,
        entity_id: UUID,
        label_value: str,
        new_label_id: UUID | None = None,
    ):
        """Mark an existing label as superseded."""
        existing = (
            self.session.query(Label)
            .filter(Label.entity_type == self.ENTITY_TYPE)
            .filter(Label.entity_id == entity_id)
            .filter(Label.label_type == self.LABEL_TYPE)
            .filter(Label.label_value == label_value)
            .filter(Label.superseded_at.is_(None))
            .first()
        )
        
        if existing:
            existing.superseded_at = datetime.now(timezone.utc)
            existing.superseded_by = new_label_id


class LabelManager:
    """
    Manages label operations and labeler execution.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.labelers: list[Labeler] = []
    
    def register(self, labeler_class: type[Labeler]):
        """Register a labeler class."""
        labeler = labeler_class(self.session)
        self.labelers.append(labeler)
    
    def run_all(self) -> dict[str, int]:
        """Run all registered labelers."""
        results = {}
        
        for labeler in self.labelers:
            name = labeler.__class__.__name__
            try:
                count = labeler.compute()
                results[name] = count
                logger.info(f"{name}: {count} labels")
            except Exception as e:
                logger.error(f"{name} failed: {e}")
                results[name] = -1
                self.session.rollback()
        
        self.session.commit()
        return results
    
    def get_labels(
        self,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        label_type: str | None = None,
        active_only: bool = True,
    ) -> list[Label]:
        """Query labels with filters."""
        query = self.session.query(Label)
        
        if entity_type:
            query = query.filter(Label.entity_type == entity_type)
        if entity_id:
            query = query.filter(Label.entity_id == entity_id)
        if label_type:
            query = query.filter(Label.label_type == label_type)
        if active_only:
            query = query.filter(Label.superseded_at.is_(None))
        
        return query.all()
    
    def get_entity_labels(self, entity_type: str, entity_id: UUID) -> dict[str, Any]:
        """Get all active labels for an entity as a dict."""
        labels = self.get_labels(entity_type=entity_type, entity_id=entity_id)
        
        result = {}
        for label in labels:
            key = f"{label.label_type}:{label.label_value}"
            result[key] = {
                'confidence': label.confidence,
                'source': label.source,
                'data': label.label_data,
            }
        
        return result
    
    def clear_labels(
        self,
        entity_type: str | None = None,
        label_type: str | None = None,
        source: str | None = None,
    ):
        """Clear labels matching filters (hard delete)."""
        query = self.session.query(Label)
        
        if entity_type:
            query = query.filter(Label.entity_type == entity_type)
        if label_type:
            query = query.filter(Label.label_type == label_type)
        if source:
            query = query.filter(Label.source == source)
        
        count = query.delete()
        logger.info(f"Deleted {count} labels")
        return count