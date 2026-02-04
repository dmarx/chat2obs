# llm_archive/builders/prompt_response.py
"""Prompt-response pair building - direct message associations without tree dependency."""

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger

from llm_archive.models import Dialogue, Message, ContentPart


class PromptResponseBuilder:
    """
    Builds prompt-response pairs directly from messages.
    
    Unlike ExchangeBuilder (which depends on tree analysis), this uses:
    1. parent_id relationship when available (ChatGPT)
    2. Sequential fallback (Claude, or when parent_id missing)
    
    Result: Each non-user message is paired with its eliciting user prompt.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def build_all(self) -> dict[str, int]:
        """Build prompt-response pairs for all dialogues."""
        dialogues = self.session.query(Dialogue).all()
        
        counts = {
            'dialogues': 0,
            'prompt_responses': 0,
            'content_records': 0,
        }
        
        for dialogue in dialogues:
            try:
                result = self.build_for_dialogue(dialogue.id)
                counts['dialogues'] += 1
                counts['prompt_responses'] += result['prompt_responses']
                counts['content_records'] += result['content_records']
            except Exception as e:
                logger.error(f"Failed to build prompt-responses for {dialogue.id}: {e}")
                self.session.rollback()
        
        self.session.commit()
        logger.info(f"Prompt-response building complete: {counts}")
        return counts
    
    def build_for_dialogue(self, dialogue_id: UUID) -> dict[str, int]:
        """Build prompt-response pairs for a single dialogue."""
        # Clear existing data
        self._clear_existing(dialogue_id)
        
        # Get messages ordered by created_at (with fallback to id for stable ordering)
        messages = (
            self.session.query(Message)
            .filter(Message.dialogue_id == dialogue_id)
            .filter(Message.deleted_at.is_(None))
            .order_by(Message.created_at.nulls_first(), Message.id)
            .all()
        )
        
        if not messages:
            return {'prompt_responses': 0, 'content_records': 0}
        
        # Build lookup by ID
        msg_by_id = {m.id: m for m in messages}
        position_by_id = {m.id: i for i, m in enumerate(messages)}
        
        # Track most recent user message for sequential fallback
        last_user_msg: Message | None = None
        
        pr_count = 0
        for msg in messages:
            if msg.role == 'user':
                last_user_msg = msg
                continue
            
            # Find the prompt for this response
            prompt_msg = self._find_prompt(msg, msg_by_id, last_user_msg)
            
            if prompt_msg is None:
                # Response without a prompt (e.g., system greeting)
                continue
            
            # Create prompt-response record
            pr_id = self._create_prompt_response(
                dialogue_id=dialogue_id,
                prompt_msg=prompt_msg,
                response_msg=msg,
                prompt_position=position_by_id[prompt_msg.id],
                response_position=position_by_id[msg.id],
            )
            pr_count += 1
        
        # Build content records
        content_count = self._build_content(dialogue_id)
        
        self.session.flush()
        
        return {
            'prompt_responses': pr_count,
            'content_records': content_count,
        }
    
    def _find_prompt(
        self,
        response_msg: Message,
        msg_by_id: dict[UUID, Message],
        last_user_msg: Message | None,
    ) -> Message | None:
        """Find the user prompt that elicited this response."""
        # Strategy 1: Use parent_id if it points to a user message
        if response_msg.parent_id and response_msg.parent_id in msg_by_id:
            parent = msg_by_id[response_msg.parent_id]
            if parent.role == 'user':
                return parent
            # Parent exists but isn't user - walk up to find user
            # (handles cases like assistant -> tool_result -> assistant)
            current = parent
            visited = {response_msg.id}
            while current and current.id not in visited:
                visited.add(current.id)
                if current.role == 'user':
                    return current
                if current.parent_id and current.parent_id in msg_by_id:
                    current = msg_by_id[current.parent_id]
                else:
                    break
        
        # Strategy 2: Fall back to most recent user message
        return last_user_msg
    
    def _create_prompt_response(
        self,
        dialogue_id: UUID,
        prompt_msg: Message,
        response_msg: Message,
        prompt_position: int,
        response_position: int,
    ) -> UUID:
        """Insert a prompt_response record and return its ID."""
        result = self.session.execute(
            text("""
                INSERT INTO derived.prompt_responses 
                    (dialogue_id, prompt_message_id, response_message_id, 
                     prompt_position, response_position, prompt_role, response_role)
                VALUES 
                    (:dialogue_id, :prompt_id, :response_id,
                     :prompt_pos, :response_pos, :prompt_role, :response_role)
                RETURNING id
            """),
            {
                'dialogue_id': dialogue_id,
                'prompt_id': prompt_msg.id,
                'response_id': response_msg.id,
                'prompt_pos': prompt_position,
                'response_pos': response_position,
                'prompt_role': prompt_msg.role,
                'response_role': response_msg.role,
            }
        )
        return result.scalar_one()
    
    def _build_content(self, dialogue_id: UUID) -> int:
        """Build content records for all prompt-responses in a dialogue."""
        # Use SQL to aggregate text content efficiently
        result = self.session.execute(
            text("""
                INSERT INTO derived.prompt_response_content 
                    (prompt_response_id, prompt_text, response_text, 
                     prompt_word_count, response_word_count)
                SELECT 
                    pr.id,
                    prompt_content.text_content as prompt_text,
                    response_content.text_content as response_text,
                    COALESCE(array_length(regexp_split_to_array(prompt_content.text_content, '\\s+'), 1), 0),
                    COALESCE(array_length(regexp_split_to_array(response_content.text_content, '\\s+'), 1), 0)
                FROM derived.prompt_responses pr
                LEFT JOIN LATERAL (
                    SELECT string_agg(cp.text_content, E'\\n' ORDER BY cp.part_index) as text_content
                    FROM raw.content_parts cp
                    WHERE cp.message_id = pr.prompt_message_id
                      AND cp.part_type = 'text'
                ) prompt_content ON true
                LEFT JOIN LATERAL (
                    SELECT string_agg(cp.text_content, E'\\n' ORDER BY cp.part_index) as text_content
                    FROM raw.content_parts cp
                    WHERE cp.message_id = pr.response_message_id
                      AND cp.part_type = 'text'
                ) response_content ON true
                WHERE pr.dialogue_id = :dialogue_id
                ON CONFLICT (prompt_response_id) DO UPDATE SET
                    prompt_text = EXCLUDED.prompt_text,
                    response_text = EXCLUDED.response_text,
                    prompt_word_count = EXCLUDED.prompt_word_count,
                    response_word_count = EXCLUDED.response_word_count
            """),
            {'dialogue_id': dialogue_id}
        )
        return result.rowcount
    
    def _clear_existing(self, dialogue_id: UUID):
        """Clear existing prompt-response data for a dialogue."""
        self.session.execute(
            text("""
                DELETE FROM derived.prompt_responses 
                WHERE dialogue_id = :dialogue_id
            """),
            {'dialogue_id': dialogue_id}
        )