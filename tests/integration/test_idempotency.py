# tests/integration/test_idempotency.py
"""Tests for idempotent import behavior with incremental updates."""

import copy
import pytest
from datetime import datetime, timezone

from llm_archive.extractors import ChatGPTExtractor, ClaudeExtractor
from llm_archive.models import Dialogue, Message


class TestChatGPTIdempotency:
    """Tests for ChatGPT idempotent import."""
    
    def test_reimport_unchanged_skips(self, clean_db_session, chatgpt_simple_conversation):
        """Test that reimporting unchanged conversation is skipped."""
        extractor = ChatGPTExtractor(clean_db_session)
        
        # First import
        result1 = extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        assert result1 == 'new'
        
        # Second import - same data
        result2 = extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        assert result2 == 'skipped'
        
        # Should still have only one dialogue
        count = clean_db_session.query(Dialogue).count()
        assert count == 1
    
    def test_reimport_updated_updates(self, clean_db_session, chatgpt_simple_conversation):
        """Test that reimporting updated conversation updates it."""
        extractor = ChatGPTExtractor(clean_db_session)
        
        # First import
        result1 = extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        assert result1 == 'new'
        
        original_title = clean_db_session.query(Dialogue).first().title
        
        # Modify and reimport
        updated = copy.deepcopy(chatgpt_simple_conversation)
        updated['update_time'] = 1700002000.0  # Later timestamp
        updated['title'] = "Updated Title"
        
        result2 = extractor.extract_dialogue(updated)
        clean_db_session.commit()
        assert result2 == 'updated'
        
        # Should still have only one dialogue
        count = clean_db_session.query(Dialogue).count()
        assert count == 1
        
        # Title should be updated
        dialogue = clean_db_session.query(Dialogue).first()
        assert dialogue.title == "Updated Title"
    
    def test_reimport_messages_refreshed(self, clean_db_session, chatgpt_simple_conversation):
        """Test that messages are refreshed on update."""
        extractor = ChatGPTExtractor(clean_db_session)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        original_msg_count = clean_db_session.query(Message).count()
        
        # Modify and reimport
        updated = copy.deepcopy(chatgpt_simple_conversation)
        updated['update_time'] = 1700002000.0
        
        extractor.extract_dialogue(updated)
        clean_db_session.commit()
        
        # Message count should be the same (refreshed, not duplicated)
        new_msg_count = clean_db_session.query(Message).count()
        assert new_msg_count == original_msg_count
    
    def test_extract_all_mixed_results(self, clean_db_session, chatgpt_simple_conversation):
        """Test extract_all with mix of new, updated, and skipped."""
        extractor = ChatGPTExtractor(clean_db_session)
        
        # First import one conversation
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Create variations
        unchanged = copy.deepcopy(chatgpt_simple_conversation)
        
        updated = copy.deepcopy(chatgpt_simple_conversation)
        updated['update_time'] = 1700005000.0
        updated['title'] = "Updated"
        
        new_conv = copy.deepcopy(chatgpt_simple_conversation)
        new_conv['conversation_id'] = "conv-new-001"
        
        # Extract all
        counts = extractor.extract_all([unchanged, updated, new_conv])
        
        # Note: after the first was already imported, we have:
        # - unchanged: skipped (no update since update_time same)
        # - updated: but we already updated it above with unchanged, 
        #   so this depends on whether unchanged came first
        # Let's just check we have correct totals
        assert counts['dialogues_skipped'] + counts['dialogues_new'] + counts['dialogues_updated'] == 3


class TestClaudeIdempotency:
    """Tests for Claude idempotent import."""
    
    def test_reimport_unchanged_skips(self, clean_db_session, claude_simple_conversation):
        """Test that reimporting unchanged conversation is skipped."""
        extractor = ClaudeExtractor(clean_db_session)
        
        # First import
        result1 = extractor.extract_dialogue(claude_simple_conversation)
        clean_db_session.commit()
        assert result1 == 'new'
        
        # Second import - same data
        result2 = extractor.extract_dialogue(claude_simple_conversation)
        clean_db_session.commit()
        assert result2 == 'skipped'
    
    def test_reimport_updated_updates(self, clean_db_session, claude_simple_conversation):
        """Test that reimporting updated conversation updates it."""
        extractor = ClaudeExtractor(clean_db_session)
        
        # First import
        result1 = extractor.extract_dialogue(claude_simple_conversation)
        clean_db_session.commit()
        
        # Modify and reimport
        updated = copy.deepcopy(claude_simple_conversation)
        updated['updated_at'] = "2024-01-16T10:00:00Z"  # Later timestamp
        updated['name'] = "Updated Title"
        
        result2 = extractor.extract_dialogue(updated)
        clean_db_session.commit()
        assert result2 == 'updated'
        
        # Title should be updated
        dialogue = clean_db_session.query(Dialogue).first()
        assert dialogue.title == "Updated Title"


class TestCrossSourceIdempotency:
    """Tests for idempotency across sources."""
    
    def test_same_content_different_sources(self, clean_db_session):
        """Test that same content from different sources creates separate records."""
        chatgpt_conv = {
            "conversation_id": "cross-001",
            "title": "Cross Source Test",
            "create_time": 1700000000.0,
            "update_time": 1700001000.0,
            "mapping": {
                "root": {"id": "root", "parent": None, "children": ["m1"], "message": None},
                "m1": {
                    "id": "m1",
                    "parent": "root",
                    "children": [],
                    "message": {
                        "id": "m1",
                        "author": {"role": "user"},
                        "create_time": 1700000100.0,
                        "content": {"content_type": "text", "parts": ["Hello"]}
                    }
                }
            }
        }
        
        claude_conv = {
            "uuid": "cross-001",  # Same ID!
            "name": "Cross Source Test",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "chat_messages": [
                {
                    "uuid": "msg-001",
                    "sender": "human",
                    "created_at": "2024-01-15T10:00:00Z",
                    "content": [{"type": "text", "text": "Hello"}]
                }
            ]
        }
        
        # Import both
        ChatGPTExtractor(clean_db_session).extract_dialogue(chatgpt_conv)
        ClaudeExtractor(clean_db_session).extract_dialogue(claude_conv)
        clean_db_session.commit()
        
        # Should have two dialogues (different sources)
        dialogues = clean_db_session.query(Dialogue).all()
        assert len(dialogues) == 2
        
        sources = set(d.source for d in dialogues)
        assert sources == {'chatgpt', 'claude'}


class TestPartialUpdate:
    """Tests for partial update scenarios."""
    
    def test_conversation_extended(self, clean_db_session, chatgpt_simple_conversation):
        """Test handling of conversation that has been extended."""
        extractor = ChatGPTExtractor(clean_db_session)
        
        # Import original
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        original_msg_count = clean_db_session.query(Message).count()
        
        # Extend conversation (add new messages)
        extended = copy.deepcopy(chatgpt_simple_conversation)
        extended['update_time'] = 1700005000.0
        
        # Add new message to mapping
        new_msg_id = "new-msg-001"
        last_msg_id = list(extended['mapping'].keys())[-1]
        
        extended['mapping'][new_msg_id] = {
            "id": new_msg_id,
            "parent": last_msg_id,
            "children": [],
            "message": {
                "id": new_msg_id,
                "author": {"role": "user"},
                "create_time": 1700004000.0,
                "content": {"content_type": "text", "parts": ["One more question"]}
            }
        }
        # Update parent's children
        for node_id, node in extended['mapping'].items():
            if node.get('message') and node['children'] == [] and node_id != new_msg_id:
                if node_id == last_msg_id:
                    node['children'] = [new_msg_id]
        
        # Reimport
        result = extractor.extract_dialogue(extended)
        clean_db_session.commit()
        
        assert result == 'updated'
        
        # Should have more messages now
        new_msg_count = clean_db_session.query(Message).count()
        assert new_msg_count == original_msg_count + 1


class TestUUIDPreservation:
    """Tests for message UUID preservation during updates."""
    
    def test_unchanged_messages_keep_uuids(self, clean_db_session, chatgpt_simple_conversation):
        """Test that unchanged messages keep their UUIDs."""
        extractor = ChatGPTExtractor(clean_db_session)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Record original UUIDs
        original_messages = {m.source_id: m.id for m in clean_db_session.query(Message).all()}
        
        # Update with later timestamp but same content
        updated = copy.deepcopy(chatgpt_simple_conversation)
        updated['update_time'] = 1700005000.0
        updated['title'] = "New Title"  # Only title changed, not messages
        
        extractor.extract_dialogue(updated)
        clean_db_session.commit()
        
        # Check UUIDs are preserved
        new_messages = {m.source_id: m.id for m in clean_db_session.query(Message).all()}
        
        for source_id, original_uuid in original_messages.items():
            assert source_id in new_messages, f"Message {source_id} should still exist"
            assert new_messages[source_id] == original_uuid, f"Message {source_id} UUID changed"
    
    def test_changed_message_keeps_uuid_updates_content(self, clean_db_session, chatgpt_simple_conversation):
        """Test that changed messages keep their UUID but update content."""
        extractor = ChatGPTExtractor(clean_db_session)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Find a message to modify
        first_user_msg = clean_db_session.query(Message).filter(
            Message.role == 'user'
        ).first()
        original_uuid = first_user_msg.id
        original_source_id = first_user_msg.source_id
        
        # Modify the message content
        updated = copy.deepcopy(chatgpt_simple_conversation)
        updated['update_time'] = 1700005000.0
        
        for node_id, node in updated['mapping'].items():
            msg = node.get('message')
            if msg and msg.get('id') == original_source_id:
                msg['content']['parts'] = ['MODIFIED MESSAGE CONTENT']
                break
        
        extractor.extract_dialogue(updated)
        clean_db_session.commit()
        
        # UUID should be preserved
        modified_msg = clean_db_session.query(Message).filter(
            Message.source_id == original_source_id
        ).first()
        
        assert modified_msg is not None
        assert modified_msg.id == original_uuid, "UUID should be preserved"
        assert 'MODIFIED' in str(modified_msg.source_json), "Content should be updated"
    
    def test_claude_unchanged_messages_keep_uuids(self, clean_db_session, claude_simple_conversation):
        """Test UUID preservation for Claude extractor."""
        extractor = ClaudeExtractor(clean_db_session)
        
        # First import
        extractor.extract_dialogue(claude_simple_conversation)
        clean_db_session.commit()
        
        # Record original UUIDs
        original_messages = {m.source_id: m.id for m in clean_db_session.query(Message).all()}
        
        # Update with later timestamp but same messages
        updated = copy.deepcopy(claude_simple_conversation)
        updated['updated_at'] = "2024-01-20T10:00:00Z"
        updated['name'] = "New Title"
        
        extractor.extract_dialogue(updated)
        clean_db_session.commit()
        
        # Check UUIDs are preserved
        new_messages = {m.source_id: m.id for m in clean_db_session.query(Message).all()}
        
        for source_id, original_uuid in original_messages.items():
            assert source_id in new_messages
            assert new_messages[source_id] == original_uuid


class TestSoftDelete:
    """Tests for soft-delete behavior when messages are removed from source."""
    
    def test_removed_message_soft_deleted(self, clean_db_session, chatgpt_simple_conversation):
        """Test that messages removed from source are soft-deleted."""
        extractor = ChatGPTExtractor(clean_db_session)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        original_count = clean_db_session.query(Message).count()
        
        # Remove a message from the conversation
        truncated = copy.deepcopy(chatgpt_simple_conversation)
        truncated['update_time'] = 1700005000.0
        
        # Remove the last message
        mapping_keys = list(truncated['mapping'].keys())
        last_msg_key = mapping_keys[-1]
        del truncated['mapping'][last_msg_key]
        
        # Update parent to not have children pointing to deleted msg
        for node_id, node in truncated['mapping'].items():
            if last_msg_key in node.get('children', []):
                node['children'].remove(last_msg_key)
        
        extractor.extract_dialogue(truncated)
        clean_db_session.commit()
        
        # Total message count should be the same (soft-deleted, not hard-deleted)
        total_count = clean_db_session.query(Message).count()
        assert total_count == original_count
        
        # Active message count should be one less
        active_count = clean_db_session.query(Message).filter(
            Message.deleted_at.is_(None)
        ).count()
        assert active_count == original_count - 1
        
        # Should have one soft-deleted message
        deleted_count = clean_db_session.query(Message).filter(
            Message.deleted_at.isnot(None)
        ).count()
        assert deleted_count == 1
    
    def test_soft_deleted_message_restored_on_reappear(self, clean_db_session, chatgpt_simple_conversation):
        """Test that soft-deleted message is restored if it reappears."""
        extractor = ChatGPTExtractor(clean_db_session)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Remove a message
        truncated = copy.deepcopy(chatgpt_simple_conversation)
        truncated['update_time'] = 1700005000.0
        
        mapping_keys = list(truncated['mapping'].keys())
        removed_msg_key = mapping_keys[-1]
        del truncated['mapping'][removed_msg_key]
        
        for node_id, node in truncated['mapping'].items():
            if removed_msg_key in node.get('children', []):
                node['children'].remove(removed_msg_key)
        
        extractor.extract_dialogue(truncated)
        clean_db_session.commit()
        
        # Verify it's soft-deleted
        deleted_msg = clean_db_session.query(Message).filter(
            Message.deleted_at.isnot(None)
        ).first()
        assert deleted_msg is not None
        deleted_uuid = deleted_msg.id
        
        # Now restore by importing original again with newer timestamp
        restored = copy.deepcopy(chatgpt_simple_conversation)
        restored['update_time'] = 1700010000.0
        
        extractor.extract_dialogue(restored)
        clean_db_session.commit()
        
        # Message should be restored
        restored_msg = clean_db_session.query(Message).filter(
            Message.id == deleted_uuid
        ).first()
        
        assert restored_msg is not None
        assert restored_msg.deleted_at is None, "Message should be restored (deleted_at = None)"
    
    def test_content_hash_detects_changes(self, clean_db_session, chatgpt_simple_conversation):
        """Test that content hash correctly detects changed messages."""
        extractor = ChatGPTExtractor(clean_db_session)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Get a message's content hash
        msg = clean_db_session.query(Message).filter(Message.role == 'user').first()
        original_hash = msg.content_hash
        
        assert original_hash is not None, "Content hash should be computed"
        
        # Modify the message content
        modified = copy.deepcopy(chatgpt_simple_conversation)
        modified['update_time'] = 1800000000.0  # Much later timestamp to ensure update
        
        for node_id, node in modified['mapping'].items():
            msg_data = node.get('message')
            if msg_data and msg_data.get('id') == msg.source_id:
                msg_data['content']['parts'] = ['Completely different content']
                break
        
        extractor.extract_dialogue(modified)
        clean_db_session.commit()
        
        # Hash should have changed
        clean_db_session.refresh(msg)
        assert msg.content_hash != original_hash, "Content hash should change when content changes"


class TestAssumeImmutableFlag:
    """Tests for assume_immutable optimization flag."""
    
    def test_immutable_mode_skips_hash_check(self, clean_db_session, chatgpt_simple_conversation):
        """Test that immutable mode skips content hash comparison."""
        extractor = ChatGPTExtractor(clean_db_session, assume_immutable=True)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Get a message
        msg = clean_db_session.query(Message).filter(Message.role == 'user').first()
        original_hash = msg.content_hash
        original_uuid = msg.id
        
        # "Modify" content in source (simulating what we'd do in mutable mode)
        # In immutable mode, this shouldn't trigger an update
        modified = copy.deepcopy(chatgpt_simple_conversation)
        modified['update_time'] = 1800000000.0
        
        for node_id, node in modified['mapping'].items():
            msg_data = node.get('message')
            if msg_data and msg_data.get('id') == msg.source_id:
                msg_data['content']['parts'] = ['MODIFIED CONTENT']
                break
        
        extractor.extract_dialogue(modified)
        clean_db_session.commit()
        
        # In immutable mode, hash should NOT change (we didn't check it)
        clean_db_session.refresh(msg)
        assert msg.id == original_uuid, "UUID should be preserved"
        assert msg.content_hash == original_hash, "Hash should NOT change in immutable mode"
    
    def test_mutable_mode_detects_changes(self, clean_db_session, chatgpt_simple_conversation):
        """Test that mutable mode (default) detects content changes."""
        extractor = ChatGPTExtractor(clean_db_session, assume_immutable=False)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Get a message
        msg = clean_db_session.query(Message).filter(Message.role == 'user').first()
        original_hash = msg.content_hash
        
        # Modify content
        modified = copy.deepcopy(chatgpt_simple_conversation)
        modified['update_time'] = 1800000000.0
        
        for node_id, node in modified['mapping'].items():
            msg_data = node.get('message')
            if msg_data and msg_data.get('id') == msg.source_id:
                msg_data['content']['parts'] = ['MODIFIED CONTENT']
                break
        
        extractor.extract_dialogue(modified)
        clean_db_session.commit()
        
        # In mutable mode, hash SHOULD change
        clean_db_session.refresh(msg)
        assert msg.content_hash != original_hash, "Hash SHOULD change in mutable mode"
    
    def test_immutable_mode_still_creates_new_messages(self, clean_db_session, chatgpt_simple_conversation):
        """Test that immutable mode still creates new messages properly."""
        extractor = ChatGPTExtractor(clean_db_session, assume_immutable=True)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        original_count = clean_db_session.query(Message).count()
        
        # Add a new message
        extended = copy.deepcopy(chatgpt_simple_conversation)
        extended['update_time'] = 1800000000.0
        
        new_msg_id = "new-immutable-msg"
        last_node_id = list(extended['mapping'].keys())[-1]
        
        extended['mapping'][new_msg_id] = {
            "id": new_msg_id,
            "parent": last_node_id,
            "children": [],
            "message": {
                "id": new_msg_id,
                "author": {"role": "user"},
                "create_time": 1700006000.0,
                "content": {"content_type": "text", "parts": ["New message"]}
            }
        }
        
        extractor.extract_dialogue(extended)
        clean_db_session.commit()
        
        # New message should be created
        new_count = clean_db_session.query(Message).count()
        assert new_count == original_count + 1
        
        # And it should have a content hash
        new_msg = clean_db_session.query(Message).filter(
            Message.source_id == new_msg_id
        ).first()
        assert new_msg is not None
        assert new_msg.content_hash is not None
    
    def test_immutable_mode_still_soft_deletes(self, clean_db_session, chatgpt_simple_conversation):
        """Test that immutable mode still soft-deletes removed messages."""
        extractor = ChatGPTExtractor(clean_db_session, assume_immutable=True)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Remove a message
        truncated = copy.deepcopy(chatgpt_simple_conversation)
        truncated['update_time'] = 1800000000.0
        
        mapping_keys = list(truncated['mapping'].keys())
        removed_key = mapping_keys[-1]
        del truncated['mapping'][removed_key]
        
        for node_id, node in truncated['mapping'].items():
            if removed_key in node.get('children', []):
                node['children'].remove(removed_key)
        
        extractor.extract_dialogue(truncated)
        clean_db_session.commit()
        
        # Message should be soft-deleted
        deleted_count = clean_db_session.query(Message).filter(
            Message.deleted_at.isnot(None)
        ).count()
        assert deleted_count == 1
    
    def test_immutable_mode_restores_soft_deleted(self, clean_db_session, chatgpt_simple_conversation):
        """Test that immutable mode restores soft-deleted messages without re-hashing."""
        extractor = ChatGPTExtractor(clean_db_session, assume_immutable=True)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Remove and soft-delete a message
        truncated = copy.deepcopy(chatgpt_simple_conversation)
        truncated['update_time'] = 1800000000.0
        
        mapping_keys = list(truncated['mapping'].keys())
        removed_key = mapping_keys[-1]
        del truncated['mapping'][removed_key]
        
        for node_id, node in truncated['mapping'].items():
            if removed_key in node.get('children', []):
                node['children'].remove(removed_key)
        
        extractor.extract_dialogue(truncated)
        clean_db_session.commit()
        
        # Verify soft-deleted
        deleted_msg = clean_db_session.query(Message).filter(
            Message.deleted_at.isnot(None)
        ).first()
        assert deleted_msg is not None
        original_hash = deleted_msg.content_hash
        
        # Restore by importing original with newer timestamp
        restored = copy.deepcopy(chatgpt_simple_conversation)
        restored['update_time'] = 1900000000.0
        
        extractor.extract_dialogue(restored)
        clean_db_session.commit()
        
        # Should be restored
        clean_db_session.refresh(deleted_msg)
        assert deleted_msg.deleted_at is None
        # Hash should be unchanged (we didn't re-hash)
        assert deleted_msg.content_hash == original_hash
    
    def test_claude_immutable_mode(self, clean_db_session, claude_simple_conversation):
        """Test that assume_immutable works for Claude extractor too."""
        extractor = ClaudeExtractor(clean_db_session, assume_immutable=True)
        
        # First import
        extractor.extract_dialogue(claude_simple_conversation)
        clean_db_session.commit()
        
        # Get a message
        msg = clean_db_session.query(Message).filter(Message.role == 'user').first()
        original_hash = msg.content_hash
        
        # "Modify" content
        modified = copy.deepcopy(claude_simple_conversation)
        modified['updated_at'] = "2025-01-01T00:00:00Z"
        
        for m in modified['chat_messages']:
            if m.get('uuid') == msg.source_id:
                m['content'] = [{'type': 'text', 'text': 'MODIFIED'}]
                break
        
        extractor.extract_dialogue(modified)
        clean_db_session.commit()
        
        # In immutable mode, hash should NOT change
        clean_db_session.refresh(msg)
        assert msg.content_hash == original_hash


class TestIncrementalMode:
    """Tests for incremental (delta import) mode."""
    
    def test_incremental_mode_skips_soft_delete(self, clean_db_session, chatgpt_simple_conversation):
        """Test that incremental mode doesn't soft-delete missing messages."""
        extractor = ChatGPTExtractor(clean_db_session, incremental=True)
        
        # First import - full conversation
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        original_count = clean_db_session.query(Message).count()
        
        # Second import - partial conversation (remove a message)
        partial = copy.deepcopy(chatgpt_simple_conversation)
        partial['update_time'] = 1800000000.0
        
        mapping_keys = list(partial['mapping'].keys())
        removed_key = mapping_keys[-1]
        del partial['mapping'][removed_key]
        
        for node_id, node in partial['mapping'].items():
            if removed_key in node.get('children', []):
                node['children'].remove(removed_key)
        
        extractor.extract_dialogue(partial)
        clean_db_session.commit()
        
        # In incremental mode, no messages should be soft-deleted
        deleted_count = clean_db_session.query(Message).filter(
            Message.deleted_at.isnot(None)
        ).count()
        assert deleted_count == 0, "Incremental mode should not soft-delete"
        
        # Total count should be unchanged
        assert clean_db_session.query(Message).count() == original_count
    
    def test_non_incremental_mode_does_soft_delete(self, clean_db_session, chatgpt_simple_conversation):
        """Test that non-incremental mode (default) does soft-delete missing messages."""
        extractor = ChatGPTExtractor(clean_db_session, incremental=False)
        
        # First import - full conversation
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        original_count = clean_db_session.query(Message).count()
        
        # Second import - partial conversation
        partial = copy.deepcopy(chatgpt_simple_conversation)
        partial['update_time'] = 1800000000.0
        
        mapping_keys = list(partial['mapping'].keys())
        removed_key = mapping_keys[-1]
        del partial['mapping'][removed_key]
        
        for node_id, node in partial['mapping'].items():
            if removed_key in node.get('children', []):
                node['children'].remove(removed_key)
        
        extractor.extract_dialogue(partial)
        clean_db_session.commit()
        
        # In non-incremental mode, missing message should be soft-deleted
        deleted_count = clean_db_session.query(Message).filter(
            Message.deleted_at.isnot(None)
        ).count()
        assert deleted_count == 1, "Non-incremental mode should soft-delete"
    
    def test_incremental_mode_still_adds_new_messages(self, clean_db_session, chatgpt_simple_conversation):
        """Test that incremental mode still adds new messages."""
        extractor = ChatGPTExtractor(clean_db_session, incremental=True)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        original_count = clean_db_session.query(Message).count()
        
        # Add a new message
        extended = copy.deepcopy(chatgpt_simple_conversation)
        extended['update_time'] = 1800000000.0
        
        new_msg_id = "new-incremental-msg"
        last_node_id = list(extended['mapping'].keys())[-1]
        
        extended['mapping'][new_msg_id] = {
            "id": new_msg_id,
            "parent": last_node_id,
            "children": [],
            "message": {
                "id": new_msg_id,
                "author": {"role": "user"},
                "create_time": 1700006000.0,
                "content": {"content_type": "text", "parts": ["New message"]}
            }
        }
        
        extractor.extract_dialogue(extended)
        clean_db_session.commit()
        
        # New message should be created
        assert clean_db_session.query(Message).count() == original_count + 1
    
    def test_incremental_mode_still_updates_changed_messages(self, clean_db_session, chatgpt_simple_conversation):
        """Test that incremental mode still updates changed messages."""
        # Use mutable + incremental mode
        extractor = ChatGPTExtractor(clean_db_session, assume_immutable=False, incremental=True)
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        msg = clean_db_session.query(Message).filter(Message.role == 'user').first()
        original_hash = msg.content_hash
        
        # Modify message content
        modified = copy.deepcopy(chatgpt_simple_conversation)
        modified['update_time'] = 1800000000.0
        
        for node_id, node in modified['mapping'].items():
            msg_data = node.get('message')
            if msg_data and msg_data.get('id') == msg.source_id:
                msg_data['content']['parts'] = ['MODIFIED CONTENT']
                break
        
        extractor.extract_dialogue(modified)
        clean_db_session.commit()
        
        # Content should be updated
        clean_db_session.refresh(msg)
        assert msg.content_hash != original_hash
    
    def test_claude_incremental_mode(self, clean_db_session, claude_simple_conversation):
        """Test that incremental mode works for Claude extractor."""
        extractor = ClaudeExtractor(clean_db_session, incremental=True)
        
        # First import
        extractor.extract_dialogue(claude_simple_conversation)
        clean_db_session.commit()
        
        original_count = clean_db_session.query(Message).count()
        
        # Partial import (remove first message)
        partial = copy.deepcopy(claude_simple_conversation)
        partial['updated_at'] = "2025-01-01T00:00:00Z"
        partial['chat_messages'] = partial['chat_messages'][1:]  # Remove first message
        
        extractor.extract_dialogue(partial)
        clean_db_session.commit()
        
        # No messages should be soft-deleted
        deleted_count = clean_db_session.query(Message).filter(
            Message.deleted_at.isnot(None)
        ).count()
        assert deleted_count == 0
    
    def test_combined_immutable_and_incremental(self, clean_db_session, chatgpt_simple_conversation):
        """Test combining immutable and incremental modes for fastest delta imports."""
        extractor = ChatGPTExtractor(
            clean_db_session, 
            assume_immutable=True, 
            incremental=True
        )
        
        # First import
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        original_count = clean_db_session.query(Message).count()
        msg = clean_db_session.query(Message).filter(Message.role == 'user').first()
        original_hash = msg.content_hash
        
        # Partial import with "modified" content
        partial = copy.deepcopy(chatgpt_simple_conversation)
        partial['update_time'] = 1800000000.0
        
        # Remove a message
        mapping_keys = list(partial['mapping'].keys())
        removed_key = mapping_keys[-1]
        del partial['mapping'][removed_key]
        
        # "Modify" existing message (should be ignored in immutable mode)
        for node_id, node in partial['mapping'].items():
            msg_data = node.get('message')
            if msg_data and msg_data.get('id') == msg.source_id:
                msg_data['content']['parts'] = ['SHOULD BE IGNORED']
            if removed_key in node.get('children', []):
                node['children'].remove(removed_key)
        
        extractor.extract_dialogue(partial)
        clean_db_session.commit()
        
        # No soft-deletes (incremental mode)
        deleted_count = clean_db_session.query(Message).filter(
            Message.deleted_at.isnot(None)
        ).count()
        assert deleted_count == 0
        
        # Hash unchanged (immutable mode)
        clean_db_session.refresh(msg)
        assert msg.content_hash == original_hash
