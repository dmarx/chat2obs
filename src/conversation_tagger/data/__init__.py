# conversation_tagger/data/__init__.py
"""
Data loading and processing machinery.
"""

from .loaders import ConversationLoader, load_conversations
from .config import DataSourceConfig, get_default_config

__all__ = [
    'ConversationLoader', 
    'load_conversations',
    'DataSourceConfig',
    'get_default_config'
]
