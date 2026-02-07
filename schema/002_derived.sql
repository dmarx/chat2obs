-- schema/002_derived.sql
-- Derived data layer: computed/analyzed structures

-- ============================================================
-- SCHEMA SETUP
-- ============================================================

create schema if not exists derived;

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
    
    created_at             timestamptz default now(),
    
    unique (entity_type, entity_id, hash_scope, normalization)
);

-- ============================================================
-- DERIVED INDEXES
-- ============================================================

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
