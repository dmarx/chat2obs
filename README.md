# LLM Archive

Ingest, normalize, and analyze LLM conversation exports for downstream processing.

## Features

- **Multi-source ingestion**: ChatGPT and Claude exports
- **Tree analysis**: Full dialogue tree preservation with branch classification
- **Exchange grouping**: Logical interaction units with continuation detection
- **Content hashing**: Deduplication preparation
- **Polymorphic labeling**: Flexible annotation system

## Requirements

- Python 3.11+
- Docker (for PostgreSQL)

## Installation

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -e .

# Or install directly without explicit venv creation
uv pip install -e . --system

# Install with dev dependencies
uv pip install -e ".[dev]"
```

## Database Setup

### Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit if needed (defaults work out of the box)
# vim .env
```

### Start PostgreSQL (pgvector)

```bash
# Start the database (data persists in ./data/postgres/)
docker compose up -d

# Check it's running
docker compose ps

# View logs if needed
docker compose logs -f db
```

The database configuration is read from `.env`:
- **Host**: `POSTGRES_HOST` (default: `localhost`)
- **Port**: `POSTGRES_PORT` (default: `5432`)
- **Database**: `POSTGRES_DB` (default: `llm_archive`)
- **User**: `POSTGRES_USER` (default: `postgres`)
- **Password**: `POSTGRES_PASSWORD` (default: `postgres`)

### Initialize Schema

```bash
uv run llm-archive init --schema_dir=schema
```

### Stop Database

```bash
# Stop but keep data
docker compose down

# Stop and DELETE all data
docker compose down -v
rm -rf data/postgres
```

## Usage

### Import

```bash
# Import ChatGPT export
uv run llm-archive import_chatgpt /path/to/conversations.json

# Import Claude export
uv run llm-archive import_claude /path/to/claude.json

# Import both
uv run llm-archive import_all \
    --chatgpt_path=/path/to/chatgpt.json \
    --claude_path=/path/to/claude.json
```

### Build Derived Structures

```bash
# Build tree analysis
uv run llm-archive build_trees

# Build exchanges
uv run llm-archive build_exchanges

# Build content hashes
uv run llm-archive build_hashes

# Build all
uv run llm-archive build_all
```

### Annotations

```bash
# Run all annotators
uv run llm-archive annotate
```

### Analysis

```bash
# Show statistics
uv run llm-archive stats

# Find duplicates
uv run llm-archive find_duplicates --entity_type=exchange --scope=assistant
```

### Full Pipeline

```bash
# Run everything
uv run llm-archive run \
    --chatgpt_path=/path/to/chatgpt.json \
    --claude_path=/path/to/claude.json \
    --init_db
```

## Idempotent Import

Re-importing the same export files is safe:
- Dialogues are identified by their source ID
- If `updated_at` timestamp is newer, dialogue is updated
- If unchanged, dialogue is skipped
- Messages are replaced when a dialogue is updated

## Schema

### Raw Layer (`raw.*`)

Source of truth from imports:

- `raw.sources` - Registry of dialogue sources
- `raw.dialogues` - Conversations/chats
- `raw.messages` - Individual messages (with tree structure)
- `raw.content_parts` - Message content segments
- `raw.citations` - Source citations
- `raw.attachments` - File attachments
- `raw.chatgpt_*` - ChatGPT-specific extensions
- `raw.claude_*` - Claude-specific extensions

### Derived Layer (`derived.*`)

Computed/analyzed structures:

- `derived.dialogue_trees` - Tree analysis per dialogue
- `derived.message_paths` - Materialized paths for each message
- `derived.linear_sequences` - Root-to-leaf paths
- `derived.sequence_messages` - Sequence membership
- `derived.exchanges` - Logical interaction units (built from tree, deduplicated)
- `derived.exchange_messages` - Exchange membership
- `derived.sequence_exchanges` - Links sequences to exchanges (many-to-many)
- `derived.exchange_content` - Aggregated content with hashes
- `derived.annotations` - Polymorphic entity annotations
- `derived.content_hashes` - Multi-scope content hashes

## Data Model

```
raw.dialogues
    └── raw.messages (tree structure via parent_id)
            ├── raw.content_parts
            │       └── raw.citations
            └── raw.attachments

derived.dialogue_trees (1:1 with dialogues)
    └── derived.linear_sequences (one per leaf)
            ├── derived.sequence_messages
            └── derived.sequence_exchanges → derived.exchanges (many-to-many)
                                                    ├── derived.exchange_messages
                                                    └── derived.exchange_content

derived.annotations (polymorphic, references any entity)
derived.content_hashes (multi-scope hashes)
```

### Exchange Deduplication

Exchanges are built from the tree and identified by `(dialogue_id, first_message_id, last_message_id)`. When a conversation branches, the shared prefix produces the same exchanges, which are reused rather than duplicated. Each linear sequence references its exchanges via the `sequence_exchanges` join table.

## Annotation Types

| Entity | Type | Key | Example Values |
|--------|------|-----|----------------|
| message | feature | - | has_wiki_links, has_code_blocks, has_latex |
| message | feature | code_language | python, javascript, sql |
| message | feature | continuation_signal | continue, elaborate, quote_elaborate |
| exchange | tag | exchange_type | coding, wiki_article, qa, discussion |
| exchange | title | - | (generated title for wiki export) |
| dialogue | tag | category | coding, research, writing |

## Custom Annotators

Create custom annotators by subclassing `Annotator`:

```python
from llm_archive.annotators import Annotator
from llm_archive.models import Exchange, ExchangeContent

class MyAnnotator(Annotator):
    ANNOTATION_TYPE = 'tag'       # 'tag', 'title', 'feature', etc.
    ENTITY_TYPE = 'exchange'      # 'message', 'exchange', 'dialogue'
    SOURCE = 'heuristic'          # 'heuristic', 'model', 'manual'
    VERSION = '1.0'
    
    def compute(self) -> int:
        exchanges = (
            self.session.query(Exchange, ExchangeContent)
            .join(ExchangeContent)
            .all()
        )
        
        count = 0
        for exchange, content in exchanges:
            if self._matches_criteria(content):
                if self.add_annotation(
                    entity_id=exchange.id,
                    value='my_tag_value',
                    key='optional_namespace',
                    confidence=0.9,
                    data={'extra': 'info'},
                ):
                    count += 1
        return count
```

Register and run:

```python
from llm_archive.annotators import AnnotationManager

manager = AnnotationManager(session)
manager.register(MyAnnotator)
results = manager.run_all()
```

## Tree Analysis

For branched dialogues (ChatGPT), the system:

1. Preserves full tree structure in `raw.messages.parent_id`
2. Computes materialized paths in `derived.message_paths`
3. Creates `derived.linear_sequences` for each leaf (root-to-leaf path)
4. Classifies branches as `regeneration` (same role) or `edit` (different role)
5. Selects primary path (longest, then most recent)

For linear dialogues (Claude), produces degenerate trees with `branch_count=0`.

## Pipeline

```
Import → Tree Analysis → Exchange Building → Annotating → Hashing
                                                   ↓
                                            [Future: Article extraction,
                                             Knowledge graph, Wiki export]
```

## Testing

### Setup Test Database

```bash
# Create test database (separate from main)
docker exec -it llm_archive_db psql -U postgres -c "CREATE DATABASE llm_archive_test"

# Or set custom test database URL
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/llm_archive_test"
```

### Run Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=llm_archive --cov-report=html

# Run specific test file
uv run pytest tests/test_extractors.py

# Run specific test
uv run pytest tests/test_extractors.py::TestChatGPTExtractor::test_extract_simple_conversation

# Run in parallel (faster)
uv run pytest -n auto
```

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── test_extractors.py    # ChatGPT/Claude extraction tests
├── test_builders.py      # Tree/Exchange/Hash builder tests
├── test_annotators.py    # Annotation system tests
└── test_idempotency.py   # Re-import behavior tests
```

### Key Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `db_session` | function | Session with transaction rollback |
| `clean_db_session` | function | Session that commits (with cleanup) |
| `chatgpt_simple_conversation` | function | Linear ChatGPT conversation |
| `chatgpt_branched_conversation` | function | Branched ChatGPT conversation |
| `claude_simple_conversation` | function | Simple Claude conversation |
| `fully_populated_db` | function | DB with conversations + derived data |
