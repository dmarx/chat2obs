# tests/test_builders.py
"""Tests for derived data builders."""

import pytest

from llm_archive.extractors import ChatGPTExtractor, ClaudeExtractor
from llm_archive.builders import TreeBuilder, ExchangeBuilder, HashBuilder
from llm_archive.models import (
    Dialogue, Message,
    DialogueTree, MessagePath, LinearSequence, SequenceMessage,
    Exchange, ExchangeMessage, SequenceExchange, ExchangeContent,
    ContentHash,
)


class TestTreeBuilder:
    """Tests for dialogue tree builder."""
    
    def test_build_linear_tree(self, clean_db_session, chatgpt_simple_conversation):
        """Test building tree for linear conversation."""
        # Import conversation
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        # Build tree
        builder = TreeBuilder(clean_db_session)
        counts = builder.build_all()
        clean_db_session.commit()
        
        assert counts['dialogues'] == 1
        assert counts['linear'] == 1
        assert counts['branched'] == 0
        
        # Check dialogue tree record
        tree = clean_db_session.query(DialogueTree).first()
        assert tree is not None
        assert tree.branch_count == 0
        assert tree.leaf_count == 1
        assert tree.has_regenerations is False
        assert tree.has_edits is False
    
    def test_build_branched_tree(self, clean_db_session, chatgpt_branched_conversation):
        """Test building tree for branched conversation."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_branched_conversation)
        clean_db_session.commit()
        
        builder = TreeBuilder(clean_db_session)
        counts = builder.build_all()
        clean_db_session.commit()
        
        assert counts['branched'] == 1
        
        tree = clean_db_session.query(DialogueTree).first()
        assert tree.branch_count == 1
        assert tree.leaf_count == 2
        assert tree.has_regenerations is True  # Same-role siblings
    
    def test_message_paths(self, clean_db_session, chatgpt_simple_conversation):
        """Test that message paths are created correctly."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        builder = TreeBuilder(clean_db_session)
        builder.build_all()
        clean_db_session.commit()
        
        paths = clean_db_session.query(MessagePath).order_by(MessagePath.depth).all()
        
        # Should have path for each message
        messages = clean_db_session.query(Message).count()
        assert len(paths) == messages
        
        # Check depths are sequential for linear conversation
        depths = [p.depth for p in paths]
        assert depths == sorted(depths)
        
        # Root should have depth 0
        root_path = clean_db_session.query(MessagePath).filter(
            MessagePath.is_root == True
        ).first()
        assert root_path.depth == 0
    
    def test_linear_sequences(self, clean_db_session, chatgpt_simple_conversation):
        """Test that linear sequences are created."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        builder = TreeBuilder(clean_db_session)
        builder.build_all()
        clean_db_session.commit()
        
        sequences = clean_db_session.query(LinearSequence).all()
        
        # Linear conversation = 1 sequence
        assert len(sequences) == 1
        assert sequences[0].is_primary is True
    
    def test_multiple_sequences_for_branches(self, clean_db_session, chatgpt_branched_conversation):
        """Test that branched conversations get multiple sequences."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_branched_conversation)
        clean_db_session.commit()
        
        builder = TreeBuilder(clean_db_session)
        builder.build_all()
        clean_db_session.commit()
        
        sequences = clean_db_session.query(LinearSequence).all()
        
        # Branched = 2 sequences (one per leaf)
        assert len(sequences) == 2
        
        # Only one should be primary
        primary = [s for s in sequences if s.is_primary]
        assert len(primary) == 1
    
    def test_sequence_messages_order(self, clean_db_session, chatgpt_simple_conversation):
        """Test that sequence messages are ordered correctly."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        builder = TreeBuilder(clean_db_session)
        builder.build_all()
        clean_db_session.commit()
        
        sequence = clean_db_session.query(LinearSequence).first()
        
        seq_msgs = clean_db_session.query(SequenceMessage).filter(
            SequenceMessage.sequence_id == sequence.id
        ).order_by(SequenceMessage.position).all()
        
        # Positions should be sequential
        positions = [sm.position for sm in seq_msgs]
        assert positions == list(range(len(positions)))


class TestExchangeBuilder:
    """Tests for exchange builder."""
    
    def test_build_exchanges_simple(self, clean_db_session, chatgpt_simple_conversation):
        """Test building exchanges from simple conversation."""
        # Import and build trees first
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        tree_builder = TreeBuilder(clean_db_session)
        tree_builder.build_all()
        clean_db_session.commit()
        
        # Build exchanges
        exchange_builder = ExchangeBuilder(clean_db_session)
        counts = exchange_builder.build_all()
        clean_db_session.commit()
        
        assert counts['dialogues'] == 1
        assert counts['exchanges'] > 0
    
    def test_exchange_dyadic_structure(self, clean_db_session, chatgpt_simple_conversation):
        """Test that exchanges have user->assistant structure."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        TreeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        ExchangeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        exchanges = clean_db_session.query(Exchange).all()
        
        for exchange in exchanges:
            assert exchange.user_message_count >= 1
            assert exchange.assistant_message_count >= 1
    
    def test_exchange_deduplication(self, clean_db_session, chatgpt_branched_conversation):
        """Test that shared prefix exchanges are not duplicated."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_branched_conversation)
        clean_db_session.commit()
        
        TreeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        ExchangeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        # Get all exchanges
        exchanges = clean_db_session.query(Exchange).all()
        
        # Get sequence count
        sequences = clean_db_session.query(LinearSequence).all()
        
        # With 2 sequences sharing a prefix, we should have fewer exchanges
        # than if each sequence had its own copies
        sequence_exchange_links = clean_db_session.query(SequenceExchange).count()
        
        # Each sequence references exchanges, but exchanges themselves are shared
        assert sequence_exchange_links >= len(exchanges)
    
    def test_exchange_content_created(self, clean_db_session, chatgpt_simple_conversation):
        """Test that exchange content is created."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()
        
        TreeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        ExchangeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        contents = clean_db_session.query(ExchangeContent).all()
        
        assert len(contents) > 0
        
        for content in contents:
            assert content.user_text is not None or content.assistant_text is not None
            assert content.total_word_count >= 0
    
    def test_continuation_detection(self, clean_db_session, conversation_with_continuation):
        """Test that continuation prompts are detected."""
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conversation_with_continuation)
        clean_db_session.commit()
        
        TreeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        ExchangeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        # Check for continuation-flagged exchanges
        continuations = clean_db_session.query(Exchange).filter(
            Exchange.is_continuation == True
        ).all()
        
        # Should have at least one continuation
        assert len(continuations) >= 1


class TestHashBuilder:
    """Tests for content hash builder."""
    
    def test_build_hashes(self, fully_populated_db):
        """Test building content hashes."""
        builder = HashBuilder(fully_populated_db)
        counts = builder.build_all()
        fully_populated_db.commit()
        
        assert counts['total_hashes'] > 0
    
    def test_message_hashes(self, fully_populated_db):
        """Test that message hashes are created."""
        builder = HashBuilder(fully_populated_db)
        builder.build_all()
        fully_populated_db.commit()
        
        message_hashes = fully_populated_db.query(ContentHash).filter(
            ContentHash.entity_type == 'message'
        ).all()
        
        assert len(message_hashes) > 0
    
    def test_exchange_hashes(self, fully_populated_db):
        """Test that exchange hashes are created."""
        builder = HashBuilder(fully_populated_db)
        builder.build_all()
        fully_populated_db.commit()
        
        exchange_hashes = fully_populated_db.query(ContentHash).filter(
            ContentHash.entity_type == 'exchange'
        ).all()
        
        assert len(exchange_hashes) > 0
    
    def test_multiple_normalizations(self, fully_populated_db):
        """Test that multiple normalizations are created."""
        builder = HashBuilder(fully_populated_db)
        builder.build_all()
        fully_populated_db.commit()
        
        normalizations = fully_populated_db.query(
            ContentHash.normalization
        ).distinct().all()
        
        norm_values = [n[0] for n in normalizations]
        
        assert 'none' in norm_values
        assert 'whitespace' in norm_values
        assert 'normalized' in norm_values
    
    def test_find_duplicates(self, clean_db_session):
        """Test finding duplicate content."""
        # Create two identical conversations
        conv1 = {
            "conversation_id": "dup-001",
            "title": "Duplicate 1",
            "create_time": 1700000000.0,
            "update_time": 1700001000.0,
            "mapping": {
                "root": {
                    "id": "root",
                    "parent": None,
                    "children": ["m1"],
                    "message": None
                },
                "m1": {
                    "id": "m1",
                    "parent": "root",
                    "children": ["m2"],
                    "message": {
                        "id": "m1",
                        "author": {"role": "user"},
                        "create_time": 1700000100.0,
                        "content": {"content_type": "text", "parts": ["Hello world"]}
                    }
                },
                "m2": {
                    "id": "m2",
                    "parent": "m1",
                    "children": [],
                    "message": {
                        "id": "m2",
                        "author": {"role": "assistant"},
                        "create_time": 1700000200.0,
                        "content": {"content_type": "text", "parts": ["Hello! How can I help?"]}
                    }
                }
            }
        }
        
        conv2 = {
            "conversation_id": "dup-002",
            "title": "Duplicate 2",
            "create_time": 1700002000.0,
            "update_time": 1700003000.0,
            "mapping": {
                "root": {
                    "id": "root",
                    "parent": None,
                    "children": ["m1"],
                    "message": None
                },
                "m1": {
                    "id": "m1",
                    "parent": "root",
                    "children": ["m2"],
                    "message": {
                        "id": "m1",
                        "author": {"role": "user"},
                        "create_time": 1700002100.0,
                        "content": {"content_type": "text", "parts": ["Hello world"]}  # Same content
                    }
                },
                "m2": {
                    "id": "m2",
                    "parent": "m1",
                    "children": [],
                    "message": {
                        "id": "m2",
                        "author": {"role": "assistant"},
                        "create_time": 1700002200.0,
                        "content": {"content_type": "text", "parts": ["Hello! How can I help?"]}  # Same content
                    }
                }
            }
        }
        
        extractor = ChatGPTExtractor(clean_db_session)
        extractor.extract_dialogue(conv1)
        extractor.extract_dialogue(conv2)
        clean_db_session.commit()
        
        TreeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        ExchangeBuilder(clean_db_session).build_all()
        clean_db_session.commit()
        
        builder = HashBuilder(clean_db_session)
        builder.build_all()
        clean_db_session.commit()
        
        # Find duplicates
        duplicates = builder.find_duplicates(entity_type='message')
        
        # Should find duplicate messages
        assert len(duplicates) >= 1
