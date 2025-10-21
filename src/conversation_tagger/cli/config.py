# conversation_tagger/cli/config.py
"""
Minimal configuration for CLI discovery functionality.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CLIConfig:
    """Simple configuration for discovered conversation exports."""
    
    name: str
    root_path: str  
    parser_type: str  # 'oai' or 'claude'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'root_path': self.root_path,
            'parser_type': self.parser_type
        }


def create_cli_config(name: str, root_path: str, parser_type: str) -> CLIConfig:
    """Create a CLI configuration object."""
    return CLIConfig(
        name=name,
        root_path=str(Path(root_path).absolute()),
        parser_type=parser_type
    )


def get_default_exports_dir() -> str:
    """Get the default exports directory, with environment override."""
    return os.environ.get('CHAT2OBS_EXPORTS_DIR', './data/exports')
