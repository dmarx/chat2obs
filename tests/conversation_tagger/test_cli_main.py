# tests/conversation_tagger/test_cli_main.py
"""
Tests for CLI main functionality.
"""

import argparse
import pytest
from unittest.mock import patch, MagicMock, call
from io import StringIO
import sys

from conversation_tagger.cli.main import (
    create_cli_parser,
    setup_command,
    discover_command,
    process_command
)


class TestCLIParser:
    """Test CLI argument parsing."""
    
    def test_create_cli_parser(self):
        """Test CLI parser creation."""
        parser = create_cli_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == 'chat2obs'
    
    def test_process_command_args(self):
        """Test process command argument parsing."""
        parser = create_cli_parser()
        
        args = parser.parse_args(['process', '--exports-dir', './test', '--output-dir', './output'])
        
        assert args.command == 'process'
        assert args.exports_dir == './test'
        assert args.output_dir == './output'
        assert args.source_type is None
        assert args.no_notes is False
        assert args.cleanup is False
    
    def test_discover_command_args(self):
        """Test discover command argument parsing."""
        parser = create_cli_parser()
        
        args = parser.parse_args(['discover', '--exports-dir', './custom'])
        
        assert args.command == 'discover'
        assert args.exports_dir == './custom'
    
    def test_setup_command_args(self):
        """Test setup command parsing."""
        parser = create_cli_parser()
        
        args = parser.parse_args(['setup'])
        
        assert args.command == 'setup'


class TestCLICommands:
    """Test CLI command implementations."""
    
    @patch('conversation_tagger.cli.main.Path')
    @patch('builtins.print')
    def test_setup_command(self, mock_print, mock_path_class):
        """Test setup command."""
        mock_path_exports = MagicMock()
        mock_path_output = MagicMock()
        mock_path_class.side_effect = [mock_path_exports, mock_path_output]
        
        setup_command()
        
        mock_path_exports.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_path_output.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # Check that setup message was printed
        mock_print.assert_called()
        print_calls = [call.args[0] if call.args else str(call) for call in mock_print.call_args_list]
        setup_messages = [msg for msg in print_calls if 'setup complete' in str(msg)]
        assert len(setup_messages) > 0
    
    @patch('conversation_tagger.cli.main.discover_and_configure')
    @patch('builtins.print')
    def test_discover_command_success(self, mock_print, mock_discover):
        """Test successful discover command."""
        mock_configs = [MagicMock()]
        mock_discoveries = [{
            'source_type': 'oai',
            'conversations_count': 5,
            'source_file': '/path/to/file',
            'type': 'direct'
        }]
        mock_discover.return_value = (mock_configs, mock_discoveries)
        
        result = discover_command('./test/exports')
        
        assert result == 0
        mock_discover.assert_called_once_with('./test/exports')
        
        # Check that discovery results were printed
        mock_print.assert_called()
        print_calls = [str(call.args[0]) if call.args else '' for call in mock_print.call_args_list]
        oai_messages = [msg for msg in print_calls if 'OAI: 5 conversations' in msg]
        assert len(oai_messages) > 0
    
    @patch('conversation_tagger.cli.main.discover_and_configure')
    @patch('builtins.print')
    def test_discover_command_no_exports(self, mock_print, mock_discover):
        """Test discover command when no exports found."""
        mock_discover.return_value = ([], [])
        
        result = discover_command('./test/exports')
        
        assert result == 1
        
        # Check that "not found" message was printed
        print_calls = [str(call.args[0]) if call.args else '' for call in mock_print.call_args_list]
        not_found_messages = [msg for msg in print_calls if 'No conversation exports found' in msg]
        assert len(not_found_messages) > 0
    
    @patch('conversation_tagger.cli.main.discover_and_configure')
    @patch('builtins.print')
    def test_discover_command_error(self, mock_print, mock_discover):
        """Test discover command with error."""
        mock_discover.side_effect = Exception("Test error")
        
        result = discover_command('./test/exports')
        
        assert result == 1
    
    @patch('conversation_tagger.cli.main.discover_and_configure')
    @patch('conversation_tagger.cli.main.BatchProcessor')
    @patch('builtins.print')
    def test_process_command_success(self, mock_print, mock_batch_processor_class, mock_discover):
        """Test successful process command."""
        # Mock discovery
        mock_config = MagicMock()
        mock_config.name = 'oai'
        mock_config.parser_type = 'oai'
        mock_config.root_path = '/test/path'
        
        mock_discovery = {
            'source_type': 'oai',
            'conversations_count': 3
        }
        
        mock_discover.return_value = ([mock_config], [mock_discovery])
        
        # Mock batch processor
        mock_processor = MagicMock()
        mock_results = {
            'total_generated': 3,
            'results_by_source': {
                'oai': {
                    'filtered_count': 3,
                    'generated_count': 3
                }
            }
        }
        mock_processor.process_all.return_value = mock_results
        mock_batch_processor_class.return_value = mock_processor
        
        with patch.dict('os.environ', {}, clear=True):
            result = process_command(
                exports_dir='./test/exports',
                output_dir='./test/output',
                source_type=None,
                template='test.jinja',
                no_notes=False,
                cleanup=False
            )
        
        assert result == 0
        mock_discover.assert_called_once_with('./test/exports')
        mock_batch_processor_class.assert_called_once()
        mock_processor.process_all.assert_called_once()
    
    @patch('conversation_tagger.cli.main.discover_and_configure')
    @patch('builtins.print')
    def test_process_command_no_exports(self, mock_print, mock_discover):
        """Test process command when no exports found."""
        mock_discover.return_value = ([], [])
        
        result = process_command(
            exports_dir='./test/exports',
            output_dir='./test/output',
            source_type=None,
            template='test.jinja',
            no_notes=False,
            cleanup=False
        )
        
        assert result == 1
    
    @patch('conversation_tagger.cli.main.discover_and_configure')
    @patch('builtins.print')
    def test_process_command_source_type_filter(self, mock_print, mock_discover):
        """Test process command with source type filtering."""
        # Create configs for both OAI and Claude
        mock_config_oai = MagicMock()
        mock_config_oai.name = 'oai'
        mock_config_oai.parser_type = 'oai'
        mock_config_oai.root_path = '/path/to/oai'
        
        mock_config_claude = MagicMock()
        mock_config_claude.name = 'claude'
        mock_config_claude.parser_type = 'claude'
        mock_config_claude.root_path = '/path/to/claude'
        
        mock_discovery_oai = {'source_type': 'oai', 'conversations_count': 2}
        mock_discovery_claude = {'source_type': 'claude', 'conversations_count': 3}
        
        mock_discover.return_value = (
            [mock_config_oai, mock_config_claude],
            [mock_discovery_oai, mock_discovery_claude]
        )
        
        # Test filtering for OAI only
        with patch('conversation_tagger.cli.main.BatchProcessor') as mock_batch_processor_class:
            mock_processor = MagicMock()
            mock_processor.process_all.return_value = {
                'total_generated': 0,
                'results_by_source': {}
            }
            mock_batch_processor_class.return_value = mock_processor
            
            with patch.dict('os.environ', {}, clear=True):
                result = process_command(
                    exports_dir='./test/exports',
                    output_dir='./test/output',
                    source_type='oai',
                    template='test.jinja',
                    no_notes=False,
                    cleanup=False
                )
        
        # Should succeed and only process OAI
        assert result == 0


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    @patch('sys.argv', ['chat2obs', 'setup'])
    @patch('conversation_tagger.cli.main.setup_command')
    def test_main_setup(self, mock_setup):
        """Test main function with setup command."""
        from conversation_tagger.cli.main import main
        
        with patch('sys.stderr', new_callable=StringIO):
            result = main()
        
        assert result == 0
        mock_setup.assert_called_once()
    
    @patch('sys.argv', ['chat2obs'])
    def test_main_no_command(self):
        """Test main function without command."""
        from conversation_tagger.cli.main import main
        
        with patch('sys.stderr', new_callable=StringIO):
            result = main()
        
        assert result == 1
