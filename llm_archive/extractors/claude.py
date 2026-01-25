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
from llm_archive.extractors.base import BaseExtractor, parse_timestamp, normalize_role


class ClaudeExtractor(BaseExtractor):
    """Extracts Claude conversations into the raw schema."""
    
    SOURCE_ID = 'claude'
    
    def extract_dialogue(self, raw: dict[str, Any]) -> UUID | None:
        """Extract a complete Claude conversation."""
        source_id = raw.get('uuid')
        if not source_id:
            logger.warning("Conversation missing UUID")
            return None
        
        dialogue = Dialogue(
            source=self.SOURCE_ID,
            source_id=source_id,
            title=raw.get('name'),
            created_at=parse_timestamp(raw.get('created_at')),
            updated_at=parse_timestamp(raw.get('updated_at')),
            source_json=raw,
        )
        self.session.add(dialogue)
        self.session.flush()
        
        self._message_id_map = {}
        
        # Claude is linear, so we chain messages via parent_id
        chat_messages = raw.get('chat_messages', [])
        prev_message_id = None
        
        for msg_data in chat_messages:
            message_id = self._extract_message(dialogue.id, msg_data, prev_message_id)
            if message_id:
                prev_message_id = message_id
        
        return dialogue.id
    
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
            parent_id=parent_id,
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
        
        self._extract_content_parts(message.id, msg_data)
        self._extract_attachments(message.id, msg_data)
        self._extract_claude_meta(message.id, msg_data)
        
        return message.id
    
    def _extract_content_parts(self, message_id: UUID, msg_data: dict[str, Any]):
        """Extract content parts from a Claude message."""
        main_text = msg_data.get('text')
        content_array = msg_data.get('content', [])
        
        if content_array:
            for seq, part in enumerate(content_array):
                part_type, text_content = self._classify_content_part(part)
                
                content_part = ContentPart(
                    message_id=message_id,
                    sequence=seq,
                    part_type=part_type,
                    text_content=text_content,
                    started_at=parse_timestamp(part.get('start_timestamp')),
                    ended_at=parse_timestamp(part.get('stop_timestamp')),
                    is_error=part.get('is_error', False),
                    source_json=part,
                )
                self.session.add(content_part)
                self.session.flush()
                
                citations = part.get('citations', [])
                if citations:
                    self._extract_citations(content_part.id, citations)
        
        elif main_text:
            content_part = ContentPart(
                message_id=message_id,
                sequence=0,
                part_type='text',
                text_content=main_text,
                source_json={'text': main_text},
            )
            self.session.add(content_part)
    
    def _classify_content_part(self, part: dict[str, Any]) -> tuple[str, str | None]:
        """Classify a Claude content part and extract text."""
        part_type = part.get('type', 'unknown').lower()
        
        type_map = {
            'text': 'text',
            'tool_use': 'tool_use',
            'tool_result': 'tool_result',
            'thinking': 'thinking',
        }
        
        normalized_type = type_map.get(part_type, part_type)
        
        text_content = None
        
        if part_type == 'text':
            text_content = part.get('text')
        elif part_type == 'thinking':
            text_content = part.get('thinking')
        elif part_type == 'tool_result':
            content = part.get('content')
            if isinstance(content, str):
                text_content = content
            elif isinstance(content, list):
                texts = []
                for item in content:
                    if isinstance(item, dict) and item.get('text'):
                        texts.append(item['text'])
                    elif isinstance(item, str):
                        texts.append(item)
                text_content = '\n'.join(texts) if texts else None
        
        return normalized_type, text_content
    
    def _extract_citations(self, content_part_id: UUID, citations: list[dict[str, Any]]):
        """Extract citations from a content part."""
        for cit in citations:
            details = cit.get('details', {})
            
            citation = Citation(
                content_part_id=content_part_id,
                source_id=cit.get('uuid'),
                url=details.get('url'),
                start_index=cit.get('start_index'),
                end_index=cit.get('end_index'),
                citation_type=details.get('type'),
                source_json=cit,
            )
            self.session.add(citation)
    
    def _extract_attachments(self, message_id: UUID, msg_data: dict[str, Any]):
        """Extract attachments from a Claude message."""
        for att in msg_data.get('attachments', []):
            attachment = Attachment(
                message_id=message_id,
                file_name=att.get('file_name'),
                file_type=att.get('file_type'),
                file_size=att.get('file_size'),
                extracted_text=att.get('extracted_content'),
                source_json=att,
            )
            self.session.add(attachment)
        
        for f in msg_data.get('files', []):
            if isinstance(f, dict) and f.get('file_name'):
                attachment = Attachment(
                    message_id=message_id,
                    file_name=f.get('file_name'),
                    source_json=f,
                )
                self.session.add(attachment)
    
    def _extract_claude_meta(self, message_id: UUID, msg_data: dict[str, Any]):
        """Extract Claude-specific metadata."""
        meta = ClaudeMessageMeta(
            message_id=message_id,
            source_json=msg_data,
        )
        self.session.add(meta)