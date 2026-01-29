-- schema/006_views_chunks.sql
-- Ordered chunk streams, and chunk+annotation convenience views.

-- Latest chunk run per message (helper)
create or replace view derived.v_latest_chunk_run as
select
    message_id,
    max(run_id) as run_id
from derived.message_chunks
group by message_id;

-- Chunks (latest run) joined with active annotations
create or replace view derived.v_message_chunks as
select
    mc.*,
    a.annotation_type,
    a.annotation_key,
    a.annotation_value,
    a.confidence,
    a.source as annotation_source
from derived.message_chunks mc
join derived.v_latest_chunk_run l
  on l.message_id = mc.message_id and l.run_id = mc.run_id
left join derived.v_annotations a
  on a.entity_type = 'chunk' and a.entity_id = mc.id;

-- Exchange chunk stream (latest chunks), ordered across messages then within message
create or replace view derived.v_exchange_chunk_stream as
select
    e.id as exchange_id,
    em.position as message_position,
    mc.chunk_index as chunk_position_in_message,
    (em.position * 1000000 + mc.chunk_index) as exchange_chunk_position,

    m.id as message_id,
    m.role,
    m.created_at as message_created_at,

    mc.id as chunk_id,
    mc.chunk_type,
    mc.heading_level,
    mc.heading_text,
    mc.info_string,
    mc.text,
    mc.start_line,
    mc.end_line,
    mc.start_char,
    mc.end_char,
    mc.run_id as chunk_run_id,
    mc.chunker,
    mc.chunker_version,
    mc.data,
    mc.computed_at

from derived.exchanges e
join derived.exchange_messages em on em.exchange_id = e.id
join raw.messages m on m.id = em.message_id and m.deleted_at is null
join derived.message_chunks mc on mc.message_id = m.id
join derived.v_latest_chunk_run l on l.message_id = mc.message_id and l.run_id = mc.run_id;
