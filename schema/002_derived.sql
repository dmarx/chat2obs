-- schema/002_derived.sql
-- Derived data layer: computed/analyzed structures

-- ============================================================
-- SCHEMA SETUP
-- ============================================================

create schema if not exists derived;

-- ============================================================
-- derived.dialogue_trees
-- ============================================================

create table derived.dialogue_trees (
    dialogue_id             uuid primary key references raw.dialogues on delete cascade,
    
    total_nodes             int not null,
    max_depth               int not null,
    branch_count            int not null,
    leaf_count              int not null,
    
    primary_leaf_id         uuid references raw.messages,
    primary_path_length     int,
    
    is_linear               boolean generated always as (branch_count = 0) stored,
    has_regenerations       boolean not null default false,
    has_edits               boolean not null default false,
    
    computed_at             timestamptz default now()
);

-- ============================================================
-- derived.message_paths
-- ============================================================

create table derived.message_paths (
    message_id              uuid primary key references raw.messages on delete cascade,
    dialogue_id             uuid not null references raw.dialogues on delete cascade,
    
    ancestor_path           uuid[] not null,
    depth                   int not null,
    
    is_root                 boolean not null,
    is_leaf                 boolean not null,
    child_count             int not null,
    sibling_index           int not null,
    
    is_on_primary_path      boolean not null,
    
    computed_at             timestamptz default now()
);

-- ============================================================
-- derived.linear_sequences
-- ============================================================

create table derived.linear_sequences (
    id                      uuid primary key default gen_random_uuid(),
    dialogue_id             uuid not null references raw.dialogues on delete cascade,
    leaf_message_id         uuid not null references raw.messages,
    
    sequence_length         int not null,
    is_primary              boolean not null,
    
    branch_reason           text,
    branched_at_message_id  uuid references raw.messages,
    branched_at_depth       int,
    
    computed_at             timestamptz default now(),
    
    unique (dialogue_id, leaf_message_id)
);

create table derived.sequence_messages (
    sequence_id             uuid not null references derived.linear_sequences on delete cascade,
    message_id              uuid not null references raw.messages,
    position                int not null,
    
    primary key (sequence_id, message_id)
);

-- ============================================================
-- derived.exchanges
-- Exchanges are built from the TREE, not from sequences.
-- An exchange is a dyadic unit: user prompt(s) + assistant response(s).
-- Identified by (dialogue_id, first_message_id, last_message_id).
-- ============================================================

create table derived.exchanges (
    id                      uuid primary key default gen_random_uuid(),
    dialogue_id             uuid not null references raw.dialogues on delete cascade,
    
    -- Message range (on a tree path)
    first_message_id        uuid not null references raw.messages,
    last_message_id         uuid not null references raw.messages,
    
    -- Stats
    message_count           int not null,
    user_message_count      int not null,
    assistant_message_count int not null,
    
    -- Continuation tracking
    is_continuation         boolean default false,
    continuation_of_id      uuid references derived.exchanges,
    merged_count            int default 1,
    
    -- Timestamps from messages
    started_at              timestamptz,
    ended_at                timestamptz,
    
    computed_at             timestamptz default now(),
    
    -- An exchange is uniquely identified by its message range
    unique (dialogue_id, first_message_id, last_message_id)
);

create table derived.exchange_messages (
    exchange_id             uuid not null references derived.exchanges on delete cascade,
    message_id              uuid not null references raw.messages,
    position                int not null,
    
    primary key (exchange_id, message_id)
);

-- ============================================================
-- derived.sequence_exchanges
-- Links sequences to exchanges (many-to-many).
-- A sequence is an ordered list of exchanges.
-- ============================================================

create table derived.sequence_exchanges (
    sequence_id             uuid not null references derived.linear_sequences on delete cascade,
    exchange_id             uuid not null references derived.exchanges on delete cascade,
    position                int not null,
    
    primary key (sequence_id, exchange_id)
);

-- ============================================================
-- derived.exchange_content
-- ============================================================

create table derived.exchange_content (
    exchange_id             uuid primary key references derived.exchanges on delete cascade,
    
    user_text               text,
    assistant_text          text,
    full_text               text,
    
    user_text_hash          text,
    assistant_text_hash     text,
    full_text_hash          text,
    
    user_word_count         int,
    assistant_word_count    int,
    total_word_count        int,
    
    computed_at             timestamptz default now()
);

-- ============================================================
-- derived.annotations
-- Polymorphic annotation system for any entity.
-- Supports: tags (filtering), metadata (titles), multi-value (export).
-- ============================================================

create table derived.annotations (
    id                      uuid primary key default gen_random_uuid(),
    
    -- Polymorphic target
    entity_type             text not null,  -- 'message', 'exchange', 'dialogue', 'content_part'
    entity_id               uuid not null,
    
    -- Annotation content
    annotation_type         text not null,  -- 'tag', 'title', 'summary', 'topic', 'quality', etc.
    annotation_key          text,           -- optional sub-key (e.g., 'language' for code blocks)
    annotation_value        text not null,  -- the actual value
    annotation_data         jsonb,          -- additional structured data
    
    -- Provenance
    confidence              float,
    source                  text not null,  -- 'manual', 'heuristic', 'model'
    source_version          text,
    
    -- Lifecycle
    created_at              timestamptz default now(),
    superseded_at           timestamptz,
    superseded_by           uuid references derived.annotations,
    
    -- Unique active annotation per (entity, type, key, value)
    unique nulls not distinct (entity_type, entity_id, annotation_type, annotation_key, annotation_value, superseded_at)
);

-- ============================================================
-- derived.content_hashes
-- ============================================================

create table derived.content_hashes (
    id                      uuid primary key default gen_random_uuid(),
    
    entity_type             text not null,
    entity_id               uuid not null,
    hash_scope              text not null,  -- 'full' | 'user' | 'assistant'
    
    hash_sha256             text not null,
    hash_simhash            text,
    
    normalization           text not null default 'none',
    
    computed_at             timestamptz default now(),
    
    unique (entity_type, entity_id, hash_scope, normalization)
);

-- ============================================================
-- DERIVED INDEXES
-- ============================================================

create index idx_derived_trees_linear on derived.dialogue_trees(is_linear);
create index idx_derived_trees_branched on derived.dialogue_trees(branch_count) where branch_count > 0;

create index idx_derived_paths_dialogue on derived.message_paths(dialogue_id);
create index idx_derived_paths_depth on derived.message_paths(depth);
create index idx_derived_paths_leaf on derived.message_paths(dialogue_id) where is_leaf;
create index idx_derived_paths_primary on derived.message_paths(dialogue_id) where is_on_primary_path;

create index idx_derived_sequences_dialogue on derived.linear_sequences(dialogue_id);
create index idx_derived_sequences_primary on derived.linear_sequences(dialogue_id) where is_primary;
create index idx_derived_sequence_msgs_seq on derived.sequence_messages(sequence_id, position);
create index idx_derived_sequence_msgs_msg on derived.sequence_messages(message_id);

create index idx_derived_exchanges_dialogue on derived.exchanges(dialogue_id);
create index idx_derived_exchanges_first_msg on derived.exchanges(first_message_id);
create index idx_derived_exchanges_last_msg on derived.exchanges(last_message_id);
create index idx_derived_exchange_msgs_exch on derived.exchange_messages(exchange_id, position);

create index idx_derived_seq_exchanges_seq on derived.sequence_exchanges(sequence_id, position);
create index idx_derived_seq_exchanges_exch on derived.sequence_exchanges(exchange_id);

create index idx_derived_exchange_content_asst_hash on derived.exchange_content(assistant_text_hash);
create index idx_derived_exchange_content_full_hash on derived.exchange_content(full_text_hash);

create index idx_derived_annotations_entity on derived.annotations(entity_type, entity_id) where superseded_at is null;
create index idx_derived_annotations_type on derived.annotations(annotation_type, annotation_value) where superseded_at is null;
create index idx_derived_annotations_source on derived.annotations(source) where superseded_at is null;

create index idx_derived_hashes_hash on derived.content_hashes(hash_sha256);
create index idx_derived_hashes_entity on derived.content_hashes(entity_type, entity_id);

-- ============================================================
-- derived.annotator_cursors
-- ============================================================
-- Tracks processing state for each annotator version.
-- Allows incremental annotation without re-processing old entities.

create table derived.annotator_cursors (
    id                      uuid primary key default gen_random_uuid(),
    
    annotator_name          text not null,
    annotator_version       text not null,
    entity_type             text not null,  -- 'message', 'exchange', etc.
    
    -- High water mark: last entity created_at timestamp processed
    high_water_mark         timestamptz not null,
    
    -- Stats for this cursor
    entities_processed      int not null default 0,
    annotations_created     int not null default 0,
    
    updated_at              timestamptz default now(),
    
    unique (annotator_name, annotator_version, entity_type)
);

create index idx_annotator_cursors_lookup on derived.annotator_cursors(annotator_name, entity_type);