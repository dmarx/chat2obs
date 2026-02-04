# docs/architecture.md
# LLM Archive: System Architecture

## Overview

LLM Archive is a system for importing, normalizing, analyzing, and annotating conversation data from multiple LLM platforms (ChatGPT, Claude, and future sources). It transforms heterogeneous export formats into a unified data model that supports both tree-structured and linear conversation representations.

## Design Philosophy

### Core Principles

1. **Source Fidelity**: Raw data is preserved exactly as received; normalization happens in derived layers
2. **Schema Separation**: Clear distinction between raw (immutable imports) and derived (computed analysis)
3. **Incremental Processing**: All analysis is cursor-based to support efficient updates
4. **Platform Abstraction**: Common abstractions with platform-specific extensions
5. **Annotation Strategy Pattern**: Multiple detection strategies can target the same semantic concept

### Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Two-schema design (raw/derived) | Preserves original data while enabling computed views |
| Tree-native message structure | ChatGPT exports are trees; linearization is derived |
| Exchange as fundamental unit | User-assistant pairs are the atomic interaction unit |
| Polymorphic annotations | Single table serves all entity types with provenance |
| Cursor-based incremental processing | Efficient re-annotation without full reprocessing |

## System Architecture

```mermaid
flowchart TB
    subgraph Sources["Data Sources"]
        ChatGPT["ChatGPT Export<br/>(JSON)"]
        Claude["Claude Export<br/>(JSON)"]
        Future["Future Sources<br/>(...)"]
    end

    subgraph Extractors["Extraction Layer"]
        BaseExtractor["BaseExtractor"]
        ChatGPTExtractor["ChatGPTExtractor"]
        ClaudeExtractor["ClaudeExtractor"]
    end

    subgraph RawSchema["raw.* Schema"]
        Dialogues["dialogues"]
        Messages["messages"]
        ContentParts["content_parts"]
        Citations["citations"]
        Attachments["attachments"]
        
        subgraph ChatGPTExt["ChatGPT Extensions"]
            CGPTMeta["chatgpt_message_meta"]
            CGPTSearch["chatgpt_search_*"]
            CGPTCode["chatgpt_code_*"]
            CGPTCanvas["chatgpt_canvas_docs"]
            CGPTDALLE["chatgpt_dalle_generations"]
        end
        
        subgraph ClaudeExt["Claude Extensions"]
            ClaudeMeta["claude_message_meta"]
        end
    end

    subgraph Builders["Builder Layer"]
        TreeBuilder["TreeBuilder"]
        ExchangeBuilder["ExchangeBuilder"]
        HashBuilder["HashBuilder"]
    end

    subgraph DerivedSchema["derived.* Schema"]
        Trees["dialogue_trees"]
        Paths["message_paths"]
        Sequences["linear_sequences"]
        Exchanges["exchanges"]
        ExchangeContent["exchange_content"]
        Annotations["annotations"]
        Hashes["content_hashes"]
        Cursors["annotator_cursors"]
    end

    subgraph Annotators["Annotation Layer"]
        Manager["AnnotationManager"]
        
        subgraph Strategies["Strategy Groups"]
            MsgAnnotators["Message Annotators"]
            ExchAnnotators["Exchange Annotators"]
            DlgAnnotators["Dialogue Annotators"]
            PlatformAnnotators["Platform Annotators"]
        end
    end

    ChatGPT --> ChatGPTExtractor
    Claude --> ClaudeExtractor
    Future --> BaseExtractor

    ChatGPTExtractor --> Dialogues
    ClaudeExtractor --> Dialogues
    ChatGPTExtractor --> CGPTMeta
    ClaudeExtractor --> ClaudeMeta
    
    Dialogues --> TreeBuilder
    Messages --> TreeBuilder
    
    TreeBuilder --> Trees
    TreeBuilder --> Paths
    TreeBuilder --> Sequences
    
    Trees --> ExchangeBuilder
    Paths --> ExchangeBuilder
    
    ExchangeBuilder --> Exchanges
    ExchangeBuilder --> ExchangeContent
    
    ExchangeContent --> HashBuilder
    HashBuilder --> Hashes
    
    Exchanges --> Annotators
    Dialogues --> Annotators
    Messages --> Annotators
    
    Annotators --> Annotations
    Annotators --> Cursors
```

## Data Flow

### Import Pipeline

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Extractor
    participant RawDB as raw.* Tables
    participant Builder
    participant DerivedDB as derived.* Tables
    participant Annotator

    User->>CLI: import [source] [file]
    CLI->>Extractor: extract(file_path)
    
    loop For each conversation
        Extractor->>RawDB: Insert dialogue
        loop For each message
            Extractor->>RawDB: Insert message
            Extractor->>RawDB: Insert content_parts
            Extractor->>RawDB: Insert platform extensions
        end
    end
    
    CLI->>Builder: build_trees()
    Builder->>RawDB: Query messages
    Builder->>DerivedDB: Insert dialogue_trees
    Builder->>DerivedDB: Insert message_paths
    Builder->>DerivedDB: Insert linear_sequences
    
    CLI->>Builder: build_exchanges()
    Builder->>DerivedDB: Query trees/paths
    Builder->>DerivedDB: Insert exchanges
    Builder->>DerivedDB: Insert exchange_content
    
    CLI->>Annotator: run_all()
    loop For each annotator (by priority)
        Annotator->>DerivedDB: Check cursor
        Annotator->>DerivedDB: Query entities > cursor
        Annotator->>DerivedDB: Insert annotations
        Annotator->>DerivedDB: Update cursor
    end
    
    Annotator-->>User: Complete
```

### Incremental Update Flow

```mermaid
sequenceDiagram
    participant CLI
    participant Extractor
    participant RawDB
    participant Builder
    participant DerivedDB
    participant Annotator

    CLI->>Extractor: import(file, mode=incremental)
    
    loop For each conversation
        Extractor->>RawDB: Check source_id exists
        alt New conversation
            Extractor->>RawDB: INSERT dialogue + messages
        else Existing conversation
            Extractor->>RawDB: Compare content_hash
            alt Changed
                Extractor->>RawDB: UPDATE messages
            end
        end
    end
    
    CLI->>Builder: build (incremental)
    Builder->>DerivedDB: Process only new/changed dialogues
    
    CLI->>Annotator: run_all()
    Annotator->>DerivedDB: Get cursor (high_water_mark)
    Annotator->>DerivedDB: Query WHERE created_at > cursor
    Note over Annotator: Only processes new entities
```

## Component Responsibilities

### Extractors

Transform platform-specific export formats into the universal raw schema:

| Component | Responsibility |
|-----------|---------------|
| `BaseExtractor` | Common interface, deduplication, transaction management |
| `ChatGPTExtractor` | Parse conversations.json, handle tree structure, extract platform features |
| `ClaudeExtractor` | Parse Claude exports, synthesize linear parent-child relationships |

### Builders

Compute derived structures from raw data:

| Component | Responsibility |
|-----------|---------------|
| `TreeBuilder` | Analyze tree topology, compute paths, identify primary sequences |
| `ExchangeBuilder` | Segment conversations into user-assistant exchange pairs |
| `HashBuilder` | Compute content hashes for deduplication and change detection |

### Annotators

Apply labels, tags, and metadata to entities:

| Component | Responsibility |
|-----------|---------------|
| `AnnotationManager` | Coordinate annotator execution, strategy resolution |
| `MessageTextAnnotator` | Base class for message content analysis |
| `ExchangeAnnotator` | Base class for exchange-level analysis |
| `DialogueAnnotator` | Base class for dialogue-level aggregate analysis |
| `ExchangePlatformAnnotator` | Base class for platform feature queries |

## Deployment Architecture

```mermaid
flowchart LR
    subgraph Host["Host Machine"]
        CLI["CLI<br/>(Python)"]
        PG["PostgreSQL<br/>(Docker)"]
        Data["Export Files<br/>(.json)"]
    end
    
    CLI -->|"psycopg2"| PG
    Data -->|"read"| CLI
    
    subgraph PGInternal["PostgreSQL Instance"]
        Raw["raw schema"]
        Derived["derived schema"]
    end
```

### Container Setup

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: llm_archive
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
```

## Extension Points

### Adding a New Source

1. Create extractor class extending `BaseExtractor`
2. Add source entry to `raw.sources` table
3. Create platform extension tables if needed
4. Implement message tree/linearization logic

### Adding a New Annotator

1. Choose base class based on entity type
2. Define `ANNOTATION_KEY` for strategy grouping
3. Set `PRIORITY` relative to existing strategies
4. Implement `annotate()` method
5. Register with `AnnotationManager`

### Adding a New Derived Structure

1. Design schema in `002_derived.sql`
2. Create SQLAlchemy model in `models/derived.py`
3. Create builder class in `builders/`
4. Integrate with CLI pipeline

## Performance Considerations

### Indexing Strategy

- Raw tables: Indexed on `dialogue_id`, `parent_id`, `created_at`
- Derived tables: Indexed on foreign keys and filtered columns
- Annotations: Partial indexes on `superseded_at IS NULL`

### Batch Processing

- Extractors use batch inserts (1000 messages/batch)
- Builders process dialogues in batches
- Annotators track cursors to avoid re-processing

### Memory Management

- Tree analysis uses iterative algorithms (not recursive)
- Content aggregation streams results
- Large dialogues processed incrementally

## Security Considerations

- All data stored locally (no cloud dependencies)
- Database credentials via environment variables
- Source JSON preserved for audit trail
- No PII-specific handling (user responsibility)

## Related Documentation

- [Schema Design](schema.md) - Database schema details
- [Models](models.md) - SQLAlchemy ORM models  
- [Extractors](extractors.md) - Data extraction system
- [Builders](builders.md) - Derived data construction
- [Annotators](annotators.md) - Annotation system
- [CLI Reference](cli.md) - Command-line interface