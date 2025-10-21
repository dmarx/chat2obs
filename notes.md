# Development Notes

## Recent Major Changes

### Database-Backed Incremental Processing System
- Implemented complete SQLite-based architecture for conversation storage
- Added incremental processing with diff detection (only processes new/changed conversations)
- Created rich CLI with query, stats, and notes commands
- Maintained full backward compatibility with file-based processing

### Architecture Changes
- `DatabaseManager`: SQLite connection and CRUD operations
- `IncrementalIngester`: Detects changes and processes only deltas
- `DatabaseTagger`: Database-backed tagging engine  
- `ConversationQuery`: Rich querying interface
- `DatabaseBatchProcessor`: End-to-end incremental pipeline

### Performance Improvements
- Second run on same export: 0 conversations processed vs full reprocessing
- Fast querying without reprocessing data
- Efficient for large conversation archives (1000s of conversations)

### Vestigial Code Cleanup
- Removed detection_old.py (600+ lines of non-functional legacy code)
- Removed duplicate cli_integration.py (200+ lines)
- Renamed db BatchProcessor → DatabaseBatchProcessor to avoid naming conflicts
- Organized imports clearly: file-based (legacy) vs database-backed (recommended)
- Updated examples with proper deprecation warnings and guidance

### CLI Enhancements
- `chat2obs db-process`: Incremental processing pipeline
- `chat2obs query`: Filter conversations by annotations/metadata
- `chat2obs stats`: Database and processing statistics
- `chat2obs notes`: Generate Obsidian notes from database queries

### Key Benefits
- Dramatic performance improvement for repeat processing
- Rich querying capabilities without reprocessing
- Same Obsidian markdown output
- Clear migration path from notebooks to CLI
- Enterprise-grade scalability for large archives

## Implementation Notes

The system maintains two distinct processing approaches:
1. **File-based** (legacy): Full reprocessing each time, maintained for compatibility
2. **Database-backed** (recommended): Incremental processing with rich querying

Both approaches generate identical Obsidian-compatible markdown output, ensuring smooth migration paths.
