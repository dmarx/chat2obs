-- schema/003b_prompt_response_views.sql
-- Optional views for convenient querying of prompt-response data

-- ============================================================
-- Exchange-like view: Group responses by their prompt
-- 
-- This gives you an "exchange" perspective where you can see
-- all responses associated with a given prompt message.
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
-- Wiki articles with their annotation status
-- ============================================================

CREATE OR REPLACE VIEW derived.wiki_article_status AS
SELECT 
    pr.id as prompt_response_id,
    pr.dialogue_id,
    d.title as dialogue_title,
    d.source as platform,
    
    prc.prompt_text,
    prc.response_text,
    prc.response_word_count,
    
    -- Title extraction status
    title_ann.annotation_value as extracted_title,
    title_ann.confidence as title_confidence,
    
    -- Count of wiki links
    (wiki_ann.annotation_data->>'wiki_link_count')::int as wiki_link_count,
    
    -- For manual inspection
    SPLIT_PART(prc.response_text, E'\n', 1) as first_line,
    SPLIT_PART(prc.response_text, E'\n', 2) as second_line,
    
    pr.created_at

FROM derived.prompt_responses pr
JOIN raw.dialogues d ON d.id = pr.dialogue_id
LEFT JOIN derived.prompt_response_content prc ON prc.prompt_response_id = pr.id

-- Must have wiki_article tag
JOIN derived.annotations wiki_ann ON 
    wiki_ann.entity_type = 'prompt_response' 
    AND wiki_ann.entity_id = pr.id
    AND wiki_ann.annotation_key = 'exchange_type'
    AND wiki_ann.annotation_value = 'wiki_article'
    AND wiki_ann.superseded_at IS NULL

-- May or may not have title
LEFT JOIN derived.annotations title_ann ON 
    title_ann.entity_type = 'prompt_response'
    AND title_ann.entity_id = pr.id
    AND title_ann.annotation_key = 'proposed_title'
    AND title_ann.superseded_at IS NULL

WHERE pr.response_role = 'assistant';


-- ============================================================
-- Annotation summary per entity
-- ============================================================

CREATE OR REPLACE VIEW derived.prompt_response_annotations AS
SELECT 
    pr.id as prompt_response_id,
    pr.dialogue_id,
    
    -- Collect all annotations as JSONB
    JSONB_OBJECT_AGG(
        COALESCE(a.annotation_key, a.annotation_type),
        JSONB_BUILD_OBJECT(
            'value', a.annotation_value,
            'confidence', a.confidence,
            'data', a.annotation_data
        )
    ) FILTER (WHERE a.id IS NOT NULL) as annotations,
    
    -- Quick access to common annotations
    MAX(CASE WHEN a.annotation_key = 'exchange_type' THEN a.annotation_value END) as exchange_type,
    MAX(CASE WHEN a.annotation_key = 'proposed_title' THEN a.annotation_value END) as proposed_title

FROM derived.prompt_responses pr
LEFT JOIN derived.annotations a ON 
    a.entity_type = 'prompt_response'
    AND a.entity_id = pr.id
    AND a.superseded_at IS NULL
GROUP BY pr.id, pr.dialogue_id;