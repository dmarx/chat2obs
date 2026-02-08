-- schema/001_raw.sql
-- Raw data layer: imported conversation data
create extension if not exists vector;
-- ============================================================
-- SCHEMA SETUP
-- ============================================================

create schema if not exists raw;

-- ============================================================
-- raw.sources
-- 
-- Registry of conversation sources (platforms).
-- ============================================================

create table if not exists raw.sources (
    id                  text primary key,
    display_name        text not null,
    has_native_trees    boolean not null,
    role_vocabulary     text[] not null,
    metadata            jsonb
);

-- Insert known sources
insert into raw.sources (id, display_name, has_native_trees, role_vocabulary, metadata) values
    ('chatgpt', 'ChatGPT', true, array['system', 'user', 'assistant', 'tool'], '{"provider": "OpenAI"}'::jsonb),
    ('claude', 'Claude', false, array['user', 'assistant'], '{"provider": "Anthropic"}'::jsonb)
on conflict (id) do nothing;

-- ============================================================
-- raw.dialogues
-- 
-- Universal dialogue container.
-- ============================================================

create table if not exists raw.dialogues (
    id                  uuid primary key default gen_random_uuid(),
    source              text not null references raw.sources(id),
    source_id           text not null,
    
    title               text,
    
    -- Source timestamps (from archive export)
    source_created_at   timestamptz,
    source_updated_at   timestamptz,
    
    source_json         jsonb not null,
    
    -- Database timestamps
    created_at          timestamptz default now(),
    updated_at          timestamptz default now(),
    
    unique (source, source_id)
);

create index if not exists idx_dialogues_source on raw.dialogues(source);
create index if not exists idx_dialogues_source_id on raw.dialogues(source_id);
create index if not exists idx_dialogues_created_at on raw.dialogues(source_created_at);

-- ============================================================
-- raw.messages
-- 
-- Universal message with tree structure support.
-- ============================================================

create table if not exists raw.messages (
    id                  uuid primary key default gen_random_uuid(),
    dialogue_id         uuid not null references raw.dialogues on delete cascade,
    source_id           text not null,
    
    -- Tree structure
    parent_id           uuid references raw.messages,
    
    -- Normalized fields
    role                text not null,
    author_id           text,
    author_name         text,
    
    -- Source timestamps
    source_created_at   timestamptz,
    source_updated_at   timestamptz,
    
    -- Change tracking
    content_hash        text,
    deleted_at          timestamptz,
    
    source_json         jsonb not null,
    
    -- Database timestamps
    created_at          timestamptz default now(),
    updated_at          timestamptz default now(),
    
    unique (dialogue_id, source_id)
);

create index if not exists idx_messages_dialogue on raw.messages(dialogue_id);
create index if not exists idx_messages_parent on raw.messages(parent_id);
create index if not exists idx_messages_role on raw.messages(role);
create index if not exists idx_messages_created_at on raw.messages(created_at);

-- ============================================================
-- raw.content_parts
-- 
-- Segmented content within a message (text, code, images, tool use).
-- ============================================================

create table if not exists raw.content_parts (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    sequence            int not null,
    
    part_type           text not null,
    text_content        text,
    
    -- Code-specific
    language            text,
    
    -- Media-specific
    media_type          text,
    url                 text,
    
    -- Tool use-specific
    tool_name           text,
    tool_use_id         text,
    tool_input          jsonb,
    is_error            boolean,
    
    -- Preserve original source data
    source_json         jsonb,
    
    created_at          timestamptz default now(),
    
    unique (message_id, sequence)
);

create index if not exists idx_content_parts_message on raw.content_parts(message_id);
create index if not exists idx_content_parts_type on raw.content_parts(part_type);
create index if not exists idx_content_parts_created_at on raw.content_parts(created_at);

-- ============================================================
-- raw.citations
-- 
-- Source citations within messages.
-- ============================================================

create table if not exists raw.citations (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    sequence            int not null,
    
    citation_text       text,
    url                 text,
    title               text,
    
    unique (message_id, sequence)
);

create index if not exists idx_citations_message on raw.citations(message_id);

-- ============================================================
-- raw.attachments
-- 
-- File attachments associated with messages.
-- ============================================================

create table if not exists raw.attachments (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    
    filename            text,
    file_size           bigint,
    mime_type           text,
    url                 text,
    
    unique (message_id, filename)
);

create index if not exists idx_attachments_message on raw.attachments(message_id);

-- ============================================================
-- ChatGPT Extensions
-- ============================================================

-- ChatGPT message metadata
create table if not exists raw.chatgpt_message_meta (
    message_id          uuid primary key references raw.messages on delete cascade,
    
    weight              float,
    end_turn            boolean,
    recipient           text,
    model_slug          text,
    is_complete         boolean,
    finish_details      jsonb
);

-- ChatGPT web search groups
create table if not exists raw.chatgpt_search_groups (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    sequence            int not null,
    
    search_query        text,
    
    unique (message_id, sequence)
);

create index if not exists idx_chatgpt_search_groups_message 
    on raw.chatgpt_search_groups(message_id);

-- ChatGPT web search entries
create table if not exists raw.chatgpt_search_entries (
    id                  uuid primary key default gen_random_uuid(),
    search_group_id     uuid not null references raw.chatgpt_search_groups on delete cascade,
    sequence            int not null,
    
    title               text,
    url                 text,
    snippet             text,
    
    unique (search_group_id, sequence)
);

create index if not exists idx_chatgpt_search_entries_group 
    on raw.chatgpt_search_entries(search_group_id);

-- ChatGPT code execution
create table if not exists raw.chatgpt_code_executions (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    sequence            int not null,
    
    language            text,
    code_text           text,
    
    unique (message_id, sequence)
);

create index if not exists idx_chatgpt_code_executions_message 
    on raw.chatgpt_code_executions(message_id);

-- ChatGPT code execution outputs
create table if not exists raw.chatgpt_code_outputs (
    id                  uuid primary key default gen_random_uuid(),
    execution_id        uuid not null references raw.chatgpt_code_executions on delete cascade,
    sequence            int not null,
    
    output_type         text,
    output_text         text,
    
    unique (execution_id, sequence)
);

create index if not exists idx_chatgpt_code_outputs_execution 
    on raw.chatgpt_code_outputs(execution_id);

-- ChatGPT DALL-E generations
create table if not exists raw.chatgpt_dalle_generations (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    sequence            int not null,
    
    prompt              text,
    asset_pointer       text,
    
    unique (message_id, sequence)
);

create index if not exists idx_chatgpt_dalle_message 
    on raw.chatgpt_dalle_generations(message_id);

-- ChatGPT Canvas documents
create table if not exists raw.chatgpt_canvas_docs (
    id                  uuid primary key default gen_random_uuid(),
    message_id          uuid not null references raw.messages on delete cascade,
    
    document_id         text,
    title               text,
    content_type        text,
    
    unique (message_id, document_id)
);

create index if not exists idx_chatgpt_canvas_message 
    on raw.chatgpt_canvas_docs(message_id);

-- ============================================================
-- Claude Extensions
-- ============================================================

-- Claude message metadata
create table if not exists raw.claude_message_meta (
    message_id          uuid primary key references raw.messages on delete cascade,
    
    model               text,
    usage_input_tokens  int,
    usage_output_tokens int
);
