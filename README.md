# chat2obs

Convert ChatGPT and Claude conversation exports into Obsidian notes with automatic processing and tagging.

## Quick Start

1. **Install the package:**
   ```bash
   pip install -e .
   ```

2. **Set up directories:**
   ```bash
   chat2obs setup
   ```

3. **Drop your conversation exports** in `./data/exports/`:
   - **ChatGPT**: Save the `.zip` export file directly
   - **Claude**: Extract and save the directory with `conversations.json`

4. **Process conversations:**
   ```bash
   chat2obs process
   ```

5. **Find your notes** in `./data/notes/`

## Features

### 🤖 **Auto-Discovery**
- Automatically finds ChatGPT `.zip` exports and Claude directories
- Detects conversation format and configures processing accordingly
- No manual configuration required

### ⚙️ **Processing Pipeline**
- **Exchange-based analysis** with 50+ detection rules
- **Flexible filtering** by conversation type, features, or custom criteria  
- **Batch processing** across multiple sources
- **Template-based** note generation with Obsidian wiki-links

### 🏷️ **Smart Tagging**
Conversations are automatically tagged with:
- **Content features**: code blocks, GitHub repos, attachments, reasoning
- **Interaction patterns**: continuations, large context, Q&A sessions
- **Tool usage**: gizmos, plugins, canvas operations, web search
- **Conversation metrics**: length, prompt statistics, consistency

## CLI Usage

### Basic Commands

```bash
# Process all conversation exports
chat2obs process

# Discover what exports are available
chat2obs discover

# Process only ChatGPT conversations
chat2obs process --source-type oai

# Use custom directories
chat2obs process --exports-dir ~/Downloads --output-dir ~/notes

# Skip note generation, just tag conversations
chat2obs process --no-notes
```

### Directory Structure

```
./data/
├── exports/                 # Drop export files here
│   ├── chatgpt-export.zip  # ChatGPT export
│   ├── claude-data/        # Claude export directory  
│   │   └── conversations.json
│   └── conversations.json   # Direct conversation file
└── notes/                  # Generated Obsidian notes
    ├── conversation-1.md
    └── conversation-2.md
```

## Python API

For programmatic use or integration with notebooks:

```python
from conversation_tagger import BatchProcessor, ProcessingConfig

# Simple processing
config = ProcessingConfig(
    sources=['oai', 'claude'],
    output_dir='./notes'
)
processor = BatchProcessor(config)
results = processor.process_all()

# With filtering
from conversation_tagger import FilterCriteria
criteria = FilterCriteria(
    required_annotations={'has_code_blocks'},
    forbidden_annotations={'user_has_attachments'}
)
config = ProcessingConfig(
    sources=['oai'],
    filter_criteria=criteria,
    output_dir='./coding-notes'
)
```

## Configuration

### Environment Variables
```bash
export CHAT2OBS_CHATGPT_ROOT="/path/to/chatgpt/data"
export CHAT2OBS_CLAUDE_ROOT="/path/to/claude/data"
```

### Data Sources
The system supports multiple conversation formats:
- **OpenAI/ChatGPT**: Export format with `mapping` structure
- **Claude**: Anthropic export format with `uuid` and `chat_messages`

## Development

### Running Tests
```bash
# Install development dependencies
pip install -e .[dev]

# Run the test suite
python -m pytest tests/ -v
```

### Project Structure
```
src/conversation_tagger/
├── core/           # Core conversation analysis
├── data/           # Data loading and configuration  
├── processing/     # Batch processing pipelines
├── cli/            # Command-line interface
└── templates/      # Jinja templates for note generation
```

## Examples

### Batch Processing Multiple Sources
```python
from conversation_tagger.cli.discovery import discover_and_configure
from conversation_tagger import BatchProcessor, ProcessingConfig

# Auto-discover exports
configs, discoveries = discover_and_configure("./my-exports")

# Process all discovered sources
config = ProcessingConfig(
    sources=[c.name for c in configs],
    output_dir="./all-notes"
)
processor = BatchProcessor(config)
results = processor.process_all()
```

### Custom Filtering
```python
from conversation_tagger import FilterCriteria, create_gizmo_filter

# Filter for specific gizmo usage
gizmo_filter = create_gizmo_filter('g-dall-e-3')

# Custom filter for long coding sessions
coding_filter = FilterCriteria(
    required_annotations={'has_code_blocks', 'has_github_repos'},
    custom_filters=[
        lambda conv: conv.exchange_count > 10,
        lambda conv: 'python' in conv.get_all_user_text().lower()
    ]
)
```

## License

MIT License - see LICENSE file for details.
