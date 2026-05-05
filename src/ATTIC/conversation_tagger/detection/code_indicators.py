# conversation_tagger/detection/code_indicators.py
"""
Individual code detection functions - each detects a specific type of code evidence.
"""

from typing import Dict, Any

from .helpers import get_all_text_from_message


def has_code_blocks(conversation: Dict[str, Any]) -> bool:
    """Check for explicit code blocks (``` markdown syntax)."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        if '```' in all_text:
            return True
    
    return False


def has_function_definitions(conversation: Dict[str, Any]) -> bool:
    """Check for function/class definition keywords."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        definition_keywords = ['def ', 'function ', 'class ']
        if any(keyword in all_text for keyword in definition_keywords):
            return True
    
    return False


def has_import_statements(conversation: Dict[str, Any]) -> bool:
    """Check for import/require statements."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        import_keywords = ['import ', 'from ', 'require(']
        if any(keyword in all_text for keyword in import_keywords):
            return True
    
    return False


def has_script_headers(conversation: Dict[str, Any]) -> bool:
    """Check for script headers and system includes."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        script_indicators = ['#!/bin/', '#include', 'using namespace']
        if any(indicator in all_text for indicator in script_indicators):
            return True
    
    return False


def has_high_keyword_density(conversation: Dict[str, Any]) -> bool:
    """Check for high density of programming keywords in large text."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        
        # Only check substantial text
        if len(all_text) <= 1000:
            continue
        
        coding_keywords = ['function', 'class', 'import', 'def ', 'const ', 'let ', 'var ', 'return', 'if ', 'for ', 'while ']
        keyword_count = sum(1 for keyword in coding_keywords if keyword in all_text.lower())
        
        # High threshold to avoid false positives in articles
        if keyword_count >= 5:
            return True
    
    return False


def has_code_structure_patterns(conversation: Dict[str, Any]) -> bool:
    """Check for actual code structure patterns (syntax combinations that suggest real code)."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        
        # Look for combinations that strongly suggest actual code
        patterns = [
            # Function definition pattern
            ('def ' in all_text and '(' in all_text and ':' in all_text and 'return' in all_text),
            # Class definition pattern  
            ('class ' in all_text and '(' in all_text and ':' in all_text and 'def ' in all_text),
            # JavaScript function pattern
            ('function(' in all_text or 'function ' in all_text) and '{' in all_text and '}' in all_text,
            # Multiple assignment pattern
            all_text.count('=') >= 3 and ('let ' in all_text or 'const ' in all_text or 'var ' in all_text),
        ]
        
        if any(pattern for pattern in patterns):
            return True
    
    return False


def has_code_patterns(conversation: Dict[str, Any]) -> bool:
    """Check for any code patterns (combines individual indicators)."""
    return (has_code_blocks(conversation) or 
            has_function_definitions(conversation) or 
            has_import_statements(conversation) or 
            has_script_headers(conversation) or
            has_code_structure_patterns(conversation) or
            has_high_keyword_density(conversation))