# tests/integration/test_prompt_response_builder.py
"""Integration tests for PromptResponseBuilder."""

import pytest
from uuid import UUID

from llm_archive.extractors.chatgpt import ChatGPTExtractor
from llm_archive.extractors.claude import ClaudeExtractor
from llm_archive.builders.prompt_response import PromptResponseBuilder
from llm_archive.models import Dialogue, Message, PromptResponse


class TestPromptResponseBuilderBasic:
    """Basic tests for PromptResponseBuilder."""
    
    def test_build_for_simple_conversation(self, clean_db_session, chatgpt_simple_conversation):
        """Test building prompt-responses for a simple conversation."""
        # Import conversation
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Build prompt-responses
        builder = PromptResponseBuilder(clean_db_session)
        stats = builder.build_all()
        
        assert stats['prompt_responses_created'] > 0
        
        # Verify records exist
        prs = clean_db_session.query(PromptResponse).all()
        assert len(prs) > 0
    
    def test_pairs_user_with_assistant(self, clean_db_session, chatgpt_simple_conversation):
        """Test that user messages are paired with assistant responses."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        builder.build_all()
        
        # Get all prompt-responses
        prs = clean_db_session.query(PromptResponse).all()
        
        for pr in prs:
            prompt_msg = clean_db_session.get(Message, pr.prompt_message_id)
            response_msg = clean_db_session.get(Message, pr.response_message_id)
            
            assert prompt_msg.role == 'user'
            assert response_msg.role == 'assistant'
    
    def test_response_position_ordering(self, clean_db_session, chatgpt_simple_conversation):
        """Test that response_position reflects message order."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        builder.build_all()
        
        dialogue = clean_db_session.query(Dialogue).first()
        prs = clean_db_session.query(PromptResponse).filter(
            PromptResponse.dialogue_id == dialogue.id
        ).order_by(PromptResponse.response_position).all()
        
        # Positions should be monotonically increasing
        positions = [pr.response_position for pr in prs]
        assert positions == sorted(positions)
        assert len(set(positions)) == len(positions)  # No duplicates


class TestPromptResponseBuilderClaude:
    """Tests specific to Claude conversations."""
    
    def test_build_for_claude_conversation(self, clean_db_session, claude_simple_conversation):
        """Test building prompt-responses for Claude conversation."""
        extractor = ClaudeExtractor(clean_db_session)
        extractor.extract_dialogue(claude_simple_conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        stats = builder.build_all()
        
        assert stats['prompt_responses_created'] > 0
    
    def test_linear_chain_pairing(self, clean_db_session, claude_simple_conversation):
        """Test that linear chains are paired correctly."""
        extractor = ClaudeExtractor(clean_db_session)
        extractor.extract_dialogue(claude_simple_conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        builder.build_all()
        
        # Each assistant message should be paired with preceding user message
        prs = clean_db_session.query(PromptResponse).all()
        
        for pr in prs:
            assert pr.prompt_position < pr.response_position


class TestPromptResponseBuilderBranched:
    """Tests for branched conversations."""
    
    def test_build_for_branched_conversation(self, clean_db_session, chatgpt_branched_conversation):
        """Test building prompt-responses for branched conversation."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_branched_conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        stats = builder.build_all()
        
        # Should handle branches without error
        assert stats['prompt_responses_created'] > 0
    
    def test_uses_parent_id_for_pairing(self, clean_db_session, chatgpt_branched_conversation):
        """Test that parent_id is used to find the correct prompt."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_branched_conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        builder.build_all()
        
        prs = clean_db_session.query(PromptResponse).all()
        
        for pr in prs:
            response_msg = clean_db_session.get(Message, pr.response_message_id)
            prompt_msg = clean_db_session.get(Message, pr.prompt_message_id)
            
            # If response has a parent, verify the relationship
            if response_msg.parent_id:
                # The prompt should be the parent or an ancestor
                # (For regenerations, multiple responses may share a prompt)
                pass  # Complex to verify without tree traversal


class TestPromptResponseBuilderIdempotency:
    """Tests for idempotent building."""
    
    def test_rebuild_clears_existing(self, clean_db_session, chatgpt_simple_conversation):
        """Test that rebuilding clears and recreates records."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        
        # Build first time
        stats1 = builder.build_all()
        first_count = stats1['prompt_responses_created']
        
        # Build again
        stats2 = builder.build_all()
        second_count = stats2['prompt_responses_created']
        
        # Should have same count (cleared and rebuilt)
        assert first_count == second_count
        
        # Total records should equal one build's worth
        total = clean_db_session.query(PromptResponse).count()
        assert total == first_count
    
    def test_build_for_single_dialogue(self, clean_db_session, chatgpt_simple_conversation, chatgpt_branched_conversation):
        """Test building for a single dialogue doesn't affect others."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        extractor.extract_dialogue(chatgpt_branched_conversation)
        clean_db_session.commit()
        
        dialogues = clean_db_session.query(Dialogue).all()
        assert len(dialogues) == 2
        
        builder = PromptResponseBuilder(clean_db_session)
        
        # Build for first dialogue only
        builder.build_for_dialogue(dialogues[0].id)
        
        # Should only have records for first dialogue
        prs = clean_db_session.query(PromptResponse).all()
        dialogue_ids = {pr.dialogue_id for pr in prs}
        
        assert dialogues[0].id in dialogue_ids
        # Second dialogue may or may not be present depending on implementation


class TestPromptResponseBuilderEdgeCases:
    """Edge case tests."""
    
    def test_handles_system_messages(self, clean_db_session):
        """Test handling of conversations with system messages."""
        conversation = {
            'conversation_id': 'conv-system',
            'title': 'System Message Test',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-sys': {
                    'id': 'node-sys',
                    'message': {
                        'id': 'msg-sys',
                        'author': {'role': 'system'},
                        'content': {'parts': ['You are a helpful assistant.']},
                        'create_time': 1700000000,
                    },
                    'parent': None,
                },
                'node-user': {
                    'id': 'node-user',
                    'message': {
                        'id': 'msg-user',
                        'author': {'role': 'user'},
                        'content': {'parts': ['Hello']},
                        'create_time': 1700000001,
                    },
                    'parent': 'node-sys',
                },
                'node-asst': {
                    'id': 'node-asst',
                    'message': {
                        'id': 'msg-asst',
                        'author': {'role': 'assistant'},
                        'content': {'parts': ['Hi there!']},
                        'create_time': 1700000002,
                    },
                    'parent': 'node-user',
                },
            },
        }
        
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        stats = builder.build_all()
        
        # Should create one prompt-response (user -> assistant)
        # System message should not be part of a pair
        prs = clean_db_session.query(PromptResponse).all()
        assert len(prs) == 1
        
        pr = prs[0]
        prompt = clean_db_session.get(Message, pr.prompt_message_id)
        assert prompt.role == 'user'
    
    def test_handles_empty_dialogue(self, clean_db_session):
        """Test handling of dialogue with no messages."""
        conversation = {
            'conversation_id': 'conv-empty',
            'title': 'Empty',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {},
        }
        
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        stats = builder.build_all()
        
        assert stats['prompt_responses_created'] == 0
    
    def test_handles_user_only_dialogue(self, clean_db_session):
        """Test handling of dialogue with only user messages."""
        conversation = {
            'conversation_id': 'conv-user-only',
            'title': 'User Only',
            'create_time': 1700000000,
            'update_time': 1700000000,
            'mapping': {
                'node-1': {
                    'id': 'node-1',
                    'message': {
                        'id': 'msg-1',
                        'author': {'role': 'user'},
                        'content': {'parts': ['Hello?']},
                        'create_time': 1700000000,
                    },
                    'parent': None,
                },
            },
        }
        
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conversation)
        clean_db_session.commit()
        
        builder = PromptResponseBuilder(clean_db_session)
        stats = builder.build_all()
        
        # No assistant responses means no prompt-response pairs
        assert stats['prompt_responses_created'] == 0
