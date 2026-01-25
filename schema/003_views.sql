-- schema/003_views.sql
-- Convenience views for analysis

-- ============================================================
-- Active labels
-- ============================================================

create or replace view derived.v_labels as
select * from derived.labels where superseded_at is null;

-- ============================================================
-- Dialogue summary
-- ============================================================

create or replace view derived.v_dialogue_summary as
select 
    d.id,
    d.source,
    d.source_id,
    d.title,
    d.created_at,
    d.imported_at,
    t.total_nodes,
    t.max_depth,
    t.branch_count,
    t.leaf_count,
    t.is_linear,
    t.has_regenerations,
    t.has_edits,
    t.primary_path_length
from raw.dialogues d
left join derived.dialogue_trees t on t.dialogue_id = d.id;

-- ============================================================
-- Primary path messages
-- ============================================================

create or replace view derived.v_primary_messages as
select 
    m.*,
    p.depth,
    p.child_count,
    p.sibling_index
from raw.messages m
join derived.message_paths p on p.message_id = m.id
where p.is_on_primary_path;

-- ============================================================
-- Branch points
-- ============================================================

create or replace view derived.v_branch_points as
select 
    m.id as message_id,
    m.dialogue_id,
    m.role,
    m.created_at,
    p.depth,
    p.child_count,
    (
        select count(distinct c.role) = 1 
        from raw.messages c 
        where c.parent_id = m.id
    ) as is_regeneration
from raw.messages m
join derived.message_paths p on p.message_id = m.id
where p.child_count > 1;

-- ============================================================
-- Regeneration attempts
-- ============================================================

create or replace view derived.v_regenerations as
select 
    m.dialogue_id,
    m.parent_id,
    m.role,
    array_agg(m.id order by m.created_at) as attempt_ids,
    array_agg(m.created_at order by m.created_at) as attempt_times,
    count(*) as attempt_count
from raw.messages m
where m.parent_id is not null
group by m.dialogue_id, m.parent_id, m.role
having count(*) > 1;

-- ============================================================
-- Exchanges with content
-- ============================================================

create or replace view derived.v_exchanges as
select 
    e.*,
    c.user_text,
    c.assistant_text,
    c.user_word_count,
    c.assistant_word_count,
    c.total_word_count,
    c.assistant_text_hash,
    c.full_text_hash
from derived.exchanges e
left join derived.exchange_content c on c.exchange_id = e.id;

-- ============================================================
-- Message with content
-- ============================================================

create or replace view raw.v_message_content as
select 
    m.id as message_id,
    m.dialogue_id,
    m.role,
    m.created_at,
    string_agg(cp.text_content, E'\n' order by cp.sequence) as full_text
from raw.messages m
left join raw.content_parts cp on cp.message_id = m.id and cp.text_content is not null
group by m.id, m.dialogue_id, m.role, m.created_at;

-- ============================================================
-- Content duplicates
-- ============================================================

create or replace view derived.v_content_duplicates as
select 
    hash_sha256,
    hash_scope,
    entity_type,
    normalization,
    array_agg(entity_id order by computed_at) as entity_ids,
    count(*) as duplicate_count
from derived.content_hashes
group by hash_sha256, hash_scope, entity_type, normalization
having count(*) > 1;

-- ============================================================
-- Non-primary sequences
-- ============================================================

create or replace view derived.v_abandoned_sequences as
select 
    ls.*,
    d.title as dialogue_title,
    d.source
from derived.linear_sequences ls
join raw.dialogues d on d.id = ls.dialogue_id
where not ls.is_primary;