# llm_archive/builders/exchanges.py
"""Exchange building from dialogue trees."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import (
    Dialogue, Message, ContentPart,
    LinearSequence, SequenceMessage,
    Exchange, ExchangeMessage, SequenceExchange, ExchangeContent,
)


CONTINUATION_PATTERNS = [
    'continue', 'more', 'keep going', 'go on', 'next',
    'tell me more', 'expand', 'keep writing', 'finish',
    'elaborate', 'do go on', 'make it so', 'yes', 'please',
    'do it', 'proceed', 'carry on', 'and then', 'what else',
    'go ahead', 'sure', 'ok', 'okay', 'yes please',
]


@dataclass
class MessageInfo:
    """Lightweight message info for exchange building."""
    message_id: UUID
    role: str
    created_at: datetime | None
    text_content: str | None


def is_continuation_prompt(text: str | None) -> bool:
    """Check if text is a continuation prompt."""
    if not text:
        return False
    
    text = text.strip().lower()
    
    # Very short messages that match patterns
    word_count = len(text.split())
    if word_count <= 5:
        for pattern in CONTINUATION_PATTERNS:
            if text == pattern or text.startswith(pattern + ' ') or text.startswith(pattern + '?'):
                return True
    
    # Quote + elaboration pattern
    if text.startswith('>'):
        lines = text.split('\n')
        last_line = lines[-1].strip().lower() if lines else ''
        if last_line in ('elaborate', 'continue', 'expand', 'more'):
            return True
    
    return False


def compute_hash(text: str | None) -> str | None:
    """Compute SHA-256 hash of text."""
    if not text:
        return None
    normalized = ' '.join(text.split())
    return hashlib.sha256(normalized.encode()).hexdigest()


class ExchangeBuilder:
    """
    Builds exchanges from dialogue trees.
    
    An exchange is a dyadic unit:
    - USER message(s) followed by ASSISTANT response(s)
    - Ends when next USER message starts a new topic (not a continuation)
    
    Exchanges are built from the TREE and identified by 
    (dialogue_id, first_message_id, last_message_id).
    
    Sequences then REFERENCE exchanges via sequence_exchanges join table.
    This avoids duplicate exchange creation for shared prefixes.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self._exchange_cache: dict[tuple[UUID, UUID, UUID], UUID] = {}  # (dialogue, first, last) -> exchange_id
    
    def build_all(self) -> dict[str, int]:
        """Build exchanges for all dialogues."""
        dialogues = self.session.query(Dialogue).all()
        
        counts = {
            'dialogues': 0,
            'exchanges': 0,
            'exchange_messages': 0,
            'sequence_links': 0,
            'continuations': 0,
        }
        
        for dialogue in dialogues:
            try:
                result = self.build_for_dialogue(dialogue.id)
                counts['dialogues'] += 1
                counts['exchanges'] += result['exchanges']
                counts['exchange_messages'] += result['exchange_messages']
                counts['sequence_links'] += result['sequence_links']
                counts['continuations'] += result['continuations']
            except Exception as e:
                logger.error(f"Failed to build exchanges for {dialogue.id}: {e}")
                self.session.rollback()
        
        self.session.commit()
        logger.info(f"Exchange building complete: {counts}")
        return counts
    
    def build_for_dialogue(self, dialogue_id: UUID) -> dict[str, int]:
        """Build exchanges for a single dialogue."""
        # Clear cache for this dialogue
        self._exchange_cache = {k: v for k, v in self._exchange_cache.items() if k[0] != dialogue_id}
        
        # Clear existing sequence_exchanges links for this dialogue
        self._clear_sequence_links(dialogue_id)
        
        # Get all sequences for this dialogue
        sequences = (
            self.session.query(LinearSequence)
            .filter(LinearSequence.dialogue_id == dialogue_id)
            .all()
        )
        
        total_exchanges = 0
        total_messages = 0
        total_links = 0
        total_continuations = 0
        
        for sequence in sequences:
            result = self._build_for_sequence(sequence)
            total_exchanges += result['exchanges']
            total_messages += result['exchange_messages']
            total_links += result['sequence_links']
            total_continuations += result['continuations']
        
        self.session.flush()
        
        return {
            'exchanges': total_exchanges,
            'exchange_messages': total_messages,
            'sequence_links': total_links,
            'continuations': total_continuations,
        }
    
    def _build_for_sequence(self, sequence: LinearSequence) -> dict[str, int]:
        """Build/link exchanges for a single sequence."""
        # Load messages in order
        messages = self._load_sequence_messages(sequence.id)
        
        if not messages:
            return {'exchanges': 0, 'exchange_messages': 0, 'sequence_links': 0, 'continuations': 0}
        
        # Group into dyadic exchanges
        dyadic_groups = self._create_dyadic_groups(messages)
        
        # Merge continuations
        merged_groups = self._merge_continuations(dyadic_groups)
        
        # Create/find exchanges and link to sequence
        exchanges_created = 0
        messages_created = 0
        links_created = 0
        continuations = 0
        
        for position, (group_messages, is_continuation) in enumerate(merged_groups):
            if not group_messages:
                continue
            
            exchange_id, was_new, msg_count = self._get_or_create_exchange(
                sequence.dialogue_id, group_messages, is_continuation
            )
            
            if was_new:
                exchanges_created += 1
                messages_created += msg_count
            
            if is_continuation:
                continuations += 1
            
            # Link sequence to exchange
            seq_ex = SequenceExchange(
                sequence_id=sequence.id,
                exchange_id=exchange_id,
                position=position,
            )
            self.session.add(seq_ex)
            links_created += 1
        
        return {
            'exchanges': exchanges_created,
            'exchange_messages': messages_created,
            'sequence_links': links_created,
            'continuations': continuations,
        }
    
    def _load_sequence_messages(self, sequence_id: UUID) -> list[MessageInfo]:
        """Load message info for a sequence in order."""
        results = (
            self.session.query(
                Message.id,
                Message.role,
                Message.created_at,
            )
            .join(SequenceMessage, SequenceMessage.message_id == Message.id)
            .filter(SequenceMessage.sequence_id == sequence_id)
            .order_by(SequenceMessage.position)
            .all()
        )
        
        messages = []
        for msg_id, role, created_at in results:
            text_content = self._get_message_text(msg_id)
            messages.append(MessageInfo(
                message_id=msg_id,
                role=role,
                created_at=created_at,
                text_content=text_content,
            ))
        
        return messages
    
    def _get_message_text(self, message_id: UUID) -> str | None:
        """Get concatenated text content for a message."""
        parts = (
            self.session.query(ContentPart.text_content)
            .filter(ContentPart.message_id == message_id)
            .filter(ContentPart.text_content.isnot(None))
            .order_by(ContentPart.sequence)
            .all()
        )
        
        texts = [p[0] for p in parts if p[0]]
        return '\n'.join(texts) if texts else None
    
    def _create_dyadic_groups(self, messages: list[MessageInfo]) -> list[list[MessageInfo]]:
        """
        Group messages into dyadic exchanges.
        
        A dyadic exchange starts with USER message(s) and includes
        all following ASSISTANT message(s) until the next USER message.
        """
        groups = []
        current_group = []
        
        for msg in messages:
            if msg.role not in ('user', 'assistant'):
                continue
            
            # Start new group on USER after ASSISTANT
            if msg.role == 'user' and current_group:
                last_role = current_group[-1].role if current_group else None
                if last_role == 'assistant':
                    groups.append(current_group)
                    current_group = []
            
            current_group.append(msg)
        
        # Don't forget the last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _merge_continuations(
        self, 
        groups: list[list[MessageInfo]]
    ) -> list[tuple[list[MessageInfo], bool]]:
        """
        Merge groups when USER message is a continuation signal.
        
        Returns list of (messages, is_continuation) tuples.
        """
        if not groups:
            return []
        
        result = []
        accumulated = groups[0]
        
        for i in range(1, len(groups)):
            group = groups[i]
            
            # Check if first user message in this group is a continuation
            first_user = next((m for m in group if m.role == 'user'), None)
            
            if first_user and is_continuation_prompt(first_user.text_content):
                # Merge with accumulated
                accumulated.extend(group)
            else:
                # Save accumulated and start new
                is_continuation = len(result) > 0 and any(
                    is_continuation_prompt(m.text_content) 
                    for m in accumulated if m.role == 'user'
                )
                result.append((accumulated, is_continuation))
                accumulated = group
        
        # Don't forget the last accumulated group
        if accumulated:
            is_continuation = any(
                is_continuation_prompt(m.text_content) 
                for m in accumulated if m.role == 'user'
            )
            result.append((accumulated, is_continuation))
        
        return result
    
    def _get_or_create_exchange(
        self,
        dialogue_id: UUID,
        messages: list[MessageInfo],
        is_continuation: bool,
    ) -> tuple[UUID, bool, int]:
        """
        Get existing exchange or create new one.
        
        Returns (exchange_id, was_newly_created, message_count).
        """
        if not messages:
            raise ValueError("Empty message list")
        
        first_id = messages[0].message_id
        last_id = messages[-1].message_id
        
        cache_key = (dialogue_id, first_id, last_id)
        
        # Check cache
        if cache_key in self._exchange_cache:
            return self._exchange_cache[cache_key], False, 0
        
        # Check database
        existing = (
            self.session.query(Exchange)
            .filter(Exchange.dialogue_id == dialogue_id)
            .filter(Exchange.first_message_id == first_id)
            .filter(Exchange.last_message_id == last_id)
            .first()
        )
        
        if existing:
            self._exchange_cache[cache_key] = existing.id
            return existing.id, False, 0
        
        # Create new exchange
        user_count = sum(1 for m in messages if m.role == 'user')
        assistant_count = sum(1 for m in messages if m.role == 'assistant')
        
        exchange = Exchange(
            dialogue_id=dialogue_id,
            first_message_id=first_id,
            last_message_id=last_id,
            message_count=len(messages),
            user_message_count=user_count,
            assistant_message_count=assistant_count,
            is_continuation=is_continuation,
            merged_count=1 if not is_continuation else user_count,
            started_at=messages[0].created_at,
            ended_at=messages[-1].created_at,
        )
        self.session.add(exchange)
        self.session.flush()
        
        # Create exchange messages
        for pos, msg in enumerate(messages):
            ex_msg = ExchangeMessage(
                exchange_id=exchange.id,
                message_id=msg.message_id,
                position=pos,
            )
            self.session.add(ex_msg)
        
        # Create exchange content
        self._create_exchange_content(exchange.id, messages)
        
        self._exchange_cache[cache_key] = exchange.id
        return exchange.id, True, len(messages)
    
    def _create_exchange_content(self, exchange_id: UUID, messages: list[MessageInfo]):
        """Create aggregated content for an exchange."""
        user_texts = [m.text_content for m in messages if m.role == 'user' and m.text_content]
        assistant_texts = [m.text_content for m in messages if m.role == 'assistant' and m.text_content]
        
        user_text = '\n\n'.join(user_texts) if user_texts else None
        assistant_text = '\n\n'.join(assistant_texts) if assistant_texts else None
        full_text = '\n\n'.join(filter(None, [user_text, assistant_text]))
        
        content = ExchangeContent(
            exchange_id=exchange_id,
            user_text=user_text,
            assistant_text=assistant_text,
            full_text=full_text if full_text else None,
            user_text_hash=compute_hash(user_text),
            assistant_text_hash=compute_hash(assistant_text),
            full_text_hash=compute_hash(full_text) if full_text else None,
            user_word_count=len(user_text.split()) if user_text else 0,
            assistant_word_count=len(assistant_text.split()) if assistant_text else 0,
            total_word_count=len(full_text.split()) if full_text else 0,
        )
        self.session.add(content)
    
    def _clear_sequence_links(self, dialogue_id: UUID):
        """Clear existing sequence_exchanges for this dialogue."""
        self.session.execute(
            text("""
                DELETE FROM derived.sequence_exchanges 
                WHERE sequence_id IN (
                    SELECT id FROM derived.linear_sequences 
                    WHERE dialogue_id = :did
                )
            """),
            {'did': str(dialogue_id)}
        )
