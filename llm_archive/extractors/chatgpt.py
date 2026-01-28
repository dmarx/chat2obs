# llm_archive/extractors/chatgpt.py
"""ChatGPT conversation extractor."""

from datetime import datetime, timezone
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
    BaseExtractor, parse_timestamp, normalize_role, safe_get, compute_content_hash
)


class ChatGPTExtractor(BaseExtractor):
    """Extracts ChatGPT conversations into the raw schema."""
    
    SOURCE_ID = 'chatgpt'
    
    def __init__(
        self, 
        session: Session, 
        assume_immutable: bool = False,
        incremental: bool = False,
    ):
        super().__init__(session, assume_immutable=assume_immutable, incremental=incremental)
        self.counts = {}
    
    def extract_dialogue(self, raw: dict[str, Any]) -> str | None:
        """
        Extract a complete ChatGPT conversation with incremental updates.
        
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
                # Update existing dialogue metadata
                logger.debug(f"Updating dialogue {source_id}")
                existing.title = raw.get('title')
                existing.updated_at = updated_at
                existing.source_json = raw
                dialogue_id = existing.id
                
                # Incremental message sync
                self._message_id_map = {}
                mapping = raw.get('mapping', {})
                self._sync_messages(dialogue_id, mapping)
                
                return 'updated'
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
            
            # Clear message ID map and extract all messages
            self._message_id_map = {}
            mapping = raw.get('mapping', {})
            self._extract_messages_new(dialogue_id, mapping)
            
            return 'new'
    
    def _sync_messages(self, dialogue_id: UUID, mapping: dict[str, Any]):
        """
        Incrementally sync messages - preserve UUIDs for unchanged messages.
        
        This method:
        1. Compares existing messages with new data (unless assume_immutable=True)
        2. Updates changed messages in place
        3. Creates new messages
        4. Soft-deletes messages removed from source
        
        When assume_immutable=True, existing messages are assumed unchanged and
        skipped without hash comparison. This is faster but won't detect edits.
        """
        existing_messages = self.get_existing_messages(dialogue_id)
        seen_source_ids = set()
        
        # First pass: collect message data
        message_data = {}
        for node_id, node in mapping.items():
            msg_data = node.get('message')
            if not msg_data:
                continue
            
            msg_source_id = msg_data.get('id')
            if not msg_source_id:
                continue
            
            message_data[msg_source_id] = {
                'node': node,
                'msg_data': msg_data,
            }
            seen_source_ids.add(msg_source_id)
        
        # Second pass: sync each message
        for source_id, data in message_data.items():
            msg_data = data['msg_data']
            
            if source_id in existing_messages:
                existing = existing_messages[source_id]
                
                if self.assume_immutable:
                    # Fast path: assume content unchanged, just restore if deleted
                    if existing.deleted_at is not None:
                        existing.deleted_at = None
                        logger.debug(f"Restored message {source_id}")
                    self.register_message_id(source_id, existing.id)
                else:
                    # Full check: compute hash and compare
                    new_hash = compute_content_hash(msg_data)
                    
                    if existing.content_hash == new_hash and existing.deleted_at is None:
                        # Unchanged - just register the ID mapping
                        self.register_message_id(source_id, existing.id)
                    else:
                        # Changed or was soft-deleted - update in place
                        self._update_message(existing, msg_data, new_hash)
                        self.register_message_id(source_id, existing.id)
            else:
                # New message - always compute hash for storage
                new_hash = compute_content_hash(msg_data)
                msg_id = self._create_message(dialogue_id, msg_data, new_hash)
                if msg_id:
                    self.register_message_id(source_id, msg_id)
        
        # Third pass: update parent links (now that all messages exist)
        for source_id, data in message_data.items():
            node = data['node']
            parent_source_id = node.get('parent')
            
            native_id = self.resolve_message_id(source_id)
            parent_native_id = self.resolve_message_id(parent_source_id)
            
            if native_id:
                msg = self.session.get(Message, native_id)
                if msg and msg.parent_id != parent_native_id:
                    msg.parent_id = parent_native_id
        
        # Fourth pass: soft-delete messages no longer in source (unless incremental mode)
        if not self.incremental:
            for source_id, existing in existing_messages.items():
                if source_id not in seen_source_ids and existing.deleted_at is None:
                    existing.deleted_at = datetime.now(timezone.utc)
                    logger.debug(f"Soft-deleted message {source_id}")
    
    def _update_message(self, message: Message, msg_data: dict[str, Any], content_hash: str):
        """Update an existing message in place."""
        # Update message fields
        message.role = normalize_role(safe_get(msg_data, 'author', 'role'), self.SOURCE_ID)
        message.author_id = safe_get(msg_data, 'author', 'metadata', 'user_id')
        message.author_name = safe_get(msg_data, 'author', 'name')
        message.created_at = parse_timestamp(msg_data.get('create_time'))
        message.updated_at = parse_timestamp(msg_data.get('update_time'))
        message.content_hash = content_hash
        message.source_json = msg_data
        
        # Restore if was soft-deleted
        if message.deleted_at is not None:
            message.deleted_at = None
            logger.debug(f"Restored message {message.source_id}")
        
        # Delete related data before re-extracting
        self._delete_message_content(message.id)
        self._delete_message_metadata(message.id)
        
        # Re-extract related data
        self._extract_content_parts(message.id, msg_data)
        self._extract_attachments(message.id, msg_data)
        self._extract_chatgpt_meta(message.id, msg_data)
    
    def _delete_message_metadata(self, message_id: UUID):
        """Delete ChatGPT-specific metadata for a message."""
        self.session.query(ChatGPTMessageMeta).filter(
            ChatGPTMessageMeta.message_id == message_id
        ).delete()
        self.session.query(Attachment).filter(
            Attachment.message_id == message_id
        ).delete()
    
    def _create_message(self, dialogue_id: UUID, msg_data: dict[str, Any], content_hash: str) -> UUID | None:
        """Create a new message."""
        source_id = msg_data.get('id')
        if not source_id:
            return None
        
        message = Message(
            dialogue_id=dialogue_id,
            source_id=source_id,
            parent_id=None,  # Set in later pass
            role=normalize_role(safe_get(msg_data, 'author', 'role'), self.SOURCE_ID),
            author_id=safe_get(msg_data, 'author', 'metadata', 'user_id'),
            author_name=safe_get(msg_data, 'author', 'name'),
            created_at=parse_timestamp(msg_data.get('create_time')),
            updated_at=parse_timestamp(msg_data.get('update_time')),
            content_hash=content_hash,
            source_json=msg_data,
        )
        self.session.add(message)
        self.session.flush()
        
        # Extract content parts and metadata
        self._extract_content_parts(message.id, msg_data)
        self._extract_attachments(message.id, msg_data)
        self._extract_chatgpt_meta(message.id, msg_data)
        
        return message.id
    
    def _extract_messages_new(self, dialogue_id: UUID, mapping: dict[str, Any]):
        """Extract all messages for a new dialogue."""
        # First pass: create all messages without parent links
        for node_id, node in mapping.items():
            msg_data = node.get('message')
            if not msg_data:
                continue
            
            content_hash = compute_content_hash(msg_data)
            msg_id = self._create_message(dialogue_id, msg_data, content_hash)
            if msg_id:
                self.register_message_id(msg_data.get('id'), msg_id)
        
        # Second pass: set parent links
        for node_id, node in mapping.items():
            msg_data = node.get('message')
            if not msg_data:
                continue
            
            source_id = msg_data.get('id')
            parent_source_id = node.get('parent')
            
            native_id = self.resolve_message_id(source_id)
            parent_native_id = self.resolve_message_id(parent_source_id)
            
            if native_id and parent_native_id:
                msg = self.session.get(Message, native_id)
                if msg:
                    msg.parent_id = parent_native_id
    
    def _extract_content_parts(self, message_id: UUID, msg_data: dict[str, Any]):
        """Extract content parts from a message."""
        content = msg_data.get('content', {})
        parts = content.get('parts', [])
        
        for seq, part in enumerate(parts):
            part_info = self._classify_content_part(part)
            
            content_part = ContentPart(
                message_id=message_id,
                sequence=seq,
                part_type=part_info.get('part_type', 'unknown'),
                text_content=part_info.get('text_content'),
                language=part_info.get('language'),
                media_type=part_info.get('media_type'),
                url=part_info.get('url'),
                source_json=part_info.get('source_json', {}),
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
    
    def _classify_content_part(self, part: str | dict[str, Any]) -> dict[str, Any]:
        """
        Classify a content part and extract all relevant fields.
        
        Returns dict with: part_type, text_content, language, media_type, url, source_json
        """
        if isinstance(part, str):
            return {
                'part_type': 'text',
                'text_content': part,
                'source_json': {'text': part},
            }
        
        if not isinstance(part, dict):
            return {
                'part_type': 'unknown',
                'source_json': {'raw': str(part)},
            }
        
        content_type = part.get('content_type', '')
        result = {'source_json': part}
        
        # Image content
        if 'image' in content_type:
            result['part_type'] = 'image'
            result['media_type'] = part.get('content_type')
            
            # Try to find URL in various places
            asset_pointer = part.get('asset_pointer', '')
            if asset_pointer and asset_pointer.startswith('file-service://'):
                result['url'] = asset_pointer
            elif part.get('url'):
                result['url'] = part.get('url')
            
            return result
        
        # Audio content
        if 'audio' in content_type:
            result['part_type'] = 'audio'
            result['media_type'] = part.get('content_type')
            result['url'] = part.get('url') or part.get('asset_pointer')
            return result
        
        # Video content
        if 'video' in content_type:
            result['part_type'] = 'video'
            result['media_type'] = part.get('content_type')
            result['url'] = part.get('url') or part.get('asset_pointer')
            return result
        
        # Code content (from code interpreter)
        if content_type == 'code' or part.get('language'):
            result['part_type'] = 'code'
            result['language'] = part.get('language')
            result['text_content'] = part.get('text') or part.get('code')
            return result
        
        # Text content - might be in various places
        text = part.get('text') or part.get('result') or part.get('content')
        if text and isinstance(text, str):
            result['part_type'] = 'text'
            result['text_content'] = text
            return result
        
        # Fallback
        result['part_type'] = content_type or 'unknown'
        return result
    
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
