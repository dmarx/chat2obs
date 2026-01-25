# LLM Archive

Ingest, normalize, and analyze LLM conversation exports for downstream processing.

## Features

- **Multi-source ingestion**: ChatGPT and Claude exports
- **Tree analysis**: Full dialogue tree preservation with branch classification
- **Exchange grouping**: Logical interaction units with continuation detection
- **Content hashing**: Deduplication preparation
- **Polymorphic labeling**: Flexible annotation system

## Installation

```bash
pip install -e .
```

Requires PostgreSQL 14+.

## Database Setup

```bash
# Create database
createdb llm_archive

# Initialize schema
llm-archive init --schema_dir=schema
```

## Usage

### Import

```bash
# Import ChatGPT export
llm-archive import_chatgpt /path/to/conversations.json

# Import Claude export
llm-archive import_claude /path/to/claude.json

# Import both
llm-archive import_all \
    --chatgpt_path=/path/to/chatgpt.json \
    --claude_path=/path/to/claude.json
```

### Build Derived Structures

```bash
# Build tree analysis
llm-archive build_trees

# Build exchanges
llm-archive build_exchanges

# Build content hashes
llm-archive build_hashes

# Build all
llm-archive build_all
```

### Labeling

```bash
# Run all labelers
llm-archive label
```

### Analysis

```bash
# Show statistics
llm-archive stats

# Find duplicates
llm-archive find_duplicates --entity_type=exchange --scope=assistant
```

### Full Pipeline

```bash
# Run everything
llm-archive run \
    --chatgpt_path=/path/to/chatgpt.json \
    --claude_path=/path/to/claude.json \
    --init_db
```

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
- `derived.exchanges` - Logical interaction units
- `derived.exchange_messages` - Exchange membership
- `derived.exchange_content` - Aggregated content with hashes
- `derived.labels` - Polymorphic entity labels
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
            └── derived.exchanges
                    ├── derived.exchange_messages
                    └── derived.exchange_content

derived.labels (polymorphic, references any entity)
derived.content_hashes (multi-scope hashes)
```

## Label Types

| Entity | Label Type | Example Values |
|--------|-----------|----------------|
| message | feature | has_wiki_links, has_code_blocks, has_latex |
| message | continuation_signal | continue, elaborate, quote_elaborate |
| exchange | exchange_type | coding, wiki_article, qa, discussion |

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
Import → Tree Analysis → Exchange Building → Labeling → Hashing
                                                   ↓
                                            [Future: Article extraction,
                                             Knowledge graph, etc.]
```