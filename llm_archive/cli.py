# llm_archive/cli.py
"""Command-line interface for LLM archive operations."""

import json
from pathlib import Path

import fire
from loguru import logger

from llm_archive.db import get_session, init_schema, reset_schema
from llm_archive.extractors import ChatGPTExtractor, ClaudeExtractor
from llm_archive.builders import TreeBuilder, ExchangeBuilder, HashBuilder
from llm_archive.labelers import (
    LabelManager,
    WikiLinkLabeler,
    CodeBlockLabeler,
    LatexLabeler,
    ContinuationLabeler,
)


class CLI:
    """LLM Archive - Conversation ingestion and analysis."""
    
    def __init__(self, db_url: str = "postgresql://localhost/llm_archive"):
        self.db_url = db_url
    
    # ================================================================
    # Schema Management
    # ================================================================
    
    def init(self, schema_dir: str = "schema"):
        """Initialize database schema."""
        init_schema(self.db_url, Path(schema_dir))
        logger.info("Schema initialized")
    
    def reset(self, confirm: bool = False):
        """Reset database (drops all data!)."""
        if not confirm:
            logger.warning("Pass --confirm to reset database")
            return
        reset_schema(self.db_url)
        logger.info("Database reset")
    
    # ================================================================
    # Import
    # ================================================================
    
    def import_chatgpt(self, path: str):
        """Import ChatGPT conversations.json export."""
        data = self._load_json(path)
        
        with get_session(self.db_url) as session:
            extractor = ChatGPTExtractor(session)
            counts = extractor.extract_all(data)
        
        return counts
    
    def import_claude(self, path: str):
        """Import Claude conversations.json export."""
        data = self._load_json(path)
        
        with get_session(self.db_url) as session:
            extractor = ClaudeExtractor(session)
            counts = extractor.extract_all(data)
        
        return counts
    
    def import_all(
        self,
        chatgpt_path: str | None = None,
        claude_path: str | None = None,
    ):
        """Import from multiple sources."""
        results = {}
        
        if chatgpt_path:
            results['chatgpt'] = self.import_chatgpt(chatgpt_path)
        
        if claude_path:
            results['claude'] = self.import_claude(claude_path)
        
        return results
    
    # ================================================================
    # Build Derived Structures
    # ================================================================
    
    def build_trees(self):
        """Build dialogue tree analysis."""
        with get_session(self.db_url) as session:
            builder = TreeBuilder(session)
            counts = builder.build_all()
        
        return counts
    
    def build_exchanges(self):
        """Build exchanges from linear sequences."""
        with get_session(self.db_url) as session:
            builder = ExchangeBuilder(session)
            counts = builder.build_all()
        
        return counts
    
    def build_hashes(self):
        """Build content hashes for deduplication."""
        with get_session(self.db_url) as session:
            builder = HashBuilder(session)
            counts = builder.build_all()
        
        return counts
    
    def build_all(self):
        """Build all derived structures."""
        results = {}
        results['trees'] = self.build_trees()
        results['exchanges'] = self.build_exchanges()
        results['hashes'] = self.build_hashes()
        return results
    
    # ================================================================
    # Labeling
    # ================================================================
    
    def label(self):
        """Run all labelers."""
        with get_session(self.db_url) as session:
            manager = LabelManager(session)
            manager.register(WikiLinkLabeler)
            manager.register(CodeBlockLabeler)
            manager.register(LatexLabeler)
            manager.register(ContinuationLabeler)
            results = manager.run_all()
        
        return results
    
    # ================================================================
    # Analysis
    # ================================================================
    
    def find_duplicates(
        self,
        entity_type: str = 'exchange',
        scope: str = 'assistant',
    ):
        """Find duplicate content."""
        with get_session(self.db_url) as session:
            builder = HashBuilder(session)
            duplicates = builder.find_duplicates(
                entity_type=entity_type,
                scope=scope,
            )
        
        logger.info(f"Found {len(duplicates)} duplicate groups")
        
        for dup in duplicates[:10]:  # Show first 10
            print(f"\nHash: {dup['hash'][:16]}...")
            print(f"  Type: {dup['entity_type']}, Scope: {dup['scope']}")
            print(f"  Count: {dup['count']}")
            print(f"  IDs: {[str(i)[:8] for i in dup['entity_ids'][:5]]}")
        
        return duplicates
    
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
            
            # Derived counts
            stats['dialogue_trees'] = session.execute(
                text("SELECT COUNT(*) FROM derived.dialogue_trees")
            ).scalar()
            
            stats['linear_sequences'] = session.execute(
                text("SELECT COUNT(*) FROM derived.linear_sequences")
            ).scalar()
            
            stats['exchanges'] = session.execute(
                text("SELECT COUNT(*) FROM derived.exchanges")
            ).scalar()
            
            stats['labels'] = session.execute(
                text("SELECT COUNT(*) FROM derived.labels WHERE superseded_at IS NULL")
            ).scalar()
            
            stats['content_hashes'] = session.execute(
                text("SELECT COUNT(*) FROM derived.content_hashes")
            ).scalar()
            
            # Tree stats
            tree_stats = session.execute(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_linear THEN 1 ELSE 0 END) as linear,
                        SUM(CASE WHEN has_regenerations THEN 1 ELSE 0 END) as with_regenerations,
                        SUM(CASE WHEN has_edits THEN 1 ELSE 0 END) as with_edits
                    FROM derived.dialogue_trees
                """)
            ).fetchone()
            
            if tree_stats:
                stats['tree_analysis'] = {
                    'total': tree_stats[0],
                    'linear': tree_stats[1],
                    'with_regenerations': tree_stats[2],
                    'with_edits': tree_stats[3],
                }
        
        # Print nicely
        print("\n=== LLM Archive Statistics ===\n")
        print("Raw Data:")
        print(f"  Dialogues: {stats['dialogues']}")
        print(f"  Messages: {stats['messages']}")
        print(f"  Content Parts: {stats['content_parts']}")
        print(f"  By Source: {stats['by_source']}")
        
        print("\nDerived Data:")
        print(f"  Dialogue Trees: {stats['dialogue_trees']}")
        print(f"  Linear Sequences: {stats['linear_sequences']}")
        print(f"  Exchanges: {stats['exchanges']}")
        print(f"  Labels: {stats['labels']}")
        print(f"  Content Hashes: {stats['content_hashes']}")
        
        if stats.get('tree_analysis'):
            ta = stats['tree_analysis']
            print("\nTree Analysis:")
            print(f"  Total: {ta['total']}")
            print(f"  Linear: {ta['linear']}")
            print(f"  With Regenerations: {ta['with_regenerations']}")
            print(f"  With Edits: {ta['with_edits']}")
        
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
    ):
        """Run full pipeline: import, build, label."""
        results = {}
        
        if init_db:
            self.init(schema_dir)
        
        # Import
        if chatgpt_path or claude_path:
            results['import'] = self.import_all(
                chatgpt_path=chatgpt_path,
                claude_path=claude_path,
            )
        
        # Build
        results['build'] = self.build_all()
        
        # Label
        results['label'] = self.label()
        
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