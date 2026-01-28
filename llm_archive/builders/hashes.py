# llm_archive/builders/hashes.py
"""Content hashing for deduplication."""

import hashlib
import re
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import (
    Message, ContentPart, Exchange, ExchangeContent, ContentHash,
)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text."""
    return ' '.join(text.split())


def normalize_for_comparison(text: str) -> str:
    """Normalize text for fuzzy comparison."""
    # Lowercase
    text = text.lower()
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text


def compute_sha256(text: str) -> str:
    """Compute SHA-256 hash."""
    return hashlib.sha256(text.encode()).hexdigest()


class HashBuilder:
    """
    Builds content hashes for deduplication.
    
    Creates hashes at multiple levels:
    - Message level: individual message content
    - Exchange level: aggregated exchange content
    
    Supports multiple normalizations:
    - none: raw text
    - whitespace: normalized whitespace
    - normalized: lowercase, no punctuation, normalized whitespace
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def build_all(self) -> dict[str, int]:
        """Build hashes for all entities."""
        counts = {
            'messages': 0,
            'exchanges': 0,
            'total_hashes': 0,
        }
        
        # Hash messages
        msg_count, msg_hashes = self._hash_messages()
        counts['messages'] = msg_count
        counts['total_hashes'] += msg_hashes
        
        # Hash exchanges
        ex_count, ex_hashes = self._hash_exchanges()
        counts['exchanges'] = ex_count
        counts['total_hashes'] += ex_hashes
        
        self.session.commit()
        logger.info(f"Hash building complete: {counts}")
        return counts
    
    def _hash_messages(self) -> tuple[int, int]:
        """Hash all message content."""
        # Get messages with text content
        messages = (
            self.session.query(
                Message.id,
                Message.dialogue_id,
            )
            .all()
        )
        
        msg_count = 0
        hash_count = 0
        
        for msg_id, dialogue_id in messages:
            # Get concatenated text
            parts = (
                self.session.query(ContentPart.text_content)
                .filter(ContentPart.message_id == msg_id)
                .filter(ContentPart.text_content.isnot(None))
                .order_by(ContentPart.sequence)
                .all()
            )
            
            texts = [p[0] for p in parts if p[0]]
            if not texts:
                continue
            
            full_text = '\n'.join(texts)
            
            # Create hashes with different normalizations
            hashes_created = self._create_hashes(
                entity_type='message',
                entity_id=msg_id,
                text=full_text,
                scope='full',
            )
            
            msg_count += 1
            hash_count += hashes_created
        
        return msg_count, hash_count
    
    def _hash_exchanges(self) -> tuple[int, int]:
        """Hash all exchange content."""
        # ExchangeContent already has text aggregated
        contents = self.session.query(ExchangeContent).all()
        
        ex_count = 0
        hash_count = 0
        
        for content in contents:
            # Hash user text
            if content.user_text:
                hash_count += self._create_hashes(
                    entity_type='exchange',
                    entity_id=content.exchange_id,
                    text=content.user_text,
                    scope='user',
                )
            
            # Hash assistant text
            if content.assistant_text:
                hash_count += self._create_hashes(
                    entity_type='exchange',
                    entity_id=content.exchange_id,
                    text=content.assistant_text,
                    scope='assistant',
                )
            
            # Hash full text
            if content.full_text:
                hash_count += self._create_hashes(
                    entity_type='exchange',
                    entity_id=content.exchange_id,
                    text=content.full_text,
                    scope='full',
                )
            
            ex_count += 1
        
        return ex_count, hash_count
    
    def _create_hashes(
        self,
        entity_type: str,
        entity_id: UUID,
        text: str,
        scope: str,
    ) -> int:
        """Create hashes with multiple normalizations."""
        count = 0
        
        normalizations = [
            ('none', text),
            ('whitespace', normalize_whitespace(text)),
            ('normalized', normalize_for_comparison(text)),
        ]
        
        for norm_name, norm_text in normalizations:
            if not norm_text:
                continue
            
            hash_value = compute_sha256(norm_text)
            
            # Check if exists
            existing = (
                self.session.query(ContentHash)
                .filter(ContentHash.entity_type == entity_type)
                .filter(ContentHash.entity_id == entity_id)
                .filter(ContentHash.hash_scope == scope)
                .filter(ContentHash.normalization == norm_name)
                .first()
            )
            
            if existing:
                # Update if changed
                if existing.hash_sha256 != hash_value:
                    existing.hash_sha256 = hash_value
                    count += 1
            else:
                # Create new
                content_hash = ContentHash(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    hash_scope=scope,
                    hash_sha256=hash_value,
                    normalization=norm_name,
                )
                self.session.add(content_hash)
                count += 1
        
        return count
    
    def find_duplicates(
        self,
        entity_type: str | None = None,
        scope: str | None = None,
        normalization: str = 'normalized',
    ) -> list[dict]:
        """Find duplicate content by hash."""
        query = (
            self.session.query(
                ContentHash.hash_sha256,
                ContentHash.entity_type,
                ContentHash.hash_scope,
            )
            .filter(ContentHash.normalization == normalization)
        )
        
        if entity_type:
            query = query.filter(ContentHash.entity_type == entity_type)
        if scope:
            query = query.filter(ContentHash.hash_scope == scope)
        
        # Group and find duplicates
        from sqlalchemy import func
        
        results = (
            query
            .group_by(
                ContentHash.hash_sha256,
                ContentHash.entity_type,
                ContentHash.hash_scope,
            )
            .having(func.count(ContentHash.id) > 1)
            .all()
        )
        
        duplicates = []
        for hash_val, ent_type, scope in results:
            # Get all entity IDs with this hash
            entities = (
                self.session.query(ContentHash.entity_id)
                .filter(ContentHash.hash_sha256 == hash_val)
                .filter(ContentHash.entity_type == ent_type)
                .filter(ContentHash.hash_scope == scope)
                .filter(ContentHash.normalization == normalization)
                .all()
            )
            
            duplicates.append({
                'hash': hash_val,
                'entity_type': ent_type,
                'scope': scope,
                'entity_ids': [e[0] for e in entities],
                'count': len(entities),
            })
        
        return duplicates