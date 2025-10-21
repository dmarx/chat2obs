# Database-Backed Incremental Processing Architecture

## Overview

This system provides incremental processing of conversation exports from ChatGPT and Claude, solving the major performance issue of reprocessing entire archives repeatedly. The architecture stores conversations in a SQLite database and only processes new or changed conversations.

## Key Features

### ✅ Incremental Processing
- **Diff Detection**: Automatically detects new/changed conversations based on timestamps
- **Fast Re-runs**: Second processing of same export processes 0 conversations (as shown in demo)
- **Scalable**: Handles large conversation archives efficiently

### ✅ Database Storage
- **SQLite Backend**: No setup required, single file database
- **Rich Schema**: Conversations → Exchanges → Messages with full annotation support
- **Fast Queries**: Indexed for efficient filtering and analysis

### ✅ Powerful CLI
```bash
# Incremental processing (recommended for large exports)
chat2obs db-process --exports-dir ~/Downloads/conversations

# Query conversations 
chat2obs query --has-annotation coding_assistance --limit 10

# Database statistics
chat2obs stats

# Generate notes from database
chat2obs notes --has-annotation gizmo --output-dir ./notes
```

### ✅ Backward Compatibility
- All existing processing still works
- Original CLI commands unchanged
- Same Obsidian markdown output

## Architecture Components

### Database Layer (`src/conversation_tagger/db/`)

#### Models (`models.py`)
- **ConversationDB**: Conversation metadata and annotations
- **ExchangeDB**: Exchange-level data and annotations  
- **MessageDB**: Individual messages with content
- **AnnotationDB**: Searchable denormalized annotations

#### Manager (`manager.py`)
- **DatabaseManager**: SQLite connection and CRUD operations
- Handles schema creation and migrations
- Provides transaction management

#### Ingestion (`ingestion.py`)
- **IncrementalIngester**: Detects changes and processes only deltas
- **DatabaseToObjectConverter**: Converts DB records back to objects
- **MockMessage**: For loading database messages back into processing

#### Tagging (`tagging.py`)
- **DatabaseTagger**: Database-backed tagging engine
- **BatchProcessor**: End-to-end incremental pipeline
- Operates on database records, updates annotations

#### Queries (`queries.py`)
- **ConversationQuery**: Efficient querying interface
- **QueryFilter**: Rich filtering capabilities
- Supports faceting and statistical analysis

## Usage Examples

### Basic Incremental Processing
```python
from conversation_tagger.db import DatabaseManager
from conversation_tagger.db.tagging import BatchProcessor

with DatabaseManager('conversations.db') as db:
    processor = BatchProcessor(db)
    
    # Process export incrementally
    results = processor.process_export_incrementally(
        conversations,
        'oai',
        auto_tag=True,
        generate_notes=True,
        output_dir='./notes'
    )
    
    print(f"New: {results['ingestion']['new_conversations']}")
    print(f"Updated: {results['ingestion']['updated_conversations']}")
    print(f"Tagged: {results['tagging']['conversations_tagged']}")
```

### Querying and Analysis
```python
from conversation_tagger.db.queries import ConversationQuery, QueryFilter

with DatabaseManager('conversations.db') as db:
    query = ConversationQuery(db)
    
    # Find coding conversations
    coding_filter = QueryFilter(has_annotation='coding_assistance')
    coding_convs = query.find_conversations(coding_filter)
    
    # Get annotation statistics
    stats = query.get_annotation_stats('gizmo')
    
    # Facet by conversation length
    facets = query.facet_conversations('conversation_length', 'category')
```

### CLI Usage
```bash
# Process exports incrementally  
chat2obs db-process --exports-dir ./data/exports --output-dir ./notes

# Query specific conversations
chat2obs query --has-annotation gizmo --source oai --limit 20

# View processing statistics
chat2obs stats

# Generate notes for subset
chat2obs notes --has-annotation coding_assistance --limit 50
```

## Performance Benefits

### Demo Results
- **First run**: 3 conversations → 3 processed, 14 annotations
- **Second run**: 3 conversations → 0 processed, 0 new work 
- **Query time**: Instant filtering and analysis
- **Database size**: Minimal overhead, efficient storage

### Real-world Impact
- **Large Archives**: Process 1000s of conversations efficiently
- **Repeat Processing**: Near-instant re-runs when no changes
- **Rich Analysis**: Complex queries without reprocessing
- **Obsidian Integration**: Generate notes on-demand from database

## Migration Path

### Existing Users  
1. Keep using original CLI commands (`chat2obs process`)
2. Try incremental processing (`chat2obs db-process`) 
3. Migrate to database-backed workflow when ready

### New Users
- Start with `chat2obs db-process` for best performance
- Use database CLI commands for analysis
- Original commands available as fallback

## Database Schema

```sql
-- Core hierarchy
conversations(conversation_id, source, title, ...)
├── exchanges(exchange_id, conversation_id, sequence_number, ...)
    ├── messages(message_id, exchange_id, author_role, content, ...)
    
-- Searchable annotations (denormalized for performance)
annotations(conversation_id, exchange_id, annotation_name, annotation_value, ...)
```

## Future Enhancements

- **PostgreSQL Support**: For multi-user scenarios
- **Web Interface**: Browser-based conversation exploration  
- **Export Sync**: Watch folders for automatic processing
- **Advanced Analytics**: ML-powered conversation insights

---

This architecture maintains the simplicity of the original system while adding enterprise-grade incremental processing capabilities. Perfect for users with large conversation archives who want efficient, repeatable processing workflows.
