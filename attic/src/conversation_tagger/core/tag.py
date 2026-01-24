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


# Legacy Tag class for backward compatibility during transition
class Tag:
    """A tag with optional key-value attributes - DEPRECATED: Use dictionaries instead."""
    
    def __init__(self, name: str, **attributes):
        self.name = name
        self.attributes = attributes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        if not self.attributes:
            return {self.name: True}
        elif len(self.attributes) == 1 and 'value' in self.attributes:
            return {self.name: self.attributes['value']}
        else:
            return {self.name: self.attributes}
    
    def __str__(self):
        if self.attributes:
            attrs = ", ".join(f"{k}={v}" for k, v in self.attributes.items())
            return f"{self.name}({attrs})"
        return self.name
    
    def __repr__(self):
        return f"Tag('{self.name}', {self.attributes})"
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        elif isinstance(other, Tag):
            return self.name == other.name and self.attributes == other.attributes
        return False
    
    def __hash__(self):
        return hash((self.name, tuple(sorted(self.attributes.items()))))
