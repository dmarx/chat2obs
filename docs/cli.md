<!-- docs/cli.md -->
# Command-Line Interface

## Overview

The CLI provides the primary interface for importing data, building derived structures, and running annotations. It's built with Python Fire for automatic command generation.

## Installation

```bash
# Install package with CLI
pip install -e .

# Or run directly with uv
uv run llm-archive <command>
```

## Configuration

### Environment Variables

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/llm_archive"

# Or individual components
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=llm_archive
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
```

### Configuration File

```yaml
# config.yaml
database:
  host: localhost
  port: 5432
  database: llm_archive
  user: postgres
  password: postgres

import:
  batch_size: 1000
  
logging:
  level: INFO
```

---

## Command Reference

### Database Management

#### `init`

Initialize database with schemas:

```bash
# Create schemas and tables from schema/ directory
llm-archive init --schema_dir=schema

# With custom connection
llm-archive init --database_url="postgresql://..." --schema_dir=schema
```

```mermaid
flowchart LR
    Init["init"] --> CreateRaw["CREATE SCHEMA raw"]
    Init --> CreateDerived["CREATE SCHEMA derived"]
    CreateRaw --> RawTables["Create raw.* tables"]
    CreateDerived --> DerivedTables["Create derived.* tables"]
    RawTables --> InsertSources["INSERT sources"]
```

#### `reset`

Reset database (destructive):

```bash
# Drop and recreate all schemas
llm-archive reset --confirm

# Reset only derived schema
llm-archive reset --schema=derived --confirm
```

### Data Import

#### `import_chatgpt`

Import ChatGPT conversation export:

```bash
# Basic import
llm-archive import_chatgpt /path/to/conversations.json

# Incremental import (update only changed)
llm-archive import_chatgpt /path/to/conversations.json --incremental

# With batch size
llm-archive import_chatgpt /path/to/conversations.json --batch_size=500
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `file` | Path to conversations.json | Required |
| `--incremental` | Only update changed dialogues | False |
| `--batch_size` | Messages per batch | 1000 |

#### `import_claude`

Import Claude conversation export:

```bash
# Basic import
llm-archive import_claude /path/to/claude_export.json

# Incremental import
llm-archive import_claude /path/to/claude_export.json --incremental
```

#### `import_all`

Import from multiple sources:

```bash
llm-archive import_all \
    --chatgpt_path=/path/to/chatgpt.json \
    --claude_path=/path/to/claude.json \
    --incremental
```

### Building Derived Data

#### `build_prompt_responses`

Build prompt-response pairs from imported messages:

```bash
# Build all dialogues
llm-archive build_prompt_responses

# Build specific dialogue
llm-archive build_prompt_responses --dialogue_id="uuid-here"

# Rebuild (clears existing first)
llm-archive build_prompt_responses --rebuild
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `--dialogue_id` | Build for specific dialogue only | None (all) |
| `--rebuild` | Clear and rebuild | False |
| `--batch_size` | Dialogues per commit | 100 |

```mermaid
flowchart LR
    Build["build_prompt_responses"] --> Clear["Clear existing<br/>(if rebuild)"]
    Clear --> Iterate["Iterate dialogues"]
    
    Iterate --> Process["Process each dialogue"]
    Process --> Pair["Create prompt-response<br/>pairs"]
    Pair --> Content["Aggregate content"]
    Content --> Next["Next dialogue"]
    
    Next --> Commit{"Batch full?"}
    Commit -->|Yes| CommitDB["COMMIT"]
    Commit -->|No| Iterate
    CommitDB --> Iterate
```

### Annotation

#### `annotate`

Run annotators on entities:

```bash
# Run all registered annotators
llm-archive annotate

# Run specific annotator
llm-archive annotate WikiCandidateAnnotator

# Clear cursors and re-run everything
llm-archive annotate --clear
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `annotator` | Annotator name or None for all | None (all) |
| `--clear` | Clear cursors before running | False |

```mermaid
flowchart TD
    Annotate["annotate"] --> Sort["Sort by priority"]
    Sort --> Loop["For each annotator"]
    
    Loop --> GetCursor["Get/Create cursor"]
    GetCursor --> Query["Query entities > cursor"]
    
    Query --> HasEntities{"Entities?"}
    HasEntities -->|Yes| Process["Process entity"]
    Process --> Write["Write annotations"]
    Write --> Next["Next entity"]
    Next --> HasEntities
    
    HasEntities -->|No| UpdateCursor["Update cursor"]
    UpdateCursor --> NextAnnotator["Next annotator"]
    NextAnnotator --> Loop
```

### Analysis and Queries

#### `stats`

Show database statistics:

```bash
# Show overview
llm-archive stats

# Detailed stats
llm-archive stats --detailed
```

Output includes:
- Dialogue counts by source
- Message counts by role
- Prompt-response pair counts
- Annotation counts by key

#### `query_annotations`

Query entities by annotations:

```bash
# Find all wiki article candidates
llm-archive query_annotations \
    --entity_type=prompt_response \
    --annotation_key=exchange_type \
    --annotation_value=wiki_article

# Find entities with specific flag
llm-archive query_annotations \
    --entity_type=message \
    --annotation_key=has_code_blocks \
    --value_type=flag

# Export results
llm-archive query_annotations \
    --entity_type=prompt_response \
    --annotation_key=exchange_type \
    --annotation_value=wiki_article \
    --output=wiki_articles.json
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `--entity_type` | Entity type (prompt_response, message, etc.) |
| `--annotation_key` | Annotation key to filter on |
| `--annotation_value` | Annotation value to filter on (optional for flags) |
| `--value_type` | Type of annotation (flag, string, numeric, json) |
| `--output` | Output file path |

### Pipeline Commands

#### `pipeline`

Run full import and processing pipeline:

```bash
# Full pipeline with initialization
llm-archive pipeline \
    --chatgpt_path=/path/to/chatgpt.json \
    --claude_path=/path/to/claude.json \
    --init_db

# Incremental update
llm-archive pipeline \
    --chatgpt_path=/path/to/new_export.json \
    --incremental
```

**Pipeline steps:**
1. Initialize database (if `--init_db`)
2. Import ChatGPT conversations (if `--chatgpt_path`)
3. Import Claude conversations (if `--claude_path`)
4. Build prompt-responses
5. Run all annotators

---

## Usage Examples

### First-Time Setup

```bash
# 1. Initialize database
llm-archive init --schema_dir=schema

# 2. Import ChatGPT export
llm-archive import_chatgpt ~/Downloads/conversations.json

# 3. Import Claude export
llm-archive import_claude ~/Downloads/claude_export.json

# 4. Build prompt-response pairs
llm-archive build_prompt_responses

# 5. Run annotations
llm-archive annotate

# 6. Check statistics
llm-archive stats
```

### Incremental Update

```bash
# Weekly update with new export
llm-archive pipeline \
    --chatgpt_path=new_conversations.json \
    --incremental
```

### Targeted Operations

```bash
# Rebuild prompt-responses for single dialogue
llm-archive build_prompt_responses --dialogue_id="12345678-..."

# Re-run specific annotator
llm-archive annotate WikiCandidateAnnotator --clear

# Query wiki article candidates
llm-archive query_annotations \
    --entity_type=prompt_response \
    --annotation_key=exchange_type \
    --annotation_value=wiki_article \
    --output=wiki_articles.json
```

### Development Workflow

```bash
# Reset database
llm-archive reset --confirm

# Import test data
llm-archive import_chatgpt tests/fixtures/sample.json

# Build and annotate
llm-archive build_prompt_responses
llm-archive annotate

# Check results
llm-archive stats --detailed
```

---

## Error Handling

### Common Issues

**Database connection failed:**
```bash
# Check environment variables
echo $DATABASE_URL

# Or check individual vars
echo $POSTGRES_HOST
echo $POSTGRES_PORT

# Test connection
psql -h localhost -U postgres -d llm_archive
```

**Import fails with duplicate key:**
```bash
# Use incremental mode to update existing
llm-archive import_chatgpt file.json --incremental

# Or clear and reimport
llm-archive reset --schema=raw --confirm
llm-archive import_chatgpt file.json
```

**Annotation cursor stuck:**
```bash
# Clear cursors and re-run
llm-archive annotate --clear
```

### Verbose Output

```bash
# Set log level
export LOG_LEVEL=DEBUG
llm-archive import_chatgpt file.json

# Or use python directly with debug
python -m llm_archive.cli import_chatgpt file.json
```

---

## Shell Completion

### Bash

```bash
# Add to ~/.bashrc
eval "$(llm-archive --completion bash)"
```

### Zsh

```bash
# Add to ~/.zshrc
eval "$(llm-archive --completion zsh)"
```

---

## Related Documentation

- [Architecture Overview](architecture.md)
- [Extractors](extractors.md) - Import details
- [Builders](builders.md) - Build process
- [Annotators](annotators.md) - Annotation system
- [Testing](testing.md) - Testing commands
