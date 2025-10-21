# conversation_tagger/analysis/faceting.py
"""
Faceting functionality for analyzing conversations by different dimensions.
Updated to use dictionary-based annotations.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict

# Tag import removed - using dictionary-based annotations


def get_facet_value(annotations: Dict[str, Any], facet_annotation_name: str, 
                   facet_attribute: Optional[str] = None) -> str:
    """Extract facet value from a conversation's annotations."""
    if facet_annotation_name not in annotations:
        return "<none>"
    
    annotation_value = annotations[facet_annotation_name]
    
    if facet_attribute is None:
        # Just check for presence of the annotation
        if annotation_value is True:
            return f"has_{facet_annotation_name}"
        else:
            return str(annotation_value)
    
    # Extract specific attribute values from structured annotation
    if isinstance(annotation_value, dict) and facet_attribute in annotation_value:
        return str(annotation_value[facet_attribute])
    
    return f"<{facet_annotation_name}_no_{facet_attribute}>"


def do_facet_conversations(tagged_conversations: List[Dict[str, Any]], 
                       facet_annotation_name: str, 
                       facet_attribute: Optional[str] = None,
                       max_facets: int = 50) -> Dict[str, List[Dict[str, Any]]]:
    """Group conversations by facet values."""
    facets = defaultdict(list)
    
    for tagged_conv in tagged_conversations:
        # Use annotations directly (legacy Tag format support removed)
        annotations = tagged_conv.get('annotations', {})
        
        facet_value = get_facet_value(annotations, facet_annotation_name, facet_attribute)
        facets[facet_value].append(tagged_conv)
    
    # Sort by facet size (largest first) and limit
    sorted_facets = dict(sorted(facets.items(), key=lambda x: len(x[1]), reverse=True))
    
    if len(sorted_facets) > max_facets:
        # Keep top facets and group rest into "others"
        items = list(sorted_facets.items())
        top_facets = dict(items[:max_facets-1])
        
        other_conversations = []
        for _, conversations in items[max_facets-1:]:
            other_conversations.extend(conversations)
        
        if other_conversations:
            top_facets["<other>"] = other_conversations
        
        return top_facets
    
    return sorted_facets


def print_faceted_summary(tagged_conversations: List[Dict[str, Any]], 
                         facet_annotation_name: str, 
                         facet_attribute: Optional[str] = None,
                         show_details: bool = False,
                         max_facets: int = 20):
    """Print annotation summary broken down by facets."""
    total = len(tagged_conversations)
    facets = do_facet_conversations(tagged_conversations, facet_annotation_name, facet_attribute, max_facets)
    
    print(f"Tagged {total} conversations")
    print(f"Faceted by: {facet_annotation_name}" + 
          (f".{facet_attribute}" if facet_attribute else ""))
    print(f"Found {len(facets)} facet values")
    
    print(f"\n{'='*80}")
    print(f"FACETED ANNOTATION SUMMARY")
    print(f"{'='*80}")
    
    for facet_value, facet_conversations in facets.items():
        facet_size = len(facet_conversations)
        facet_percentage = (facet_size / total) * 100
        
        print(f"\n📊 FACET: {facet_value}")
        print(f"    Conversations: {facet_size} ({facet_percentage:.1f}% of total)")
        print(f"    {'-' * 60}")
        
        # Calculate annotation statistics for this facet
        annotation_counts = defaultdict(int)
        annotation_attributes = defaultdict(lambda: defaultdict(list))
        unique_structured_annotations = defaultdict(set)
        
        for tagged_conv in facet_conversations:
            # Use annotations directly (legacy Tag format support removed) 
            annotations = tagged_conv.get('annotations', {})
            
            for annotation_name, annotation_value in annotations.items():
                annotation_counts[annotation_name] += 1
                
                # Collect attribute information
                if isinstance(annotation_value, dict):
                    for attr_name, attr_value in annotation_value.items():
                        if isinstance(attr_value, (int, float)):
                            annotation_attributes[annotation_name][attr_name].append(attr_value)
                        else:
                            unique_structured_annotations[annotation_name].add(f"{attr_name}={attr_value}")
                elif isinstance(annotation_value, (int, float)):
                    annotation_attributes[annotation_name]['value'].append(annotation_value)
        
        # Sort annotations for this facet (show all annotations)
        sorted_annotations = sorted(annotation_counts.items(), key=lambda x: x[1], reverse=True)
        
        for annotation_name, count in sorted_annotations:
            percentage = (count / facet_size) * 100
            print(f"    {annotation_name}: {count} ({percentage:.1f}%)")
            
            if show_details:
                # Show numeric attribute statistics
                if annotation_name in annotation_attributes:
                    for attr_name, values in annotation_attributes[annotation_name].items():
                        if values:
                            avg_val = sum(values) / len(values)
                            min_val = min(values)
                            max_val = max(values)
                            print(f"        {attr_name}: avg={avg_val:.1f}, range=[{min_val}, {max_val}]")
                
                # Show unique structured values
                if annotation_name in unique_structured_annotations:
                    unique_vals = sorted(unique_structured_annotations[annotation_name])
                    if len(unique_vals) <= 5:
                        print(f"        values: {', '.join(unique_vals)}")
                    else:
                        print(f"        values: {', '.join(unique_vals[:5])} ... (+{len(unique_vals)-5} more)")
