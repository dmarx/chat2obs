# low-key suspect we can get rid of this whole file
# conversation_tagger/analysis/debugging.py
"""
Debugging functions for understanding tag application.
"""

from typing import Dict, Any, List
from collections import defaultdict

from .faceting import get_facet_value
from ..detection.helpers import get_all_text_from_message


def debug_code_detection(tagged_conversations: List[Dict[str, Any]], 
                        facet_tag_name: str = None, 
                        facet_value: str = None,
                        max_examples: int = 5):
    """Debug why conversations are being tagged as having code patterns."""
    # Filter conversations if faceting specified
    conversations_to_analyze = tagged_conversations
    if facet_tag_name and facet_value:
        conversations_to_analyze = []
        for tagged_conv in tagged_conversations:
            facet_val = get_facet_value(tagged_conv['tags'], facet_tag_name, 
                                       'gizmo_id' if facet_tag_name == 'gizmo' else None)
            if facet_val == facet_value:
                conversations_to_analyze.append(tagged_conv)
    
    # Show breakdown of different indicators
    indicator_counts = {
        'code_blocks': 0, 'function_definitions': 0, 'import_statements': 0,
        'script_headers': 0, 'high_keyword_density': 0, 'code_structure_patterns': 0,
        'code_patterns': 0, 'wiki_links': 0, 'latex_math': 0,
        'markdown_features': 0, 'documentation_patterns': 0,
    }
    
    evidence_counts = {
        'strong_code_evidence': 0, 'moderate_code_evidence': 0, 'weak_code_evidence': 0,
        'likely_coding_assistance': 0, 'conservative_coding_assistance': 0,
        'obsidian_content': 0, 'mathematical_content': 0, 'structured_documentation': 0,
        'likely_wiki_article': 0, 'programming_article': 0,
    }
    
    for tagged_conv in conversations_to_analyze:
        for tag in tagged_conv['tags']:
            if tag.name in indicator_counts:
                indicator_counts[tag.name] += 1
            if tag.name in evidence_counts:
                evidence_counts[tag.name] += 1
    
    total = len(conversations_to_analyze)
    
    print(f"\n{'='*80}")
    print(f"CODE DETECTION DEBUG")
    if facet_tag_name and facet_value:
        print(f"Filtering by: {facet_tag_name} = {facet_value}")
    print(f"Analyzing {total} conversations")
    print(f"{'='*80}")
    
    print(f"\n📊 INDIVIDUAL INDICATOR BREAKDOWN:")
    for indicator, count in indicator_counts.items():
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"    {indicator}: {count} ({percentage:.1f}%)")
    
    print(f"\n🎯 EVIDENCE LEVEL BREAKDOWN:")
    for evidence, count in evidence_counts.items():
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"    {evidence}: {count} ({percentage:.1f}%)")
    
    # Show detailed examples
    code_indicator_conversations = []
    for tagged_conv in conversations_to_analyze:
        has_any_indicator = any(tag.name in indicator_counts for tag in tagged_conv['tags'])
        if has_any_indicator:
            code_indicator_conversations.append(tagged_conv)
    
    print(f"\n🔍 DETAILED EXAMPLES:")
    print(f"Found {len(code_indicator_conversations)} conversations with indicators")
    
    for i, tagged_conv in enumerate(code_indicator_conversations[:max_examples]):
        print(f"\n--- Example {i+1}: {tagged_conv['title'][:60]}... ---")
        
        triggered_indicators = [tag.name for tag in tagged_conv['tags'] if tag.name in indicator_counts]
        triggered_evidence = [tag.name for tag in tagged_conv['tags'] if tag.name in evidence_counts]
        
        print(f"    Triggered indicators: {', '.join(triggered_indicators) if triggered_indicators else 'None'}")
        print(f"    Evidence levels: {', '.join(triggered_evidence) if triggered_evidence else 'None'}")
        
        # Show sample content
        conversation = tagged_conv['conversation']
        mapping = conversation.get('mapping', {})
        
        for node_id, node in mapping.items():
            message = node.get('message')
            if message:
                text = get_all_text_from_message(message)
                if text and len(text) > 50:
                    sample = text[:200] + "..." if len(text) > 200 else text
                    print(f"    Content sample: \"{sample}\"")
                    break


def print_summary(tagged_conversations: List[Dict[str, Any]], show_details: bool = True):
    """Print comprehensive summary with all tag types and optional details."""
    total = len(tagged_conversations)
    tag_counts = defaultdict(int)
    tag_attributes = defaultdict(lambda: defaultdict(list))
    unique_structured_tags = defaultdict(set)
    
    # Collect all tag information
    for tagged_conv in tagged_conversations:
        for tag in tagged_conv['tags']:
            tag_counts[tag.name] += 1
            
            # Collect attribute information
            for attr_name, attr_value in tag.attributes.items():
                if isinstance(attr_value, (int, float)):
                    tag_attributes[tag.name][attr_name].append(attr_value)
                else:
                    # For non-numeric attributes, track unique values
                    unique_structured_tags[tag.name].add(f"{attr_name}={attr_value}")
    
    print(f"Tagged {total} conversations")
    print(f"\n=== TAG SUMMARY ===")
    
    # Sort tags by frequency for better readability
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    for tag_name, count in sorted_tags:
        percentage = (count / total) * 100
        print(f"{tag_name}: {count} ({percentage:.1f}%)")
        
        if show_details:
            # Show numeric attribute statistics
            if tag_name in tag_attributes:
                for attr_name, values in tag_attributes[tag_name].items():
                    if values:
                        avg_val = sum(values) / len(values)
                        min_val = min(values)
                        max_val = max(values)
                        print(f"    {attr_name}: avg={avg_val:.1f}, range=[{min_val}, {max_val}]")
            
            # Show unique structured values for non-numeric attributes
            if tag_name in unique_structured_tags:
                unique_vals = sorted(unique_structured_tags[tag_name])
                if len(unique_vals) <= 10:  # Show all if not too many
                    print(f"    values: {', '.join(unique_vals)}")
                else:  # Show top 10 most common
                    print(f"    values: {', '.join(unique_vals[:10])} ... (+{len(unique_vals)-10} more)")
