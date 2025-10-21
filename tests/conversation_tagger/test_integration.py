# tests/conversation_tagger/test_integration.py
"""
Integration tests for the processing machinery.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from conversation_tagger import (
    load_conversations,
    ProcessingPipeline,
    BatchProcessor,
    ProcessingConfig,
    ConversationFilter,
    FilterCriteria
)
from conversation_tagger.data.validation import validate_and_generate_schema


class TestDataLoadingIntegration:
    """Test integration of data loading components."""
    
    def test_load_conversations_full_flow(self, tmp_path):
        """Test complete data loading flow with real files."""
        # Create test conversation data
        test_conversations = [
            {
                "conversation_id": "test-conv-1",
                "title": "Test Conversation 1",
                "mapping": {
                    "node-1": {
                        "message": {
                            "id": "msg-1",
                            "content": {"text": "Hello"}
                        }
                    }
                }
            },
            {
                "conversation_id": "test-conv-2", 
                "title": "Test Conversation 2",
                "mapping": {
                    "node-2": {
                        "message": {
                            "id": "msg-2",
                            "content": {"text": "World"}
                        }
                    }
                }
            }
        ]
        
        # Write test data to file
        conversations_file = tmp_path / "conversations.json"
        with open(conversations_file, 'w') as f:
            json.dump(test_conversations, f)
        
        # Mock the configuration to point to our test file
        with patch('conversation_tagger.data.config.get_default_config') as mock_config:
            from conversation_tagger.data.config import DataSourceConfig
            mock_config.return_value = {
                'oai': DataSourceConfig(
                    name='oai',
                    root_path=str(tmp_path),
                    parser_type='oai'
                )
            }
            
            # Test loading
            conversations = load_conversations('oai')
            
            assert len(conversations) == 2
            assert conversations[0]['conversation_id'] == 'test-conv-1'
            assert conversations[1]['conversation_id'] == 'test-conv-2'


class TestSchemaValidationIntegration:
    """Test integration of schema validation with real data."""
    
    @patch('conversation_tagger.data.validation.HAS_GENSON', True)
    def test_schema_validation_flow(self, tmp_path):
        """Test complete schema validation flow."""
        # Test data that matches expected ChatGPT structure
        test_conversations = [
            {
                "conversation_id": "test-1",
                "title": "Test Chat",
                "mapping": {
                    "a1b2c3d4-e5f6-7890-abcd-ef1234567890": {
                        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "message": {
                            "id": "msg-1",
                            "content": {"text": "Hello"}
                        }
                    }
                }
            }
        ]
        
        output_path = tmp_path / "generated_schema.json"
        
        with patch('conversation_tagger.data.validation.SchemaBuilder') as mock_builder_class:
            mock_builder = MagicMock()
            mock_schema = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string"},
                        "title": {"type": "string"}
                    }
                }
            }
            mock_builder.to_schema.return_value = mock_schema
            mock_builder_class.return_value = mock_builder
            
            # Test validation and schema generation
            result_schema = validate_and_generate_schema(
                test_conversations,
                'oai',
                str(output_path)
            )
            
            assert result_schema == mock_schema
            mock_builder.add_schema.assert_called_once()
            mock_builder.add_object.assert_called_once_with(test_conversations)


class TestProcessingPipelineIntegration:
    """Test integration of complete processing pipeline."""
    
    def test_pipeline_with_mocked_components(self, tmp_path):
        """Test processing pipeline with mocked external dependencies."""
        # Create test output directory
        output_dir = tmp_path / "output"
        
        # Mock all external dependencies
        with patch('conversation_tagger.processing.pipeline.load_conversations') as mock_load, \
             patch('conversation_tagger.processing.pipeline.create_default_tagger') as mock_create_tagger, \
             patch('conversation_tagger.processing.pipeline.generate_notes') as mock_generate:
            
            # Setup mocks
            test_conversations = [
                {'conversation_id': 'conv-1'},
                {'conversation_id': 'conv-2'}
            ]
            mock_load.return_value = test_conversations
            
            mock_tagger = MagicMock()
            mock_tagged_conv1 = MagicMock()
            mock_tagged_conv1.conversation_id = 'conv-1'
            mock_tagged_conv1.annotations = {'has_code': True}
            mock_tagged_conv1.has_annotation.side_effect = lambda x: x == 'has_code'
            
            mock_tagged_conv2 = MagicMock() 
            mock_tagged_conv2.conversation_id = 'conv-2'
            mock_tagged_conv2.annotations = {'has_attachments': True}
            mock_tagged_conv2.has_annotation.side_effect = lambda x: x == 'has_attachments'
            
            mock_tagger.tag_conversation.side_effect = [mock_tagged_conv1, mock_tagged_conv2]
            mock_create_tagger.return_value = mock_tagger
            
            # Create pipeline with filter
            filter_criteria = FilterCriteria(required_annotations={'has_code'})
            config = ProcessingConfig(
                sources=['oai'],
                output_dir=str(output_dir),
                filter_criteria=filter_criteria
            )
            
            pipeline = ProcessingPipeline('oai', config)
            
            # Run pipeline
            result = pipeline.process()
            
            # Verify results
            assert result['source'] == 'oai'
            assert result['raw_count'] == 2
            assert result['tagged_count'] == 2
            assert result['filtered_count'] == 1  # Only one has 'has_code'
            assert result['generated_count'] == 1
            
            # Verify calls
            mock_load.assert_called_once_with('oai')
            assert mock_tagger.tag_conversation.call_count == 2
            mock_generate.assert_called_once()  # Only for filtered conversation


class TestBatchProcessorIntegration:
    """Test integration of batch processing across sources."""
    
    def test_batch_processor_multiple_sources(self, tmp_path):
        """Test batch processing with multiple sources."""
        output_dir = tmp_path / "batch_output"
        
        with patch('conversation_tagger.processing.pipeline.ProcessingPipeline') as mock_pipeline_class:
            # Create mock pipelines that return different results
            mock_oai_pipeline = MagicMock()
            mock_oai_pipeline.process.return_value = {
                'source': 'oai',
                'raw_count': 10,
                'tagged_count': 10,
                'filtered_count': 8,
                'generated_count': 8
            }
            
            mock_claude_pipeline = MagicMock()
            mock_claude_pipeline.process.return_value = {
                'source': 'claude', 
                'raw_count': 5,
                'tagged_count': 5,
                'filtered_count': 3,
                'generated_count': 3
            }
            
            mock_pipeline_class.side_effect = [mock_oai_pipeline, mock_claude_pipeline]
            
            # Create batch processor
            config = ProcessingConfig(
                sources=['oai', 'claude'],
                output_dir=str(output_dir)
            )
            
            processor = BatchProcessor(config)
            
            # Run batch processing
            result = processor.process_all()
            
            # Verify results
            assert result['sources_processed'] == 2
            assert result['total_generated'] == 11  # 8 + 3
            
            assert 'oai' in result['results_by_source']
            assert 'claude' in result['results_by_source']
            
            assert result['results_by_source']['oai']['generated_count'] == 8
            assert result['results_by_source']['claude']['generated_count'] == 3
            
            # Verify pipeline creation
            assert mock_pipeline_class.call_count == 2


class TestFilteringIntegration:
    """Test integration of filtering with real conversation objects."""
    
    def test_conversation_filtering_integration(self):
        """Test filtering with mock conversation objects."""
        from conversation_tagger.core.conversation import Conversation
        
        # Create mock conversations with different annotations
        conv1 = MagicMock(spec=Conversation)
        conv1.conversation_id = 'conv-1'
        conv1.annotations = {'has_code': True, 'has_github': True}
        conv1.has_annotation.side_effect = lambda x: x in conv1.annotations
        
        conv2 = MagicMock(spec=Conversation)
        conv2.conversation_id = 'conv-2'
        conv2.annotations = {'has_attachments': True}
        conv2.has_annotation.side_effect = lambda x: x in conv2.annotations
        
        conv3 = MagicMock(spec=Conversation)
        conv3.conversation_id = 'conv-3'
        conv3.annotations = {'has_code': True, 'has_attachments': True}
        conv3.has_annotation.side_effect = lambda x: x in conv3.annotations
        
        conversations = [conv1, conv2, conv3]
        
        # Test filtering for code conversations without attachments
        criteria = FilterCriteria(
            required_annotations={'has_code'},
            forbidden_annotations={'has_attachments'}
        )
        
        filtered = ConversationFilter.filter_conversations(conversations, criteria)
        
        # Should only include conv1 (has code, no attachments)
        assert len(filtered) == 1
        assert filtered[0] == conv1


class TestEndToEndWorkflow:
    """Test end-to-end processing workflows."""
    
    def test_complete_workflow_simulation(self, tmp_path):
        """Test a complete workflow from data loading to output generation."""
        # This simulates the notebook workflow that was factored out
        
        output_dir = tmp_path / "e2e_output"
        
        # Mock all the dependencies but ensure they're called in the right order
        call_order = []
        
        def track_call(name):
            def wrapper(*args, **kwargs):
                call_order.append(name)
                return MagicMock()
            return wrapper
        
        def mock_load_with_data(*args, **kwargs):
            call_order.append('load')
            return [{'conversation_id': 'test1'}]  # Return some data so generate gets called
        
        with patch('conversation_tagger.processing.pipeline.load_conversations', side_effect=mock_load_with_data), \
             patch('conversation_tagger.processing.pipeline.create_default_tagger', side_effect=track_call('create_tagger')), \
             patch('conversation_tagger.processing.pipeline.generate_notes', side_effect=track_call('generate')):
            
            # Simulate the old notebook workflow: 
            # for source in ['oai', 'claude']: ...
            
            config = ProcessingConfig(
                sources=['oai', 'claude'],
                output_dir=str(output_dir),
                generate_notes_enabled=True
            )
            
            processor = BatchProcessor(config)
            processor.process_all()
            
            # Verify the workflow executed in the expected order
            # Should have: load -> create_tagger -> load -> create_tagger -> generate calls
            assert 'load' in call_order
            assert 'create_tagger' in call_order
            assert 'generate' in call_order