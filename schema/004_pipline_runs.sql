-- schema/004_pipeline_runs.sql
-- Track reproducible derived builds (chunking / annotation / exchange build / render)

create table if not exists derived.pipeline_runs (
    id              uuid primary key default gen_random_uuid(),

    run_type        text not null,                         -- 'chunk'|'chunk_annotate'|'exchange_build'|'article_extract'|'render'|...
    name            text,                                  -- optional label
    params          jsonb not null default '{}'::jsonb,
    git_sha         text,

    started_at      timestamptz default now(),
    ended_at        timestamptz,
    status          text not null default 'running',        -- 'running'|'success'|'failed'
    notes           text
);

create index if not exists idx_pipeline_runs_type_time
    on derived.pipeline_runs(run_type, started_at desc);
