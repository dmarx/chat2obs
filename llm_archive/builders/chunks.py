# llm_archive/builders/chunks.py
"""
Message-level markdown chunking.

- Aggregates raw.content_parts.text_content (ordered by sequence) into message full_text
- Parses with markdown-it-py into block-level chunks
- Stores into derived.message_chunks
- Incremental: if a message's content_hash unchanged since last successful chunk run, skip
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from llm_archive.models import Message, ContentPart
from llm_archive.models.derived import PipelineRun, MessageChunk


@dataclass
class ChunkRecord:
    chunk_index: int
    chunk_type: str
    text: str
    heading_level: int | None = None
    heading_text: str | None = None
    info_string: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    start_char: int | None = None
    end_char: int | None = None
    data: dict | None = None


class MessageChunkBuilder:
    def __init__(self, session: Session):
        self.session = session

    def build_all(self, name: str | None = None, params: dict | None = None) -> dict[str, int]:
        run = PipelineRun(
            run_type="chunk",
            name=name,
            params=params or {},
            status="running",
        )
        self.session.add(run)
        self.session.flush()

        counts = {"messages_seen": 0, "messages_chunked": 0, "chunks_created": 0}

        try:
            # naive first pass: chunk all non-deleted messages that have any text content
            # (you can optimize by checking content_hash vs prior run later)
            msg_ids = (
                self.session.query(Message.id)
                .filter(Message.deleted_at.is_(None))
                .all()
            )
            msg_ids = [m[0] for m in msg_ids]

            for mid in msg_ids:
                counts["messages_seen"] += 1
                created = self._chunk_message(mid, run.id)
                if created:
                    counts["messages_chunked"] += 1
                    counts["chunks_created"] += created

            run.status = "success"
            run.ended_at = datetime.now(timezone.utc)
            self.session.commit()
            logger.info(f"Chunking complete: {counts}")
            return counts

        except Exception as e:
            run.status = "failed"
            run.ended_at = datetime.now(timezone.utc)
            run.notes = str(e)
            self.session.rollback()
            self.session.commit()
            raise

    def _chunk_message(self, message_id, run_id) -> int:
        msg = self.session.get(Message, message_id)
        if not msg:
            return 0

        full_text = self._get_message_text(message_id)
        if not full_text:
            return 0

        # wipe any chunks for this message+run (idempotent if rerun)
        self.session.execute(
            text("delete from derived.message_chunks where message_id = :mid and run_id = :rid"),
            {"mid": str(message_id), "rid": str(run_id)},
        )

        chunks = list(self._parse_markdown(full_text))
        for c in chunks:
            row = MessageChunk(
                message_id=message_id,
                dialogue_id=msg.dialogue_id,
                role=msg.role,
                chunk_index=c.chunk_index,
                chunk_type=c.chunk_type,
                heading_level=c.heading_level,
                heading_text=c.heading_text,
                info_string=c.info_string,
                text=c.text,
                start_line=c.start_line,
                end_line=c.end_line,
                start_char=c.start_char,
                end_char=c.end_char,
                run_id=run_id,
                chunker="markdown-it-py",
                chunker_version=None,
                data=c.data or {},
            )
            self.session.add(row)

        self.session.flush()
        return len(chunks)

    def _get_message_text(self, message_id) -> str | None:
        parts = (
            self.session.query(ContentPart.text_content)
            .filter(ContentPart.message_id == message_id)
            .filter(ContentPart.text_content.isnot(None))
            .order_by(ContentPart.sequence)
            .all()
        )
        texts = [p[0] for p in parts if p[0]]
        return "\n".join(texts) if texts else None

    def _parse_markdown(self, text_in: str) -> Iterable[ChunkRecord]:
        # markdown-it-py + plugins
        from markdown_it import MarkdownIt
        #from mdit_py_plugins.table import table
        #md = MarkdownIt("commonmark", {"html": True}).use(table)
        
        md = MarkdownIt("commonmark", {"html": True}).enable('table')
        tokens = md.parse(text_in)

        # Precompute line-start offsets for char mapping
        lines = text_in.splitlines(keepends=True)
        line_offsets = [0]
        for ln in lines:
            line_offsets.append(line_offsets[-1] + len(ln))

        def line_to_char(line_no: int) -> int:
            if line_no < 0:
                return 0
            if line_no >= len(line_offsets):
                return line_offsets[-1]
            return line_offsets[line_no]

        out: list[ChunkRecord] = []
        i = 0

        def grab_text_for_map(map_pair):
            if not map_pair or len(map_pair) != 2:
                return None, None, None, None
            start_line, end_line = map_pair[0], map_pair[1]
            start_char = line_to_char(start_line)
            end_char = line_to_char(end_line)
            return start_line, end_line, start_char, end_char

        # Block-level chunking by common patterns
        while i < len(tokens):
            t = tokens[i]

            if t.type == "heading_open":
                level = int(t.tag[1]) if t.tag and len(t.tag) == 2 else None
                inline = tokens[i + 1] if i + 1 < len(tokens) else None
                heading_text = inline.content if inline and inline.type == "inline" else ""
                start_line, end_line, start_char, end_char = grab_text_for_map(t.map)
                out.append(ChunkRecord(
                    chunk_index=len(out),
                    chunk_type="heading",
                    heading_level=level,
                    heading_text=heading_text,
                    text=heading_text,
                    start_line=start_line, end_line=end_line,
                    start_char=start_char, end_char=end_char,
                ))
                # skip heading_close too
                i += 3
                continue

            if t.type == "fence":
                start_line, end_line, start_char, end_char = grab_text_for_map(t.map)
                out.append(ChunkRecord(
                    chunk_index=len(out),
                    chunk_type="code_fence",
                    info_string=(t.info or "").strip() or None,
                    text=t.content or "",
                    start_line=start_line, end_line=end_line,
                    start_char=start_char, end_char=end_char,
                    data={"info": t.info or ""},
                ))
                i += 1
                continue

            if t.type == "blockquote_open":
                # collect until blockquote_close
                start_map = t.map
                j = i + 1
                content_texts = []
                while j < len(tokens) and tokens[j].type != "blockquote_close":
                    if tokens[j].type == "inline":
                        content_texts.append(tokens[j].content)
                    j += 1
                start_line, end_line, start_char, end_char = grab_text_for_map(start_map)
                out.append(ChunkRecord(
                    chunk_index=len(out),
                    chunk_type="blockquote",
                    text="\n".join(content_texts).strip(),
                    start_line=start_line, end_line=end_line,
                    start_char=start_char, end_char=end_char,
                ))
                i = j + 1
                continue

            if t.type == "paragraph_open":
                inline = tokens[i + 1] if i + 1 < len(tokens) else None
                para = inline.content if inline and inline.type == "inline" else ""
                start_line, end_line, start_char, end_char = grab_text_for_map(t.map)
                out.append(ChunkRecord(
                    chunk_index=len(out),
                    chunk_type="paragraph",
                    text=para,
                    start_line=start_line, end_line=end_line,
                    start_char=start_char, end_char=end_char,
                ))
                i += 3
                continue

            if t.type in ("bullet_list_open", "ordered_list_open"):
                start_map = t.map
                j = i + 1
                content_texts = []
                depth = 1
                while j < len(tokens) and depth > 0:
                    if tokens[j].type in ("bullet_list_open", "ordered_list_open"):
                        depth += 1
                    elif tokens[j].type in ("bullet_list_close", "ordered_list_close"):
                        depth -= 1
                    elif tokens[j].type == "inline":
                        content_texts.append(tokens[j].content)
                    j += 1
                start_line, end_line, start_char, end_char = grab_text_for_map(start_map)
                out.append(ChunkRecord(
                    chunk_index=len(out),
                    chunk_type="list",
                    text="\n".join(content_texts).strip(),
                    start_line=start_line, end_line=end_line,
                    start_char=start_char, end_char=end_char,
                ))
                i = j
                continue

            if t.type == "hr":
                start_line, end_line, start_char, end_char = grab_text_for_map(t.map)
                out.append(ChunkRecord(
                    chunk_index=len(out),
                    chunk_type="hr",
                    text="---",
                    start_line=start_line, end_line=end_line,
                    start_char=start_char, end_char=end_char,
                ))
                i += 1
                continue

            # skip other token types by default
            i += 1

        return out
