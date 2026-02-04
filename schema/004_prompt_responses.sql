-- schema/003_prompt_responses.sql
-- Prompt-response pairs: direct user→assistant associations without tree dependency

-- ============================================================
-- derived.prompt_responses
-- 
-- Associates each assistant response with its eliciting user prompt.
-- Unlike exchanges (which depend on tree analysis), this is built
-- directly from message parent_id relationships with sequential fallback.
--
-- Design:
-- - One record per (prompt, response) pair
-- - A prompt_message_id can appear multiple times (regenerations)
-- - Each response_message_id appears exactly once
-- ============================================================

create table if not exists derived.prompt_responses (
    id                      uuid primary key default gen_random_uuid(),
    dialogue_id             uuid not null references raw.dialogues(id) on delete cascade,
    
    prompt_message_id       uuid not null references raw.messages(id),
    response_message_id     uuid not null references raw.messages(id),
    
    -- Position within dialogue (for ordering)
    prompt_position         int not null,
    response_position       int not null,
    
    -- Denormalized roles (for filtering without joins)
    prompt_role             text not null,
    response_role           text not null,
    
    created_at              timestamptz default now(),
    
    -- Each response belongs to exactly one prompt-response record
    unique (response_message_id)
);

create index if not exists idx_prompt_responses_dialogue 
    on derived.prompt_responses(dialogue_id);

create index if not exists idx_prompt_responses_prompt 
    on derived.prompt_responses(prompt_message_id);

create index if not exists idx_prompt_responses_roles 
    on derived.prompt_responses(prompt_role, response_role);


-- ============================================================
-- derived.prompt_response_content
-- 
-- Denormalized text content for annotation/search without joins.
-- Mirrors exchange_content pattern.
-- ============================================================

create table if not exists derived.prompt_response_content (
    prompt_response_id      uuid primary key references derived.prompt_responses(id) on delete cascade,
    
    prompt_text             text,
    response_text           text,
    
    prompt_word_count       int,
    response_word_count     int,
    
    created_at              timestamptz default now()
);