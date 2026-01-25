# llm_archive/extractors/base.py
"""Shared extraction utilities and base classes."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from loguru import logger


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
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (ValueError, OSError):
            return None
    
    return None


def normalize_role(role: str | None, source: str) -> str:
    """Normalize role/sender to standard vocabulary."""
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
    """Base class for source extractors."""
    
    SOURCE_ID: str = None
    
    def __init__(self, session: Session):
        self.session = session
        self._message_id_map: dict[str, UUID] = {}
    
    @abstractmethod
    def extract_dialogue(self, raw: dict[str, Any]) -> UUID | None:
        """Extract a single dialogue. Returns native UUID or None on failure."""
        pass
    
    def extract_all(self, data: list[dict[str, Any]]) -> dict[str, int]:
        """Extract all dialogues from a data list."""
        counts = {
            'dialogues': 0,
            'messages': 0,
            'content_parts': 0,
            'citations': 0,
            'attachments': 0,
            'failed': 0,
        }
        
        for i, raw in enumerate(data):
            try:
                result = self.extract_dialogue(raw)
                if result:
                    counts['dialogues'] += 1
                else:
                    counts['failed'] += 1
            except Exception as e:
                logger.error(f"Failed to extract dialogue {i}: {e}")
                counts['failed'] += 1
                self.session.rollback()
        
        self.session.commit()
        logger.info(f"{self.SOURCE_ID} extraction complete: {counts}")
        return counts
    
    def register_message_id(self, source_id: str, native_id: UUID):
        """Register source message ID to native UUID mapping."""
        self._message_id_map[source_id] = native_id
    
    def resolve_message_id(self, source_id: str | None) -> UUID | None:
        """Resolve source message ID to native UUID."""
        if source_id is None:
            return None
        return self._message_id_map.get(source_id)