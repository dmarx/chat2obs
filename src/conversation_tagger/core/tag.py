
# =============================================================================
# conversation_tagger/core/tag.py
"""
Basic Tag class with optional attributes.
"""

from typing import Any


class Tag:
    """A tag with optional key-value attributes."""
    
    def __init__(self, name: str, **attributes):
        self.name = name
        self.attributes = attributes
    
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

