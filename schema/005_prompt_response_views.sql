-- schema/005_prompt_response_views.sql
-- Prompt-response convenience views for querying and analysis

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
-- wiki_article_status
-- 
-- Wiki articles with their annotation status.
-- Uses new typed annotation tables.
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
    
    -- Title extraction status (from string annotations)
    title_ann.annotation_value as extracted_title,
    title_ann.confidence as title_confidence,
    
    -- Count of wiki links (from numeric annotations)
    wiki_count_ann.annotation_value as wiki_link_count,
    
    -- For manual inspection
    SPLIT_PART(prc.response_text, E'\n', 1) as first_line,
    SPLIT_PART(prc.response_text, E'\n', 2) as second_line,
    
    pr.created_at

FROM derived.prompt_responses pr
JOIN raw.dialogues d ON d.id = pr.dialogue_id
LEFT JOIN derived.prompt_response_content prc ON prc.prompt_response_id = pr.id

-- Must have wiki_article exchange_type (string annotation)
JOIN derived.prompt_response_annotations_string wiki_ann ON 
    wiki_ann.entity_id = pr.id
    AND wiki_ann.annotation_key = 'exchange_type'
    AND wiki_ann.annotation_value = 'wiki_article'

-- May have extracted title (string annotation)
LEFT JOIN derived.prompt_response_annotations_string title_ann ON 
    title_ann.entity_id = pr.id
    AND title_ann.annotation_key = 'proposed_title'

-- May have wiki link count (numeric annotation)
LEFT JOIN derived.prompt_response_annotations_numeric wiki_count_ann ON
    wiki_count_ann.entity_id = pr.id
    AND wiki_count_ann.annotation_key = 'wiki_link_count'

WHERE pr.response_role = 'assistant';


-- ============================================================
-- prompt_response_annotations_summary
-- 
-- Aggregate view of all annotations per prompt-response.
-- Uses union across all typed annotation tables.
-- ============================================================

CREATE OR REPLACE VIEW derived.prompt_response_annotations_summary AS
SELECT 
    pr.id as prompt_response_id,
    pr.dialogue_id,
    
    -- Aggregate all annotations as JSONB
    JSONB_OBJECT_AGG(
        ann.annotation_key,
        JSONB_BUILD_OBJECT(
            'value', ann.annotation_value,
            'value_type', ann.value_type,
            'confidence', ann.confidence,
            'source', ann.source
        )
    ) FILTER (WHERE ann.annotation_key IS NOT NULL) as annotations,
    
    -- Quick access to common annotations
    MAX(CASE WHEN ann.annotation_key = 'exchange_type' AND ann.value_type = 'string' 
        THEN ann.annotation_value END) as exchange_type,
    MAX(CASE WHEN ann.annotation_key = 'proposed_title' AND ann.value_type = 'string' 
        THEN ann.annotation_value END) as proposed_title

FROM derived.prompt_responses pr
LEFT JOIN derived.prompt_response_annotations_all ann ON 
    ann.entity_id = pr.id
GROUP BY pr.id, pr.dialogue_id;
