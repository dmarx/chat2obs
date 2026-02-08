-- schema/005_annotations.sql
-- Typed annotation tables for all entity types

-- ============================================================
-- CONTENT_PART ANNOTATIONS
-- ============================================================

create table if not exists derived.content_part_annotations_flag (
    id                  uuid primary key default gen_random_uuid(),
    entity_id           uuid not null references raw.content_parts(id) on delete cascade,
    annotation_key      text not null,
    
    confidence          float,
    reason              text,
    source              text not null,
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
    
    unique (entity_id, annotation_key)
);

create index idx_cp_ann_json_key on derived.content_part_annotations_json(annotation_key);
create index idx_cp_ann_json_entity on derived.content_part_annotations_json(entity_id);


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
