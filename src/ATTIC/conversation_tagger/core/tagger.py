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