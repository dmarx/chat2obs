-- schema/008_annotation_views.sql
-- Views that depend on annotation tables
-- Must run AFTER 006_annotations.sql

-- ============================================================
-- wiki_article_status
-- 
-- Wiki articles with their annotation status.
-- Uses typed annotation tables.
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
