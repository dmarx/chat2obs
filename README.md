# chat2obs

Process ChatGPT and Claude conversation exports into Obsidian-compatible markdown notes with intelligent tagging and incremental database storage.

## Features

### 🚀 Database-Backed Incremental Processing
- **SQLite storage** with automatic diff detection
- **Only processes new/changed conversations** (massive performance improvement)
- **Rich querying** without reprocessing data
- **Perfect for large conversation archives**

### 📝 Obsidian Integration  
- Generates clean markdown files compatible with Obsidian
- Intelligent conversation tagging and categorization
- Customizable templates for note generation

### 🔍 Advanced Analysis
- Automatic detection of coding assistance, research sessions, multi-turn conversations
- Support for gizmos, plugins, and enhanced conversation features
- Powerful filtering and faceting capabilities

## Quick Start

### Installation
```bash
git clone https://github.com/dmarx/chat2obs.git
cd chat2obs
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Basic Usage

```bash
# Drop your ChatGPT/Claude exports in ./data/exports/
mkdir -p data/exports
# Copy your conversation exports here

# Process incrementally (only new/changed conversations)
chat2obs process --exports-dir ./data/exports --output-dir ./notes

# Query conversations
chat2obs query --has-annotation coding_assistance --limit 10

# Show database statistics
chat2obs stats

# Generate notes for specific conversations
chat2obs notes --has-annotation gizmo --output-dir ./gizmo-notes
```

## Commands

- `chat2obs process` - Process exports incrementally using database
- `chat2obs query` - Query conversations by annotations, source, etc.
- `chat2obs stats` - Show database and processing statistics
- `chat2obs notes` - Generate Obsidian notes for filtered conversations

## Performance Benefits

- **First Run**: Processes all conversations and stores in database
- **Subsequent Runs**: Only processes new/changed conversations (~100x faster)
- **Querying**: Instant queries without reprocessing data
- **Scalability**: Handles thousands of conversations efficiently

## Supported Export Formats

### ChatGPT/OpenAI
- ZIP archives from ChatGPT export
- Direct `conversations.json` files
- Supports gizmos, plugins, code execution, attachments

### Claude/Anthropic  
- Export directories with `conversations.json`
- Direct conversation JSON files
- Supports Claude-specific features and metadata

## Directory Structure
```
./
├── data/
│   ├── exports/          # Drop your export files here
│   │   ├── chatgpt-export.zip
│   │   ├── claude-data/conversations.json
│   │   └── conversations.json
│   └── notes/           # Generated Obsidian notes
├── conversations.db     # SQLite database (auto-created)
└── examples/           # Usage examples
```

## Database Architecture

Uses SQLite with this schema for fast incremental processing:

```
conversations → exchanges → messages
               ↓
            annotations (searchable)
```

- **conversations**: High-level metadata, processing status, change detection
- **exchanges**: User-assistant interaction pairs with timestamps
- **messages**: Individual messages with content and metadata
- **annotations**: Denormalized tags for instant querying and filtering

## Examples

### Python API
```python
# Database-backed processing
from conversation_tagger import DatabaseManager, DatabaseBatchProcessor

with DatabaseManager('conversations.db') as db:
    processor = DatabaseBatchProcessor(db)
    results = processor.process_export_incrementally(
        conversations, 'oai', auto_tag=True, generate_notes=True
    )

# Query conversations
from conversation_tagger.db.queries import ConversationQuery, QueryFilter

query = ConversationQuery(db)
coding_convs = query.query_conversations(
    QueryFilter(has_annotation='coding_assistance')
)
```

### CLI Examples
```bash
# Process new exports incrementally
chat2obs process --exports-dir ~/Downloads/conversations

# Find conversations with specific features
chat2obs query --has-annotation gizmo --source oai --limit 20

# Generate notes for coding conversations only
chat2obs notes --has-annotation coding_assistance --output-dir ./coding-notes

# Show processing statistics
chat2obs stats
```

## Migration from Notebooks

If you were previously using the Jupyter notebooks directly:

**Old approach (notebooks):**
```python
# Manual processing in notebooks - now replaced
convs = load_convs('oai')  
tagger = create_default_tagger('oai')
tagged = [tagger.tag_conversation(c) for c in convs]
generate_notes(tagged_results, output_dir="data/staging")
```

**New approach (database-backed):**
```bash
# Simple CLI with incremental processing
chat2obs process --exports-dir ./data/exports --output-dir ./notes
```

## Development

### Running Tests
```bash
python -m pytest tests/ -v
```

### Examples
- `examples/incremental_processing_example.py` - Database-backed processing workflow

## Requirements

- Python 3.8+
- SQLite (included with Python)
- Dependencies: `loguru`, `jinja2`, `python-frontmatter`, `genson`

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]