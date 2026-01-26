-- schema/001_raw.sql

create extension if not exists vector;

-- Raw data layer: source of truth from imports

create schema if not exists raw;

-- ============================================================
-- raw.sources
-- ============================================================

create table if not exists raw.sources (
    id                  text primary key,
    display_name        text not null,
    has_native_trees    boolean not null,
    role_vocabulary     text[] not null,
    metadata            jsonb
);

insert into raw.sources (id, display_name, has_native_trees, role_vocabulary)
values
    ('chatgpt', 'ChatGPT', true, array['user', 'assistant', 'system', 'tool']),
    ('claude', 'Claude', false, array['user', 'assistant'])
on conflict (id) do nothing;

-- ============================================================
-- raw.dialogues
-- ============================================================

create table if not exists raw.dialogues (
    id                  uuid primary key default gen_random_uuid(),
    source              text not null references raw.sources(id),
    source_id           text not null,
    
    title               text,
    created_at          timestamptz,
    updated_at          timestamptz,
    
    source_json         jsonb not null,
    imported_at         timestamptz default now(),
    
    unique (source, source_id)
);

-- ============================================================
-- raw.messages
-- ============================================================

create table if not exists raw.messages (
    id                  uuid primary key default gen_random_uuid(),
    dialogue_id         uuid not null references raw.dialogues on delete cascade,
    source_id           text not null,
    
    parent_id           uuid references raw.messages,
    
    role                text not null,
    author_id           text,
    author_name         text,
    created_at          timestamptz,
    updated_at          timestamptz,
    
    source_json         jsonb not null,
    
    unique (dialogue_id, source_id)
);

-- ============================================================
-- raw.content_parts
-- ============================================================

create table if not exists raw.content_parts (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    sequence            int not null,
    
    part_type           text not null,
    text_content        text,
    
    started_at          timestamptz,
    ended_at            timestamptz,
    is_error            boolean default false,
    
    source_json         jsonb not null,
    
    unique (message_id, sequence)
);

-- ============================================================
-- raw.citations
-- ============================================================

create table if not exists raw.citations (
    id                  uuid primary key default gen_random_uuid(),
    content_part_id     uuid not null references raw.content_parts on delete cascade,
    source_id           text,
    
    url                 text,
    title               text,
    snippet             text,
    published_at        timestamptz,
    
    start_index         int,
    end_index           int,
    citation_type       text,
    
    source_json         jsonb
);

-- ============================================================
-- raw.attachments
-- ============================================================

create table if not exists raw.attachments (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    
    file_name           text,
    file_type           text,
    file_size           int,
    extracted_text      text,
    
    source_json         jsonb
);

-- ============================================================
-- ChatGPT Extensions
-- ============================================================

create table if not exists raw.chatgpt_message_meta (
    message_id          uuid primary key references raw.messages on delete cascade,
    model_slug          text,
    status              text,
    end_turn            boolean,
    gizmo_id            text,
    source_json         jsonb not null
);

create table if not exists raw.chatgpt_search_groups (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    group_type          text,
    domain              text,
    source_json         jsonb not null
);

create table if not exists raw.chatgpt_search_entries (
    id                  uuid primary key default gen_random_uuid(),
    group_id            uuid not null references raw.chatgpt_search_groups on delete cascade,
    sequence            int not null,
    url                 text,
    title               text,
    snippet             text,
    published_at        timestamptz,
    attribution         text,
    source_json         jsonb not null
);

create table if not exists raw.chatgpt_code_executions (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    run_id              text,
    status              text,
    code                text,
    started_at          timestamptz,
    ended_at            timestamptz,
    final_output        text,
    exception_name      text,
    exception_traceback text,
    source_json         jsonb not null
);

create table if not exists raw.chatgpt_code_outputs (
    id                  uuid primary key default gen_random_uuid(),
    execution_id        uuid not null references raw.chatgpt_code_executions on delete cascade,
    sequence            int not null,
    output_type         text,
    stream_name         text,
    text_content        text,
    image_url           text,
    source_json         jsonb not null
);

create table if not exists raw.chatgpt_dalle_generations (
    id                  uuid primary key default gen_random_uuid(),
    content_part_id     uuid not null references raw.content_parts on delete cascade,
    gen_id              text,
    prompt              text,
    seed                bigint,
    parent_gen_id       text,
    edit_op             text,
    width               int,
    height              int,
    source_json         jsonb not null
);

create table if not exists raw.chatgpt_canvas_docs (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    textdoc_id          text,
    textdoc_type        text,
    version             int,
    title               text,
    from_version        int,
    content_length      int,
    has_user_edit       boolean,
    source_json         jsonb not null
);

-- ============================================================
-- Claude Extensions
-- ============================================================

create table if not exists raw.claude_message_meta (
    message_id          uuid primary key references raw.messages on delete cascade,
    source_json         jsonb not null
);

-- ============================================================
-- Indexes
-- ============================================================

create index if not exists idx_raw_dialogues_source on raw.dialogues(source, source_id);
create index if not exists idx_raw_dialogues_created on raw.dialogues(created_at);
create index if not exists idx_raw_messages_dialogue on raw.messages(dialogue_id);
create index if not exists idx_raw_messages_parent on raw.messages(parent_id);
create index if not exists idx_raw_messages_role on raw.messages(role);
create index if not exists idx_raw_content_parts_message on raw.content_parts(message_id, sequence);
create index if not exists idx_raw_content_parts_type on raw.content_parts(part_type);
create index if not exists idx_raw_citations_part on raw.citations(content_part_id);
create index if not exists idx_raw_attachments_message on raw.attachments(message_id);