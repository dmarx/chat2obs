# llm_archive/extractors/base.py
"""Shared extraction utilities and base classes."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import Dialogue, Message


def parse_timestamp(value: int | float | str | None) -> datetime | None:
    """
    Parse timestamp from various formats to timezone-aware datetime.
    
    Handles:
    - Epoch floats/ints (ChatGPT)
    - ISO 8601 strings (Claude)
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        # ISO 8601 format
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    
    if isinstance(value, (int, float)):
        # Epoch seconds
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (ValueError, OSError):
            return None
    
    return None


def normalize_role(role: str, source: str) -> str:
    """
    Normalize role/sender to standard vocabulary.
    
    Standard roles: 'user', 'assistant', 'system', 'tool'
    """
    if role is None:
        return 'unknown'
    
    role_lower = role.lower()
    
    # Claude uses 'human' instead of 'user'
    if role_lower == 'human':
        return 'user'
    
    return role_lower


def safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dict."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
        if current is None:
            return default
    return current


class BaseExtractor(ABC):
    """
    Base class for source extractors.
    
    Supports idempotent ingestion - re-importing the same data will:
    - Skip dialogues that already exist (by source_id)
    - Update dialogues if their updated_at timestamp is newer
    """
    
    SOURCE_ID: str = None  # Override in subclass
    
    def __init__(self, session: Session):
        self.session = session
        self._message_id_map: dict[str, UUID] = {}  # source_id -> native UUID
    
    @abstractmethod
    def extract_dialogue(self, raw: dict[str, Any]) -> UUID | None:
        """
        Extract a single dialogue and all its contents.
        Returns the native dialogue UUID or None on failure.
        """
        pass
    
    def extract_all(self, data: list[dict[str, Any]]) -> dict[str, int]:
        """Extract all dialogues from a data list."""
        counts = {
            'dialogues_new': 0,
            'dialogues_updated': 0,
            'dialogues_skipped': 0,
            'messages': 0,
            'content_parts': 0,
            'failed': 0,
        }
        
        for i, raw in enumerate(data):
            try:
                result = self.extract_dialogue(raw)
                if result == 'new':
                    counts['dialogues_new'] += 1
                elif result == 'updated':
                    counts['dialogues_updated'] += 1
                elif result == 'skipped':
                    counts['dialogues_skipped'] += 1
                elif result is None:
                    counts['failed'] += 1
            except Exception as e:
                logger.error(f"Failed to extract dialogue {i}: {e}")
                counts['failed'] += 1
                self.session.rollback()
        
        self.session.commit()
        total = counts['dialogues_new'] + counts['dialogues_updated']
        logger.info(f"{self.SOURCE_ID} extraction complete: {total} processed ({counts})")
        return counts
    
    def get_existing_dialogue(self, source_id: str) -> Dialogue | None:
        """Check if dialogue already exists."""
        return (
            self.session.query(Dialogue)
            .filter(Dialogue.source == self.SOURCE_ID)
            .filter(Dialogue.source_id == source_id)
            .first()
        )
    
    def get_existing_message(self, dialogue_id: UUID, source_id: str) -> Message | None:
        """Check if message already exists."""
        return (
            self.session.query(Message)
            .filter(Message.dialogue_id == dialogue_id)
            .filter(Message.source_id == source_id)
            .first()
        )
    
    def should_update(self, existing: Dialogue, new_updated_at: datetime | None) -> bool:
        """Determine if existing dialogue should be updated."""
        if new_updated_at is None:
            return False
        if existing.updated_at is None:
            return True
        return new_updated_at > existing.updated_at
    
    def register_message_id(self, source_id: str, native_id: UUID):
        """Register a mapping from source message ID to native UUID."""
        self._message_id_map[source_id] = native_id
    
    def resolve_message_id(self, source_id: str | None) -> UUID | None:
        """Resolve a source message ID to native UUID."""
        if source_id is None:
            return None
        return self._message_id_map.get(source_id)
