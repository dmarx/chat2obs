# conversation_tagger/detection/content.py
"""
Basic content detection functions.
"""

from typing import Dict, Any

from .helpers import get_all_conversation_text


def has_large_content(conversation: Dict[str, Any], min_length: int = 2000) -> bool:
    """Check if conversation has unusually large content anywhere."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        content = message.get('content', {})
        text = content.get('text', '')
        if len(text) > min_length:
            return True
            
        parts = content.get('parts', [])
        for part in parts:
            if isinstance(part, str) and len(part) > min_length:
                return True
    
    return False


def has_github_repos(conversation: Dict[str, Any]) -> bool:
    """Check if GitHub repositories were selected for context."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        metadata = message.get('metadata', {})
        repos = metadata.get('selected_github_repos', [])
        if repos:  # Non-empty list
            return True
    
    return False


def has_canvas_operations(conversation: Dict[str, Any]) -> bool:
    """Check for canvas/document operations."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        metadata = message.get('metadata', {})
        if metadata.get('canvas'):
            return True
    
    return False


def has_web_search(conversation: Dict[str, Any]) -> bool:
    """Check for web search operations."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        metadata = message.get('metadata', {})
        if (metadata.get('search_queries') or 
            metadata.get('search_result_groups') or
            metadata.get('content_references')):
            return True
    
    return False


def has_reasoning_thoughts(conversation: Dict[str, Any]) -> bool:
    """Check for reasoning/thinking patterns."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        content = message.get('content', {})
        if content.get('thoughts'):  # Reasoning thoughts
            return True
    
    return False


def has_code_execution(conversation: Dict[str, Any]) -> bool:
    """Check for code execution artifacts."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        metadata = message.get('metadata', {})
        if (metadata.get('aggregate_result') or 
            metadata.get('jupyter_messages')):
            return True
    
    return False