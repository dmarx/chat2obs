# conversation_tagger/cli/main.py
"""
Main CLI interface for database-backed conversation processing.
"""

import argparse
import sys
from typing import Optional
from loguru import logger

from .discovery import discover_and_configure
from .db_commands import add_db_commands, DB_COMMANDS


def create_cli_parser() -> argparse.ArgumentParser:
    """Create the main CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog='chat2obs',
        description='Process conversation exports from ChatGPT and Claude using database-backed incremental processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process exports incrementally (only new/changed conversations)
  chat2obs process --exports-dir ./data/exports --output-dir ./notes
  
  # Process only ChatGPT conversations
  chat2obs process --source-type oai
  
  # Query conversations by annotations
  chat2obs query --has-annotation coding_assistance --limit 10
  
  # Generate notes for filtered conversations
  chat2obs notes --has-annotation gizmo --output-dir ./gizmo-notes
  
  # Show database statistics
  chat2obs stats
  
Directory Structure:
  ./data/exports/          # Drop your export files here
  ├── chatgpt-export.zip   # ChatGPT export archive
  ├── claude-data/         # Claude export directory
  │   └── conversations.json
  └── conversations.json   # Direct conversation file
  
  ./conversations.db       # SQLite database (auto-created)
        """)
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command (database-backed incremental processing)
    process_parser = subparsers.add_parser('process', help='Process conversation exports incrementally')
    process_parser.add_argument('--db-path', default='conversations.db', help='Database path')
    process_parser.add_argument('--exports-dir', default='./data/exports', help='Exports directory')
    process_parser.add_argument('--output-dir', default='./data/notes', help='Output directory')
    process_parser.add_argument('--source-type', choices=['oai', 'claude'], help='Filter by source')
    process_parser.add_argument('--no-notes', action='store_true', help='Skip note generation')
    process_parser.add_argument('--force-retag', action='store_true', help='Force re-tagging')
    
    # Add database commands (query, stats, notes)
    add_db_commands(subparsers)
    
    return parser


def handle_process_command(args) -> int:
    """Handle the main process command using database-backed incremental processing."""
    print("🗄️ Starting incremental database processing...")

    from ..db.manager import DatabaseManager
    from ..db.tagging import DatabaseBatchProcessor
    import json
    from pathlib import Path

    # Create database manager
    with DatabaseManager(args.db_path) as db:
        batch_processor = DatabaseBatchProcessor(db)

        # Discover conversation exports
        print(f"🔍 Discovering exports in {args.exports_dir}")
        discovery_results = discover_and_configure(args.exports_dir)

        if not discovery_results:
            print("❌ No conversation exports found!")
            print("   Ensure your exports are in the specified directory and correctly formatted.")
            return 1

        all_results = {}

        for discovery in discovery_results:
            config = discovery['config']
            
            if not Path(config.root_path).exists():
                print(f"⚠️  Skipping {config.name}: path not found - {config.root_path}")
                continue

            # Filter by source type if specified
            if args.source_type and config.parser_type != args.source_type:
                print(f"  Skipping {config.name} (source type filter: {args.source_type})")
                continue

            print(f"\n📁 Processing {config.name} from {config.root_path}")

            # Load conversations directly from JSON
            conversations_file = Path(config.root_path) / "conversations.json"
            try:
                with open(conversations_file, 'r', encoding='utf-8') as f:
                    conversations = json.load(f)
            except Exception as e:
                print(f"  ❌ Error loading conversations: {e}")
                continue

            if not conversations:
                print(f"  No conversations found in {conversations_file}")
                continue

            print(f"  Found {len(conversations)} conversations")

            # Process with incremental pipeline
            results = batch_processor.process_export_incrementally(
                conversations,
                config.parser_type,
                auto_tag=True,
                generate_notes=not args.no_notes,
                output_dir=args.output_dir,
                force_retag=args.force_retag
            )

            all_results[config.name] = results

            # Print results
            ing_stats = results['ingestion']
            tag_stats = results['tagging']
            note_stats = results['note_generation']

            print(f"  📥 Ingestion: {ing_stats['new_conversations']} new, {ing_stats['updated_conversations']} updated, {ing_stats['unchanged_conversations']} unchanged")
            print(f"  🏷️  Tagging: {tag_stats.get('conversations_tagged', 0)} tagged, {tag_stats.get('annotations_added', 0)} annotations")
            print(f"  📝 Notes: {note_stats.get('notes_generated', 0)} generated")

        print("\n✅ Incremental processing complete!")
        return 0


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
    
    if args.command == 'process':
        return handle_process_command(args)
    
    elif args.command in DB_COMMANDS:
        # Handle database commands
        return DB_COMMANDS[args.command](args)
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())