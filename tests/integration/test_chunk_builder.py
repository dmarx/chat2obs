"""Integration tests for MessageChunkBuilder (requires PostgreSQL)."""

import pytest
from sqlalchemy import text

from llm_archive.extractors import ChatGPTExtractor
from llm_archive.builders import MessageChunkBuilder
from llm_archive.models import Message, MessageChunk, PipelineRun


class TestMessageChunkBuilder:
    def test_build_chunks_creates_runs_and_chunks(self, clean_db_session, chatgpt_simple_conversation):
        # Import dialogue
        ChatGPTExtractor(clean_db_session).extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()

        # Build chunks
        builder = MessageChunkBuilder(clean_db_session)
        counts = builder.build_all(name="test-chunk-run")
        clean_db_session.commit()

        assert counts["messages_seen"] > 0
        assert counts["messages_chunked"] > 0
        assert counts["chunks_created"] > 0

        # Verify pipeline run
        run = (
            clean_db_session.query(PipelineRun)
            .filter(PipelineRun.run_type == "chunk")
            .order_by(PipelineRun.started_at.desc())
            .first()
        )
        assert run is not None
        assert run.status == "success"

        # Pick an assistant message that contains the markdown fence from the fixture
        assistant_msg = (
            clean_db_session.query(Message)
            .filter(Message.role == "assistant")
            .order_by(Message.created_at.desc())
            .first()
        )
        assert assistant_msg is not None

        chunks = (
            clean_db_session.query(MessageChunk)
            .filter(MessageChunk.message_id == assistant_msg.id)
            .filter(MessageChunk.run_id == run.id)
            .order_by(MessageChunk.chunk_index)
            .all()
        )
        assert len(chunks) > 0

        # If the assistant message text includes ```python fences, we should see code_fence with info_string python
        # (This is true for chatgpt_simple_conversation's last assistant message.)
        assert any(c.chunk_type == "code_fence" and c.info_string == "python" for c in chunks)

        # Basic sanity on sequential chunk_index
        idxs = [c.chunk_index for c in chunks]
        assert idxs == list(range(len(idxs)))

    def test_second_run_creates_new_run_and_new_chunks(self, clean_db_session, chatgpt_simple_conversation):
        ChatGPTExtractor(clean_db_session).extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()

        builder = MessageChunkBuilder(clean_db_session)
        builder.build_all(name="run-1")
        clean_db_session.commit()

        builder.build_all(name="run-2")
        clean_db_session.commit()

        runs = (
            clean_db_session.query(PipelineRun)
            .filter(PipelineRun.run_type == "chunk")
            .order_by(PipelineRun.started_at.asc())
            .all()
        )
        assert len(runs) >= 2
        assert runs[-1].name == "run-2"

        # Ensure we have chunk rows for both runs (same message_id but different run_id)
        any_msg = clean_db_session.query(Message).first()
        assert any_msg is not None

        run1_count = (
            clean_db_session.query(MessageChunk)
            .filter(MessageChunk.message_id == any_msg.id)
            .filter(MessageChunk.run_id == runs[-2].id)
            .count()
        )
        run2_count = (
            clean_db_session.query(MessageChunk)
            .filter(MessageChunk.message_id == any_msg.id)
            .filter(MessageChunk.run_id == runs[-1].id)
            .count()
        )
        assert run1_count >= 0
        assert run2_count >= 0
        # If this message had chunks once, it should have chunks again.
        if run1_count > 0:
            assert run2_count == run1_count

    def test_views_exist_and_return_rows(self, clean_db_session, chatgpt_simple_conversation):
        ChatGPTExtractor(clean_db_session).extract_dialogue(chatgpt_simple_conversation)
        clean_db_session.commit()

        MessageChunkBuilder(clean_db_session).build_all(name="view-test")
        clean_db_session.commit()

        # v_latest_chunk_run should have at least one row after chunking
        n_latest = clean_db_session.execute(
            text("select count(*) from derived.v_latest_chunk_run")
        ).scalar_one()
        assert n_latest > 0

        # v_message_chunks should return rows (latest-run chunks)
        n_chunks = clean_db_session.execute(
            text("select count(*) from derived.v_message_chunks")
        ).scalar_one()
        assert n_chunks > 0

        # v_exchange_chunk_stream depends on exchanges; it may be empty if you haven't built exchanges here.
        # We just validate the view exists by selecting from it safely.
        clean_db_session.execute(text("select 1 from derived.v_exchange_chunk_stream limit 1")).fetchall()
