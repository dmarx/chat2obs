# conversation_tagger/cli/main.py
"""
Main CLI interface for conversation processing.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

from .discovery import discover_and_configure
from ..processing.pipeline import ProcessingConfig, BatchProcessor
from ..processing.filters import FilterCriteria


def create_cli_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog='chat2obs',
        description='Process conversation exports from ChatGPT and Claude',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all exports in default directory (./data/exports/)
  chat2obs process
  
  # Process exports from custom directory
  chat2obs process --exports-dir ~/Downloads/conversations
  
  # Process with custom output directory
  chat2obs process --output-dir ./notes
  
  # Process only ChatGPT conversations
  chat2obs process --source-type oai
  
  # Discovery mode - just show what would be processed
  chat2obs discover --exports-dir ./my-exports
  
Directory Structure:
  ./data/exports/          # Drop your export files here
  ├── chatgpt-export.zip   # ChatGPT export archive
  ├── claude-data/         # Claude export directory
  │   └── conversations.json
  └── conversations.json   # Direct conversation file
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process conversation exports')
    process_parser.add_argument(
        '--exports-dir', 
        default='./data/exports',
        help='Directory containing conversation exports (default: ./data/exports)'
    )
    process_parser.add_argument(
        '--output-dir',
        default='./data/notes', 
        help='Output directory for generated notes (default: ./data/notes)'
    )
    process_parser.add_argument(
        '--source-type',
        choices=['oai', 'claude', 'chatgpt'],
        help='Only process specific source type (default: process all)'
    )
    process_parser.add_argument(
        '--template',
        default='article_body.md.jinja',
        help='Template file to use for note generation (default: article_body.md.jinja)'
    )
    process_parser.add_argument(
        '--no-notes',
        action='store_true',
        help='Skip note generation, only tag conversations'
    )
    process_parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up extracted archive files after processing'
    )
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover conversation exports')
    discover_parser.add_argument(
        '--exports-dir',
        default='./data/exports',
        help='Directory containing conversation exports (default: ./data/exports)'
    )
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup directories and show usage')
    
    return parser


def setup_command():
    """Setup directories and show usage information."""
    exports_dir = Path('./data/exports')
    output_dir = Path('./data/notes')
    
    exports_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 chat2obs setup complete!")
    print()
    print("📁 Directories created:")
    print(f"   Exports: {exports_dir.absolute()}")
    print(f"   Output:  {output_dir.absolute()}")
    print()
    print("💡 Usage:")
    print("1. Drop your ChatGPT or Claude export files in the exports directory:")
    print(f"   - ChatGPT: Save .zip export to {exports_dir}/")
    print(f"   - Claude: Extract and save to {exports_dir}/claude-data/")
    print()
    print("2. Run processing:")
    print("   chat2obs process")
    print()
    print("3. Check generated notes:")
    print(f"   ls {output_dir}/")


def discover_command(exports_dir: str):
    """Discover and show conversation exports."""
    print(f"🔍 Discovering conversation exports in: {exports_dir}")
    print()
    
    try:
        configs, discoveries = discover_and_configure(exports_dir)
        
        if not discoveries:
            print("❌ No conversation exports found!")
            print()
            print("💡 Supported formats:")
            print("   - ChatGPT .zip export files")
            print("   - Claude directories with conversations.json")
            print("   - Direct conversations.json files")
            print()
            print("   Run 'chat2obs setup' to create the directory structure.")
            return 1
        
        print(f"✅ Found {len(discoveries)} conversation export(s):")
        print()
        
        for discovery in discoveries:
            source_type = discovery['source_type'].upper()
            count = discovery['conversations_count']
            path = discovery['source_file']
            
            print(f"📊 {source_type}: {count} conversations")
            print(f"   Source: {path}")
            print(f"   Type: {discovery['type']}")
            print()
        
        print("🚀 Ready to process! Run:")
        print(f"   chat2obs process --exports-dir {exports_dir}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        print(f"❌ Discovery failed: {e}")
        return 1


def process_command(exports_dir: str, output_dir: str, source_type: Optional[str], 
                   template: str, no_notes: bool, cleanup: bool):
    """Process conversation exports."""
    print(f"🚀 Processing conversation exports...")
    print(f"   Exports: {exports_dir}")
    print(f"   Output:  {output_dir}")
    print()
    
    try:
        # Discover exports
        configs, discoveries = discover_and_configure(exports_dir)
        
        if not discoveries:
            print("❌ No conversation exports found!")
            print("   Run 'chat2obs discover' to see supported formats.")
            return 1
        
        # Filter by source type if specified
        if source_type:
            # Handle aliases
            if source_type == 'chatgpt':
                source_type = 'oai'
            
            configs = [c for c in configs if c.parser_type == source_type]
            discoveries = [d for d in discoveries if d['source_type'] == source_type]
            
            if not configs:
                print(f"❌ No {source_type.upper()} exports found!")
                return 1
        
        # Show what will be processed
        print("📊 Processing:")
        for discovery in discoveries:
            source_type_display = discovery['source_type'].upper()
            count = discovery['conversations_count']
            print(f"   {source_type_display}: {count} conversations")
        print()
        
        # Create processing configuration with discovered configs
        from ..data.loaders import ConversationLoader
        from ..processing.pipeline import ProcessingPipeline
        
        # Override the default configs by patching the config system
        import os
        config_overrides = {}
        for config in configs:
            env_var = f"CHAT2OBS_{config.parser_type.upper()}_ROOT"
            os.environ[env_var] = config.root_path
            config_overrides[config.name] = config
        
        # Monkey patch the config system temporarily
        original_get_config = None
        try:
            from .. import data
            original_get_config = data.config.get_config_for_source
            
            def patched_get_config(source_name):
                if source_name in config_overrides:
                    return config_overrides[source_name]
                return original_get_config(source_name)
            
            data.config.get_config_for_source = patched_get_config
            
            # Also patch in the loaders module
            from ..data import loaders
            loaders.get_config_for_source = patched_get_config
            
            source_names = [config.name for config in configs]
            processing_config = ProcessingConfig(
                sources=source_names,
                output_dir=output_dir,
                generate_notes_enabled=not no_notes,
                template_name=template
            )
        
            # Process conversations
            processor = BatchProcessor(processing_config)
            results = processor.process_all()
            
        finally:
            # Restore original config function
            if original_get_config:
                data.config.get_config_for_source = original_get_config
                loaders.get_config_for_source = original_get_config
        
        # Show results
        print("✅ Processing complete!")
        print()
        print("📈 Results:")
        for source, result in results['results_by_source'].items():
            if 'error' in result:
                print(f"   {source.upper()}: ❌ Error - {result['error']}")
            else:
                filtered = result['filtered_count']
                generated = result['generated_count']
                print(f"   {source.upper()}: {filtered} conversations → {generated} notes")
        
        total_generated = results['total_generated']
        print()
        print(f"🎉 Generated {total_generated} total notes in {output_dir}")
        
        # Cleanup if requested
        if cleanup:
            from .discovery import ExportDiscovery
            discovery_obj = ExportDiscovery(exports_dir)
            discovery_obj.cleanup_extracted()
        
        return 0
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(f"❌ Processing failed: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level="INFO",
        format="<level>{level}</level>: {message}",
        colorize=True
    )
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'setup':
        setup_command()
        return 0
    
    elif args.command == 'discover':
        return discover_command(args.exports_dir)
    
    elif args.command == 'process':
        return process_command(
            exports_dir=args.exports_dir,
            output_dir=args.output_dir,
            source_type=args.source_type,
            template=args.template,
            no_notes=args.no_notes,
            cleanup=args.cleanup
        )
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
