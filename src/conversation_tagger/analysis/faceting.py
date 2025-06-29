# conversation_tagger/analysis/faceting.py
"""
Faceting functionality for analyzing conversations by different dimensions.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict

from ..core.tag import Tag


def get_facet_value(tags: List[Tag], facet_tag_name: str, 
                   facet_attribute: Optional[str] = None) -> str:
    """Extract facet value from a conversation's tags."""
    matching_tags = [tag for tag in tags if tag.name == facet_tag_name]
    
    if not matching_tags:
        return "<none>"
    
    if facet_attribute is None:
        # Just check for presence of the tag
        return f"has_{facet_tag_name}"
    
    # Extract specific attribute values
    values = []
    for tag in matching_tags:
        if facet_attribute in tag.attributes:
            values.append(str(tag.attributes[facet_attribute]))
    
    if not values:
        return f"<{facet_tag_name}_no_{facet_attribute}>"
    
    # If multiple values, join them
    return "; ".join(sorted(set(values)))


def do_facet_conversations(tagged_conversations: List[Dict[str, Any]], 
                       facet_tag_name: str, 
                       facet_attribute: Optional[str] = None,
                       max_facets: int = 50) -> Dict[str, List[Dict[str, Any]]]:
    """Group conversations by facet values."""
    facets = defaultdict(list)
    
    for tagged_conv in tagged_conversations:
        facet_value = get_facet_value(tagged_conv['tags'], facet_tag_name, facet_attribute)
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
                         facet_tag_name: str, 
                         facet_attribute: Optional[str] = None,
                         show_details: bool = False,
                         max_facets: int = 20):
    """Print tag summary broken down by facets."""
    total = len(tagged_conversations)
    facets = do_facet_conversations(tagged_conversations, facet_tag_name, facet_attribute, max_facets)
    
    print(f"Tagged {total} conversations")
    print(f"Faceted by: {facet_tag_name}" + 
          (f".{facet_attribute}" if facet_attribute else ""))
    print(f"Found {len(facets)} facet values")
    
    print(f"\n{'='*80}")
    print(f"FACETED TAG SUMMARY")
    print(f"{'='*80}")
    
    for facet_value, facet_conversations in facets.items():
        facet_size = len(facet_conversations)
        facet_percentage = (facet_size / total) * 100
        
        print(f"\n📊 FACET: {facet_value}")
        print(f"    Conversations: {facet_size} ({facet_percentage:.1f}% of total)")
        print(f"    {'-' * 60}")
        
        # Calculate tag statistics for this facet
        tag_counts = defaultdict(int)
        tag_attributes = defaultdict(lambda: defaultdict(list))
        unique_structured_tags = defaultdict(set)
        
        for tagged_conv in facet_conversations:
            for tag in tagged_conv['tags']:
                tag_counts[tag.name] += 1
                
                # Collect attribute information
                for attr_name, attr_value in tag.attributes.items():
                    if isinstance(attr_value, (int, float)):
                        tag_attributes[tag.name][attr_name].append(attr_value)
                    else:
                        unique_structured_tags[tag.name].add(f"{attr_name}={attr_value}")
        
        # Sort tags for this facet (show all tags)
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        for tag_name, count in sorted_tags:
            percentage = (count / facet_size) * 100
            print(f"    {tag_name}: {count} ({percentage:.1f}%)")
            
            if show_details:
                # Show numeric attribute statistics
                if tag_name in tag_attributes:
                    for attr_name, values in tag_attributes[tag.name].items():
                        if values:
                            avg_val = sum(values) / len(values)
                            min_val = min(values)
                            max_val = max(values)
                            print(f"        {attr_name}: avg={avg_val:.1f}, range=[{min_val}, {max_val}]")
                
                # Show unique structured values
                if tag_name in unique_structured_tags:
                    unique_vals = sorted(unique_structured_tags[tag.name])
                    if len(unique_vals) <= 5:
                        print(f"        values: {', '.join(unique_vals)}")
                    else:
                        print(f"        values: {', '.join(unique_vals[:5])} ... (+{len(unique_vals)-5} more)")
