# llm_archive/builders/exchanges.py
"""Exchange building from linear sequences."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import (
    Message, ContentPart,
    LinearSequence, SequenceMessage,
    Exchange, ExchangeMessage, ExchangeContent,
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


@dataclass
class DyadicExchange:
    """Pre-merge exchange unit."""
    messages: list[MessageInfo] = field(default_factory=list)
    
    @property
    def first_user_text(self) -> str | None:
        for msg in self.messages:
            if msg.role == 'user':
                return msg.text_content
        return None
    
    @property
    def started_at(self) -> datetime | None:
        if self.messages:
            return self.messages[0].created_at
        return None
    
    @property
    def ended_at(self) -> datetime | None:
        if self.messages:
            return self.messages[-1].created_at
        return None


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
    Builds exchanges from linear sequences.
    
    An exchange is a logical unit consisting of:
    - One or more user messages (prompts)
    - One or more assistant messages (responses)
    
    Continuation prompts are detected and merged into single exchanges.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def build_all(self) -> dict[str, int]:
        """Build exchanges for all linear sequences."""
        sequences = self.session.query(LinearSequence).all()
        
        counts = {
            'sequences': 0,
            'exchanges': 0,
            'exchange_messages': 0,
            'continuations': 0,
        }
        
        for sequence in sequences:
            try:
                result = self.build_for_sequence(sequence.id)
                counts['sequences'] += 1
                counts['exchanges'] += result['exchanges']
                counts['exchange_messages'] += result['exchange_messages']
                counts['continuations'] += result['continuations']
            except Exception as e:
                logger.error(f"Failed to build exchanges for sequence {sequence.id}: {e}")
                self.session.rollback()
        
        self.session.commit()
        logger.info(f"Exchange building complete: {counts}")
        return counts
    
    def build_for_sequence(self, sequence_id: UUID) -> dict[str, int]:
        """Build exchanges for a single linear sequence."""
        # Clear existing
        self._clear_derived(sequence_id)
        
        # Load message info in sequence order
        messages = self._load_sequence_messages(sequence_id)
        
        if not messages:
            return {'exchanges': 0, 'exchange_messages': 0, 'continuations': 0}
        
        # Create dyadic exchanges
        dyadic = self._create_dyadic_exchanges(messages)
        
        # Merge continuations
        merged = self._merge_continuations(dyadic)
        
        # Persist exchanges
        exchange_count = 0
        message_count = 0
        continuation_count = 0
        
        for position, group in enumerate(merged):
            exchange, msg_count = self._persist_exchange(
                sequence_id, position, group, len(group) > 1
            )
            exchange_count += 1
            message_count += msg_count
            if len(group) > 1:
                continuation_count += 1
        
        self.session.flush()
        
        return {
            'exchanges': exchange_count,
            'exchange_messages': message_count,
            'continuations': continuation_count,
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
            # Get text content
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
    
    def _create_dyadic_exchanges(self, messages: list[MessageInfo]) -> list[DyadicExchange]:
        """Create simple user-assistant dyadic exchanges."""
        dyadic = []
        current = DyadicExchange()
        
        for msg in messages:
            if msg.role not in ('user', 'assistant'):
                continue
            
            current.messages.append(msg)
            
            # Complete pair: user followed by assistant
            if (len(current.messages) >= 2 and
                current.messages[-2].role == 'user' and
                current.messages[-1].role == 'assistant'):
                
                dyadic.append(current)
                current = DyadicExchange()
        
        # Handle trailing messages
        if current.messages:
            dyadic.append(current)
        
        return dyadic
    
    def _merge_continuations(
        self, 
        dyadic: list[DyadicExchange]
    ) -> list[list[DyadicExchange]]:
        """Merge exchanges when continuations are detected."""
        if not dyadic:
            return []
        
        merged = []
        current_group = [dyadic[0]]
        
        for i in range(1, len(dyadic)):
            d = dyadic[i]
            
            if is_continuation_prompt(d.first_user_text):
                current_group.append(d)
            else:
                merged.append(current_group)
                current_group = [d]
        
        merged.append(current_group)
        return merged
    
    def _persist_exchange(
        self,
        sequence_id: UUID,
        position: int,
        group: list[DyadicExchange],
        is_continuation: bool,
    ) -> tuple[Exchange, int]:
        """Persist an exchange and its messages."""
        # Collect all messages
        all_messages = []
        for d in group:
            all_messages.extend(d.messages)
        
        if not all_messages:
            raise ValueError("Empty exchange")
        
        # Compute stats
        user_count = sum(1 for m in all_messages if m.role == 'user')
        assistant_count = sum(1 for m in all_messages if m.role == 'assistant')
        
        exchange = Exchange(
            sequence_id=sequence_id,
            position=position,
            first_message_id=all_messages[0].message_id,
            last_message_id=all_messages[-1].message_id,
            message_count=len(all_messages),
            user_message_count=user_count,
            assistant_message_count=assistant_count,
            is_continuation=is_continuation,
            merged_count=len(group),
            started_at=all_messages[0].created_at,
            ended_at=all_messages[-1].created_at,
        )
        self.session.add(exchange)
        self.session.flush()
        
        # Create exchange messages
        for pos, msg in enumerate(all_messages):
            ex_msg = ExchangeMessage(
                exchange_id=exchange.id,
                message_id=msg.message_id,
                position=pos,
            )
            self.session.add(ex_msg)
        
        # Create exchange content
        user_texts = [m.text_content for m in all_messages if m.role == 'user' and m.text_content]
        assistant_texts = [m.text_content for m in all_messages if m.role == 'assistant' and m.text_content]
        
        user_text = '\n\n'.join(user_texts) if user_texts else None
        assistant_text = '\n\n'.join(assistant_texts) if assistant_texts else None
        full_text = '\n\n'.join(filter(None, [user_text, assistant_text]))
        
        content = ExchangeContent(
            exchange_id=exchange.id,
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
        
        return exchange, len(all_messages)
    
    def _clear_derived(self, sequence_id: UUID):
        """Clear existing exchange data for a sequence."""
        sid = str(sequence_id)
        
        self.session.execute(
            text("""
                DELETE FROM derived.exchange_content
                WHERE exchange_id IN (
                    SELECT id FROM derived.exchanges WHERE sequence_id = :sid
                )
            """),
            {'sid': sid}
        )
        self.session.execute(
            text("""
                DELETE FROM derived.exchange_messages
                WHERE exchange_id IN (
                    SELECT id FROM derived.exchanges WHERE sequence_id = :sid
                )
            """),
            {'sid': sid}
        )
        self.session.execute(
            text("DELETE FROM derived.exchanges WHERE sequence_id = :sid"),
            {'sid': sid}
        )