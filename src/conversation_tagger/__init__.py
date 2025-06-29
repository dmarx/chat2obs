# conversation_tagger/__init__.py
"""
Minimal conversation tagging system with exchange-based analysis.
"""

from .core.tag import Tag
from .core.tagger import ConversationTagger
from .factory import create_default_tagger

__all__ = ['Tag', 'ConversationTagger', 'create_default_tagger']