# CURRENT PROJECT FILE TREE
"""
conversation_tagger/
├── __init__.py                                 ✅ EXISTS
├── core/
│   ├── __init__.py                            ⚠️  NEEDS CREATION
│   ├── tag.py                                 ✅ EXISTS  
│   ├── tagger.py                              🔄 NEEDS UPDATE (integrate exchange-based)
│   ├── exchange.py                            ✅ EXISTS
│   ├── exchange_parser.py                     ✅ EXISTS (with quote+elaborate)
│   ├── exchange_tagger.py                     ✅ EXISTS
│   └── conversation_aggregator.py             ✅ EXISTS
├── detection/
│   ├── __init__.py                            ⚠️  NEEDS CREATION
│   ├── helpers.py                             ✅ EXISTS
│   ├── content.py                             ✅ EXISTS
│   ├── code_indicators.py                     ✅ EXISTS
│   ├── wiki_markdown.py                       ✅ EXISTS
│   ├── structured_tags.py                     ✅ EXISTS
│   ├── first_user.py                          ✅ EXISTS
│   └── exchange_rules.py                      ✅ EXISTS (with quote+elaborate)
├── analysis/
│   ├── __init__.py                            ⚠️  NEEDS CREATION
│   ├── faceting.py                            ✅ EXISTS
│   ├── comparison.py                          ✅ EXISTS
│   └── debugging.py                           ✅ EXISTS
├── factory.py                                 🔄 NEEDS UPDATE (integrate exchange-based)
└── examples.py                                ✅ EXISTS

docs/
├── README.md                                  ✅ EXISTS
└── API.md                                     ✅ EXISTS

tests/
├── conftest.py                                ✅ EXISTS
├── test_core.py                               ✅ EXISTS
├── test_detection.py                          ✅ EXISTS
├── test_integration.py                        ✅ EXISTS
├── test_helpers.py                            ✅ EXISTS
└── test_exchange_minimal.py                   ✅ EXISTS

pytest.ini                                     ✅ EXISTS
Makefile                                       ✅ EXISTS
setup.py                                       ✅ EXISTS

Legend:
✅ EXISTS - File exists with current content
🔄 NEEDS UPDATE - File exists but needs updates for integration
⚠️  NEEDS CREATION - Missing __init__.py files
"""

# =============================================================================
# MISSING FILES THAT NEED TO BE CREATED:

# conversation_tagger/core/__init__.py
"""Core classes for conversation tagging."""

from .tag import Tag
from .tagger import ConversationTagger
from .exchange import Exchange
from .exchange_parser import ExchangeParser
from .exchange_tagger import ExchangeTagger
from .conversation_aggregator import ConversationAggregator

__all__ = [
    'Tag', 'ConversationTagger', 'Exchange', 'ExchangeParser', 
    'ExchangeTagger', 'ConversationAggregator'
]


# =============================================================================
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


# =============================================================================
# conversation_tagger/analysis/__init__.py
"""Analysis functions for conversation data."""

from .faceting import print_faceted_summary, facet_conversations, get_facet_value
from .comparison import compare_facets
from .debugging import debug_code_detection, print_summary

__all__ = [
    'print_faceted_summary', 'facet_conversations', 'get_facet_value',
    'compare_facets', 'debug_code_detection', 'print_summary'
]


# =============================================================================
# UPDATED FILES THAT NEED INTEGRATION:

# conversation_tagger/core/tagger.py (UPDATED VERSION)
"""
Updated ConversationTagger that uses exchange-based analysis internally.
"""

from typing import Dict, Any, List, Callable, Optional, Union
from collections import defaultdict

from .tag import Tag
from .exchange_parser import ExchangeParser
from .exchange_tagger import ExchangeTagger
from .conversation_aggregator import ConversationAggregator


class ConversationTagger:
    """
    Enhanced tagging system that analyzes conversations at both exchange and conversation levels.
    
    Flow:
    1. Parse conversation into exchanges
    2. Tag each exchange with exchange-level rules
    3. Aggregate exchange tags to conversation-level tags
    4. Apply conversation-level supplemental rules
    """
    
    def __init__(self, use_exchange_analysis: bool = True):
        # Legacy conversation-level rules (for backwards compatibility)
        self.base_rules: Dict[str, Callable] = {}
        self.multi_tag_rules: Dict[str, Callable] = {}
        self.supplemental_rules: Dict[str, Callable] = {}
        self.rule_descriptions: Dict[str, str] = {}
        
        # Exchange-based analysis components
        self.use_exchange_analysis = use_exchange_analysis
        if use_exchange_analysis:
            self.exchange_parser = ExchangeParser()
            self.exchange_tagger = ExchangeTagger()
            self.conversation_aggregator = ConversationAggregator()
    
    # ===== EXCHANGE-LEVEL API =====
    
    def add_user_rule(self, tag_name: str, rule_function: Callable, description: str = ""):
        """Add rule that analyzes user messages in exchanges."""
        if self.use_exchange_analysis:
            self.exchange_tagger.add_user_rule(tag_name, rule_function, description)
    
    def add_assistant_rule(self, tag_name: str, rule_function: Callable, description: str = ""):
        """Add rule that analyzes assistant messages in exchanges."""
        if self.use_exchange_analysis:
            self.exchange_tagger.add_assistant_rule(tag_name, rule_function, description)
    
    def add_exchange_rule(self, tag_name: str, rule_function: Callable, description: str = ""):
        """Add rule that analyzes entire exchanges."""
        if self.use_exchange_analysis:
            self.exchange_tagger.add_exchange_rule(tag_name, rule_function, description)
    
    def add_exchange_supplemental_rule(self, tag_name: str, rule_function: Callable, description: str = ""):
        """Add exchange-level supplemental rule."""
        if self.use_exchange_analysis:
            self.exchange_tagger.add_supplemental_rule(tag_name, rule_function, description)
    
    # ===== LEGACY API (backwards compatibility) =====
    
    def add_base_rule(self, tag_name: str, rule_function: Callable, description: str = ""):
        """Add a conversation-level base rule (legacy API)."""
        self.base_rules[tag_name] = rule_function
        self.rule_descriptions[tag_name] = description
    
    def add_multi_tag_rule(self, rule_name: str, rule_function: Callable, description: str = ""):
        """Add a conversation-level multi-tag rule (legacy API)."""
        self.multi_tag_rules[rule_name] = rule_function
        self.rule_descriptions[rule_name] = description
    
    def add_supplemental_rule(self, tag_name: str, rule_function: Callable, description: str = ""):
        """Add a conversation-level supplemental rule (legacy API)."""
        self.supplemental_rules[tag_name] = rule_function
        self.rule_descriptions[tag_name] = description
    
    # ===== MAIN TAGGING API =====
    
    def tag_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Tag a conversation using exchange-based analysis."""
        if self.use_exchange_analysis:
            return self._tag_conversation_exchange_based(conversation)
        else:
            return self._tag_conversation_legacy(conversation)
    
    def _tag_conversation_exchange_based(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Tag conversation using exchange-based analysis."""
        # Step 1: Parse into exchanges
        exchanges = self.exchange_parser.parse_conversation(conversation)
        
        # Step 2: Tag each exchange
        tagged_exchanges = self.exchange_tagger.tag_exchanges(exchanges)
        
        # Step 3: Aggregate to conversation level
        conversation_result = self.conversation_aggregator.aggregate_to_conversation(
            tagged_exchanges, conversation
        )
        
        # Step 4: Apply conversation-level supplemental rules
        conversation_tags = set(conversation_result['tags'])
        debug_info = defaultdict(list)
        
        for tag_name, rule_func in self.supplemental_rules.items():
            if any(tag.name == tag_name for tag in conversation_tags):
                continue
                
            try:
                result = rule_func(conversation, conversation_tags)
                if result:
                    if isinstance(result, bool):
                        tag = Tag(tag_name)
                    else:
                        tag = self._normalize_tag(result)
                    conversation_tags.add(tag)
                    debug_info['applied_rules'].append(f"CONV_SUPP: {tag}")
            except Exception as e:
                debug_info['errors'].append(f"CONV_SUPP: {tag_name} - {str(e)}")
        
        # Update result
        conversation_result['tags'] = list(conversation_tags)
        if 'debug_info' not in conversation_result:
            conversation_result['debug_info'] = {}
        conversation_result['debug_info'].update(debug_info)
        
        return conversation_result
    
    def _tag_conversation_legacy(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Tag conversation using legacy conversation-level analysis."""
        tags = set()
        debug_info = defaultdict(list)
        
        # Apply base rules
        for tag_name, rule_func in self.base_rules.items():
            try:
                result = rule_func(conversation)
                if result:
                    if isinstance(result, bool):
                        tag = Tag(tag_name)
                    else:
                        tag = self._normalize_tag(result)
                    tags.add(tag)
                    debug_info['applied_rules'].append(f"BASE: {tag}")
            except Exception as e:
                debug_info['errors'].append(f"BASE: {tag_name} - {str(e)}")
        
        # Apply multi-tag rules
        for rule_name, rule_func in self.multi_tag_rules.items():
            try:
                new_tags = rule_func(conversation)
                if new_tags:
                    normalized_tags = [self._normalize_tag(tag) for tag in new_tags]
                    tags.update(normalized_tags)
                    debug_info['applied_rules'].append(f"MULTI: {rule_name} -> {[str(t) for t in normalized_tags]}")
            except Exception as e:
                debug_info['errors'].append(f"MULTI: {rule_name} - {str(e)}")
        
        # Apply supplemental rules
        for tag_name, rule_func in self.supplemental_rules.items():
            if any(tag.name == tag_name for tag in tags):
                continue
                
            try:
                result = rule_func(conversation, tags)
                if result:
                    if isinstance(result, bool):
                        tag = Tag(tag_name)
                    else:
                        tag = self._normalize_tag(result)
                    tags.add(tag)
                    debug_info['applied_rules'].append(f"SUPP: {tag}")
            except Exception as e:
                debug_info['errors'].append(f"SUPP: {tag_name} - {str(e)}")
        
        return {
            'conversation_id': conversation.get('conversation_id', conversation.get('id', 'unknown')),
            'title': conversation.get('title', 'Untitled'),
            'tags': list(tags),
            'debug_info': dict(debug_info),
            'conversation': conversation
        }
    
    def tag_conversations(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Tag multiple conversations."""
        return [self.tag_conversation(conv) for conv in conversations]
    
    def get_exchange_analysis(self, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get detailed exchange-level analysis for a conversation."""
        if not self.use_exchange_analysis:
            raise ValueError("Exchange analysis not enabled. Set use_exchange_analysis=True")
        
        exchanges = self.exchange_parser.parse_conversation(conversation)
        return self.exchange_tagger.tag_exchanges(exchanges)
    
    def filter_by_tags(self, tagged_conversations: List[Dict[str, Any]], 
                      include_tags: List[Union[str, Dict]] = None,
                      exclude_tags: List[Union[str, Dict]] = None) -> List[Dict[str, Any]]:
        """Filter conversations by tags with attribute support."""
        filtered = []
        
        for tagged_conv in tagged_conversations:
            tags = tagged_conv['tags']
            
            # Check exclusions first
            if exclude_tags:
                should_exclude = False
                for exclude_criterion in exclude_tags:
                    if self._matches_criterion(tags, exclude_criterion):
                        should_exclude = True
                        break
                if should_exclude:
                    continue
            
            # Check inclusions
            if include_tags:
                should_include = True
                for include_criterion in include_tags:
                    if not self._matches_criterion(tags, include_criterion):
                        should_include = False
                        break
                if not should_include:
                    continue
            
            filtered.append(tagged_conv)
        
        return filtered
    
    def _matches_criterion(self, tags: List[Tag], criterion: Union[str, Dict]) -> bool:
        """Check if any tag matches the given criterion."""
        if isinstance(criterion, str):
            return any(tag.name == criterion for tag in tags)
        
        elif isinstance(criterion, dict):
            name = criterion.get('name')
            if not name:
                return False
            
            criteria = {k: v for k, v in criterion.items() if k != 'name'}
            return any(tag.matches(name, **criteria) for tag in tags)
        
        return False
    
    def _normalize_tag(self, tag: Union[str, Tag]) -> Tag:
        """Convert string tags to Tag objects."""
        if isinstance(tag, str):
            return Tag(tag)
        return tag


# =============================================================================
# conversation_tagger/factory.py (UPDATED VERSION)
"""
Updated factory function that creates exchange-enabled tagger.
"""

from .core.tagger import ConversationTagger
from .detection.exchange_rules import *


def create_default_tagger(use_exchange_analysis: bool = True) -> ConversationTagger:
    """
    Create a conversation tagger with all default rules.
    
    Args:
        use_exchange_analysis: If True, uses exchange-based analysis (recommended).
                              If False, uses legacy conversation-level analysis only.
    """
    tagger = ConversationTagger(use_exchange_analysis=use_exchange_analysis)
    
    if use_exchange_analysis:
        _configure_exchange_based_tagger(tagger)
    else:
        _configure_legacy_tagger(tagger)
    
    return tagger


def _configure_exchange_based_tagger(tagger: ConversationTagger):
    """Configure tagger with exchange-based rules."""
    
    # ===== EXCHANGE-LEVEL RULES =====
    
    # User message rules
    tagger.add_user_rule('user_has_code_blocks', user_has_code_blocks, 'User messages contain code blocks')
    tagger.add_user_rule('user_has_attachments', user_has_attachments, 'User messages have attachments')
    tagger.add_user_rule('user_has_error_messages', user_has_error_messages, 'User messages contain error patterns')
    tagger.add_user_rule('user_prompt_length', user_prompt_length_category, 'User prompt length statistics')
    tagger.add_user_rule('user_is_continuation', user_is_continuation, 'Exchange started with continuation prompt')
    tagger.add_user_rule('user_has_quote_elaborate', user_has_quote_elaborate, 'User messages contain quote+elaborate pattern')
    
    # Assistant message rules
    tagger.add_assistant_rule('assistant_has_code_blocks', assistant_has_code_blocks, 'Assistant messages contain code blocks')
    tagger.add_assistant_rule('assistant_has_wiki_links', assistant_has_wiki_links, 'Assistant messages contain wiki-style links')
    tagger.add_assistant_rule('assistant_has_latex_math', assistant_has_latex_math, 'Assistant messages contain mathematical formulas')
    tagger.add_assistant_rule('assistant_response_length', assistant_response_length_category, 'Assistant response length statistics')
    tagger.add_assistant_rule('assistant_has_reasoning', assistant_has_reasoning, 'Assistant messages contain reasoning/thinking')
    
    # Exchange-level rules
    tagger.add_exchange_rule('exchange_is_coding_focused', exchange_is_coding_focused, 'Exchange focuses on coding topics')
    tagger.add_exchange_rule('exchange_is_wiki_article_focused', exchange_is_wiki_article_focused, 'Exchange focuses on wiki/documentation content')
    tagger.add_exchange_rule('exchange_has_error_resolution', exchange_has_error_resolution, 'Exchange involves error troubleshooting')
    tagger.add_exchange_rule('interaction_pattern', exchange_interaction_pattern, 'Pattern of interaction in this exchange')
    tagger.add_exchange_rule('exchange_timing', exchange_timing_stats, 'Timing statistics for the exchange')
    
    # Exchange supplemental rules
    tagger.add_exchange_supplemental_rule('coding_exchange', 
                                         lambda exch, tags: any(tag.name in ['user_has_code_blocks', 'assistant_has_code_blocks', 'exchange_is_coding_focused'] for tag in tags),
                                         'Exchange involves coding activity')
    
    tagger.add_exchange_supplemental_rule('wiki_exchange',
                                         lambda exch, tags: any(tag.name in ['assistant_has_wiki_links', 'exchange_is_wiki_article_focused'] for tag in tags),
                                         'Exchange involves wiki/documentation content')
    
    tagger.add_exchange_supplemental_rule('elaboration_exchange',
                                         lambda exch, tags: any(tag.name == 'user_has_quote_elaborate' for tag in tags),
                                         'Exchange contains quote+elaborate continuation pattern')
    
    # ===== CONVERSATION-LEVEL SUPPLEMENTAL RULES =====
    
    # High-level conversation classifications based on aggregated exchange data
    tagger.add_supplemental_rule('primarily_coding_conversation',
                                lambda conv, tags: any(tag.name.startswith('has_exchange_is_coding_focused') and 
                                                     hasattr(tag, 'attributes') and tag.attributes.get('level') in ['often', 'always'] for tag in tags),
                                'Conversation is primarily about coding (based on exchange frequency)')
    
    tagger.add_supplemental_rule('primarily_wiki_conversation',
                                lambda conv, tags: any(tag.name.startswith('has_exchange_is_wiki_article_focused') and 
                                                     hasattr(tag, 'attributes') and tag.attributes.get('level') in ['often', 'always'] for tag in tags),
                                'Conversation is primarily about wiki/documentation content')
    
    tagger.add_supplemental_rule('elaboration_heavy_conversation',
                                lambda conv, tags: any(tag.name == 'uses_continuations' and 
                                                     hasattr(tag, 'attributes') and tag.attributes.get('continuation_frequency', 0) > 0.3 for tag in tags),
                                'Conversation makes heavy use of elaboration/continuation patterns')


def _configure_legacy_tagger(tagger: ConversationTagger):
    """Configure tagger with legacy conversation-level rules for backwards compatibility."""
    from .detection.content import has_large_content
    from .detection.code_indicators import has_code_patterns
    from .detection.structured_tags import create_conversation_length_tag, create_prompt_stats_tag, create_gizmo_plugin_tags
    
    tagger.add_base_rule('large_content', lambda conv: has_large_content(conv, 2000), 'Content longer than 2000 characters')
    tagger.add_base_rule('code_patterns', has_code_patterns, 'Contains code patterns')
    tagger.add_base_rule('conversation_length', create_conversation_length_tag, 'Conversation length with count and category')
    tagger.add_base_rule('prompt_stats', create_prompt_stats_tag, 'User message statistics')
    tagger.add_multi_tag_rule('gizmo_plugin_usage', create_gizmo_plugin_tags, 'Specific gizmos and plugins used')


# =============================================================================
# SUMMARY OF WHAT NEEDS TO BE DONE:

print("""
ACTIONS NEEDED TO COMPLETE PROJECT STATE:

🔧 CREATE MISSING FILES:
1. conversation_tagger/core/__init__.py
2. conversation_tagger/detection/__init__.py  
3. conversation_tagger/analysis/__init__.py

🔄 UPDATE EXISTING FILES:
1. conversation_tagger/core/tagger.py - Replace with exchange-based version
2. conversation_tagger/factory.py - Replace with integrated version

✅ EXISTING FILES (NO CHANGES NEEDED):
- All other core/, detection/, analysis/ files are up to date
- All test files are current
- Documentation is current
- Exchange functionality is fully implemented

📋 VERIFICATION STEPS:
1. Run: pytest tests/ -v
2. Test: from conversation_tagger import create_default_tagger
3. Verify: tagger = create_default_tagger(); result = tagger.tag_conversation(sample_conv)
4. Check: result should include 'exchanges' key with detailed exchange analysis

🎯 RESULT:
After these updates, you'll have a fully integrated exchange-based conversation tagger 
that maintains API compatibility while providing rich granular analysis.
""")