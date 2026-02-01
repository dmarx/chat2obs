-- schema/001_raw.sql
-- Raw data layer: source of truth from imports

-- ============================================================
-- EXTENSIONS
-- ============================================================

create extension if not exists vector;

-- ============================================================
-- SCHEMA SETUP
-- ============================================================

create schema if not exists raw;

-- ============================================================
-- raw.sources
-- ============================================================

create table raw.sources (
    id                  text primary key,
    display_name        text not null,
    has_native_trees    boolean not null,
    role_vocabulary     text[] not null,
    metadata            jsonb
);

insert into raw.sources (id, display_name, has_native_trees, role_vocabulary) values
    ('chatgpt', 'ChatGPT', true, array['user', 'assistant', 'system', 'tool']),
    ('claude', 'Claude', false, array['user', 'assistant']);

-- ============================================================
-- raw.dialogues
-- ============================================================

create table raw.dialogues (
    id                  uuid primary key default gen_random_uuid(),
    source              text not null references raw.sources(id),
    source_id           text not null,
    
    title               text,
    
    -- Source timestamps (from archive)
    source_created_at   timestamptz,
    source_updated_at   timestamptz,
    
    source_json         jsonb not null,
    
    -- DB timestamps
    created_at          timestamptz default now(),
    updated_at          timestamptz default now(),
    
    unique (source, source_id)
);

-- ============================================================
-- raw.messages
-- ============================================================

create table raw.messages (
    id                  uuid primary key default gen_random_uuid(),
    dialogue_id         uuid not null references raw.dialogues on delete cascade,
    source_id           text not null,
    
    -- Tree structure
    parent_id           uuid references raw.messages,
    
    -- Normalized fields
    role                text not null,
    author_id           text,
    author_name         text,
    
    -- Source timestamps (from archive)
    source_created_at   timestamptz,
    source_updated_at   timestamptz,
    
    -- Change tracking
    content_hash        text,               -- hash of content for change detection
    deleted_at          timestamptz,        -- soft delete (removed from source)
    
    source_json         jsonb not null,
    
    -- DB timestamps
    created_at          timestamptz default now(),
    updated_at          timestamptz default now(),
    
    unique (dialogue_id, source_id)
);

-- ============================================================
-- raw.content_parts
-- ============================================================

create table raw.content_parts (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    sequence            int not null,
    
    part_type           text not null,
    text_content        text,
    
    -- Code-specific fields
    language            text,               -- programming language for code blocks
    
    -- Media fields
    media_type          text,               -- MIME type (image/png, audio/mp3, etc.)
    url                 text,               -- URL for external resources
    
    -- Tool use fields (Claude)
    tool_name           text,               -- name of tool being used
    tool_use_id         text,               -- links tool_result back to tool_use
    tool_input          jsonb,              -- tool input parameters
    
    -- Timing and status
    started_at          timestamptz,
    ended_at            timestamptz,
    is_error            boolean default false,
    
    source_json         jsonb not null,
    
    unique (message_id, sequence)
);

-- ============================================================
-- raw.citations
-- ============================================================

create table raw.citations (
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

create table raw.attachments (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    
    file_name           text,
    file_type           text,
    file_size           int,
    extracted_text      text,
    
    source_json         jsonb
);

-- ============================================================
-- SOURCE EXTENSIONS: ChatGPT
-- ============================================================

create table raw.chatgpt_message_meta (
    message_id          uuid primary key references raw.messages on delete cascade,
    model_slug          text,
    status              text,
    end_turn            boolean,
    gizmo_id            text,
    source_json         jsonb not null
);

create table raw.chatgpt_search_groups (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    group_type          text,
    domain              text,
    source_json         jsonb not null
);

create table raw.chatgpt_search_entries (
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

create table raw.chatgpt_code_executions (
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

create table raw.chatgpt_code_outputs (
    id                  uuid primary key default gen_random_uuid(),
    execution_id        uuid not null references raw.chatgpt_code_executions on delete cascade,
    sequence            int not null,
    output_type         text,
    stream_name         text,
    text_content        text,
    image_url           text,
    source_json         jsonb not null
);

create table raw.chatgpt_dalle_generations (
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

create table raw.chatgpt_canvas_docs (
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
-- SOURCE EXTENSIONS: Claude
-- ============================================================

create table raw.claude_message_meta (
    message_id          uuid primary key references raw.messages on delete cascade,
    source_json         jsonb not null
);

-- ============================================================
-- RAW INDEXES
-- ============================================================

create index idx_raw_dialogues_source on raw.dialogues(source, source_id);
create index idx_raw_dialogues_created on raw.dialogues(created_at);

create index idx_raw_messages_dialogue on raw.messages(dialogue_id);
create index idx_raw_messages_parent on raw.messages(parent_id);
create index idx_raw_messages_role on raw.messages(role);
create index idx_raw_messages_created on raw.messages(created_at);

create index idx_raw_content_parts_message on raw.content_parts(message_id, sequence);
create index idx_raw_content_parts_type on raw.content_parts(part_type);

create index idx_raw_citations_part on raw.citations(content_part_id);
create index idx_raw_citations_url on raw.citations(url);

create index idx_raw_attachments_message on raw.attachments(message_id);

create index idx_raw_chatgpt_search_groups_msg on raw.chatgpt_search_groups(message_id);
create index idx_raw_chatgpt_search_entries_group on raw.chatgpt_search_entries(group_id);
create index idx_raw_chatgpt_code_exec_msg on raw.chatgpt_code_executions(message_id);
create index idx_raw_chatgpt_code_outputs_exec on raw.chatgpt_code_outputs(execution_id);
create index idx_raw_chatgpt_dalle_part on raw.chatgpt_dalle_generations(content_part_id);
create index idx_raw_chatgpt_canvas_msg on raw.chatgpt_canvas_docs(message_id);