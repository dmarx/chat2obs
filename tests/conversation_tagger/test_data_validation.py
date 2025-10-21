# tests/conversation_tagger/test_data_validation.py
"""
Tests for schema validation functionality.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from conversation_tagger.data.validation import (
    ConversationSchemaValidator,
    validate_and_generate_schema,
    SEED_SCHEMA_CHATGPT,
    SEED_SCHEMA_CLAUDE
)


class TestConversationSchemaValidator:
    """Test ConversationSchemaValidator class."""
    
    def test_init_chatgpt_format(self):
        """Test initialization with ChatGPT format."""
        validator = ConversationSchemaValidator("chatgpt")
        assert validator.dataset_type == "chatgpt"
        assert validator.seed_schema == SEED_SCHEMA_CHATGPT
    
    def test_init_oai_format(self):
        """Test initialization with OAI format (alias for ChatGPT)."""
        validator = ConversationSchemaValidator("oai")
        assert validator.dataset_type == "oai"
        assert validator.seed_schema == SEED_SCHEMA_CHATGPT
    
    def test_init_claude_format(self):
        """Test initialization with Claude format."""
        validator = ConversationSchemaValidator("claude")
        assert validator.dataset_type == "claude"
        assert validator.seed_schema == SEED_SCHEMA_CLAUDE
    
    def test_init_invalid_format(self):
        """Test initialization with invalid format."""
        with pytest.raises(ValueError, match="Unknown dataset type: invalid"):
            ConversationSchemaValidator("invalid")
    
    @patch('conversation_tagger.data.validation.HAS_GENSON', True)
    def test_init_with_genson(self):
        """Test initialization when genson is available."""
        with patch('conversation_tagger.data.validation.SchemaBuilder') as mock_builder_class:
            mock_builder = MagicMock()
            mock_builder_class.return_value = mock_builder
            
            validator = ConversationSchemaValidator("oai")
            
            assert validator.builder == mock_builder
            mock_builder_class.assert_called_once()
            mock_builder.add_schema.assert_called_once_with(SEED_SCHEMA_CHATGPT)
    
    @patch('conversation_tagger.data.validation.HAS_GENSON', False)
    def test_init_without_genson(self):
        """Test initialization when genson is not available."""
        validator = ConversationSchemaValidator("oai")
        assert validator.builder is None
    
    @patch('conversation_tagger.data.validation.HAS_GENSON', True)
    def test_validate_conversations_success(self):
        """Test successful conversation validation."""
        with patch('conversation_tagger.data.validation.SchemaBuilder') as mock_builder_class:
            mock_builder = MagicMock()
            mock_builder_class.return_value = mock_builder
            
            validator = ConversationSchemaValidator("oai")
            conversations = [{"mapping": {"node1": {}}}]
            
            result = validator.validate_conversations(conversations)
            
            assert result is True
            mock_builder.add_object.assert_called_once_with(conversations)
            mock_builder.to_schema.assert_called_once()
    
    @patch('conversation_tagger.data.validation.HAS_GENSON', True)
    def test_validate_conversations_failure(self):
        """Test conversation validation failure."""
        with patch('conversation_tagger.data.validation.SchemaBuilder') as mock_builder_class:
            mock_builder = MagicMock()
            mock_builder.add_object.side_effect = Exception("Validation error")
            mock_builder_class.return_value = mock_builder
            
            validator = ConversationSchemaValidator("oai")
            conversations = [{"invalid": "data"}]
            
            result = validator.validate_conversations(conversations)
            
            assert result is False
    
    @patch('conversation_tagger.data.validation.HAS_GENSON', False)
    def test_validate_conversations_no_genson(self):
        """Test validation when genson is not available."""
        validator = ConversationSchemaValidator("oai")
        conversations = [{"mapping": {"node1": {}}}]
        
        result = validator.validate_conversations(conversations)
        
        # Should return True (skip validation) when genson not available
        assert result is True
    
    @patch('conversation_tagger.data.validation.HAS_GENSON', True)
    def test_get_schema_success(self):
        """Test getting schema when available."""
        with patch('conversation_tagger.data.validation.SchemaBuilder') as mock_builder_class:
            mock_builder = MagicMock()
            expected_schema = {"type": "array", "items": {}}
            mock_builder.to_schema.return_value = expected_schema
            mock_builder_class.return_value = mock_builder
            
            validator = ConversationSchemaValidator("oai")
            schema = validator.get_schema()
            
            assert schema == expected_schema
    
    @patch('conversation_tagger.data.validation.HAS_GENSON', False)
    def test_get_schema_no_genson(self):
        """Test getting schema when genson not available."""
        validator = ConversationSchemaValidator("oai")
        schema = validator.get_schema()
        
        assert schema is None
    
    @patch('conversation_tagger.data.validation.HAS_GENSON', True)
    def test_save_schema_success(self, tmp_path):
        """Test successful schema saving."""
        with patch('conversation_tagger.data.validation.SchemaBuilder') as mock_builder_class:
            mock_builder = MagicMock()
            test_schema = {"type": "array", "items": {}}
            mock_builder.to_schema.return_value = test_schema
            mock_builder_class.return_value = mock_builder
            
            validator = ConversationSchemaValidator("oai")
            output_path = tmp_path / "test_schema.json"
            
            result = validator.save_schema(str(output_path))
            
            assert result is True
            assert output_path.exists()
            
            # Verify saved content
            with open(output_path) as f:
                saved_schema = json.load(f)
            assert saved_schema == test_schema
    
    def test_save_schema_no_schema(self):
        """Test saving when no schema available."""
        validator = ConversationSchemaValidator("oai")
        validator.builder = None
        
        result = validator.save_schema("/tmp/test.json")
        
        assert result is False
    
    @patch('conversation_tagger.data.validation.HAS_GENSON', True)
    def test_save_schema_write_error(self):
        """Test schema saving with write error."""
        with patch('conversation_tagger.data.validation.SchemaBuilder') as mock_builder_class:
            mock_builder = MagicMock()
            mock_builder.to_schema.return_value = {"type": "array"}
            mock_builder_class.return_value = mock_builder
            
            validator = ConversationSchemaValidator("oai")
            
            # Try to save to invalid path
            result = validator.save_schema("/nonexistent/directory/schema.json")
            
            assert result is False


class TestValidateAndGenerateSchema:
    """Test validate_and_generate_schema convenience function."""
    
    @patch('conversation_tagger.data.validation.ConversationSchemaValidator')
    def test_validate_and_generate_success(self, mock_validator_class, tmp_path):
        """Test successful validation and schema generation."""
        mock_validator = MagicMock()
        mock_validator.validate_conversations.return_value = True
        test_schema = {"type": "array", "items": {}}
        mock_validator.get_schema.return_value = test_schema
        mock_validator.save_schema.return_value = True
        mock_validator_class.return_value = mock_validator
        
        conversations = [{"conversation_id": "test1"}]
        output_path = str(tmp_path / "schema.json")
        
        result = validate_and_generate_schema(
            conversations, 
            "oai", 
            output_path
        )
        
        assert result == test_schema
        mock_validator_class.assert_called_once_with("oai")
        mock_validator.validate_conversations.assert_called_once_with(conversations)
        mock_validator.get_schema.assert_called_once()
        mock_validator.save_schema.assert_called_once_with(output_path)
    
    @patch('conversation_tagger.data.validation.ConversationSchemaValidator')
    def test_validate_and_generate_validation_failure(self, mock_validator_class):
        """Test validation failure."""
        mock_validator = MagicMock()
        mock_validator.validate_conversations.return_value = False
        mock_validator_class.return_value = mock_validator
        
        conversations = [{"invalid": "data"}]
        
        result = validate_and_generate_schema(conversations, "oai")
        
        assert result is None
        mock_validator.validate_conversations.assert_called_once_with(conversations)
        # Should not call get_schema if validation fails
        mock_validator.get_schema.assert_not_called()
    
    @patch('conversation_tagger.data.validation.ConversationSchemaValidator')
    def test_validate_and_generate_no_output_path(self, mock_validator_class):
        """Test validation without saving schema."""
        mock_validator = MagicMock()
        mock_validator.validate_conversations.return_value = True
        test_schema = {"type": "array"}
        mock_validator.get_schema.return_value = test_schema
        mock_validator_class.return_value = mock_validator
        
        conversations = [{"conversation_id": "test1"}]
        
        result = validate_and_generate_schema(conversations, "claude")
        
        assert result == test_schema
        # Should not call save_schema when no output path provided
        mock_validator.save_schema.assert_not_called()
