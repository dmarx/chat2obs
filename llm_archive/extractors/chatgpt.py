# llm_archive/extractors/chatgpt.py
"""ChatGPT conversation extractor."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import (
    Dialogue, Message, ContentPart, Citation, Attachment,
    ChatGPTMessageMeta, ChatGPTSearchGroup, ChatGPTSearchEntry,
    ChatGPTCodeExecution, ChatGPTCodeOutput, ChatGPTDalleGeneration,
    ChatGPTCanvasDoc,
)
from llm_archive.extractors.base import (
    BaseExtractor, parse_timestamp, normalize_role, safe_get
)


class ChatGPTExtractor(BaseExtractor):
    """Extracts ChatGPT conversations into the raw schema."""
    
    SOURCE_ID = 'chatgpt'
    
    def __init__(self, session: Session):
        super().__init__(session)
        self.counts = {}
    
    def extract_dialogue(self, raw: dict[str, Any]) -> str | None:
        """
        Extract a complete ChatGPT conversation.
        
        Returns:
            'new' - new dialogue created
            'updated' - existing dialogue updated
            'skipped' - existing dialogue unchanged
            None - extraction failed
        """
        source_id = raw.get('conversation_id') or raw.get('id')
        if not source_id:
            logger.warning("Conversation missing ID, skipping")
            return None
        
        updated_at = parse_timestamp(raw.get('update_time'))
        
        # Check for existing dialogue
        existing = self.get_existing_dialogue(source_id)
        
        if existing:
            if self.should_update(existing, updated_at):
                # Update existing - delete old messages and re-extract
                logger.debug(f"Updating dialogue {source_id}")
                self._delete_dialogue_messages(existing.id)
                existing.title = raw.get('title')
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
                title=raw.get('title'),
                created_at=parse_timestamp(raw.get('create_time')),
                updated_at=updated_at,
                source_json=raw,
            )
            self.session.add(dialogue)
            self.session.flush()
            dialogue_id = dialogue.id
            result = 'new'
        
        # Clear message ID map for this dialogue
        self._message_id_map = {}
        
        # Extract messages from mapping
        mapping = raw.get('mapping', {})
        self._extract_messages(dialogue_id, mapping)
        
        return result
    
    def _delete_dialogue_messages(self, dialogue_id: UUID):
        """Delete all messages for a dialogue (cascade deletes content)."""
        self.session.query(Message).filter(Message.dialogue_id == dialogue_id).delete()
    
    def _extract_messages(self, dialogue_id: UUID, mapping: dict[str, Any]):
        """Extract all messages from the mapping tree."""
        # First pass: create all messages without parent links
        for node_id, node in mapping.items():
            msg_data = node.get('message')
            if not msg_data:
                continue
            
            author = msg_data.get('author', {})
            role = author.get('role')
            if not role:
                continue
            
            source_id = msg_data.get('id', node_id)
            
            message = Message(
                dialogue_id=dialogue_id,
                source_id=source_id,
                parent_id=None,  # Set in second pass
                role=normalize_role(role, self.SOURCE_ID),
                author_id=author.get('name'),
                author_name=author.get('name'),
                created_at=parse_timestamp(msg_data.get('create_time')),
                updated_at=parse_timestamp(msg_data.get('update_time')),
                source_json=node,
            )
            self.session.add(message)
            self.session.flush()
            
            # Register for parent resolution
            self.register_message_id(node_id, message.id)
            if source_id != node_id:
                self.register_message_id(source_id, message.id)
            
            # Extract content parts
            self._extract_content_parts(message.id, msg_data)
            
            # Extract ChatGPT-specific metadata
            self._extract_chatgpt_meta(message.id, msg_data)
            
            # Extract attachments
            self._extract_attachments(message.id, msg_data)
        
        # Second pass: set parent links
        for node_id, node in mapping.items():
            parent_node_id = node.get('parent')
            if not parent_node_id:
                continue
            
            message_id = self.resolve_message_id(node_id)
            parent_id = self.resolve_message_id(parent_node_id)
            
            if message_id and parent_id:
                self.session.execute(
                    Message.__table__.update()
                    .where(Message.id == message_id)
                    .values(parent_id=parent_id)
                )
    
    def _extract_content_parts(self, message_id: UUID, msg_data: dict[str, Any]):
        """Extract content parts from a message."""
        content = msg_data.get('content', {})
        parts = content.get('parts', [])
        
        for seq, part in enumerate(parts):
            part_type, text_content, part_json = self._classify_content_part(part)
            
            content_part = ContentPart(
                message_id=message_id,
                sequence=seq,
                part_type=part_type,
                text_content=text_content,
                source_json=part_json,
            )
            self.session.add(content_part)
            self.session.flush()
            
            # Extract DALL-E generations if present
            if isinstance(part, dict):
                self._extract_dalle_generation(content_part.id, part)
        
        # Extract citations from metadata
        metadata = msg_data.get('metadata', {})
        citations = metadata.get('citations', [])
        
        # Link citations to first text content part (if any)
        if citations and parts:
            first_part = self.session.query(ContentPart).filter(
                ContentPart.message_id == message_id,
                ContentPart.sequence == 0
            ).first()
            
            if first_part:
                self._extract_citations(first_part.id, citations)
    
    def _classify_content_part(self, part: str | dict[str, Any]) -> tuple[str, str | None, dict]:
        """Classify a content part and extract text."""
        if isinstance(part, str):
            return 'text', part, {'text': part}
        
        if not isinstance(part, dict):
            return 'unknown', None, {'raw': str(part)}
        
        content_type = part.get('content_type', '')
        
        if 'image' in content_type:
            return 'image', None, part
        if 'audio' in content_type:
            return 'audio', None, part
        if 'video' in content_type:
            return 'video', None, part
        
        # Text might be in various places
        text = part.get('text') or part.get('result') or part.get('content')
        if text and isinstance(text, str):
            return 'text', text, part
        
        return content_type or 'unknown', None, part
    
    def _extract_citations(self, content_part_id: UUID, citations: list[dict[str, Any]]):
        """Extract citations from metadata."""
        for cit in citations:
            meta = cit.get('metadata', {})
            
            citation = Citation(
                content_part_id=content_part_id,
                source_id=None,
                url=meta.get('url'),
                title=meta.get('title'),
                snippet=meta.get('text'),
                published_at=parse_timestamp(meta.get('pub_date')),
                start_index=cit.get('start_ix'),
                end_index=cit.get('end_ix'),
                citation_type=meta.get('type'),
                source_json=cit,
            )
            self.session.add(citation)
    
    def _extract_attachments(self, message_id: UUID, msg_data: dict[str, Any]):
        """Extract attachments from message metadata."""
        metadata = msg_data.get('metadata', {})
        attachments = metadata.get('attachments', [])
        
        for att in attachments:
            attachment = Attachment(
                message_id=message_id,
                file_name=att.get('name'),
                file_type=att.get('mime_type') or att.get('mimeType'),
                file_size=att.get('size'),
                extracted_text=None,  # ChatGPT doesn't provide this
                source_json=att,
            )
            self.session.add(attachment)
    
    def _extract_chatgpt_meta(self, message_id: UUID, msg_data: dict[str, Any]):
        """Extract ChatGPT-specific metadata."""
        metadata = msg_data.get('metadata', {})
        
        # Message metadata
        meta = ChatGPTMessageMeta(
            message_id=message_id,
            model_slug=metadata.get('model_slug'),
            status=msg_data.get('status'),
            end_turn=msg_data.get('end_turn'),
            gizmo_id=metadata.get('gizmo_id'),
            source_json=metadata,
        )
        self.session.add(meta)
        
        # Search result groups
        search_groups = metadata.get('search_result_groups', [])
        for group_data in search_groups:
            self._extract_search_group(message_id, group_data)
        
        # Code executions
        agg_result = metadata.get('aggregate_result')
        if agg_result:
            self._extract_code_execution(message_id, agg_result)
        
        # Canvas documents
        canvas = metadata.get('canvas')
        if canvas:
            self._extract_canvas_doc(message_id, canvas)
    
    def _extract_search_group(self, message_id: UUID, group_data: dict[str, Any]):
        """Extract a search result group and its entries."""
        group = ChatGPTSearchGroup(
            message_id=message_id,
            group_type=group_data.get('type'),
            domain=group_data.get('domain'),
            source_json=group_data,
        )
        self.session.add(group)
        self.session.flush()
        
        entries = group_data.get('entries', [])
        for seq, entry_data in enumerate(entries):
            entry = ChatGPTSearchEntry(
                group_id=group.id,
                sequence=seq,
                url=entry_data.get('url'),
                title=entry_data.get('title'),
                snippet=entry_data.get('snippet'),
                published_at=parse_timestamp(entry_data.get('pub_date')),
                attribution=entry_data.get('attribution'),
                source_json=entry_data,
            )
            self.session.add(entry)
    
    def _extract_code_execution(self, message_id: UUID, agg_result: dict[str, Any]):
        """Extract code execution data."""
        exception = agg_result.get('in_kernel_exception') or {}
        
        execution = ChatGPTCodeExecution(
            message_id=message_id,
            run_id=agg_result.get('run_id'),
            status=agg_result.get('status'),
            code=agg_result.get('code'),
            started_at=parse_timestamp(agg_result.get('start_time')),
            ended_at=parse_timestamp(agg_result.get('end_time')),
            final_output=agg_result.get('final_expression_output'),
            exception_name=exception.get('name'),
            exception_traceback='\n'.join(exception.get('traceback', [])) or None,
            source_json=agg_result,
        )
        self.session.add(execution)
        self.session.flush()
        
        # Extract outputs
        messages = agg_result.get('messages', [])
        for seq, msg in enumerate(messages):
            output = ChatGPTCodeOutput(
                execution_id=execution.id,
                sequence=seq,
                output_type=msg.get('message_type'),
                stream_name=msg.get('stream_name'),
                text_content=msg.get('text'),
                image_url=msg.get('image_url'),
                source_json=msg,
            )
            self.session.add(output)
    
    def _extract_dalle_generation(self, content_part_id: UUID, part: dict[str, Any]):
        """Extract DALL-E generation data from a content part."""
        metadata = part.get('metadata') or {}
        dalle = metadata.get('dalle') or metadata.get('generation')
        
        if not dalle:
            return
        
        generation = ChatGPTDalleGeneration(
            content_part_id=content_part_id,
            gen_id=dalle.get('gen_id'),
            prompt=dalle.get('prompt'),
            seed=dalle.get('seed'),
            parent_gen_id=dalle.get('parent_gen_id'),
            edit_op=dalle.get('edit_op'),
            width=dalle.get('width') or part.get('width'),
            height=dalle.get('height') or part.get('height'),
            source_json=dalle,
        )
        self.session.add(generation)
    
    def _extract_canvas_doc(self, message_id: UUID, canvas: dict[str, Any]):
        """Extract canvas document data."""
        doc = ChatGPTCanvasDoc(
            message_id=message_id,
            textdoc_id=canvas.get('textdoc_id'),
            textdoc_type=canvas.get('textdoc_type'),
            version=canvas.get('version'),
            title=canvas.get('title'),
            from_version=canvas.get('from_version'),
            content_length=canvas.get('textdoc_content_length'),
            has_user_edit=canvas.get('has_user_edit'),
            source_json=canvas,
        )
        self.session.add(doc)
