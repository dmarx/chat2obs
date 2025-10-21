# tests/conversation_tagger/test_data_config.py
"""
Tests for data configuration management.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from conversation_tagger.data.config import (
    DataSourceConfig, 
    get_default_config, 
    get_config_for_source
)


class TestDataSourceConfig:
    """Test DataSourceConfig class."""
    
    def test_init(self):
        """Test basic initialization."""
        config = DataSourceConfig(
            name="test",
            root_path="/test/path",
            conversations_file="test.json",
            parser_type="oai"
        )
        
        assert config.name == "test"
        assert config.root_path == "/test/path"
        assert config.conversations_file == "test.json"
        assert config.parser_type == "oai"
    
    def test_conversations_path(self):
        """Test conversations_path property."""
        config = DataSourceConfig(
            name="test",
            root_path="/test/path"
        )
        
        expected_path = Path("/test/path") / "conversations.json"
        assert config.conversations_path == expected_path
    
    def test_conversations_path_custom_file(self):
        """Test conversations_path with custom filename."""
        config = DataSourceConfig(
            name="test",
            root_path="/test/path",
            conversations_file="custom.json"
        )
        
        expected_path = Path("/test/path") / "custom.json"
        assert config.conversations_path == expected_path
    
    def test_exists_file_not_found(self):
        """Test exists() when file doesn't exist."""
        config = DataSourceConfig(
            name="test",
            root_path="/nonexistent/path"
        )
        
        assert not config.exists()
    
    def test_exists_file_found(self, tmp_path):
        """Test exists() when file exists."""
        # Create test file
        test_file = tmp_path / "conversations.json"
        test_file.write_text("[]")
        
        config = DataSourceConfig(
            name="test",
            root_path=str(tmp_path)
        )
        
        assert config.exists()


class TestGetDefaultConfig:
    """Test get_default_config function."""
    
    def test_default_config_structure(self):
        """Test that default config has expected structure."""
        config = get_default_config()
        
        assert isinstance(config, dict)
        assert 'oai' in config
        assert 'claude' in config
        assert 'chatgpt' in config  # Alias for oai
        
        # Check oai config
        oai_config = config['oai']
        assert isinstance(oai_config, DataSourceConfig)
        assert oai_config.name == 'oai'
        assert oai_config.parser_type == 'oai'
        
        # Check claude config
        claude_config = config['claude']
        assert isinstance(claude_config, DataSourceConfig)
        assert claude_config.name == 'claude'
        assert claude_config.parser_type == 'claude'
    
    @patch.dict(os.environ, {
        'CHAT2OBS_CHATGPT_ROOT': '/custom/chatgpt/path',
        'CHAT2OBS_CLAUDE_ROOT': '/custom/claude/path'
    })
    def test_environment_variable_override(self):
        """Test that environment variables override default paths."""
        config = get_default_config()
        
        assert config['oai'].root_path == '/custom/chatgpt/path'
        assert config['claude'].root_path == '/custom/claude/path'
        assert config['chatgpt'].root_path == '/custom/chatgpt/path'  # Alias
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_paths_when_no_env_vars(self):
        """Test default paths when no environment variables are set."""
        config = get_default_config()
        
        # Should use hardcoded defaults
        assert 'chatgpt' in config['oai'].root_path
        assert 'data-' in config['claude'].root_path.lower()  # More flexible check


class TestGetConfigForSource:
    """Test get_config_for_source function."""
    
    def test_valid_source_oai(self, tmp_path):
        """Test getting config for valid oai source."""
        # Create test conversations file
        conversations_file = tmp_path / "conversations.json"
        conversations_file.write_text("[]")
        
        with patch('conversation_tagger.data.config.get_default_config') as mock_config:
            mock_config.return_value = {
                'oai': DataSourceConfig(
                    name='oai',
                    root_path=str(tmp_path),
                    parser_type='oai'
                )
            }
            
            config = get_config_for_source('oai')
            assert config.name == 'oai'
            assert config.parser_type == 'oai'
    
    def test_valid_source_claude(self, tmp_path):
        """Test getting config for valid claude source."""
        # Create test conversations file
        conversations_file = tmp_path / "conversations.json"
        conversations_file.write_text("[]")
        
        with patch('conversation_tagger.data.config.get_default_config') as mock_config:
            mock_config.return_value = {
                'claude': DataSourceConfig(
                    name='claude',
                    root_path=str(tmp_path),
                    parser_type='claude'
                )
            }
            
            config = get_config_for_source('claude')
            assert config.name == 'claude'
            assert config.parser_type == 'claude'
    
    def test_invalid_source(self):
        """Test error handling for invalid source."""
        with pytest.raises(ValueError, match="Unknown source: invalid"):
            get_config_for_source('invalid')
    
    def test_missing_conversations_file(self):
        """Test error handling when conversations file doesn't exist."""
        with patch('conversation_tagger.data.config.get_default_config') as mock_config:
            mock_config.return_value = {
                'oai': DataSourceConfig(
                    name='oai',
                    root_path='/nonexistent/path',
                    parser_type='oai'
                )
            }
            
            with pytest.raises(FileNotFoundError, match="Conversations file not found"):
                get_config_for_source('oai')
