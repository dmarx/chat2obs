-- schema/005_prompt_response_views.sql
-- Prompt-response views that don't depend on annotation tables

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
