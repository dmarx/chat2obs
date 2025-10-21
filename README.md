# chat2obs

Process ChatGPT and Claude conversation exports into Obsidian-compatible markdown notes with intelligent tagging and analysis.

## Features

### 🚀 Incremental Processing (Recommended)
- **Database-backed storage** with automatic diff detection
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
- Flexible filtering and faceting capabilities

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

#### Incremental Processing (Recommended)
```bash
# Drop your ChatGPT/Claude exports in ./data/exports/
mkdir -p data/exports
# Copy your conversation exports here

# Process incrementally (only new/changed conversations)
chat2obs db-process --exports-dir ./data/exports --output-dir ./notes

# Query conversations
chat2obs query --has-annotation coding_assistance --limit 10
chat2obs stats
```

#### Traditional Processing (Legacy)
```bash
# One-time processing (processes everything each time)
chat2obs process --exports-dir ./data/exports --output-dir ./notes
```

## Commands

### Incremental Processing Commands
- `chat2obs db-process` - Process exports incrementally using database
- `chat2obs query` - Query conversations by annotations, source, etc.
- `chat2obs stats` - Show database and processing statistics
- `chat2obs notes` - Generate Obsidian notes for filtered conversations

### Traditional Commands
- `chat2obs process` - Process all exports (legacy, slower)
- `chat2obs discover` - Show what exports were found
- `chat2obs setup` - Create directory structure and show usage

## Performance Comparison

| Approach | First Run | Second Run (No Changes) | Querying |
|----------|-----------|-------------------------|----------|
| **Incremental** | Normal | ~0 conversations processed | Instant |
| **Traditional** | Normal | Full reprocessing | Requires reprocessing |

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

The incremental processing system uses SQLite with this schema:

```
conversations → exchanges → messages
               ↓
            annotations (searchable)
```

- **conversations**: High-level metadata, processing status
- **exchanges**: User-assistant interaction pairs  
- **messages**: Individual messages with content
- **annotations**: Denormalized tags for fast querying

## Examples

### Python API
```python
# Incremental processing
from conversation_tagger import DatabaseManager, DatabaseBatchProcessor

with DatabaseManager('conversations.db') as db:
    processor = DatabaseBatchProcessor(db)
    results = processor.process_export_incrementally(
        conversations, 'oai', auto_tag=True, generate_notes=True
    )

# Query conversations
from conversation_tagger.db.queries import ConversationQuery, QueryFilter

query = ConversationQuery(db)
coding_convs = query.find_conversations(
    QueryFilter(has_annotation='coding_assistance')
)
```

### CLI Examples
```bash
# Process new exports incrementally
chat2obs db-process --exports-dir ~/Downloads/conversations

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
# Manual processing in notebooks
convs = load_convs('oai')  
tagger = create_default_tagger('oai')
tagged = [tagger.tag_conversation(c) for c in convs]
generate_notes(tagged_results, output_dir="data/staging")
```

**New approach (incremental):**
```bash
# Just use the CLI
chat2obs db-process --exports-dir ./data/exports --output-dir ./notes
```

## Development

### Running Tests
```bash
python -m pytest tests/ -v
```

### Examples
- `examples/incremental_processing_example.py` - Database-backed processing
- `examples/legacy_processing_example.py` - Traditional file-based processing

## Requirements

- Python 3.8+
- SQLite (included with Python)
- Dependencies: `loguru`, `jinja2`, `python-frontmatter`, `genson`

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]