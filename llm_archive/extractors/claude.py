# llm_archive/extractors/claude.py
"""Claude conversation extractor."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import (
    Dialogue, Message, ContentPart, Citation, Attachment,
    ClaudeMessageMeta,
)
from llm_archive.extractors.base import (
    BaseExtractor, parse_timestamp, normalize_role, safe_get
)


class ClaudeExtractor(BaseExtractor):
    """Extracts Claude conversations into the raw schema."""
    
    SOURCE_ID = 'claude'
    
    def __init__(self, session: Session):
        super().__init__(session)
    
    def extract_dialogue(self, raw: dict[str, Any]) -> str | None:
        """
        Extract a complete Claude conversation.
        
        Returns:
            'new' - new dialogue created
            'updated' - existing dialogue updated
            'skipped' - existing dialogue unchanged
            None - extraction failed
        """
        source_id = raw.get('uuid')
        if not source_id:
            logger.warning("Conversation missing UUID, skipping")
            return None
        
        updated_at = parse_timestamp(raw.get('updated_at'))
        
        # Check for existing dialogue
        existing = self.get_existing_dialogue(source_id)
        
        if existing:
            if self.should_update(existing, updated_at):
                # Update existing - delete old messages and re-extract
                logger.debug(f"Updating dialogue {source_id}")
                self._delete_dialogue_messages(existing.id)
                existing.title = raw.get('name')
                existing.updated_at = updated_at
                existing.source_json = raw
                dialogue_id = existing.id
                result = 'updated'
            else:
                # Skip - no changes
                logger.debug(f"Skipping unchanged dialogue {source_id}")
                return 'skipped'
        else:
            # Create new dialogue
            dialogue = Dialogue(
                source=self.SOURCE_ID,
                source_id=source_id,
                title=raw.get('name'),
                created_at=parse_timestamp(raw.get('created_at')),
                updated_at=updated_at,
                source_json=raw,
            )
            self.session.add(dialogue)
            self.session.flush()
            dialogue_id = dialogue.id
            result = 'new'
        
        # Clear message ID map for this dialogue
        self._message_id_map = {}
        
        # Extract messages (Claude is linear, so no tree structure)
        chat_messages = raw.get('chat_messages', [])
        prev_message_id = None
        
        for msg_data in chat_messages:
            message_id = self._extract_message(dialogue_id, msg_data, prev_message_id)
            if message_id:
                prev_message_id = message_id
        
        return result
    
    def _delete_dialogue_messages(self, dialogue_id: UUID):
        """Delete all messages for a dialogue (cascade deletes content)."""
        self.session.query(Message).filter(Message.dialogue_id == dialogue_id).delete()
    
    def _extract_message(
        self, 
        dialogue_id: UUID, 
        msg_data: dict[str, Any],
        parent_id: UUID | None
    ) -> UUID | None:
        """Extract a single Claude message."""
        source_id = msg_data.get('uuid')
        if not source_id:
            return None
        
        sender = msg_data.get('sender', 'unknown')
        
        message = Message(
            dialogue_id=dialogue_id,
            source_id=source_id,
            parent_id=parent_id,  # Linear chain
            role=normalize_role(sender, self.SOURCE_ID),
            author_id=None,
            author_name=None,
            created_at=parse_timestamp(msg_data.get('created_at')),
            updated_at=parse_timestamp(msg_data.get('updated_at')),
            source_json=msg_data,
        )
        self.session.add(message)
        self.session.flush()
        
        self.register_message_id(source_id, message.id)
        
        # Extract content parts
        self._extract_content_parts(message.id, msg_data)
        
        # Extract attachments
        self._extract_attachments(message.id, msg_data)
        
        # Extract Claude-specific metadata
        self._extract_claude_meta(message.id, msg_data)
        
        return message.id
    
    def _extract_content_parts(self, message_id: UUID, msg_data: dict[str, Any]):
        """Extract content parts from a Claude message."""
        # Claude has top-level 'text' field and structured 'content' array
        
        # First, add the main text as a content part
        main_text = msg_data.get('text')
        content_array = msg_data.get('content', [])
        
        # If there's structured content, use that
        if content_array:
            for seq, part in enumerate(content_array):
                part_info = self._classify_content_part(part)
                
                content_part = ContentPart(
                    message_id=message_id,
                    sequence=seq,
                    part_type=part_info.get('part_type', 'unknown'),
                    text_content=part_info.get('text_content'),
                    language=part_info.get('language'),
                    media_type=part_info.get('media_type'),
                    url=part_info.get('url'),
                    tool_name=part_info.get('tool_name'),
                    tool_use_id=part_info.get('tool_use_id'),
                    tool_input=part_info.get('tool_input'),
                    started_at=parse_timestamp(part.get('start_timestamp')),
                    ended_at=parse_timestamp(part.get('stop_timestamp')),
                    is_error=part_info.get('is_error') or part.get('is_error', False),
                    source_json=part,
                )
                self.session.add(content_part)
                self.session.flush()
                
                # Extract citations within this content part
                citations = part.get('citations', [])
                if citations:
                    self._extract_citations(content_part.id, citations)
        
        elif main_text:
            # Fall back to main text field
            content_part = ContentPart(
                message_id=message_id,
                sequence=0,
                part_type='text',
                text_content=main_text,
                source_json={'text': main_text},
            )
            self.session.add(content_part)
    
    def _classify_content_part(self, part: dict[str, Any]) -> dict[str, Any]:
        """
        Classify a Claude content part and extract all relevant fields.
        
        Returns dict with: part_type, text_content, tool_name, tool_use_id, tool_input, media_type, url
        """
        part_type = part.get('type', 'unknown').lower()
        
        # Map Claude types to our taxonomy
        type_map = {
            'text': 'text',
            'tool_use': 'tool_use',
            'tool_result': 'tool_result',
            'thinking': 'thinking',
            'image': 'image',
        }
        
        result = {
            'part_type': type_map.get(part_type, part_type),
        }
        
        # Extract fields based on type
        if part_type == 'text':
            result['text_content'] = part.get('text')
        
        elif part_type == 'thinking':
            result['text_content'] = part.get('thinking')
        
        elif part_type == 'tool_use':
            result['tool_name'] = part.get('name')
            result['tool_use_id'] = part.get('id')
            result['tool_input'] = part.get('input')
            # Some tools have text output
            if isinstance(part.get('input'), dict):
                # Try to capture any query or text input
                result['text_content'] = part['input'].get('query') or part['input'].get('text')
        
        elif part_type == 'tool_result':
            result['tool_use_id'] = part.get('tool_use_id')
            result['is_error'] = part.get('is_error', False)
            
            # Tool results might have text in various places
            content = part.get('content')
            if isinstance(content, str):
                result['text_content'] = content
            elif isinstance(content, list):
                # Concatenate text from nested content
                texts = []
                for item in content:
                    if isinstance(item, dict) and item.get('text'):
                        texts.append(item['text'])
                    elif isinstance(item, str):
                        texts.append(item)
                result['text_content'] = '\n'.join(texts) if texts else None
        
        elif part_type == 'image':
            result['media_type'] = part.get('media_type')
            # Claude images might have URL or base64 source
            source = part.get('source', {})
            if source.get('type') == 'url':
                result['url'] = source.get('url')
            # base64 data stays in source_json
        
        return result
    
    def _extract_citations(self, content_part_id: UUID, citations: list[dict[str, Any]]):
        """Extract citations from a content part."""
        for cit in citations:
            details = cit.get('details', {})
            
            citation = Citation(
                content_part_id=content_part_id,
                source_id=cit.get('uuid'),
                url=details.get('url'),
                title=None,  # Claude citations don't include title
                snippet=None,
                published_at=None,
                start_index=cit.get('start_index'),
                end_index=cit.get('end_index'),
                citation_type=details.get('type'),
                source_json=cit,
            )
            self.session.add(citation)
    
    def _extract_attachments(self, message_id: UUID, msg_data: dict[str, Any]):
        """Extract attachments from a Claude message."""
        attachments = msg_data.get('attachments', [])
        
        for att in attachments:
            attachment = Attachment(
                message_id=message_id,
                file_name=att.get('file_name'),
                file_type=att.get('file_type'),
                file_size=att.get('file_size'),
                extracted_text=att.get('extracted_content'),
                source_json=att,
            )
            self.session.add(attachment)
        
        # Also check 'files' array
        files = msg_data.get('files', [])
        for f in files:
            # Files array is simpler, just has file_name
            if isinstance(f, dict) and f.get('file_name'):
                attachment = Attachment(
                    message_id=message_id,
                    file_name=f.get('file_name'),
                    source_json=f,
                )
                self.session.add(attachment)
    
    def _extract_claude_meta(self, message_id: UUID, msg_data: dict[str, Any]):
        """Extract Claude-specific metadata."""
        # For now, just store the raw message data
        # We can add specific fields as we discover what's useful
        meta = ClaudeMessageMeta(
            message_id=message_id,
            source_json=msg_data,
        )
        self.session.add(meta)
