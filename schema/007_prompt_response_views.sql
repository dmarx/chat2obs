-- schema/004_prompt_response_views.sql
-- Prompt-response convenience views for annotation and analysis

-- ============================================================
-- prompt_response_content_v
--
-- Join prompt_responses with their content and roles.
-- This is the primary view used by prompt-response annotators.
-- ============================================================

CREATE OR REPLACE VIEW derived.prompt_response_content_v AS
SELECT 
    pr.id as prompt_response_id,
    pr.dialogue_id,
    pr.prompt_message_id,
    pr.response_message_id,
    
    -- Content (from prompt_response_content table)
    prc.prompt_text,
    prc.response_text,
    prc.prompt_word_count,
    prc.response_word_count,
    
    -- Roles (denormalized for convenience)
    pr.prompt_role,
    pr.response_role,
    
    -- Position info
    pr.prompt_position,
    pr.response_position,
    
    -- Timestamps
    pr.created_at
FROM derived.prompt_responses pr
LEFT JOIN derived.prompt_response_content prc 
    ON prc.prompt_response_id = pr.id;


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
    
    -- Prompt content (same for all responses, so just take first)
    MIN(prc.prompt_text) as prompt_text,
    MIN(prc.prompt_word_count) as prompt_word_count,
    
    -- Aggregate response content
    STRING_AGG(prc.response_text, E'\n---\n' ORDER BY pr.response_position) as all_responses_text,
    SUM(prc.response_word_count) as total_response_words,
    
    MIN(pr.created_at) as created_at
FROM derived.prompt_responses pr
LEFT JOIN derived.prompt_response_content prc 
    ON prc.prompt_response_id = pr.id
GROUP BY pr.prompt_message_id, pr.dialogue_id;


-- ============================================================
-- prompt_response_with_annotations
--
-- Join prompt-response pairs with their typed annotations.
-- Useful for filtering/querying annotated content.
-- ============================================================

CREATE OR REPLACE VIEW derived.prompt_response_with_annotations AS
SELECT 
    prc.*,
    
    -- Aggregate all annotations as JSONB
    (
        SELECT jsonb_object_agg(annotation_key, jsonb_build_object('type', value_type, 'value', annotation_value))
        FROM derived.prompt_response_annotations_all pra
        WHERE pra.entity_id = prc.prompt_response_id
    ) as annotations
FROM derived.prompt_response_content_v prc;
