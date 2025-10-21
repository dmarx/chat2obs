# tests/conversation_tagger/test_data_loaders.py
"""
Tests for data loading functionality.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from conversation_tagger.data.loaders import ConversationLoader, load_conversations
from conversation_tagger.data.config import DataSourceConfig


class TestConversationLoader:
    """Test ConversationLoader class."""
    
    def test_init_with_config(self):
        """Test initialization with config."""
        config = DataSourceConfig(name="test", root_path="/test")
        loader = ConversationLoader(config)
        assert loader.config == config
    
    def test_init_without_config(self):
        """Test initialization without config."""
        loader = ConversationLoader()
        assert loader.config is None
    
    def test_from_source(self, tmp_path):
        """Test creating loader from source name."""
        # Create test conversations file
        conversations_file = tmp_path / "conversations.json"
        conversations_file.write_text("[]")
        
        with patch('conversation_tagger.data.loaders.get_config_for_source') as mock_get_config:
            mock_config = DataSourceConfig(name="oai", root_path=str(tmp_path))
            mock_get_config.return_value = mock_config
            
            loader = ConversationLoader.from_source("oai")
            assert loader.config == mock_config
            mock_get_config.assert_called_once_with("oai")
    
    def test_load_with_valid_json(self, tmp_path):
        """Test loading valid conversation data."""
        # Create test data
        test_data = [
            {"conversation_id": "test1", "title": "Test 1"},
            {"conversation_id": "test2", "title": "Test 2"}
        ]
        
        conversations_file = tmp_path / "conversations.json"
        with open(conversations_file, 'w') as f:
            json.dump(test_data, f)
        
        config = DataSourceConfig(name="test", root_path=str(tmp_path))
        loader = ConversationLoader(config)
        
        result = loader.load()
        assert result == test_data
    
    def test_load_with_source_override(self, tmp_path):
        """Test loading with source override parameter."""
        # Create test data
        test_data = [{"conversation_id": "test1"}]
        
        conversations_file = tmp_path / "conversations.json"
        with open(conversations_file, 'w') as f:
            json.dump(test_data, f)
        
        with patch('conversation_tagger.data.loaders.get_config_for_source') as mock_get_config:
            mock_config = DataSourceConfig(name="claude", root_path=str(tmp_path))
            mock_get_config.return_value = mock_config
            
            loader = ConversationLoader()
            result = loader.load(source="claude")
            
            assert result == test_data
            mock_get_config.assert_called_once_with("claude")
    
    def test_load_file_not_found(self):
        """Test loading when file doesn't exist."""
        config = DataSourceConfig(name="test", root_path="/nonexistent")
        loader = ConversationLoader(config)
        
        with pytest.raises(FileNotFoundError, match="Conversations file not found"):
            loader.load()
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading with invalid JSON."""
        conversations_file = tmp_path / "conversations.json"
        conversations_file.write_text("invalid json content")
        
        config = DataSourceConfig(name="test", root_path=str(tmp_path))
        loader = ConversationLoader(config)
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            loader.load()
    
    def test_load_no_config_no_source(self):
        """Test loading without config or source."""
        loader = ConversationLoader()
        
        with pytest.raises(ValueError, match="No source specified"):
            loader.load()
    
    def test_validate_structure_valid_list(self):
        """Test structure validation with valid conversation list."""
        # Use a loader with no specific parser type (should pass basic validation)
        loader = ConversationLoader()
        conversations = [
            {"conversation_id": "test1", "mapping": {"node1": {}}},  # OAI format
            {"conversation_id": "test2", "mapping": {"node2": {}}}
        ]
        
        assert loader.validate_structure(conversations)
    
    def test_validate_structure_not_list(self):
        """Test structure validation with non-list input."""
        loader = ConversationLoader()
        
        assert not loader.validate_structure({"not": "a list"})
    
    def test_validate_structure_empty_list(self):
        """Test structure validation with empty list."""
        loader = ConversationLoader()
        
        assert loader.validate_structure([])
    
    def test_validate_structure_claude_format(self):
        """Test structure validation for Claude format."""
        config = DataSourceConfig(name="claude", root_path="/test", parser_type="claude")
        loader = ConversationLoader(config)
        
        conversations = [{"conversation_id": "test1"}]
        assert loader.validate_structure(conversations)
        
        # Missing required field
        conversations = [{"title": "test1"}]
        assert not loader.validate_structure(conversations)
    
    def test_validate_structure_oai_format(self):
        """Test structure validation for OAI format."""
        config = DataSourceConfig(name="oai", root_path="/test", parser_type="oai")
        loader = ConversationLoader(config)
        
        conversations = [{"mapping": {"node1": {}}}]
        assert loader.validate_structure(conversations)
        
        # Missing required field
        conversations = [{"title": "test1"}]
        assert not loader.validate_structure(conversations)


class TestLoadConversations:
    """Test load_conversations convenience function."""
    
    def test_load_conversations_success(self, tmp_path):
        """Test successful conversation loading."""
        # Create test data
        test_data = [{"conversation_id": "test1"}]
        
        conversations_file = tmp_path / "conversations.json"
        with open(conversations_file, 'w') as f:
            json.dump(test_data, f)
        
        with patch('conversation_tagger.data.loaders.ConversationLoader') as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = test_data
            mock_loader.validate_structure.return_value = True
            mock_loader_class.from_source.return_value = mock_loader
            
            result = load_conversations("oai")
            
            assert result == test_data
            mock_loader_class.from_source.assert_called_once_with("oai")
            mock_loader.load.assert_called_once()
            mock_loader.validate_structure.assert_called_once_with(test_data)
    
    def test_load_conversations_validation_failed(self, tmp_path):
        """Test conversation loading with failed validation."""
        test_data = [{"conversation_id": "test1"}]
        
        with patch('conversation_tagger.data.loaders.ConversationLoader') as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load.return_value = test_data
            mock_loader.validate_structure.return_value = False
            mock_loader_class.from_source.return_value = mock_loader
            
            # Should still return data despite validation failure
            result = load_conversations("oai")
            assert result == test_data
