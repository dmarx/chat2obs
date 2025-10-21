# conversation_tagger/data/loaders.py
"""
Data loading machinery for conversation files.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

from .config import DataSourceConfig, get_config_for_source


class ConversationLoader:
    """Handles loading conversation data from different sources."""
    
    def __init__(self, config: Optional[DataSourceConfig] = None):
        self.config = config
    
    @classmethod
    def from_source(cls, source: str) -> 'ConversationLoader':
        """Create loader for a specific source (oai, claude, chatgpt)."""
        config = get_config_for_source(source)
        return cls(config)
    
    def load(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load conversations from the configured source.
        
        Args:
            source: Optional source override (oai, claude, chatgpt)
            
        Returns:
            List of conversation dictionaries
            
        Raises:
            FileNotFoundError: If conversations file doesn't exist
            ValueError: If source is unknown
        """
        if source:
            config = get_config_for_source(source)
        elif self.config:
            config = self.config
        else:
            raise ValueError("No source specified and no default config set")
        
        logger.info(f"Loading conversations from {config.conversations_path}")
        
        try:
            with open(config.conversations_path, 'r', encoding='utf-8') as f:
                conversations = json.load(f)
            
            logger.info(f"Loaded {len(conversations)} conversations from {config.name}")
            return conversations
            
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Conversations file not found: {config.conversations_path}"
            )
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in conversations file {config.conversations_path}: {e}"
            )
    
    def validate_structure(self, conversations: List[Dict[str, Any]]) -> bool:
        """
        Basic validation of conversation structure.
        
        Returns:
            True if structure appears valid
        """
        if not isinstance(conversations, list):
            logger.error("Conversations data is not a list")
            return False
        
        if len(conversations) == 0:
            logger.warning("No conversations found")
            return True
        
        # Check first conversation has expected structure
        sample = conversations[0]
        required_fields = ['conversation_id'] if self.config and self.config.parser_type == 'claude' else ['mapping']
        
        for field in required_fields:
            if field not in sample:
                logger.error(f"Sample conversation missing required field: {field}")
                return False
        
        logger.info(f"Conversation structure validation passed ({len(conversations)} conversations)")
        return True


def load_conversations(source: str) -> List[Dict[str, Any]]:
    """
    Convenience function to load conversations from a source.
    
    Args:
        source: Source name (oai, claude, chatgpt)
        
    Returns:
        List of conversation dictionaries
    """
    loader = ConversationLoader.from_source(source)
    conversations = loader.load()
    
    if not loader.validate_structure(conversations):
        logger.warning(f"Structure validation failed for {source}, proceeding anyway")
    
    return conversations
