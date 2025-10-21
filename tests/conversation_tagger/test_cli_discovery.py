# tests/conversation_tagger/test_cli_discovery.py
"""
Tests for CLI discovery functionality.
"""

import json
import zipfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from conversation_tagger.cli.discovery import ExportDiscovery, discover_and_configure


class TestExportDiscovery:
    """Test ExportDiscovery class."""
    
    def test_init(self, tmp_path):
        """Test initialization creates directories."""
        exports_dir = tmp_path / "exports"
        discovery = ExportDiscovery(str(exports_dir))
        
        assert discovery.exports_dir == exports_dir
        assert discovery.working_dir == Path("./data/extracted")
        assert exports_dir.exists()
    
    def test_detect_source_type_chatgpt(self, tmp_path):
        """Test detection of ChatGPT format."""
        data_dir = tmp_path / "chatgpt_data"
        data_dir.mkdir()
        
        conversations = [{
            "conversation_id": "test-1",
            "mapping": {
                "node-1": {"message": {"id": "msg-1"}}
            }
        }]
        
        conv_file = data_dir / "conversations.json"
        with open(conv_file, 'w') as f:
            json.dump(conversations, f)
        
        discovery = ExportDiscovery(str(tmp_path))
        result = discovery._detect_source_type(data_dir)
        
        assert result is not None
        assert result['source_type'] == 'oai'
        assert result['conversations_count'] == 1
        assert 'sample_data' in result
    
    def test_detect_source_type_claude(self, tmp_path):
        """Test detection of Claude format."""
        data_dir = tmp_path / "claude_data"
        data_dir.mkdir()
        
        conversations = [{
            "uuid": "test-uuid",
            "chat_messages": [
                {"uuid": "msg-1", "text": "Hello"}
            ]
        }]
        
        conv_file = data_dir / "conversations.json"
        with open(conv_file, 'w') as f:
            json.dump(conversations, f)
        
        discovery = ExportDiscovery(str(tmp_path))
        result = discovery._detect_source_type(data_dir)
        
        assert result is not None
        assert result['source_type'] == 'claude'
        assert result['conversations_count'] == 1
    
    def test_detect_source_type_invalid(self, tmp_path):
        """Test handling of invalid format."""
        data_dir = tmp_path / "invalid_data"
        data_dir.mkdir()
        
        conversations = [{"unknown_format": "data"}]
        
        conv_file = data_dir / "conversations.json"
        with open(conv_file, 'w') as f:
            json.dump(conversations, f)
        
        discovery = ExportDiscovery(str(tmp_path))
        result = discovery._detect_source_type(data_dir)
        
        assert result is None
    
    def test_discover_direct_json(self, tmp_path):
        """Test discovery of direct conversations.json files."""
        exports_dir = tmp_path / "exports"
        exports_dir.mkdir()
        
        conversations = [{
            "conversation_id": "test-1",
            "mapping": {"node-1": {}}
        }]
        
        conv_file = exports_dir / "conversations.json"
        with open(conv_file, 'w') as f:
            json.dump(conversations, f)
        
        discovery = ExportDiscovery(str(exports_dir))
        discoveries = discovery.discover_exports()
        
        assert len(discoveries) == 1
        assert discoveries[0]['type'] == 'direct'
        assert discoveries[0]['source_type'] == 'oai'
    
    def test_discover_directory_with_conversations(self, tmp_path):
        """Test discovery of directories containing conversations.json."""
        exports_dir = tmp_path / "exports"
        exports_dir.mkdir()
        
        # Create subdirectory with conversations
        subdir = exports_dir / "chatgpt_export"
        subdir.mkdir()
        
        conversations = [{
            "conversation_id": "test-1",
            "mapping": {"node-1": {}}
        }]
        
        conv_file = subdir / "conversations.json"
        with open(conv_file, 'w') as f:
            json.dump(conversations, f)
        
        discovery = ExportDiscovery(str(exports_dir))
        discoveries = discovery.discover_exports()
        
        assert len(discoveries) == 1
        assert discoveries[0]['type'] == 'directory'
        assert discoveries[0]['source_type'] == 'oai'
    
    def test_extract_archive(self, tmp_path):
        """Test extraction of zip archives."""
        exports_dir = tmp_path / "exports"
        exports_dir.mkdir()
        
        # Create a zip file with conversations.json
        zip_path = exports_dir / "test_export.zip"
        
        conversations = [{
            "conversation_id": "test-1",
            "mapping": {"node-1": {}}
        }]
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            zip_file.writestr("conversations.json", json.dumps(conversations))
        
        discovery = ExportDiscovery(str(exports_dir))
        extracted_path = discovery._extract_archive(zip_path)
        
        assert extracted_path is not None
        assert (extracted_path / "conversations.json").exists()
    
    def test_create_configs(self, tmp_path):
        """Test creation of DataSourceConfig objects."""
        discovery = ExportDiscovery(str(tmp_path))
        
        discoveries = [
            {
                'source_type': 'oai',
                'extracted_path': '/path/to/oai',
                'conversations_count': 5
            },
            {
                'source_type': 'claude',
                'extracted_path': '/path/to/claude',
                'conversations_count': 3
            }
        ]
        
        configs = discovery.create_configs(discoveries)
        
        assert len(configs) == 2
        assert configs[0].name == 'oai'
        assert configs[0].parser_type == 'oai'
        assert configs[1].name == 'claude'
        assert configs[1].parser_type == 'claude'
    
    def test_create_configs_duplicate_types(self, tmp_path):
        """Test creation of configs with duplicate source types."""
        discovery = ExportDiscovery(str(tmp_path))
        
        discoveries = [
            {
                'source_type': 'oai',
                'extracted_path': '/path/to/oai1',
                'conversations_count': 5
            },
            {
                'source_type': 'oai',
                'extracted_path': '/path/to/oai2',
                'conversations_count': 3
            }
        ]
        
        configs = discovery.create_configs(discoveries)
        
        assert len(configs) == 2
        assert configs[0].name == 'oai_1'
        assert configs[1].name == 'oai_2'


class TestDiscoverAndConfigure:
    """Test the discover_and_configure convenience function."""
    
    def test_discover_and_configure(self, tmp_path):
        """Test the complete discover and configure flow."""
        exports_dir = tmp_path / "exports"
        exports_dir.mkdir()
        
        # Create test conversation file
        conversations = [{
            "conversation_id": "test-1",
            "mapping": {"node-1": {}}
        }]
        
        conv_file = exports_dir / "conversations.json"
        with open(conv_file, 'w') as f:
            json.dump(conversations, f)
        
        discoveries = discover_and_configure(str(exports_dir))
        
        assert len(discoveries) == 1
        discovery = discoveries[0]
        config = discovery['config']
        
        assert config.name == 'oai'
        assert discovery['source_type'] == 'oai'
