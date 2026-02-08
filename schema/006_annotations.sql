-- schema/003_annotations.sql
-- Annotation system: separate tables by entity type and value type
--
-- Design:
-- - 4 entity types: content_part, message, prompt_response, dialogue
-- - 4 value types: flag, string, numeric, json
-- - 16 tables total, each optimally indexed
--
-- Flag annotations: key presence = true (no value column)
-- String annotations: key + text value (multi-value allowed per key)
-- Numeric annotations: key + numeric value (multi-value allowed per key)
-- JSON annotations: key + jsonb value (single value per key)

-- ============================================================
-- CONTENT_PART ANNOTATIONS
-- ============================================================

create table if not exists derived.content_part_annotations_flag (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.content_parts(id) on delete cascade,
    annotation_key      text not null,
    
    confidence          float,
    reason              text,
    source              text not null,  -- 'ingestion', 'heuristic', 'model', 'manual'
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key)
);

create index idx_cp_ann_flag_key on derived.content_part_annotations_flag(annotation_key);
create index idx_cp_ann_flag_entity on derived.content_part_annotations_flag(entity_id);


create table if not exists derived.content_part_annotations_string (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.content_parts(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    text not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key, annotation_value)
);

create index idx_cp_ann_str_key on derived.content_part_annotations_string(annotation_key);
create index idx_cp_ann_str_value on derived.content_part_annotations_string(annotation_key, annotation_value);
create index idx_cp_ann_str_entity on derived.content_part_annotations_string(entity_id);


create table if not exists derived.content_part_annotations_numeric (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.content_parts(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    numeric not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key, annotation_value)
);

create index idx_cp_ann_num_key on derived.content_part_annotations_numeric(annotation_key);
create index idx_cp_ann_num_range on derived.content_part_annotations_numeric(annotation_key, annotation_value);
create index idx_cp_ann_num_entity on derived.content_part_annotations_numeric(entity_id);


create table if not exists derived.content_part_annotations_json (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.content_parts(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    jsonb not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key)  -- single JSON blob per key
);

create index idx_cp_ann_json_key on derived.content_part_annotations_json(annotation_key);
create index idx_cp_ann_json_entity on derived.content_part_annotations_json(entity_id);
create index idx_cp_ann_json_gin on derived.content_part_annotations_json using gin(annotation_value);


-- ============================================================
-- MESSAGE ANNOTATIONS
-- ============================================================

create table if not exists derived.message_annotations_flag (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.messages(id) on delete cascade,
    annotation_key      text not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key)
);

create index idx_msg_ann_flag_key on derived.message_annotations_flag(annotation_key);
create index idx_msg_ann_flag_entity on derived.message_annotations_flag(entity_id);


create table if not exists derived.message_annotations_string (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.messages(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    text not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key, annotation_value)
);

create index idx_msg_ann_str_key on derived.message_annotations_string(annotation_key);
create index idx_msg_ann_str_value on derived.message_annotations_string(annotation_key, annotation_value);
create index idx_msg_ann_str_entity on derived.message_annotations_string(entity_id);


create table if not exists derived.message_annotations_numeric (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.messages(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    numeric not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key, annotation_value)
);

create index idx_msg_ann_num_key on derived.message_annotations_numeric(annotation_key);
create index idx_msg_ann_num_range on derived.message_annotations_numeric(annotation_key, annotation_value);
create index idx_msg_ann_num_entity on derived.message_annotations_numeric(entity_id);


create table if not exists derived.message_annotations_json (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.messages(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    jsonb not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key)
);

create index idx_msg_ann_json_key on derived.message_annotations_json(annotation_key);
create index idx_msg_ann_json_entity on derived.message_annotations_json(entity_id);
create index idx_msg_ann_json_gin on derived.message_annotations_json using gin(annotation_value);


-- ============================================================
-- PROMPT_RESPONSE ANNOTATIONS
-- ============================================================

create table if not exists derived.prompt_response_annotations_flag (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references derived.prompt_responses(id) on delete cascade,
    annotation_key      text not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key)
);

create index idx_pr_ann_flag_key on derived.prompt_response_annotations_flag(annotation_key);
create index idx_pr_ann_flag_entity on derived.prompt_response_annotations_flag(entity_id);


create table if not exists derived.prompt_response_annotations_string (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references derived.prompt_responses(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    text not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key, annotation_value)
);

create index idx_pr_ann_str_key on derived.prompt_response_annotations_string(annotation_key);
create index idx_pr_ann_str_value on derived.prompt_response_annotations_string(annotation_key, annotation_value);
create index idx_pr_ann_str_entity on derived.prompt_response_annotations_string(entity_id);


create table if not exists derived.prompt_response_annotations_numeric (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references derived.prompt_responses(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    numeric not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key, annotation_value)
);

create index idx_pr_ann_num_key on derived.prompt_response_annotations_numeric(annotation_key);
create index idx_pr_ann_num_range on derived.prompt_response_annotations_numeric(annotation_key, annotation_value);
create index idx_pr_ann_num_entity on derived.prompt_response_annotations_numeric(entity_id);


create table if not exists derived.prompt_response_annotations_json (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references derived.prompt_responses(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    jsonb not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key)
);

create index idx_pr_ann_json_key on derived.prompt_response_annotations_json(annotation_key);
create index idx_pr_ann_json_entity on derived.prompt_response_annotations_json(entity_id);
create index idx_pr_ann_json_gin on derived.prompt_response_annotations_json using gin(annotation_value);


-- ============================================================
-- DIALOGUE ANNOTATIONS
-- ============================================================

create table if not exists derived.dialogue_annotations_flag (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.dialogues(id) on delete cascade,
    annotation_key      text not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key)
);

create index idx_dlg_ann_flag_key on derived.dialogue_annotations_flag(annotation_key);
create index idx_dlg_ann_flag_entity on derived.dialogue_annotations_flag(entity_id);


create table if not exists derived.dialogue_annotations_string (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.dialogues(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    text not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key, annotation_value)
);

create index idx_dlg_ann_str_key on derived.dialogue_annotations_string(annotation_key);
create index idx_dlg_ann_str_value on derived.dialogue_annotations_string(annotation_key, annotation_value);
create index idx_dlg_ann_str_entity on derived.dialogue_annotations_string(entity_id);


create table if not exists derived.dialogue_annotations_numeric (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.dialogues(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    numeric not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key, annotation_value)
);

create index idx_dlg_ann_num_key on derived.dialogue_annotations_numeric(annotation_key);
create index idx_dlg_ann_num_range on derived.dialogue_annotations_numeric(annotation_key, annotation_value);
create index idx_dlg_ann_num_entity on derived.dialogue_annotations_numeric(entity_id);


create table if not exists derived.dialogue_annotations_json (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.dialogues(id) on delete cascade,
    annotation_key      text not null,
    annotation_value    jsonb not null,
    
    confidence          float,
    reason              text,
    source              text not null,
    source_version      text,
    created_at          timestamptz default now(),
    
    unique (entity_id, annotation_key)
);

create index idx_dlg_ann_json_key on derived.dialogue_annotations_json(annotation_key);
create index idx_dlg_ann_json_entity on derived.dialogue_annotations_json(entity_id);
create index idx_dlg_ann_json_gin on derived.dialogue_annotations_json using gin(annotation_value);


-- ============================================================
-- CONVENIENCE VIEWS
-- ============================================================

-- Union view for each entity type (useful for browsing all annotations)

create or replace view derived.content_part_annotations_all as
select id, entity_id, annotation_key, null::text as annotation_value, 'flag' as value_type, confidence, reason, source, created_at
from derived.content_part_annotations_flag
union all
select id, entity_id, annotation_key, annotation_value, 'string', confidence, reason, source, created_at
from derived.content_part_annotations_string
union all
select id, entity_id, annotation_key, annotation_value::text, 'numeric', confidence, reason, source, created_at
from derived.content_part_annotations_numeric
union all
select id, entity_id, annotation_key, annotation_value::text, 'json', confidence, reason, source, created_at
from derived.content_part_annotations_json;


create or replace view derived.message_annotations_all as
select id, entity_id, annotation_key, null::text as annotation_value, 'flag' as value_type, confidence, reason, source, created_at
from derived.message_annotations_flag
union all
select id, entity_id, annotation_key, annotation_value, 'string', confidence, reason, source, created_at
from derived.message_annotations_string
union all
select id, entity_id, annotation_key, annotation_value::text, 'numeric', confidence, reason, source, created_at
from derived.message_annotations_numeric
union all
select id, entity_id, annotation_key, annotation_value::text, 'json', confidence, reason, source, created_at
from derived.message_annotations_json;


create or replace view derived.prompt_response_annotations_all as
select id, entity_id, annotation_key, null::text as annotation_value, 'flag' as value_type, confidence, reason, source, created_at
from derived.prompt_response_annotations_flag
union all
select id, entity_id, annotation_key, annotation_value, 'string', confidence, reason, source, created_at
from derived.prompt_response_annotations_string
union all
select id, entity_id, annotation_key, annotation_value::text, 'numeric', confidence, reason, source, created_at
from derived.prompt_response_annotations_numeric
union all
select id, entity_id, annotation_key, annotation_value::text, 'json', confidence, reason, source, created_at
from derived.prompt_response_annotations_json;


create or replace view derived.dialogue_annotations_all as
select id, entity_id, annotation_key, null::text as annotation_value, 'flag' as value_type, confidence, reason, source, created_at
from derived.dialogue_annotations_flag
union all
select id, entity_id, annotation_key, annotation_value, 'string', confidence, reason, source, created_at
from derived.dialogue_annotations_string
union all
select id, entity_id, annotation_key, annotation_value::text, 'numeric', confidence, reason, source, created_at
from derived.dialogue_annotations_numeric
union all
select id, entity_id, annotation_key, annotation_value::text, 'json', confidence, reason, source, created_at
from derived.dialogue_annotations_json;
