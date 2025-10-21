#!/usr/bin/env python3
"""
Example showing how to use the new processing machinery to replace notebook workflows.

This replaces the processing logic that was embedded in dev.ipynb and sandbox.ipynb.
"""

from conversation_tagger import (
    load_conversations, 
    ProcessingPipeline, 
    BatchProcessor, 
    ProcessingConfig,
    FilterCriteria
)
from conversation_tagger.data.validation import validate_and_generate_schema
from conversation_tagger.processing.filters import create_gizmo_filter, create_claude_obsidian_filter

# Example 1: Simple single-source processing (replaces load_convs + basic tagging)
def process_single_source_example():
    """Basic processing of a single source."""
    print("=== Single Source Processing ===")
    
    # Load and process conversations from OpenAI
    pipeline = ProcessingPipeline('oai', ProcessingConfig(
        sources=['oai'],
        output_dir="../data/staging"
    ))
    
    results = pipeline.process()
    print(f"Processed {results['tagged_count']} conversations from {results['source']}")


# Example 2: Batch processing multiple sources (replaces the for source in ['oai', 'claude'] loop)
def batch_processing_example():
    """Batch processing across multiple sources."""
    print("=== Batch Processing ===")
    
    config = ProcessingConfig(
        sources=['oai', 'claude'],
        output_dir="../data/staging"
    )
    
    processor = BatchProcessor(config)
    results = processor.process_all()
    
    print(f"Batch processing completed:")
    for source, source_results in results['results_by_source'].items():
        if 'error' not in source_results:
            print(f"  {source}: {source_results['generated_count']} notes generated")


# Example 3: Processing with gizmo filter (replaces the gizmo_id filtering logic)
def gizmo_filtering_example():
    """Process conversations that used a specific gizmo."""
    print("=== Gizmo Filtering ===")
    
    # Filter for specific gizmo (equivalent to the g-IibMsD7w8 filter in notebook)
    target_gizmo = 'g-IibMsD7w8'  # Replace with actual gizmo ID
    
    config = ProcessingConfig(
        sources=['oai'],
        output_dir="../data/staging",
        filter_criteria=create_gizmo_filter(target_gizmo)
    )
    
    processor = BatchProcessor(config)
    results = processor.process_all()
    
    print(f"Generated notes for conversations using gizmo {target_gizmo}")


# Example 4: Claude Obsidian chat processing (replaces the llm_obsidian_chat logic)
def claude_obsidian_example():
    """Process Claude conversations that are Obsidian chats."""
    print("=== Claude Obsidian Chats ===")
    
    # Define which conversation IDs are Obsidian chats
    llm_obsidian_chats = {
        'chat-id-1', 'chat-id-2'  # Replace with actual IDs
    }
    
    # Custom rule for Claude obsidian chats
    source_rules = {
        'claude': {
            'llm_obsidian_chat': lambda conv: conv.conversation_id in llm_obsidian_chats
        }
    }
    
    config = ProcessingConfig(
        sources=['claude'],
        output_dir="../data/staging",
        source_rules=source_rules,
        filter_criteria=create_claude_obsidian_filter(llm_obsidian_chats)
    )
    
    processor = BatchProcessor(config)
    results = processor.process_all()
    
    print(f"Processed Claude Obsidian chats: {results}")


# Example 5: Schema validation (replaces the genson SchemaBuilder logic)
def schema_validation_example():
    """Validate conversation data and generate schema."""
    print("=== Schema Validation ===")
    
    # Load conversations
    oai_conversations = load_conversations('oai')
    claude_conversations = load_conversations('claude')
    
    # Validate and generate schemas
    oai_schema = validate_and_generate_schema(
        oai_conversations, 
        'oai', 
        output_path='../docs/chatgpt.schema.json'
    )
    
    claude_schema = validate_and_generate_schema(
        claude_conversations, 
        'claude',
        output_path='../docs/claude.schema.json'
    )
    
    print(f"Generated schemas for {len(oai_conversations)} OpenAI and {len(claude_conversations)} Claude conversations")


# Example 6: Custom filtering (replaces complex notebook filtering logic)
def custom_filtering_example():
    """Example of advanced filtering criteria."""
    print("=== Custom Filtering ===")
    
    # Filter for conversations with specific characteristics
    criteria = FilterCriteria(
        required_annotations={'has_code_blocks', 'has_github_repos'},
        forbidden_annotations={'user_has_attachments'},
        custom_filters=[
            lambda conv: conv.exchange_count > 5,  # Multi-turn conversations
            lambda conv: len(conv.get_all_user_text()) > 1000  # Substantial content
        ]
    )
    
    config = ProcessingConfig(
        sources=['oai', 'claude'],
        output_dir="../data/staging",
        filter_criteria=criteria
    )
    
    processor = BatchProcessor(config)
    results = processor.process_all()
    
    print(f"Custom filtering results: {results}")


if __name__ == "__main__":
    # Run examples - comment out any you don't want to run
    
    try:
        process_single_source_example()
    except Exception as e:
        print(f"Single source example failed: {e}")
    
    try:
        batch_processing_example()
    except Exception as e:
        print(f"Batch processing example failed: {e}")
    
    try:
        schema_validation_example()
    except Exception as e:
        print(f"Schema validation example failed: {e}")
    
    # Uncomment these if you have the necessary data/IDs
    # gizmo_filtering_example()
    # claude_obsidian_example()
    # custom_filtering_example()
    
    print("\n=== Processing Machinery Examples Complete ===")
