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
from llm_archive.annotations.core import AnnotationWriter, EntityType


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


def compute_word_count(text: str | None) -> int:
    """
    Compute word count for text content.
    
    Simple whitespace-based word counting.
    Returns 0 for None or empty text.
    """
    if not text:
        return 0
    return len(text.split())


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
    - Soft-delete messages removed from source (unless incremental=True)
    - Only rebuild content_parts for actually changed messages
    
    Provides helper for creating content parts with automatic word_count annotation.
    
    Args:
        session: SQLAlchemy session
        assume_immutable: If True, assume message content never changes once created.
            This skips content hash comparison for existing messages, which is faster
            but won't detect in-place edits.
        incremental: If True, only update changed dialogues and messages.
            If False, replace entire dialogue on any change.
    """
    
    SOURCE_ID: str = None  # Override in subclass
    
    def __init__(
        self,
        session: Session,
        assume_immutable: bool = False,
        incremental: bool = False,
    ):
        if self.SOURCE_ID is None:
            raise ValueError("SOURCE_ID must be set in subclass")
        
        self.session = session
        self.assume_immutable = assume_immutable
        self.incremental = incremental
        self.annotation_writer = AnnotationWriter(session)
        self.counts: dict[str, int] = {}  # Populated by extract_all
    
    def _increment_count(self, key: str, amount: int = 1):
        """Safely increment a count (no-op if counts not initialized)."""
        if key in self.counts:
            self.counts[key] += amount
    def register_message_id(self, source_id: str, native_id: UUID):
        """Register a mapping from source message ID to native UUID."""
        self._message_id_map[source_id] = native_id
    def resolve_message_id(self, source_id: str | None) -> UUID | None:
        """Resolve a source message ID to native UUID."""
        if source_id is None:
            return None
        return self._message_id_map.get(source_id)
    def create_content_part_with_annotation(
        self,
        message_id: UUID,
        sequence: int,
        part_type: str,
        text_content: str | None = None,
        language: str | None = None,
        media_type: str | None = None,
        url: str | None = None,
        tool_name: str | None = None,
        tool_use_id: str | None = None,
        tool_input: dict | None = None,
        is_error: bool | None = None,
        source_json: dict | None = None,
    ) -> ContentPart:
        """
        Create a ContentPart and annotate it with word_count.
        
        This is the standard way to create content parts - it ensures
        word_count is always annotated consistently.
        
        Args:
            message_id: Parent message ID
            sequence: Order within message
            part_type: Type of content ('text', 'code', 'image', 'tool_use', etc.)
            text_content: Text content (if any)
            language: Programming language for code blocks
            media_type: MIME type for media
            url: URL for media or links
            tool_name: Name of tool for tool_use
            tool_use_id: ID of tool use
            tool_input: Input parameters for tool
            is_error: Whether tool result is an error
            source_json: Original source data
        
        Returns:
            Created ContentPart with word_count annotation
        """
        # Create the content part
        content_part = ContentPart(
            message_id=message_id,
            sequence=sequence,
            part_type=part_type,
            text_content=text_content,
            language=language,
            media_type=media_type,
            url=url,
            tool_name=tool_name,
            tool_use_id=tool_use_id,
            tool_input=tool_input,
            is_error=is_error,
            source_json=source_json,
        )
        
        self.session.add(content_part)
        self.session.flush()  # Get the ID
        
        # Annotate with word count
        word_count = compute_word_count(text_content)
        self.annotation_writer.write_numeric(
            entity_type=EntityType.CONTENT_PART,
            entity_id=content_part.id,
            key='word_count',
            value=word_count,
            source=self.SOURCE_ID,
        )
        
        return content_part
    
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
        
    def should_update(
        self,
        existing: Dialogue,
        new_updated_at: datetime | None,
    ) -> bool:
        """Determine if dialogue should be updated."""
        if new_updated_at is None:
            # No timestamp - always update
            return True
        
        if existing.source_updated_at is None:
            # Existing has no timestamp - update
            return True
        
        # Update if new is newer
        return new_updated_at > existing.source_updated_at
    
    @abstractmethod
    def extract_dialogue(self, raw: dict[str, Any]) -> str | None:
        """
        Extract a single dialogue.
        
        Returns:
            'new' - new dialogue created
            'updated' - existing dialogue updated
            'skipped' - existing dialogue unchanged
            None - extraction failed
        """
        pass
