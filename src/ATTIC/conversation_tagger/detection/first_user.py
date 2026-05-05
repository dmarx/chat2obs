# conversation_tagger/detection/first_user.py
"""
Detection functions specific to the first user message.
"""

from typing import Dict, Any

from .helpers import get_first_user_message, get_all_text_from_message


def first_user_has_large_content(conversation: Dict[str, Any], min_length: int = 2000) -> bool:
    """Check if the first user message has large content."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    
    all_text = get_all_text_from_message(first_message)
    return len(all_text) > min_length


def first_user_has_code_patterns(conversation: Dict[str, Any]) -> bool:
    """Check if the first user message contains code patterns."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    
    all_text = get_all_text_from_message(first_message)
    
    # Strong code indicators
    code_indicators = [
        '```',  # Code blocks
        'def ', 'function ', 'class ',  # Definitions
        'import ', 'from ', 'require(',  # Imports
        '#!/bin/', '#include',  # Script headers
    ]
    
    return any(indicator in all_text for indicator in code_indicators)


def first_user_has_attachments(conversation: Dict[str, Any]) -> bool:
    """Check if the first user message has attachments."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    
    metadata = first_message.get('metadata', {})
    attachments = metadata.get('attachments', [])
    return len(attachments) > 0


def first_user_has_code_attachments(conversation: Dict[str, Any]) -> bool:
    """Check if the first user message has code-related attachments."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    
    metadata = first_message.get('metadata', {})
    attachments = metadata.get('attachments', [])
    
    for attachment in attachments:
        mime_type = attachment.get('mime_type', '').lower()
        name = attachment.get('name', '').lower()
        
        # Check for code file extensions
        code_extensions = ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs', '.ts', '.jsx', '.tsx', '.sql', '.sh', '.rb', '.php']
        if any(ext in name for ext in code_extensions):
            return True
            
        # Check for code-related MIME types
        code_mimes = ['text/x-python', 'text/x-java', 'application/javascript', 'text/x-script']
        if any(mime in mime_type for mime in code_mimes):
            return True
    
    return False