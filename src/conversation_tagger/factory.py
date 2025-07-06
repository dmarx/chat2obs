# src/conversation_tagger/factory.py
"""
Factory functions to create configured annotators and processors.
"""

from .core.annotator import Annotator, AnnotationPipeline
from .core.parser import ExchangeParser, ConversationProcessor
from .core.rules import EXCHANGE_RULES, CONVERSATION_RULES


def create_default_annotator() -> Annotator:
    """Create annotator with all default rules."""
    annotator = Annotator()
    
    # Add all default exchange rules
    for name, rule_func in EXCHANGE_RULES.items():
        annotator.add_exchange_rule(name, rule_func)
    
    # Add all default conversation rules
    for name, rule_func in CONVERSATION_RULES.items():
        annotator.add_conversation_rule(name, rule_func)
    
    return annotator


def create_basic_annotator() -> Annotator:
    """Create annotator with only basic rules for faster processing."""
    annotator = Annotator()
    
    # Basic exchange rules
    basic_exchange_rules = [
        'has_code_blocks', 'has_wiki_links', 'has_latex_math',
        'user_has_attachments', 'user_is_continuation', 'message_counts'
    ]
    
    for rule_name in basic_exchange_rules:
        if rule_name in EXCHANGE_RULES:
            annotator.add_exchange_rule(rule_name, EXCHANGE_RULES[rule_name])
    
    # Basic conversation rules
    basic_conversation_rules = ['conversation_length_analysis']
    
    for rule_name in basic_conversation_rules:
        if rule_name in CONVERSATION_RULES:
            annotator.add_conversation_rule(rule_name, CONVERSATION_RULES[rule_name])
    
    return annotator


def create_code_focused_annotator() -> Annotator:
    """Create annotator focused on code-related annotations."""
    annotator = Annotator()
    
    # Code-focused exchange rules
    code_rules = [
        'has_code_blocks', 'has_code_structure_patterns', 'has_code_execution',
        'user_has_attachments', 'first_user_analysis'
    ]
    
    for rule_name in code_rules:
        if rule_name in EXCHANGE_RULES:
            annotator.add_exchange_rule(rule_name, EXCHANGE_RULES[rule_name])
    
    # Add conversation rules that aggregate code patterns
    annotator.add_conversation_rule('conversation_length_analysis', 
                                   CONVERSATION_RULES['conversation_length_analysis'])
    annotator.add_conversation_rule('feature_usage_summary', 
                                   CONVERSATION_RULES['feature_usage_summary'])
    
    return annotator


def create_default_parser() -> ExchangeParser:
    """Create parser with default annotator."""
    annotator = create_default_annotator()
    return ExchangeParser(annotator)


def create_basic_parser() -> ExchangeParser:
    """Create parser with basic annotator for faster processing."""
    annotator = create_basic_annotator()
    return ExchangeParser(annotator)


def create_default_processor() -> ConversationProcessor:
    """Create processor with default configuration."""
    parser = create_default_parser()
    return ConversationProcessor(parser)


def create_custom_processor(exchange_rules: dict | None = None, 
                          conversation_rules: dict | None = None) -> ConversationProcessor:
    """Create processor with custom rules.
    
    Args:
        exchange_rules: Dict of {rule_name: rule_function} for exchanges
        conversation_rules: Dict of {rule_name: rule_function} for conversations
    """
    annotator = Annotator()
    
    # Add custom exchange rules
    if exchange_rules:
        for name, rule_func in exchange_rules.items():
            annotator.add_exchange_rule(name, rule_func)
    
    # Add custom conversation rules
    if conversation_rules:
        for name, rule_func in conversation_rules.items():
            annotator.add_conversation_rule(name, rule_func)
    
    parser = ExchangeParser(annotator)
    return ConversationProcessor(parser)


def create_pipeline_processor(annotators: list[Annotator]) -> ConversationProcessor:
    """Create processor with multiple annotators in a pipeline."""
    pipeline = AnnotationPipeline(annotators)
    parser = ExchangeParser()
    processor = ConversationProcessor(parser)
    
    # Replace single annotator with pipeline
    parser.annotator = pipeline
    
    return processor


# Convenience functions for common use cases

def quick_annotate(conversation_data: dict) -> dict:
    """Quick annotation of a single conversation, returns simple dict.
    
    Args:
        conversation_data: Raw conversation data
        
    Returns:
        Dict with conversation info and all annotations
    """
    processor = create_basic_processor()
    conversation = processor.process_conversation(conversation_data)
    
    return {
        'conversation_id': conversation.conversation_id,
        'title': conversation.title,
        'exchange_count': conversation.exchange_count,
        'message_count': conversation.total_message_count,
        'annotations': conversation.get_all_annotations()
    }


def batch_annotate(conversations: list[dict], use_basic: bool = True) -> list[dict]:
    """Annotate multiple conversations quickly.
    
    Args:
        conversations: List of raw conversation data
        use_basic: If True, use basic annotator for speed
        
    Returns:
        List of annotation dicts
    """
    processor = create_basic_processor() if use_basic else create_default_processor()
    
    results = []
    for conv_data in conversations:
        try:
            conversation = processor.process_conversation(conv_data)
            results.append({
                'conversation_id': conversation.conversation_id,
                'title': conversation.title,
                'exchange_count': conversation.exchange_count,
                'message_count': conversation.total_message_count,
                'annotations': conversation.get_all_annotations()
            })
        except Exception as e:
            # Log error and continue with next conversation
            results.append({
                'conversation_id': conv_data.get('conversation_id', 'unknown'),
                'error': str(e),
                'annotations': {}
            })
    
    return results


# Legacy compatibility functions
def create_default_tagger():
    """Legacy function name - creates default processor."""
    return create_default_processor()
