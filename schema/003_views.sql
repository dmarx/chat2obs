-- schema/003_views.sql
-- Convenience views for analysis

-- ============================================================
-- REGENERATION ATTEMPTS
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
-- MESSAGE WITH CONTENT
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
