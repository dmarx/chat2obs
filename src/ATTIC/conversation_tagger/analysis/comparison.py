# conversation_tagger/analysis/comparison.py
"""
Functions for comparing tag distributions across facets.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict

from .faceting import facet_conversations


def compare_facets(tagged_conversations: List[Dict[str, Any]], 
                  facet_tag_name: str, 
                  facet_attribute: Optional[str] = None,
                  comparison_tags: List[str] = None,
                  min_facet_size: int = 10) -> None:
    """Compare specific tags across facets."""
    facets = facet_conversations(tagged_conversations, facet_tag_name, facet_attribute)
    
    # Filter facets by minimum size
    large_facets = {k: v for k, v in facets.items() if len(v) >= min_facet_size}
    
    if not large_facets:
        print(f"No facets with at least {min_facet_size} conversations found")
        return
    
    # If no specific tags provided, use most common tags overall
    if comparison_tags is None:
        overall_tag_counts = defaultdict(int)
        for tagged_conv in tagged_conversations:
            for tag in tagged_conv['tags']:
                overall_tag_counts[tag.name] += 1
        
        # Get top 10 most common tags
        comparison_tags = [tag for tag, _ in 
                         sorted(overall_tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]]
    
    print(f"\n{'='*80}")
    print(f"FACET COMPARISON")
    print(f"Comparing tags: {', '.join(comparison_tags)}")
    print(f"Across facets: {facet_tag_name}" + 
          (f".{facet_attribute}" if facet_attribute else ""))
    print(f"{'='*80}")
    
    # Calculate percentages for each tag in each facet
    results = {}
    for facet_value, facet_conversations in large_facets.items():
        facet_size = len(facet_conversations)
        facet_tag_counts = defaultdict(int)
        
        for tagged_conv in facet_conversations:
            for tag in tagged_conv['tags']:
                facet_tag_counts[tag.name] += 1
        
        results[facet_value] = {
            'size': facet_size,
            'percentages': {tag: (facet_tag_counts[tag] / facet_size) * 100 
                           for tag in comparison_tags}
        }
    
    # Print comparison table
    print(f"\n{'Facet':<30} {'Size':<8} " + 
          "".join(f"{tag:<15}" for tag in comparison_tags))
    print("-" * (30 + 8 + 15 * len(comparison_tags)))
    
    for facet_value, data in results.items():
        facet_display = facet_value[:28] + ".." if len(facet_value) > 30 else facet_value
        row = f"{facet_display:<30} {data['size']:<8} "
        row += "".join(f"{data['percentages'][tag]:<15.1f}" for tag in comparison_tags)
        print(row)
    
    # Highlight interesting differences
    print(f"\n🔍 NOTABLE DIFFERENCES:")
    for tag in comparison_tags:
        percentages = [results[facet]['percentages'][tag] for facet in results.keys()]
        if max(percentages) - min(percentages) > 20:  # 20% difference threshold
            max_facet = max(results.keys(), key=lambda f: results[f]['percentages'][tag])
            min_facet = min(results.keys(), key=lambda f: results[f]['percentages'][tag])
            print(f"    {tag}: {max_facet} ({results[max_facet]['percentages'][tag]:.1f}%) vs " +
                  f"{min_facet} ({results[min_facet]['percentages'][tag]:.1f}%)")
