-- schema/006_prompt_response_views.sql
-- Prompt-response views (aggregating content and word counts from annotations)

-- ============================================================
-- prompt_response_content_v
--
-- Join prompt_responses with their content aggregated from raw.content_parts.
-- Word counts aggregated from content_part_annotations_numeric.
-- This is the primary view used by prompt-response annotators.
-- ============================================================

CREATE OR REPLACE VIEW derived.prompt_response_content_v AS
SELECT 
    pr.id as prompt_response_id,
    pr.dialogue_id,
    pr.prompt_message_id,
    pr.response_message_id,
    
    -- Aggregate prompt text from content_parts
    (SELECT string_agg(cp.text_content, ' ' ORDER BY cp.sequence)
     FROM raw.content_parts cp 
     WHERE cp.message_id = pr.prompt_message_id 
       AND cp.text_content IS NOT NULL) as prompt_text,
    
    -- Aggregate response text from content_parts
    (SELECT string_agg(cp.text_content, ' ' ORDER BY cp.sequence)
     FROM raw.content_parts cp 
     WHERE cp.message_id = pr.response_message_id 
       AND cp.text_content IS NOT NULL) as response_text,
    
    -- Sum prompt word count from annotations
    (SELECT COALESCE(SUM(ann.annotation_value)::int, 0)
     FROM raw.content_parts cp
     LEFT JOIN derived.content_part_annotations_numeric ann 
         ON ann.entity_id = cp.id AND ann.annotation_key = 'word_count'
     WHERE cp.message_id = pr.prompt_message_id) as prompt_word_count,
    
    -- Sum response word count from annotations
    (SELECT COALESCE(SUM(ann.annotation_value)::int, 0)
     FROM raw.content_parts cp
     LEFT JOIN derived.content_part_annotations_numeric ann 
         ON ann.entity_id = cp.id AND ann.annotation_key = 'word_count'
     WHERE cp.message_id = pr.response_message_id) as response_word_count,
    
    -- Roles (denormalized for convenience)
    pr.prompt_role,
    pr.response_role,
    
    -- Position info
    pr.prompt_position,
    pr.response_position,
    
    -- Timestamps
    pr.created_at
FROM derived.prompt_responses pr;


-- ============================================================
-- prompt_exchanges
--
-- Exchange-like view: Group responses by their prompt
-- Shows all responses associated with a given prompt message.
-- ============================================================

CREATE OR REPLACE VIEW derived.prompt_exchanges AS
SELECT 
    pr.prompt_message_id,
    pr.dialogue_id,
    MIN(pr.prompt_position) as prompt_position,
    
    -- Aggregate response IDs as array
    ARRAY_AGG(pr.response_message_id ORDER BY pr.response_position) as response_message_ids,
    COUNT(*) as response_count,
    
    -- Flag if this prompt has multiple responses (regenerations)
    COUNT(*) > 1 as has_regenerations,
    
    -- Prompt content (same for all responses, so aggregate once)
    (SELECT string_agg(cp.text_content, ' ' ORDER BY cp.sequence)
     FROM raw.content_parts cp 
     WHERE cp.message_id = pr.prompt_message_id 
       AND cp.text_content IS NOT NULL
     LIMIT 1) as prompt_text,
    
    -- Prompt word count from annotations
    (SELECT COALESCE(SUM(ann.annotation_value)::int, 0)
     FROM raw.content_parts cp
     LEFT JOIN derived.content_part_annotations_numeric ann 
         ON ann.entity_id = cp.id AND ann.annotation_key = 'word_count'
     WHERE cp.message_id = pr.prompt_message_id
     LIMIT 1) as prompt_word_count,
    
    -- Aggregate all response texts
    STRING_AGG(
        (SELECT string_agg(cp.text_content, ' ' ORDER BY cp.sequence)
         FROM raw.content_parts cp 
         WHERE cp.message_id = pr.response_message_id 
           AND cp.text_content IS NOT NULL),
        E'\n---\n' 
        ORDER BY pr.response_position
    ) as all_responses_text,
    
    -- Sum all response word counts from annotations
    (SELECT COALESCE(SUM(ann.annotation_value)::int, 0)
     FROM raw.content_parts cp
     JOIN derived.prompt_responses pr2 ON cp.message_id = pr2.response_message_id
     LEFT JOIN derived.content_part_annotations_numeric ann 
         ON ann.entity_id = cp.id AND ann.annotation_key = 'word_count'
     WHERE pr2.prompt_message_id = pr.prompt_message_id) as total_response_words,
    
    MIN(pr.created_at) as created_at

FROM derived.prompt_responses pr
GROUP BY pr.prompt_message_id, pr.dialogue_id;
