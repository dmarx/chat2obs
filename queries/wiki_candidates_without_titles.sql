-- queries/wiki_candidates_without_titles.sql
-- 
-- Find wiki article candidates that don't have an extracted title.
-- These likely have preambles ("Sure, here's an article...") that 
-- obscure the actual title.
--
-- Use this for manual inspection to inform preamble detection patterns.

SELECT 
    pr.id as prompt_response_id,
    pr.dialogue_id,
    d.title as dialogue_title,
    d.source as platform,
    
    -- Wiki link count from annotation data
    wiki_ann.annotation_data->>'wiki_link_count' as wiki_link_count,
    
    -- First 100 chars of prompt (for context)
    LEFT(prc.prompt_text, 100) as prompt_preview,
    
    -- First 500 chars of response (should show preamble + title area)
    LEFT(prc.response_text, 500) as response_preview,
    
    -- Full first line for analysis
    SPLIT_PART(prc.response_text, E'\n', 1) as first_line,
    
    -- Second line (often where real title is after preamble)
    SPLIT_PART(prc.response_text, E'\n', 2) as second_line,
    
    prc.response_word_count

FROM derived.prompt_responses pr

JOIN raw.dialogues d 
    ON d.id = pr.dialogue_id

LEFT JOIN derived.prompt_response_content prc 
    ON prc.prompt_response_id = pr.id

-- Has wiki_article tag
JOIN derived.annotations wiki_ann ON 
    wiki_ann.entity_type = 'prompt_response' 
    AND wiki_ann.entity_id = pr.id
    AND wiki_ann.annotation_key = 'exchange_type'
    AND wiki_ann.annotation_value = 'wiki_article'
    AND wiki_ann.superseded_at IS NULL

-- Does NOT have proposed_title
LEFT JOIN derived.annotations title_ann ON 
    title_ann.entity_type = 'prompt_response'
    AND title_ann.entity_id = pr.id
    AND title_ann.annotation_key = 'proposed_title'
    AND title_ann.superseded_at IS NULL

WHERE 
    title_ann.id IS NULL
    AND pr.response_role = 'assistant'

ORDER BY 
    prc.response_word_count DESC NULLS LAST,
    pr.created_at DESC

LIMIT 100;


-- ============================================================
-- Additional useful queries
-- ============================================================

-- Count breakdown: wiki articles with/without titles
/*
SELECT 
    CASE WHEN title_ann.id IS NOT NULL THEN 'has_title' ELSE 'no_title' END as status,
    COUNT(*) as count
FROM derived.prompt_responses pr
JOIN derived.annotations wiki_ann ON 
    wiki_ann.entity_type = 'prompt_response' 
    AND wiki_ann.entity_id = pr.id
    AND wiki_ann.annotation_key = 'exchange_type'
    AND wiki_ann.annotation_value = 'wiki_article'
    AND wiki_ann.superseded_at IS NULL
LEFT JOIN derived.annotations title_ann ON 
    title_ann.entity_type = 'prompt_response'
    AND title_ann.entity_id = pr.id
    AND title_ann.annotation_key = 'proposed_title'
    AND title_ann.superseded_at IS NULL
WHERE pr.response_role = 'assistant'
GROUP BY 1;
*/


-- Common first-line patterns in untitled wiki articles
/*
SELECT 
    LEFT(SPLIT_PART(prc.response_text, E'\n', 1), 80) as first_line_pattern,
    COUNT(*) as occurrences
FROM derived.prompt_responses pr
JOIN derived.prompt_response_content prc ON prc.prompt_response_id = pr.id
JOIN derived.annotations wiki_ann ON 
    wiki_ann.entity_type = 'prompt_response' 
    AND wiki_ann.entity_id = pr.id
    AND wiki_ann.annotation_key = 'exchange_type'
    AND wiki_ann.annotation_value = 'wiki_article'
    AND wiki_ann.superseded_at IS NULL
LEFT JOIN derived.annotations title_ann ON 
    title_ann.entity_type = 'prompt_response'
    AND title_ann.entity_id = pr.id
    AND title_ann.annotation_key = 'proposed_title'
    AND title_ann.superseded_at IS NULL
WHERE 
    title_ann.id IS NULL
    AND pr.response_role = 'assistant'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 50;
*/