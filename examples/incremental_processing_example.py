#!/usr/bin/env python3
"""
Example: Database-backed incremental conversation processing

This example demonstrates the new incremental processing capabilities that:
1. Only processes new/changed conversations
2. Stores everything in a SQLite database 
3. Generates Obsidian notes efficiently
4. Avoids reprocessing entire exports repeatedly

Usage:
    python examples/incremental_processing_example.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from conversation_tagger.db import DatabaseManager, IncrementalIngester
from conversation_tagger.db.tagging import DatabaseTagger, DatabaseBatchProcessor
from conversation_tagger.db.queries import ConversationQuery, QueryFilter
from conversation_tagger.data.loaders import ConversationLoader
from conversation_tagger.data.config import get_default_config


def basic_incremental_example():
    """Basic example of incremental processing."""
    
    print("🗄️ Database-backed Incremental Processing Example")
    print("=" * 60)
    
    # Create database (in memory for demo)
    with DatabaseManager(':memory:') as db:
        # Create database batch processor  
        processor = DatabaseBatchProcessor(db)
        
        print("1. Loading sample conversation data...")
        
        # Load some conversations (would normally come from exports)
        try:
            config = get_default_config('oai')
            loader = ConversationLoader(config)
            conversations = loader.load_conversations()[:5]  # Just first 5 for demo
            
            if not conversations:
                print("   No conversations found - using mock data")
                conversations = create_mock_conversations()
            
        except Exception:
            print("   Using mock data for demonstration")
            conversations = create_mock_conversations()
        
        print(f"   Loaded {len(conversations)} conversations")
        
        print("\n2. First ingestion (all conversations are new)...")
        
        # First ingestion - everything is new
        results1 = processor.process_export_incrementally(
            conversations,
            'oai',
            auto_tag=True,
            generate_notes=False  # Skip notes for demo
        )
        
        ing1 = results1['ingestion']
        tag1 = results1['tagging']
        print(f"   📥 {ing1['new_conversations']} new, {ing1['updated_conversations']} updated")
        print(f"   🏷️  {tag1['conversations_tagged']} tagged, {tag1['total_annotations']} annotations")
        
        print("\n3. Second ingestion (no changes - should be fast)...")
        
        # Second ingestion - nothing should change
        results2 = processor.process_export_incrementally(
            conversations,
            'oai',
            auto_tag=True,
            generate_notes=False
        )
        
        ing2 = results2['ingestion']
        print(f"   📥 {ing2['new_conversations']} new, {ing2['updated_conversations']} updated, {ing2['unchanged_conversations']} unchanged")
        print("   ✅ No reprocessing needed!")
        
        print("\n4. Database statistics...")
        
        # Show database stats
        tagger = DatabaseTagger(db)
        stats = tagger.get_tagging_stats('oai')
        
        print(f"   Total conversations: {stats['total_conversations']}")
        print(f"   Processed: {stats['processed_conversations']} ({stats['processing_percentage']}%)")
        print(f"   Annotations: {stats['total_annotations']} ({stats['unique_annotation_types']} types)")
        
        print("\n5. Querying conversations...")
        
        # Query examples
        query = ConversationQuery(db)
        
        # Find conversations with code
        coding_filter = QueryFilter(has_annotation='coding_assistance')
        coding_convs = query.find_conversations(coding_filter, limit=5)
        print(f"   Coding conversations: {len(coding_convs)}")
        
        # Find long conversations
        long_filter = QueryFilter(min_exchanges=3)
        long_convs = query.find_conversations(long_filter, limit=5)
        print(f"   Long conversations (3+ exchanges): {len(long_convs)}")
        
        print("\n✅ Incremental processing demo complete!")
        print("\nKey benefits:")
        print("   • Only new/changed conversations are processed")
        print("   • Database provides fast querying and analysis")  
        print("   • Obsidian notes generated efficiently")
        print("   • Perfect for large conversation archives")


def create_mock_conversations():
    """Create mock conversation data for demonstration."""
    
    import time
    current_time = time.time()
    
    return [
        {
            'conversation_id': 'demo-conv-1',
            'title': 'Python Function Help',
            'mapping': {
                'msg1': {
                    'message': {
                        'id': 'msg1',
                        'author': {'role': 'user'},
                        'content': {'text': 'Can you help me write a Python function?'},
                        'create_time': current_time - 1000
                    }
                },
                'msg2': {
                    'message': {
                        'id': 'msg2', 
                        'author': {'role': 'assistant'},
                        'content': {'text': 'Sure! Here\'s a function:\n\n```python\ndef hello(name):\n    return f"Hello, {name}!"\n```'},
                        'create_time': current_time - 900
                    }
                }
            }
        },
        {
            'conversation_id': 'demo-conv-2',
            'title': 'JavaScript Question',
            'mapping': {
                'msg1': {
                    'message': {
                        'id': 'msg1',
                        'author': {'role': 'user'},
                        'content': {'text': 'How do I use async/await in JavaScript?'},
                        'create_time': current_time - 800
                    }
                },
                'msg2': {
                    'message': {
                        'id': 'msg2',
                        'author': {'role': 'assistant'},
                        'content': {'text': 'Async/await is used for handling promises:\n\n```javascript\nasync function fetchData() {\n  const response = await fetch(\'/api/data\');\n  return response.json();\n}\n```'},
                        'create_time': current_time - 700
                    }
                }
            }
        },
        {
            'conversation_id': 'demo-conv-3',
            'title': 'Recipe Request',
            'mapping': {
                'msg1': {
                    'message': {
                        'id': 'msg1',
                        'author': {'role': 'user'},
                        'content': {'text': 'Can you suggest a simple pasta recipe?'},
                        'create_time': current_time - 600
                    }
                },
                'msg2': {
                    'message': {
                        'id': 'msg2',
                        'author': {'role': 'assistant'},
                        'content': {'text': 'Here\'s a simple spaghetti aglio e olio recipe:\n\n1. Cook spaghetti in salted water\n2. Heat olive oil with sliced garlic\n3. Add red pepper flakes\n4. Toss with pasta and parsley'},
                        'create_time': current_time - 500
                    }
                }
            }
        }
    ]


if __name__ == '__main__':
    basic_incremental_example()
