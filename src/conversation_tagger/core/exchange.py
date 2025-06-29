# conversation_tagger/core/exchange.py
"""
Exchange abstraction linking user prompts to assistant responses.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class Exchange:
    """User prompt + assistant response(s) + any continuations."""
    
    exchange_id: str
    conversation_id: str
    user_messages: List[Dict[str, Any]]
    assistant_messages: List[Dict[str, Any]]
    exchange_index: int = 0
    
    def get_user_text(self) -> str:
        """Get combined text from all user messages."""
        texts = []
        for msg in self.user_messages:
            content = msg.get('content', {})
            text = content.get('text', '')
            parts = content.get('parts', [])
            all_text = text + ' ' + ' '.join(str(p) for p in parts if isinstance(p, str))
            texts.append(all_text)
        return ' '.join(texts).strip()
    
    def get_assistant_text(self) -> str:
        """Get combined text from all assistant messages."""
        texts = []
        for msg in self.assistant_messages:
            content = msg.get('content', {})
            text = content.get('text', '')
            parts = content.get('parts', [])
            all_text = text + ' ' + ' '.join(str(p) for p in parts if isinstance(p, str))
            texts.append(all_text)
        return ' '.join(texts).strip()
    
    def has_continuations(self) -> bool:
        """Check if this exchange has continuation prompts."""
        return len(self.user_messages) > 1


