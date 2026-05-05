# conversation_tagger/core/tag.py
"""
Core Tag class representing a tag with optional attributes.
"""

from typing import Dict, Any, Union


class Tag:
    """Represents a tag with optional key-value attributes."""
    
    def __init__(self, name: str, **attributes):
        self.name = name
        self.attributes = attributes
    
    def __str__(self):
        if self.attributes:
            attrs_str = ", ".join(f"{k}={v}" for k, v in self.attributes.items())
            return f"{self.name}({attrs_str})"
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
    
    def matches(self, name: str, **criteria) -> bool:
        """Check if tag matches name and optional attribute criteria."""
        if self.name != name:
            return False
        
        for key, value in criteria.items():
            if key not in self.attributes:
                return False
            
            attr_value = self.attributes[key]
            
            # Support comparison operators
            if isinstance(value, dict):
                for op, target in value.items():
                    if op == 'gt' and not (attr_value > target):
                        return False
                    elif op == 'gte' and not (attr_value >= target):
                        return False
                    elif op == 'lt' and not (attr_value < target):
                        return False
                    elif op == 'lte' and not (attr_value <= target):
                        return False
                    elif op == 'eq' and not (attr_value == target):
                        return False
                    elif op == 'ne' and not (attr_value != target):
                        return False
                    elif op == 'in' and not (attr_value in target):
                        return False
            else:
                # Direct equality
                if attr_value != value:
                    return False
        
        return True
