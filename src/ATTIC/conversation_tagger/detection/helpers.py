# conversation_tagger/detection/helpers.py
"""
Helper functions for extracting information from conversations.
"""

from typing import Dict, Any, List


def get_all_user_messages(conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get all user messages in chronological order."""
    mapping = conversation.get('mapping', {})
    user_messages = []
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
            
        author = message.get('author', {})
        if author.get('role') == 'user':
            create_time = message.get('create_time') or 0
            user_messages.append((create_time, message))
    
    user_messages.sort(key=lambda x: x[0])
    return [msg for _, msg in user_messages]


def get_first_user_message(conversation: Dict[str, Any]) -> Dict[str, Any]:
    """Find the first user message in the conversation."""
    user_messages = get_all_user_messages(conversation)
    return user_messages[0] if user_messages else None


def get_all_text_from_message(message: Dict[str, Any]) -> str:
    """Extract all text content from a message."""
    content = message.get('content', {})
    text = content.get('text', '')
    parts = content.get('parts', [])
    all_text = text + ' ' + ' '.join(str(p) for p in parts if isinstance(p, str))
    return all_text


def get_all_conversation_text(conversation: Dict[str, Any]) -> str:
    """Extract all text content from a conversation."""
    mapping = conversation.get('mapping', {})
    all_text = ""
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if message:
            all_text += " " + get_all_text_from_message(message)
    
    return all_text