-- schema/002_derived.sql
-- Derived data layer: minimal infrastructure

-- ============================================================
-- SCHEMA SETUP
-- ============================================================

create schema if not exists derived;

-- ============================================================
-- derived.annotator_cursors
-- 
-- Tracks processing state for each annotator version.
-- Allows incremental annotation without re-processing old entities.
-- ============================================================

create table if not exists derived.annotator_cursors (
    id                      uuid primary key default gen_random_uuid(),
    
    annotator_name          text not null,
    annotator_version       text not null,
    entity_type             text not null,  -- 'message', 'prompt_response', etc.
    
    -- High water mark: last entity created_at timestamp processed
    high_water_mark         timestamptz not null,
    
    -- Stats for this cursor
    entities_processed      int not null default 0,
    annotations_created     int not null default 0,
    cumulative_runtime_seconds   float DEFAULT 0.0,
    
    updated_at              timestamptz default now(),
    
    unique (annotator_name, annotator_version, entity_type)
);

-- Add cumulative_runtime_seconds column to track total processing time
COMMENT ON COLUMN derived.annotator_cursors.cumulative_runtime_seconds IS 
    'Cumulative runtime in seconds across all runs of this annotator version';

create index if not exists idx_annotator_cursors_lookup 
    on derived.annotator_cursors(annotator_name, entity_type);
