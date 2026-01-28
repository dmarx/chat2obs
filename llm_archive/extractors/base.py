# llm_archive/extractors/base.py
"""Shared extraction utilities and base classes."""

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import Dialogue, Message, ContentPart


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


def compute_content_hash(source_json: dict | list | str) -> str:
    """Compute a stable hash of message content for change detection."""
    # Serialize to JSON with sorted keys for stability
    if isinstance(source_json, str):
        content = source_json
    else:
        content = json.dumps(source_json, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content.encode()).hexdigest()


class BaseExtractor(ABC):
    """
    Base class for source extractors.
    
    Supports idempotent ingestion with incremental updates:
    - Skip dialogues that haven't changed (by updated_at timestamp)
    - Preserve message UUIDs for unchanged messages
    - Soft-delete messages removed from source
    - Only rebuild content_parts for actually changed messages
    """
    
    SOURCE_ID: str = None  # Override in subclass
    
    def __init__(self, session: Session):
        self.session = session
        self._message_id_map: dict[str, UUID] = {}  # source_id -> native UUID
    
    @abstractmethod
    def extract_dialogue(self, raw: dict[str, Any]) -> str | None:
        """
        Extract a single dialogue and all its contents.
        
        Returns:
            'new' - new dialogue created
            'updated' - existing dialogue updated  
            'skipped' - existing dialogue unchanged
            None - extraction failed
        """
        pass
    
    def extract_all(self, data: list[dict[str, Any]]) -> dict[str, int]:
        """Extract all dialogues from a data list."""
        counts = {
            'dialogues_new': 0,
            'dialogues_updated': 0,
            'dialogues_skipped': 0,
            'messages': 0,
            'messages_new': 0,
            'messages_updated': 0,
            'messages_unchanged': 0,
            'messages_restored': 0,
            'messages_soft_deleted': 0,
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
    
    def get_existing_messages(self, dialogue_id: UUID) -> dict[str, Message]:
        """Get all existing messages for a dialogue, keyed by source_id."""
        messages = (
            self.session.query(Message)
            .filter(Message.dialogue_id == dialogue_id)
            .all()
        )
        return {m.source_id: m for m in messages}
    
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
    
    def _delete_message_content(self, message_id: UUID):
        """Delete content parts and related data for a message."""
        # Content parts cascade delete citations
        self.session.query(ContentPart).filter(
            ContentPart.message_id == message_id
        ).delete()
    
    def _soft_delete_messages(self, messages: list[Message]) -> int:
        """Soft delete messages that are no longer in source."""
        now = datetime.now(timezone.utc)
        count = 0
        for msg in messages:
            if msg.deleted_at is None:
                msg.deleted_at = now
                count += 1
        return count
    
    def _restore_message(self, message: Message):
        """Restore a soft-deleted message."""
        message.deleted_at = None
