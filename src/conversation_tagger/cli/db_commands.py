# conversation_tagger/cli/db_commands.py
"""
Database-backed CLI commands for incremental conversation processing.
"""

import argparse
from pathlib import Path
from typing import List, Dict, Any

from ..db.manager import DatabaseManager
from ..db.tagging import DatabaseTagger, DatabaseBatchProcessor
from ..db.queries import ConversationQuery, QueryFilter
from ..data.loaders import ConversationLoader
from .discovery import discover_and_configure


def add_db_commands(subparsers):
    """Add database commands to CLI."""
    
    # DB process command (replaces regular process when --incremental is used)
    db_process = subparsers.add_parser('db-process', help='Database-backed incremental processing')
    db_process.add_argument('--db-path', default='conversations.db', help='Database path')
    db_process.add_argument('--exports-dir', default='./data/exports', help='Exports directory')
    db_process.add_argument('--output-dir', default='./data/notes', help='Output directory')
    db_process.add_argument('--source-type', choices=['oai', 'claude'], help='Filter by source')
    db_process.add_argument('--no-notes', action='store_true', help='Skip note generation')
    db_process.add_argument('--force-retag', action='store_true', help='Force re-tagging')
    
    # Query command
    db_query = subparsers.add_parser('query', help='Query conversation database')
    db_query.add_argument('--db-path', default='conversations.db', help='Database path')
    db_query.add_argument('--has-annotation', help='Filter by annotation name')
    db_query.add_argument('--source', choices=['oai', 'claude'], help='Filter by source')
    db_query.add_argument('--min-exchanges', type=int, help='Minimum exchanges')
    db_query.add_argument('--max-exchanges', type=int, help='Maximum exchanges')
    db_query.add_argument('--processed-only', action='store_true', help='Only processed')
    db_query.add_argument('--unprocessed-only', action='store_true', help='Only unprocessed')
    db_query.add_argument('--limit', type=int, default=20, help='Limit results')
    
    # Stats command
    db_stats = subparsers.add_parser('stats', help='Database statistics')
    db_stats.add_argument('--db-path', default='conversations.db', help='Database path')
    
    # Notes command
    db_notes = subparsers.add_parser('notes', help='Generate notes from database')
    db_notes.add_argument('--db-path', default='conversations.db', help='Database path')
    db_notes.add_argument('--has-annotation', help='Filter by annotation')
    db_notes.add_argument('--source', choices=['oai', 'claude'], help='Filter by source')
    db_notes.add_argument('--output-dir', default='./data/notes', help='Output directory')
    db_notes.add_argument('--limit', type=int, default=100, help='Limit conversations')


def handle_db_process_command(args) -> int:
    """Handle database-backed processing command."""
    
    print("🗄️ Starting incremental database processing...")
    
    # Create database manager
    with DatabaseManager(args.db_path) as db:
        batch_processor = DatabaseBatchProcessor(db)
        
        # Discover conversation exports
        print(f"🔍 Discovering exports in {args.exports_dir}")
        discovery_results = discover_and_configure(args.exports_dir)
        
        if not discovery_results['configs']:
            print("❌ No conversation exports found")
            return 1
        
        # Filter by source type if specified
        configs = discovery_results['configs']
        if args.source_type:
            configs = [c for c in configs if c.parser_type == args.source_type]
        
        if not configs:
            print(f"❌ No exports found for source type: {args.source_type}")
            return 1
        
        all_results = {}
        
        for config in configs:
            print(f"\n📁 Processing {config.name} from {config.root_path}")
            
            # Load conversations
            loader = ConversationLoader(config)
            conversations = loader.load_conversations()
            
            if not conversations:
                print(f"  No conversations found")
                continue
                
            print(f"  Found {len(conversations)} conversations")
            
            # Process incrementally
            results = batch_processor.process_export_incrementally(
                conversations,
                config.parser_type,
                auto_tag=True,
                generate_notes=not args.no_notes,
                output_dir=args.output_dir
            )
            
            all_results[config.name] = results
            
            # Print summary
            ing = results['ingestion']
            print(f"  📥 {ing['new_conversations']} new, {ing['updated_conversations']} updated, {ing['unchanged_conversations']} unchanged")
            
            if 'tagging' in results:
                tag = results['tagging']
                print(f"  🏷️  {tag['conversations_tagged']} tagged, {tag['total_annotations']} annotations")
            
            if 'note_generation' in results:
                notes = results['note_generation']
                print(f"  📝 {notes['notes_generated']} notes generated")
        
        # Overall summary
        total_new = sum(r['ingestion']['new_conversations'] for r in all_results.values())
        total_updated = sum(r['ingestion']['updated_conversations'] for r in all_results.values())
        total_tagged = sum(r.get('tagging', {}).get('conversations_tagged', 0) for r in all_results.values())
        
        print(f"\n✅ Processing complete!")
        print(f"   Total: {total_new} new, {total_updated} updated, {total_tagged} tagged")
        
        return 0


def handle_query_command(args) -> int:
    """Handle query command."""
    
    print("🔍 Querying conversation database...")
    
    with DatabaseManager(args.db_path) as db:
        query = ConversationQuery(db)
        
        # Build filter
        filter = QueryFilter(
            has_annotation=args.has_annotation,
            source=args.source,
            min_exchanges=args.min_exchanges,
            max_exchanges=args.max_exchanges,
            processed_only=args.processed_only,
            unprocessed_only=args.unprocessed_only
        )
        
        # Execute query
        conversations = query.find_conversations(filter, limit=args.limit)
        
        print(f"\nFound {len(conversations)} conversations:")
        print("-" * 80)
        
        for conv in conversations:
            # Get annotations
            annotations = db.get_annotations_for_conversation(conv.conversation_id)
            annotation_names = [a.annotation_name for a in annotations]
            
            print(f"ID: {conv.conversation_id[:12]}... | {conv.source.upper()}")
            print(f"Title: {conv.title[:60]}{'...' if len(conv.title) > 60 else ''}")
            print(f"Stats: {conv.exchange_count} exchanges, {conv.total_message_count} messages")
            print(f"Status: {'✅ Processed' if conv.processed_at else '⏳ Unprocessed'}")
            
            if annotation_names:
                tags_display = ', '.join(annotation_names[:8])
                if len(annotation_names) > 8:
                    tags_display += f" +{len(annotation_names)-8} more"
                print(f"Tags: {tags_display}")
            
            print("-" * 80)
        
        return 0


def handle_stats_command(args) -> int:
    """Handle stats command."""
    
    print("📊 Database Statistics")
    print("=" * 60)
    
    with DatabaseManager(args.db_path) as db:
        tagger = DatabaseTagger(db)
        query = ConversationQuery(db)
        
        # Database overview
        db_stats = db.get_database_stats()
        print(f"Database: {args.db_path}")
        print(f"  Conversations: {db_stats['conversations']:,}")
        print(f"  Exchanges: {db_stats['exchanges']:,}")
        print(f"  Messages: {db_stats['messages']:,}")
        print(f"  Annotations: {db_stats['annotations']:,}")
        
        # Processing stats by source
        print(f"\nProcessing Status:")
        for source in ['oai', 'claude']:
            stats = tagger.get_tagging_stats(source)
            if stats['total_conversations'] > 0:
                print(f"  {source.upper()}:")
                print(f"    Total: {stats['total_conversations']:,}")
                print(f"    Processed: {stats['processed_conversations']:,} ({stats['processing_percentage']:.1f}%)")
                print(f"    Annotations: {stats['total_annotations']:,} ({stats['unique_annotation_types']} types)")
        
        # Top annotations
        print(f"\nTop Annotations:")
        top_annotations = query.get_top_annotations(limit=15)
        for ann in top_annotations:
            print(f"  {ann['name']:<25} {ann['unique_conversations']:>6} convs ({ann['percentage']:>5.1f}%)")
        
        return 0


def handle_notes_command(args) -> int:
    """Handle notes generation command."""
    
    print("📝 Generating notes from database...")
    
    with DatabaseManager(args.db_path) as db:
        tagger = DatabaseTagger(db)
        
        # Build filter
        filter = QueryFilter(
            has_annotation=args.has_annotation,
            source=args.source,
            processed_only=True  # Only generate notes for processed conversations
        )
        
        # Generate notes
        stats = tagger.generate_notes_for_query(
            filter,
            output_dir=args.output_dir,
            limit=args.limit
        )
        
        print(f"✅ Note generation complete!")
        print(f"   Files created: {stats['notes_generated']}")
        print(f"   Conversations processed: {stats['conversations_processed']}")
        print(f"   Output directory: {args.output_dir}")
        
        return 0


# Command dispatch table
DB_COMMANDS = {
    'db-process': handle_db_process_command,
    'query': handle_query_command,
    'stats': handle_stats_command,
    'notes': handle_notes_command,
}
