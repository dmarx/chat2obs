# docs/cli.md
# Command-Line Interface

## Overview

The CLI provides the primary interface for importing data, building derived structures, and running annotations. It's built with Python Fire for automatic command generation.

## Installation

```bash
# Install package with CLI
pip install -e .

# Or run directly
python -m llm_archive.cli <command>
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

#### `init-db`

Initialize database with schemas:

```bash
# Create schemas and tables
llm-archive init-db

# With custom connection
llm-archive init-db --database-url "postgresql://..."
```

```mermaid
flowchart LR
    InitDB["init-db"] --> CreateRaw["CREATE SCHEMA raw"]
    InitDB --> CreateDerived["CREATE SCHEMA derived"]
    CreateRaw --> RawTables["Create raw.* tables"]
    CreateDerived --> DerivedTables["Create derived.* tables"]
    RawTables --> InsertSources["INSERT sources"]
```

#### `reset-db`

Reset database (destructive):

```bash
# Drop and recreate all schemas
llm-archive reset-db --confirm

# Reset only derived schema
llm-archive reset-db --schema derived --confirm
```

### Data Import

#### `import`

Import conversations from export files:

```bash
# Import ChatGPT export
llm-archive import chatgpt conversations.json

# Import Claude export
llm-archive import claude claude_export.json

# Incremental import (update only changed)
llm-archive import chatgpt conversations.json --mode incremental

# With batch size
llm-archive import chatgpt conversations.json --batch-size 500
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `source` | Platform: `chatgpt`, `claude` | Required |
| `file` | Path to export file | Required |
| `--mode` | `full` or `incremental` | `full` |
| `--batch-size` | Messages per batch | 1000 |

```mermaid
flowchart TD
    Import["import chatgpt file.json"] --> Read["Read JSON"]
    Read --> Loop["For each conversation"]
    
    Loop --> Extract["Extract dialogue"]
    Extract --> ExtractMsgs["Extract messages"]
    ExtractMsgs --> ExtractParts["Extract content parts"]
    ExtractParts --> ExtractMeta["Extract platform features"]
    ExtractMeta --> Insert["INSERT to raw.*"]
    
    Insert --> Batch{"Batch full?"}
    Batch -->|Yes| Commit["COMMIT"]
    Batch -->|No| Loop
    Commit --> Loop
    
    Loop --> Done["Complete"]
```

### Building Derived Data

#### `build`

Build derived structures from raw data:

```bash
# Build all derived structures
llm-archive build all

# Build specific structures
llm-archive build trees
llm-archive build exchanges
llm-archive build hashes

# Build for single dialogue
llm-archive build all --dialogue-id "uuid-here"

# Incremental build (new dialogues only)
llm-archive build all --incremental
```

**Subcommands:**

| Command | Builds |
|---------|--------|
| `all` | Trees, sequences, exchanges, hashes |
| `trees` | dialogue_trees, message_paths, linear_sequences |
| `exchanges` | exchanges, exchange_messages, exchange_content |
| `hashes` | content_hashes |

```mermaid
flowchart LR
    Build["build all"] --> Trees["TreeBuilder"]
    Trees --> TreeTables["dialogue_trees<br/>message_paths<br/>linear_sequences"]
    
    TreeTables --> Exchanges["ExchangeBuilder"]
    Exchanges --> ExchangeTables["exchanges<br/>exchange_messages<br/>exchange_content"]
    
    ExchangeTables --> Hashes["HashBuilder"]
    Hashes --> HashTables["content_hashes"]
```

### Annotation

#### `annotate`

Run annotators on entities:

```bash
# Run all registered annotators
llm-archive annotate all

# Run specific annotator
llm-archive annotate CodeBlockAnnotator

# Run annotators for entity type
llm-archive annotate --entity-type exchange

# Clear and re-run
llm-archive annotate all --clear
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `annotator` | Annotator name or `all` | `all` |
| `--entity-type` | Filter by entity type | None |
| `--clear` | Clear existing annotations first | False |

```mermaid
flowchart TD
    Annotate["annotate all"] --> Sort["Sort by priority"]
    Sort --> Loop["For each annotator"]
    
    Loop --> GetCursor["Get cursor"]
    GetCursor --> Query["Query entities > cursor"]
    Query --> Process["Process entities"]
    
    Process --> AnnotateLoop["For each entity"]
    AnnotateLoop --> Call["annotate(data)"]
    Call --> Insert["INSERT annotations"]
    Insert --> AnnotateLoop
    
    AnnotateLoop --> UpdateCursor["Update cursor"]
    UpdateCursor --> Loop
    
    Loop --> Done["Complete"]
```

#### `show-strategies`

Display registered annotation strategies:

```bash
llm-archive show-strategies
```

Output:
```
Annotation Key: code
  ChatGPTCodeExecutionAnnotator (priority=100)
  CodeBlockAnnotator (priority=90)
  ScriptHeaderAnnotator (priority=85)
  CodeStructureAnnotator (priority=70)
  FunctionDefinitionAnnotator (priority=50)
  CodeKeywordDensityAnnotator (priority=30)

Annotation Key: latex
  LatexAnnotator (priority=50)
  
...
```

### Query Commands

#### `stats`

Show database statistics:

```bash
llm-archive stats
```

Output:
```
Raw Schema:
  dialogues: 1,234
  messages: 45,678
  content_parts: 89,012
  
Derived Schema:
  dialogue_trees: 1,234
  exchanges: 12,345
  annotations: 67,890
  
By Source:
  chatgpt: 1,000 dialogues
  claude: 234 dialogues
```

#### `list`

List entities with filters:

```bash
# List dialogues
llm-archive list dialogues --source chatgpt --limit 10

# List exchanges with annotations
llm-archive list exchanges --has-tag coding --limit 20

# List by date range
llm-archive list dialogues --after 2024-01-01 --before 2024-02-01
```

#### `show`

Show detailed entity information:

```bash
# Show dialogue
llm-archive show dialogue <uuid>

# Show exchange with content
llm-archive show exchange <uuid> --include-content

# Show message with annotations
llm-archive show message <uuid> --include-annotations
```

### Export Commands

#### `export`

Export data to various formats:

```bash
# Export exchanges to JSONL (for training)
llm-archive export exchanges output.jsonl --format jsonl

# Export with filters
llm-archive export exchanges output.jsonl \
  --source chatgpt \
  --has-tag coding \
  --min-assistant-words 100

# Export dialogues to JSON
llm-archive export dialogues output.json --format json
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `--format` | `json`, `jsonl`, `csv` |
| `--source` | Filter by source |
| `--has-tag` | Filter by tag |
| `--min-assistant-words` | Minimum word count |
| `--primary-only` | Primary sequences only |

---

## Pipeline Commands

### `pipeline`

Run full import-build-annotate pipeline:

```bash
# Full pipeline
llm-archive pipeline chatgpt conversations.json

# Pipeline with options
llm-archive pipeline chatgpt conversations.json \
  --mode incremental \
  --skip-annotate
```

```mermaid
flowchart LR
    Pipeline["pipeline"] --> Import["import"]
    Import --> Build["build all"]
    Build --> Annotate["annotate all"]
    Annotate --> Stats["stats"]
```

---

## Output Formats

### JSON Output

```bash
llm-archive stats --format json
```

```json
{
  "raw": {
    "dialogues": 1234,
    "messages": 45678
  },
  "derived": {
    "exchanges": 12345,
    "annotations": 67890
  }
}
```

### Table Output (Default)

```bash
llm-archive stats
```

```
┌─────────────┬────────┐
│ Table       │ Count  │
├─────────────┼────────┤
│ dialogues   │ 1,234  │
│ messages    │ 45,678 │
│ exchanges   │ 12,345 │
└─────────────┴────────┘
```

---

## Logging

### Log Levels

```bash
# Debug logging
llm-archive --log-level DEBUG import chatgpt file.json

# Quiet mode
llm-archive --log-level WARNING build all
```

### Log Format

```
2024-01-15 10:30:00 | INFO     | Importing 1234 conversations
2024-01-15 10:30:05 | INFO     | Processed 100/1234 dialogues
2024-01-15 10:30:10 | INFO     | Processed 200/1234 dialogues
2024-01-15 10:30:45 | INFO     | Import complete: 1234 dialogues
```

---

## Error Handling

### Common Errors

#### Connection Error

```
Error: Could not connect to database
  Host: localhost:5432
  Database: llm_archive

Solutions:
  1. Check DATABASE_URL environment variable
  2. Ensure PostgreSQL is running
  3. Verify credentials
```

#### File Not Found

```
Error: Export file not found: conversations.json

Solutions:
  1. Check file path
  2. Use absolute path
```

#### Invalid Source

```
Error: Unknown source 'openai'
Valid sources: chatgpt, claude

Solutions:
  1. Use valid source name
  2. Check available extractors
```

### Recovery

```bash
# Rollback failed import
llm-archive import chatgpt file.json
# Error during import...

# The transaction is rolled back automatically
# Re-run the import
llm-archive import chatgpt file.json
```

---

## Examples

### Full Workflow

```bash
# 1. Initialize database
llm-archive init-db

# 2. Import ChatGPT export
llm-archive import chatgpt ~/Downloads/conversations.json

# 3. Import Claude export
llm-archive import claude ~/Downloads/claude_export.json

# 4. Build derived structures
llm-archive build all

# 5. Run annotations
llm-archive annotate all

# 6. Check statistics
llm-archive stats

# 7. Export coding exchanges
llm-archive export exchanges coding_exchanges.jsonl \
  --has-tag coding \
  --min-assistant-words 100
```

### Incremental Update

```bash
# Weekly update with new export
llm-archive pipeline chatgpt new_conversations.json --mode incremental
```

### Targeted Rebuild

```bash
# Rebuild exchanges for single dialogue
llm-archive build exchanges --dialogue-id "12345678-..."

# Re-annotate with new annotator version
llm-archive annotate CodeBlockAnnotator --clear
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