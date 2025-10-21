# conversation_tagger/data/config.py
"""
Configuration management for data sources and processing parameters.
"""

import os
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class DataSourceConfig:
    """Configuration for a conversation data source."""
    
    name: str
    root_path: str
    conversations_file: str = "conversations.json"
    parser_type: str = "oai"  # "oai" or "claude"
    
    @property
    def conversations_path(self) -> Path:
        """Get the full path to the conversations file."""
        return Path(self.root_path) / self.conversations_file
    
    def exists(self) -> bool:
        """Check if the conversations file exists."""
        return self.conversations_path.exists()


def get_default_config() -> Dict[str, DataSourceConfig]:
    """Get default configuration for known data sources."""
    
    # These paths can be overridden by environment variables
    chatgpt_root = os.getenv(
        'CHAT2OBS_CHATGPT_ROOT',
        "../data/ingestion/chatgpt/a40ff5f79c1b3edd3c366f0f628fb79170bae83ecf3a1758b5b258c71f843f53-2025-06-05-03-28-15-df2ed357a4e64443bf464446686c9692/"
    )
    
    claude_root = os.getenv(
        'CHAT2OBS_CLAUDE_ROOT', 
        "/Users/dmarx/Downloads/data-2025-07-06-16-51-06"
    )
    
    return {
        'oai': DataSourceConfig(
            name='oai',
            root_path=chatgpt_root,
            parser_type='oai'
        ),
        'claude': DataSourceConfig(
            name='claude', 
            root_path=claude_root,
            parser_type='claude'
        ),
        'chatgpt': DataSourceConfig(  # Alias for oai
            name='chatgpt',
            root_path=chatgpt_root,
            parser_type='oai'
        )
    }


def get_config_for_source(source: str) -> DataSourceConfig:
    """Get configuration for a specific source."""
    configs = get_default_config()
    
    if source not in configs:
        raise ValueError(f"Unknown source: {source}. Available: {list(configs.keys())}")
    
    config = configs[source]
    
    if not config.exists():
        raise FileNotFoundError(
            f"Conversations file not found: {config.conversations_path}"
        )
    
    return config
