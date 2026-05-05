# conversation_tagger/core/exchange.py
"""
Core Exchange class representing a user prompt + assistant response(s) with continuations.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class Exchange:
    """
    Represents a complete user-assistant exchange, including continuations.
    
    An exchange consists of:
    - Initial user prompt
    - Assistant response(s) 
    - Any continuation prompts ("more", "continue") and their responses
    """
    
    exchange_id: str
    conversation_id: str
    
    # Core exchange components
    user_messages: List[Dict[str, Any]]      # Prompt + any continuations
    assistant_messages: List[Dict[str, Any]]  # All assistant responses
    
    # Metadata
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    exchange_index: int = 0  # Position in conversation (0-based)
    
    def get_user_text(self) -> str:
        """Get combined text from all user messages in this exchange."""
        texts = []
        for msg in self.user_messages:
            content = msg.get('content', {})
            text = content.get('text', '')
            parts = content.get('parts', [])
            all_text = text + ' ' + ' '.join(str(p) for p in parts if isinstance(p, str))
            texts.append(all_text)
        return ' '.join(texts).strip()
    
    def get_assistant_text(self) -> str:
        """Get combined text from all assistant messages in this exchange."""
        texts = []
        for msg in self.assistant_messages:
            content = msg.get('content', {})
            text = content.get('text', '')
            parts = content.get('parts', [])
            all_text = text + ' ' + ' '.join(str(p) for p in parts if isinstance(p, str))
            texts.append(all_text)
        return ' '.join(texts).strip()
    
    def get_total_text(self) -> str:
        """Get all text from this exchange."""
        return (self.get_user_text() + ' ' + self.get_assistant_text()).strip()
    
    def has_continuations(self) -> bool:
        """Check if this exchange has continuation prompts."""
        return len(self.user_messages) > 1
    
    def is_code_focused(self) -> bool:
        """Quick check if this exchange seems code-focused (for optimization)."""
        total_text = self.get_total_text().lower()
        return any(indicator in total_text for indicator in ['```', 'def ', 'function ', 'import '])
    
    def get_user_prompt_stats(self) -> Dict[str, Any]:
        """Get statistics about user prompts in this exchange."""
        user_text = self.get_user_text()
        return {
            'length': len(user_text),
            'message_count': len(self.user_messages),
            'has_continuations': self.has_continuations(),
            'word_count': len(user_text.split()) if user_text else 0
        }
    
    def get_assistant_response_stats(self) -> Dict[str, Any]:
        """Get statistics about assistant responses in this exchange."""
        assistant_text = self.get_assistant_text()
        return {
            'length': len(assistant_text),
            'message_count': len(self.assistant_messages),
            'word_count': len(assistant_text.split()) if assistant_text else 0
        }