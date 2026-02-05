# llm_archive/cli.py
"""Command-line interface for LLM archive operations."""

import json
from pathlib import Path

import fire
from loguru import logger

from llm_archive.config import DATABASE_URL
from llm_archive.db import get_session, init_schema, reset_schema
from llm_archive.extractors import ChatGPTExtractor, ClaudeExtractor
from llm_archive.builders import PromptResponseBuilder
from llm_archive.annotators import (
    AnnotationManager,
    WikiCandidateAnnotator,
    NaiveTitleAnnotator,
)


class CLI:
    """LLM Archive - Conversation ingestion and analysis."""
    
    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or DATABASE_URL
    
    # ================================================================
    # Schema Management
    # ================================================================
    
    def init(self, schema_dir: str = "schema"):
        """Initialize database schema."""
        init_schema(self.db_url, Path(schema_dir))
        logger.info("Schema initialized")
    
    def reset(self, confirm: bool = False, schema_dir: str = "schema"):
        """Reset database (drops and recreates schema)."""
        if not confirm:
            logger.warning("Pass --confirm to reset database")
            return
        reset_schema(self.db_url, Path(schema_dir))
        logger.info("Database reset")
    
    # ================================================================
    # Import
    # ================================================================
    
    def import_chatgpt(
        self, 
        path: str,
        assume_immutable: bool = False,
        incremental: bool = False,
    ):
        """Import ChatGPT conversations.json export.
        
        Args:
            path: Path to conversations.json file
            assume_immutable: Skip content hash checks for existing messages.
                Faster, but won't detect in-place message edits. Use when
                the provider treats messages as immutable (edits create new IDs).
            incremental: Don't soft-delete messages missing from this import.
                Use when importing partial/delta exports.
        """
        data = self._load_json(path)
        
        with get_session(self.db_url) as session:
            extractor = ChatGPTExtractor(
                session,
                assume_immutable=assume_immutable,
                incremental=incremental,
            )
            counts = extractor.extract_all(data)
        
        return counts
    
    def import_claude(
        self, 
        path: str,
        assume_immutable: bool = False,
        incremental: bool = False,
    ):
        """Import Claude conversations.json export.
        
        Args:
            path: Path to conversations.json file
            assume_immutable: Skip content hash checks for existing messages.
                Faster, but won't detect in-place message edits. Use when
                the provider treats messages as immutable (edits create new IDs).
            incremental: Don't soft-delete messages missing from this import.
                Use when importing partial/delta exports.
        """
        data = self._load_json(path)
        
        with get_session(self.db_url) as session:
            extractor = ClaudeExtractor(
                session,
                assume_immutable=assume_immutable,
                incremental=incremental,
            )
            counts = extractor.extract_all(data)
        
        return counts
    
    def import_all(
        self,
        chatgpt_path: str | None = None,
        claude_path: str | None = None,
        assume_immutable: bool = False,
        incremental: bool = False,
    ):
        """Import from multiple sources.
        
        Args:
            chatgpt_path: Path to ChatGPT conversations.json
            claude_path: Path to Claude conversations.json
            assume_immutable: Skip content hash checks for existing messages
            incremental: Don't soft-delete messages missing from this import
        """
        results = {}
        
        if chatgpt_path:
            results['chatgpt'] = self.import_chatgpt(
                chatgpt_path,
                assume_immutable=assume_immutable,
                incremental=incremental,
            )
        
        if claude_path:
            results['claude'] = self.import_claude(
                claude_path,
                assume_immutable=assume_immutable,
                incremental=incremental,
            )
        
        return results
    
    # ================================================================
    # Build Derived Structures
    # ================================================================
    

    def build_prompt_responses(self):
        """Build prompt-response pairs (no tree dependency)."""
        with get_session(self.db_url) as session:
            builder = PromptResponseBuilder(session)
            counts = builder.build_all()
        return counts

    def build_all(self):
        """Build all derived structures."""
        results = {}
        results['prompt-responses'] = self.build_prompt_responses()
        return results
    
    # ================================================================
    # Annotations
    # ================================================================
    
    def annotate(self):
        """Run all annotators."""
        with get_session(self.db_url) as session:
            manager = AnnotationManager(session)
            # Message annotators
            # manager.register(WikiLinkAnnotator)
            # manager.register(CodeBlockAnnotator)
            # manager.register(LatexAnnotator)
            # manager.register(ContinuationAnnotator)
            # # Exchange annotators
            # manager.register(ExchangeTypeAnnotator)
            
            # Prompt-response annotators
            manager.register(WikiCandidateAnnotator)
            manager.register(NaiveTitleAnnotator)
            results = manager.run_all()
        
        return results
    
    # ================================================================
    # Analysis
    # ================================================================
    
    def stats(self):
        """Show database statistics."""
        from sqlalchemy import text
        
        with get_session(self.db_url) as session:
            stats = {}
            
            # Raw counts
            stats['dialogues'] = session.execute(
                text("SELECT COUNT(*) FROM raw.dialogues")
            ).scalar()
            
            stats['messages'] = session.execute(
                text("SELECT COUNT(*) FROM raw.messages")
            ).scalar()
            
            stats['content_parts'] = session.execute(
                text("SELECT COUNT(*) FROM raw.content_parts")
            ).scalar()
            
            # By source
            sources = session.execute(
                text("SELECT source, COUNT(*) FROM raw.dialogues GROUP BY source")
            ).fetchall()
            stats['by_source'] = {s: c for s, c in sources}
            
            stats['annotations'] = session.execute(
                text("SELECT COUNT(*) FROM derived.annotations WHERE superseded_at IS NULL")
            ).scalar()
            
        
        # Print nicely
        print("\n=== LLM Archive Statistics ===\n")
        print("Raw Data:")
        print(f"  Dialogues: {stats['dialogues']}")
        print(f"  Messages: {stats['messages']}")
        print(f"  Content Parts: {stats['content_parts']}")
        print(f"  By Source: {stats['by_source']}")
        
        print("\nDerived Data:")
        print(f"  Annotations: {stats['annotations']}")
        
        return stats
    
    # ================================================================
    # Full Pipeline
    # ================================================================
    
    def run(
        self,
        chatgpt_path: str | None = None,
        claude_path: str | None = None,
        init_db: bool = False,
        schema_dir: str = "schema",
        assume_immutable: bool = False,
        incremental: bool = False,
    ):
        """Run full pipeline: import, build, annotate.
        
        Args:
            chatgpt_path: Path to ChatGPT conversations.json
            claude_path: Path to Claude conversations.json
            init_db: Initialize database schema before import
            schema_dir: Directory containing schema files
            assume_immutable: Skip content hash checks for existing messages
            incremental: Don't soft-delete messages missing from this import
        """
        results = {}
        
        if init_db:
            self.init(schema_dir)
        
        # Import
        if chatgpt_path or claude_path:
            results['import'] = self.import_all(
                chatgpt_path=chatgpt_path,
                claude_path=claude_path,
                assume_immutable=assume_immutable,
                incremental=incremental,
            )
        
        # Build
        results['build'] = self.build_all()
        
        # Annotate
        results['annotate'] = self.annotate()
        
        # Stats
        self.stats()
        
        return results
    
    # ================================================================
    # Helpers
    # ================================================================
    
    def _load_json(self, path: str) -> list[dict]:
        """Load JSON file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        logger.info(f"Loading {path}")
        with p.open() as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("Expected JSON array")
        
        logger.info(f"Loaded {len(data)} items")
        return data


def main():
    """Entry point."""
    fire.Fire(CLI)


if __name__ == "__main__":
    main()
