# conversation_tagger/core/tag.py
"""
Simplified annotation system using dictionaries instead of custom Tag objects.
"""

from typing import Any, Dict, Union


def create_annotation(name: str, value: Union[bool, int, float, str, Dict[str, Any]] = True) -> Dict[str, Any]:
    """Create a simple annotation as a dictionary entry."""
    return {name: value}


def merge_annotations(*annotation_dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple annotation dictionaries."""
    result = {}
    for annotations in annotation_dicts:
        result.update(annotations)
    return result


def has_annotation(annotations: Dict[str, Any], name: str) -> bool:
    """Check if an annotation exists."""
    return name in annotations


def get_annotation_value(annotations: Dict[str, Any], name: str, default: Any = None) -> Any:
    """Get the value of an annotation."""
    return annotations.get(name, default)


# Tag class removed - now using dictionary-based annotations directly
