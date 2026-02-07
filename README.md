# LLM Archive

Ingest, normalize, and analyze LLM conversation exports for downstream processing.

## Features

- **Multi-source ingestion**: ChatGPT and Claude exports
- **Prompt-response pairing**: Direct user→assistant associations
- **Typed annotation system**: Flag, string, numeric, and JSON annotations
- **Content hashing**: Deduplication preparation
- **Incremental processing**: Efficient re-annotation with cursor tracking

## Project Structure

```
llm_archive/
├── models/
│   ├── raw.py          # Raw schema models
│   └── derived.py      # Derived schema models
├── extractors/
│   ├── base.py         # Base extractor class
│   ├── chatgpt.py      # ChatGPT extractor
│   └── claude.py       # Claude extractor
├── builders/
│   └── prompt_response.py  # Prompt-response builder
├── annotations/
│   └── core.py         # AnnotationWriter/Reader
├── annotators/
│   └── prompt_response.py  # Prompt-response annotators
├── cli.py              # Command-line interface
└── config.py           # Environment configuration
```

## Additional Documentation

See the `docs/` folder for detailed documentation:

- [Architecture](docs/architecture.md) - System design and data flow
- [Schema](docs/schema.md) - Database schema details
- [Models](docs/models.md) - SQLAlchemy ORM models
- [Extractors](docs/extractors.md) - Platform-specific extraction
- [Builders](docs/builders.md) - Derived data construction
- [Annotators](docs/annotators.md) - Annotation system
- [CLI Reference](docs/cli.md) - Command-line interface
- [Testing](docs/testing.md) - Testing strategy


## Requirements

- Python 3.11+
- Docker (for PostgreSQL with pgvector)

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
# Build prompt-response pairs
uv run llm-archive build_prompt_responses

# Build for specific dialogue
uv run llm-archive build_prompt_responses --dialogue_id=<uuid>
```

### Annotations

```bash
# Run all registered annotators
uv run llm-archive annotate

# Run specific annotator
uv run llm-archive annotate WikiCandidateAnnotator

# Clear and re-run
uv run llm-archive annotate --clear
```

### Analysis

```bash
# Show statistics
uv run llm-archive stats

# Query annotated content
uv run llm-archive query_annotations \
    --entity_type=prompt_response \
    --annotation_key=exchange_type \
    --annotation_value=wiki_article
```

### Full Pipeline

```bash
# Run everything
uv run llm-archive pipeline \
    --chatgpt_path=/path/to/chatgpt.json \
    --claude_path=/path/to/claude.json \
    --init_db
```

## Idempotent Import

Re-importing the same export files is safe:
- Dialogues are identified by their source ID
- If `updated_at` timestamp is newer, dialogue is updated
- If unchanged, dialogue is skipped
- Messages use content hashing for change detection

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

Computed structures that can be rebuilt:

- `derived.prompt_responses` - User prompt → assistant response pairs
- `derived.prompt_response_content` - Denormalized text content
- `derived.{entity}_annotations_{type}` - Typed annotation tables
  - Entity types: `content_part`, `message`, `prompt_response`, `dialogue`
  - Value types: `flag`, `string`, `numeric`, `json`
- `derived.annotator_cursors` - Incremental processing state

## Annotation System

The annotation system supports multiple detection strategies for the same concept:

```python
from llm_archive.annotators.prompt_response import PromptResponseAnnotator
from llm_archive.annotations.core import AnnotationResult, ValueType

class MyAnnotator(PromptResponseAnnotator):
    ANNOTATION_KEY = 'my_classification'
    VALUE_TYPE = ValueType.STRING
    PRIORITY = 50  # Higher runs first
    VERSION = '1.0'
    SOURCE = 'heuristic'
    
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
        if self._matches_criteria(data):
            return [AnnotationResult(
                key=self.ANNOTATION_KEY,
                value='my_tag_value',
                confidence=0.9,
            )]
        return []
```

Register and run:

```python
from llm_archive.cli import AnnotationManager

manager = AnnotationManager(session)
manager.register(MyAnnotator)
results = manager.run_all()
```

## Pipeline

```
Import → Prompt-Response Building → Annotation → Analysis
                                         ↓
                                  [Future: Export,
                                   Knowledge graph]
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
pytest

# Run only unit tests (no database required)
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=llm_archive --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Organization

```
tests/
├── unit/               # Fast tests, no database
│   ├── test_annotations.py
│   └── test_utils.py
├── integration/        # Tests requiring database
│   ├── conftest.py     # Shared fixtures
│   ├── test_extractors.py
│   ├── test_prompt_response_builder.py
│   └── test_annotations.py
└── conftest.py         # Root configuration
```
