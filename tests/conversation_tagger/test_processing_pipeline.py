# tests/conversation_tagger/test_processing_pipeline.py
"""
Tests for processing pipeline functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from conversation_tagger.processing.pipeline import (
    ProcessingConfig,
    ProcessingPipeline,
    BatchProcessor,
    process_single_source,
    process_with_gizmo_filter,
    process_claude_obsidian_chats
)
from conversation_tagger.processing.filters import FilterCriteria


class TestProcessingConfig:
    """Test ProcessingConfig dataclass."""
    
    def test_init_defaults(self):
        """Test initialization with default values."""
        config = ProcessingConfig(sources=['oai'])
        
        assert config.sources == ['oai']
        assert config.output_dir == "../data/staging"
        assert config.source_rules == {}
        assert config.filter_criteria is None
        assert config.generate_notes_enabled is True
        assert config.template_name == 'article_body.md.jinja'
    
    def test_init_with_values(self):
        """Test initialization with specific values."""
        source_rules = {'oai': {'custom_rule': lambda x: True}}
        filter_criteria = FilterCriteria(required_annotations={'has_code'})
        
        config = ProcessingConfig(
            sources=['oai', 'claude'],
            output_dir="/custom/output",
            source_rules=source_rules,
            filter_criteria=filter_criteria,
            generate_notes_enabled=False,
            template_name='custom.jinja'
        )
        
        assert config.sources == ['oai', 'claude']
        assert config.output_dir == "/custom/output"
        assert config.source_rules == source_rules
        assert config.filter_criteria == filter_criteria
        assert config.generate_notes_enabled is False
        assert config.template_name == 'custom.jinja'


class TestProcessingPipeline:
    """Test ProcessingPipeline class."""
    
    def create_mock_config(self, **kwargs):
        """Helper to create mock config."""
        defaults = {
            'sources': ['oai'],
            'output_dir': '../data/staging',
            'source_rules': {},
            'filter_criteria': None,
            'generate_notes_enabled': True,
            'template_name': 'article_body.md.jinja'
        }
        defaults.update(kwargs)
        return ProcessingConfig(**defaults)
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    def test_init(self, mock_create_tagger):
        """Test pipeline initialization."""
        mock_tagger = MagicMock()
        mock_create_tagger.return_value = mock_tagger
        
        config = self.create_mock_config()
        pipeline = ProcessingPipeline('oai', config)
        
        assert pipeline.source == 'oai'
        assert pipeline.config == config
        assert pipeline.tagger == mock_tagger
        mock_create_tagger.assert_called_once_with(source='oai')
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    def test_init_with_custom_rules(self, mock_create_tagger):
        """Test pipeline initialization with custom rules."""
        mock_tagger = MagicMock()
        mock_create_tagger.return_value = mock_tagger
        
        custom_rule = lambda x: True
        source_rules = {'oai': {'custom_rule': custom_rule}}
        config = self.create_mock_config(source_rules=source_rules)
        
        pipeline = ProcessingPipeline('oai', config)
        
        mock_tagger.add_conversation_rule.assert_called_once_with('custom_rule', custom_rule)
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    @patch('conversation_tagger.processing.pipeline.load_conversations')
    def test_load_data(self, mock_load_conversations, mock_create_tagger):
        """Test data loading."""
        mock_create_tagger.return_value = MagicMock()
        mock_conversations = [{'conversation_id': 'test1'}]
        mock_load_conversations.return_value = mock_conversations
        
        config = self.create_mock_config()
        pipeline = ProcessingPipeline('oai', config)
        
        result = pipeline.load_data()
        
        assert result == mock_conversations
        mock_load_conversations.assert_called_once_with('oai')
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    def test_tag_conversations(self, mock_create_tagger):
        """Test conversation tagging."""
        mock_tagger = MagicMock()
        mock_create_tagger.return_value = mock_tagger
        
        # Mock tagged conversations
        mock_tagged_conv = MagicMock()
        mock_tagger.tag_conversation.return_value = mock_tagged_conv
        
        config = self.create_mock_config()
        pipeline = ProcessingPipeline('oai', config)
        
        conversations = [
            {'conversation_id': 'test1'},
            {'conversation_id': 'test2'}
        ]
        
        result = pipeline.tag_conversations(conversations)
        
        assert len(result) == 2
        assert all(conv == mock_tagged_conv for conv in result)
        assert mock_tagger.tag_conversation.call_count == 2
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    def test_tag_conversations_with_errors(self, mock_create_tagger):
        """Test conversation tagging with some failures."""
        mock_tagger = MagicMock()
        mock_create_tagger.return_value = mock_tagger
        
        mock_tagged_conv = MagicMock()
        mock_tagger.tag_conversation.side_effect = [
            mock_tagged_conv,
            Exception("Tagging error"),
            mock_tagged_conv
        ]
        
        config = self.create_mock_config()
        pipeline = ProcessingPipeline('oai', config)
        
        conversations = [
            {'conversation_id': 'test1'},
            {'conversation_id': 'test2'},
            {'conversation_id': 'test3'}
        ]
        
        result = pipeline.tag_conversations(conversations)
        
        # Should skip the failed one
        assert len(result) == 2
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    @patch('conversation_tagger.processing.pipeline.ConversationFilter')
    def test_filter_conversations(self, mock_filter_class, mock_create_tagger):
        """Test conversation filtering."""
        mock_create_tagger.return_value = MagicMock()
        mock_filter_class.filter_conversations.return_value = ['filtered_conv']
        
        filter_criteria = FilterCriteria(required_annotations={'has_code'})
        config = self.create_mock_config(filter_criteria=filter_criteria)
        pipeline = ProcessingPipeline('oai', config)
        
        conversations = ['conv1', 'conv2', 'conv3']
        result = pipeline.filter_conversations(conversations)
        
        assert result == ['filtered_conv']
        mock_filter_class.filter_conversations.assert_called_once_with(
            conversations, filter_criteria
        )
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    def test_filter_conversations_no_criteria(self, mock_create_tagger):
        """Test filtering when no criteria specified."""
        mock_create_tagger.return_value = MagicMock()
        
        config = self.create_mock_config(filter_criteria=None)
        pipeline = ProcessingPipeline('oai', config)
        
        conversations = ['conv1', 'conv2']
        result = pipeline.filter_conversations(conversations)
        
        # Should return unchanged when no filter criteria
        assert result == conversations
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    @patch('conversation_tagger.processing.pipeline.generate_notes')
    def test_generate_outputs(self, mock_generate_notes, mock_create_tagger):
        """Test output generation."""
        mock_create_tagger.return_value = MagicMock()
        
        config = self.create_mock_config()
        pipeline = ProcessingPipeline('oai', config)
        
        conversations = [MagicMock(), MagicMock()]
        
        result = pipeline.generate_outputs(conversations)
        
        assert result == 2
        assert mock_generate_notes.call_count == 2
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    @patch('conversation_tagger.processing.pipeline.generate_notes')
    def test_generate_outputs_disabled(self, mock_generate_notes, mock_create_tagger):
        """Test output generation when disabled."""
        mock_create_tagger.return_value = MagicMock()
        
        config = self.create_mock_config(generate_notes_enabled=False)
        pipeline = ProcessingPipeline('oai', config)
        
        conversations = [MagicMock(), MagicMock()]
        
        result = pipeline.generate_outputs(conversations)
        
        assert result == 0
        mock_generate_notes.assert_not_called()
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    @patch('conversation_tagger.processing.pipeline.generate_notes')
    def test_generate_outputs_with_errors(self, mock_generate_notes, mock_create_tagger):
        """Test output generation with some failures."""
        mock_create_tagger.return_value = MagicMock()
        mock_generate_notes.side_effect = [
            None,  # Success
            Exception("Generation error"),  # Failure
            None   # Success
        ]
        
        config = self.create_mock_config()
        pipeline = ProcessingPipeline('oai', config)
        
        conversations = [MagicMock(), MagicMock(), MagicMock()]
        
        result = pipeline.generate_outputs(conversations)
        
        # Should count only successful generations
        assert result == 2
    
    @patch('conversation_tagger.processing.pipeline.create_default_tagger')
    def test_process_full_pipeline(self, mock_create_tagger):
        """Test the complete processing pipeline."""
        mock_tagger = MagicMock()
        mock_create_tagger.return_value = mock_tagger
        
        config = self.create_mock_config(generate_notes_enabled=False)  # Skip note generation for simplicity
        
        with patch.object(ProcessingPipeline, 'load_data') as mock_load, \
             patch.object(ProcessingPipeline, 'tag_conversations') as mock_tag, \
             patch.object(ProcessingPipeline, 'filter_conversations') as mock_filter, \
             patch.object(ProcessingPipeline, 'generate_outputs') as mock_generate:
            
            mock_load.return_value = ['raw1', 'raw2']
            mock_tag.return_value = ['tagged1', 'tagged2']
            mock_filter.return_value = ['filtered1']
            mock_generate.return_value = 1
            
            pipeline = ProcessingPipeline('oai', config)
            result = pipeline.process()
            
            expected = {
                'source': 'oai',
                'raw_count': 2,
                'tagged_count': 2,
                'filtered_count': 1,
                'generated_count': 1
            }
            
            assert result == expected


class TestBatchProcessor:
    """Test BatchProcessor class."""
    
    @patch('conversation_tagger.processing.pipeline.Path')
    def test_init(self, mock_path_class):
        """Test batch processor initialization."""
        mock_path = MagicMock()
        mock_path_class.return_value = mock_path
        
        config = ProcessingConfig(
            sources=['oai', 'claude'],
            output_dir='/test/output'
        )
        
        processor = BatchProcessor(config)
        
        assert processor.config == config
        mock_path_class.assert_called_once_with('/test/output')
        mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    @patch('conversation_tagger.processing.pipeline.Path')
    @patch('conversation_tagger.processing.pipeline.ProcessingPipeline')
    def test_process_all_success(self, mock_pipeline_class, mock_path_class):
        """Test successful batch processing."""
        mock_path_class.return_value.mkdir = MagicMock()
        
        # Mock pipeline results
        mock_pipeline = MagicMock()
        mock_pipeline.process.return_value = {
            'source': 'oai',
            'raw_count': 10,
            'tagged_count': 10,
            'filtered_count': 8,
            'generated_count': 8
        }
        mock_pipeline_class.return_value = mock_pipeline
        
        config = ProcessingConfig(sources=['oai'])
        processor = BatchProcessor(config)
        
        result = processor.process_all()
        
        expected = {
            'sources_processed': 1,
            'total_generated': 8,
            'results_by_source': {
                'oai': {
                    'source': 'oai',
                    'raw_count': 10,
                    'tagged_count': 10,
                    'filtered_count': 8,
                    'generated_count': 8
                }
            }
        }
        
        assert result == expected
    
    @patch('conversation_tagger.processing.pipeline.Path')
    @patch('conversation_tagger.processing.pipeline.ProcessingPipeline')
    def test_process_all_with_errors(self, mock_pipeline_class, mock_path_class):
        """Test batch processing with some source errors."""
        mock_path_class.return_value.mkdir = MagicMock()
        
        mock_pipeline_class.side_effect = [
            MagicMock(process=MagicMock(return_value={'generated_count': 5})),
            Exception("Processing error")
        ]
        
        config = ProcessingConfig(sources=['oai', 'claude'])
        processor = BatchProcessor(config)
        
        result = processor.process_all()
        
        assert result['sources_processed'] == 2
        assert result['total_generated'] == 5
        assert 'oai' in result['results_by_source']
        assert result['results_by_source']['claude']['error'] == "Processing error"


class TestConvenienceFunctions:
    """Test convenience processing functions."""
    
    @patch('conversation_tagger.processing.pipeline.ProcessingPipeline')
    def test_process_single_source(self, mock_pipeline_class):
        """Test single source processing convenience function."""
        mock_pipeline = MagicMock()
        mock_result = {'source': 'oai', 'generated_count': 5}
        mock_pipeline.process.return_value = mock_result
        mock_pipeline_class.return_value = mock_pipeline
        
        result = process_single_source('oai', output_dir='/custom/output')
        
        assert result == mock_result
        # Verify ProcessingPipeline was called with correct config
        args, kwargs = mock_pipeline_class.call_args
        assert args[0] == 'oai'  # source
        config = args[1]  # config
        assert config.sources == ['oai']
        assert config.output_dir == '/custom/output'
    
    @patch('conversation_tagger.processing.pipeline.BatchProcessor')
    def test_process_with_gizmo_filter(self, mock_processor_class):
        """Test gizmo filtering convenience function."""
        mock_processor = MagicMock()
        mock_result = {'total_generated': 3}
        mock_processor.process_all.return_value = mock_result
        mock_processor_class.return_value = mock_processor
        
        result = process_with_gizmo_filter('dalle', ['oai'], '/custom/output')
        
        assert result == mock_result
        # Verify BatchProcessor was called with correct config
        args, kwargs = mock_processor_class.call_args
        config = args[0]
        assert config.sources == ['oai']
        assert config.output_dir == '/custom/output'
        assert 'dalle' in config.filter_criteria.required_gizmos
    
    @patch('conversation_tagger.processing.pipeline.BatchProcessor')
    def test_process_claude_obsidian_chats(self, mock_processor_class):
        """Test Claude Obsidian chat processing convenience function."""
        mock_processor = MagicMock()
        mock_result = {'total_generated': 2}
        mock_processor.process_all.return_value = mock_result
        mock_processor_class.return_value = mock_processor
        
        obsidian_ids = {'chat1', 'chat2'}
        result = process_claude_obsidian_chats(obsidian_ids, '/custom/output')
        
        assert result == mock_result
        # Verify BatchProcessor was called with correct config
        args, kwargs = mock_processor_class.call_args
        config = args[0]
        assert config.sources == ['claude']
        assert config.output_dir == '/custom/output'
        assert 'llm_obsidian_chat' in config.source_rules['claude']
