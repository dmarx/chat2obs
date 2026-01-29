-- schema/005_message_chunks.sql
-- Markdown-aware chunking at the MESSAGE level (user + assistant).
-- Chunks are the fundamental unit for quality, preface, continuation, title heuristics.

create table if not exists derived.message_chunks (
    id              uuid primary key default gen_random_uuid(),

    message_id      uuid not null references raw.messages on delete cascade,
    dialogue_id     uuid not null references raw.dialogues on delete cascade,

    role            text not null,  -- 'user'|'assistant'|'system'|'tool' (usually user/assistant)

    chunk_index     int not null,

    chunk_type      text not null,  -- 'heading'|'paragraph'|'code_fence'|'list'|'blockquote'|'table'|'hr'|'html'|'other'
    heading_level   int,
    heading_text    text,
    info_string     text,           -- fenced code info string

    text            text not null,

    -- mapping back to the message's aggregated full_text
    -- (concatenation of raw.content_parts.text_content ordered by sequence)
    start_line      int,
    end_line        int,            -- exclusive
    start_char      int,
    end_char        int,

    -- provenance
    run_id          uuid references derived.pipeline_runs on delete set null,
    chunker         text not null default 'markdown-it-py',
    chunker_version text,
    data            jsonb not null default '{}'::jsonb,

    computed_at     timestamptz default now(),

    unique (message_id, run_id, chunk_index)
);

create index if not exists idx_message_chunks_message
    on derived.message_chunks(message_id, run_id, chunk_index);

create index if not exists idx_message_chunks_dialogue
    on derived.message_chunks(dialogue_id, run_id);

create index if not exists idx_message_chunks_role_type
    on derived.message_chunks(role, chunk_type);

create index if not exists idx_message_chunks_heading
    on derived.message_chunks(role, heading_level)
    where chunk_type = 'heading';
