-- schema/002_derived.sql
-- Derived data layer: computed/analyzed structures

create schema if not exists derived;

-- ============================================================
-- derived.dialogue_trees
-- ============================================================

create table if not exists derived.dialogue_trees (
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

create table if not exists derived.message_paths (
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

create table if not exists derived.linear_sequences (
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

create table if not exists derived.sequence_messages (
    sequence_id             uuid not null references derived.linear_sequences on delete cascade,
    message_id              uuid not null references raw.messages,
    position                int not null,
    
    primary key (sequence_id, message_id)
);

-- ============================================================
-- derived.exchanges
-- ============================================================

create table if not exists derived.exchanges (
    id                      uuid primary key default gen_random_uuid(),
    sequence_id             uuid not null references derived.linear_sequences on delete cascade,
    position                int not null,
    
    first_message_id        uuid not null references raw.messages,
    last_message_id         uuid not null references raw.messages,
    
    message_count           int not null,
    user_message_count      int not null,
    assistant_message_count int not null,
    
    is_continuation         boolean default false,
    continuation_of_id      uuid references derived.exchanges,
    merged_count            int default 1,
    
    started_at              timestamptz,
    ended_at                timestamptz,
    
    computed_at             timestamptz default now(),
    
    unique (sequence_id, position)
);

create table if not exists derived.exchange_messages (
    exchange_id             uuid not null references derived.exchanges on delete cascade,
    message_id              uuid not null references raw.messages,
    position                int not null,
    
    primary key (exchange_id, message_id)
);

-- ============================================================
-- derived.exchange_content
-- ============================================================

create table if not exists derived.exchange_content (
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
-- derived.labels
-- ============================================================

create table if not exists derived.labels (
    id                      uuid primary key default gen_random_uuid(),
    
    entity_type             text not null,
    entity_id               uuid not null,
    
    label_type              text not null,
    label_value             text not null,
    label_data              jsonb,
    
    confidence              float,
    source                  text not null,
    source_version          text,
    
    created_at              timestamptz default now(),
    superseded_at           timestamptz,
    superseded_by           uuid references derived.labels,
    
    unique nulls not distinct (entity_type, entity_id, label_type, label_value, superseded_at)
);

-- ============================================================
-- derived.content_hashes
-- ============================================================

create table if not exists derived.content_hashes (
    id                      uuid primary key default gen_random_uuid(),
    
    entity_type             text not null,
    entity_id               uuid not null,
    hash_scope              text not null,
    
    hash_sha256             text not null,
    hash_simhash            text,
    
    normalization           text not null default 'none',
    
    computed_at             timestamptz default now(),
    
    unique (entity_type, entity_id, hash_scope, normalization)
);

-- ============================================================
-- Indexes
-- ============================================================

create index if not exists idx_derived_trees_linear on derived.dialogue_trees(is_linear);
create index if not exists idx_derived_paths_dialogue on derived.message_paths(dialogue_id);
create index if not exists idx_derived_paths_leaf on derived.message_paths(dialogue_id) where is_leaf;
create index if not exists idx_derived_paths_primary on derived.message_paths(dialogue_id) where is_on_primary_path;
create index if not exists idx_derived_sequences_dialogue on derived.linear_sequences(dialogue_id);
create index if not exists idx_derived_sequences_primary on derived.linear_sequences(dialogue_id) where is_primary;
create index if not exists idx_derived_sequence_msgs_seq on derived.sequence_messages(sequence_id, position);
create index if not exists idx_derived_exchanges_sequence on derived.exchanges(sequence_id, position);
create index if not exists idx_derived_exchange_content_hash on derived.exchange_content(assistant_text_hash);
create index if not exists idx_derived_labels_entity on derived.labels(entity_type, entity_id) where superseded_at is null;
create index if not exists idx_derived_labels_type on derived.labels(label_type, label_value) where superseded_at is null;
create index if not exists idx_derived_hashes_hash on derived.content_hashes(hash_sha256);
create index if not exists idx_derived_hashes_entity on derived.content_hashes(entity_type, entity_id);