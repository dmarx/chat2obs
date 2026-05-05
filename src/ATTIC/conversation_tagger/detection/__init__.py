# conversation_tagger/detection/__init__.py
"""Detection functions for conversation analysis."""

from .content import *
from .code_indicators import *
from .wiki_markdown import *
from .structured_tags import *
from .first_user import *
from .exchange_rules import *

# Don't export helpers by default to keep namespace clean
from . import helpers

__all__ = [
    # Content detection
    'has_large_content', 'has_github_repos', 'has_canvas_operations',
    'has_web_search', 'has_reasoning_thoughts', 'has_code_execution',
    
    # Code detection
    'has_code_blocks', 'has_function_definitions', 'has_import_statements',
    'has_script_headers', 'has_high_keyword_density', 'has_code_structure_patterns',
    'has_code_patterns',
    
    # Wiki/markdown detection
    'has_wiki_links', 'has_latex_math', 'has_markdown_features', 'has_documentation_patterns',
    
    # Structured tags
    'create_conversation_length_tag', 'create_prompt_stats_tag', 'create_gizmo_plugin_tags',
    
    # First user message
    'first_user_has_large_content', 'first_user_has_code_patterns', 
    'first_user_has_attachments', 'first_user_has_code_attachments',
    
    # Exchange rules
    'user_has_code_blocks', 'user_has_attachments', 'user_has_error_messages',
    'user_prompt_length_category', 'user_is_continuation', 'user_has_quote_elaborate',
    'assistant_has_code_blocks', 'assistant_has_wiki_links', 'assistant_has_latex_math',
    'assistant_response_length_category', 'assistant_has_reasoning',
    'exchange_is_coding_focused', 'exchange_is_wiki_article_focused',
    'exchange_has_error_resolution', 'exchange_interaction_pattern', 'exchange_timing_stats'
]
