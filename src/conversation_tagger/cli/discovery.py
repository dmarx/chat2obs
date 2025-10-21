# conversation_tagger/cli/discovery.py
"""
Auto-discovery and extraction of conversation exports.
"""

import json
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

from .config import CLIConfig, create_cli_config


class ExportDiscovery:
    """Discovers and processes conversation exports in a directory."""
    
    def __init__(self, exports_dir: str = "./data/exports"):
        self.exports_dir = Path(exports_dir)
        self.working_dir = Path("./data/extracted")
        
        # Ensure directories exist
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.working_dir.mkdir(parents=True, exist_ok=True)
    
    def discover_exports(self) -> List[Dict[str, Any]]:
        """
        Discover all conversation exports in the directory.
        
        Returns:
            List of discovered export info with source type and paths
        """
        discoveries = []
        
        # Look for zip files (ChatGPT exports)
        for zip_file in self.exports_dir.glob("*.zip"):
            logger.info(f"Found archive: {zip_file.name}")
            extracted_path = self._extract_archive(zip_file)
            if extracted_path:
                source_info = self._detect_source_type(extracted_path)
                if source_info:
                    discoveries.append({
                        'type': 'archive',
                        'source_file': zip_file,
                        'extracted_path': extracted_path,
                        **source_info
                    })
        
        # Look for direct conversation files
        for json_file in self.exports_dir.glob("*.json"):
            if json_file.name == "conversations.json":
                logger.info(f"Found conversations file: {json_file.name}")
                source_info = self._detect_source_type(json_file.parent)
                if source_info:
                    discoveries.append({
                        'type': 'direct',
                        'source_file': json_file,
                        'extracted_path': json_file.parent,
                        **source_info
                    })
        
        # Look for directories with conversations.json
        for subdir in self.exports_dir.iterdir():
            if subdir.is_dir():
                conv_file = subdir / "conversations.json"
                if conv_file.exists():
                    logger.info(f"Found conversations in directory: {subdir.name}")
                    source_info = self._detect_source_type(subdir)
                    if source_info:
                        discoveries.append({
                            'type': 'directory',
                            'source_file': subdir,
                            'extracted_path': subdir,
                            **source_info
                        })
        
        logger.info(f"Discovered {len(discoveries)} conversation exports")
        return discoveries
    
    def _extract_archive(self, zip_path: Path) -> Optional[Path]:
        """Extract a zip archive to the working directory."""
        extract_dir = self.working_dir / zip_path.stem
        
        # Skip if already extracted
        if extract_dir.exists() and (extract_dir / "conversations.json").exists():
            logger.info(f"Archive already extracted: {extract_dir}")
            return extract_dir
        
        try:
            logger.info(f"Extracting {zip_path.name} to {extract_dir}")
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Look for conversations.json in the extracted content
            conv_files = list(extract_dir.rglob("conversations.json"))
            if conv_files:
                # If conversations.json is in a subdirectory, use that as the base
                actual_dir = conv_files[0].parent
                logger.info(f"Found conversations.json in {actual_dir}")
                return actual_dir
            else:
                logger.warning(f"No conversations.json found in {zip_path.name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to extract {zip_path.name}: {e}")
            return None
    
    def _detect_source_type(self, data_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Detect the source type (ChatGPT/Claude) from conversation data.
        
        Returns:
            Dict with source_type and sample_data, or None if detection fails
        """
        conv_file = data_dir / "conversations.json"
        if not conv_file.exists():
            return None
        
        try:
            with open(conv_file, 'r', encoding='utf-8') as f:
                conversations = json.load(f)
            
            if not conversations or not isinstance(conversations, list):
                logger.warning(f"Invalid conversations format in {conv_file}")
                return None
            
            sample = conversations[0]
            
            # ChatGPT/OpenAI detection
            if 'mapping' in sample:
                logger.info(f"Detected ChatGPT/OpenAI format in {data_dir}")
                return {
                    'source_type': 'oai',
                    'conversations_count': len(conversations),
                    'sample_data': sample
                }
            
            # Claude detection  
            elif 'uuid' in sample and 'chat_messages' in sample:
                logger.info(f"Detected Claude format in {data_dir}")
                return {
                    'source_type': 'claude',
                    'conversations_count': len(conversations),
                    'sample_data': sample
                }
            
            else:
                logger.warning(f"Unknown conversation format in {conv_file}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading {conv_file}: {e}")
            return None
    
    def create_configs(self, discoveries: List[Dict[str, Any]]) -> List[CLIConfig]:
        """
        Create CLIConfig objects from discovered exports.
        
        Returns:
            List of configured CLI configs
        """
        configs = []
        
        for i, discovery in enumerate(discoveries):
            # Create unique names for multiple sources of the same type
            source_type = discovery['source_type']
            if len([d for d in discoveries if d['source_type'] == source_type]) > 1:
                config_name = f"{source_type}_{i+1}"
            else:
                config_name = source_type
            
            config = create_cli_config(
                name=config_name,
                root_path=str(discovery['extracted_path']),
                parser_type=source_type
            )
            
            configs.append(config)
            logger.info(f"Created config '{config_name}' for {discovery['conversations_count']} conversations")
        
        return configs
    
    def cleanup_extracted(self):
        """Clean up extracted files."""
        try:
            import shutil
            if self.working_dir.exists():
                shutil.rmtree(self.working_dir)
                logger.info("Cleaned up extracted files")
        except Exception as e:
            logger.warning(f"Could not clean up extracted files: {e}")


def discover_and_configure(exports_dir: str = "./data/exports") -> List[Dict[str, Any]]:
    """
    Convenience function to discover exports and create configs.
    
    Returns:
        List of discovery info with embedded config objects.
    """
    discovery = ExportDiscovery(exports_dir)
    discoveries = discovery.discover_exports()
    
    # Add config objects to each discovery
    for i, d in enumerate(discoveries):
        source_type = d['source_type']
        # Create unique names for multiple sources of the same type
        if len([disc for disc in discoveries if disc['source_type'] == source_type]) > 1:
            config_name = f"{source_type}_{i+1}"
        else:
            config_name = source_type
            
        config = create_cli_config(
            name=config_name,
            root_path=str(d['extracted_path']),
            parser_type=source_type
        )
        d['config'] = config
    
    return discoveries
