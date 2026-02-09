# llm_archive/cli.py
"""Command-line interface for LLM archive operations."""

import json
from pathlib import Path

import fire
from loguru import logger
from sqlalchemy import text

from llm_archive.config import DATABASE_URL
from llm_archive.db import get_session, init_schema, reset_schema
from llm_archive.extractors import ChatGPTExtractor, ClaudeExtractor
from llm_archive.builders import PromptResponseBuilder
from llm_archive.annotators.registry import get_default_registry


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
            incremental: Don't soft-delete messages missing from this import.
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
            incremental: Don't soft-delete messages missing from this import.
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
        """Import from multiple sources."""
        results = {}

        if chatgpt_path:
            results["chatgpt"] = self.import_chatgpt(
                chatgpt_path,
                assume_immutable=assume_immutable,
                incremental=incremental,
            )

        if claude_path:
            results["claude"] = self.import_claude(
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
        results["prompt-responses"] = self.build_prompt_responses()
        return results

    # ================================================================
    # Annotations
    # ================================================================

    def annotate(self, annotator: str | None = None, clear: bool = False):
        """Run annotators with cursor-based incremental processing.

        Args:
            annotator: Run only this annotator (by class name). Omit for all.
            clear: Delete cursors before running so all entities are reprocessed.
        """
        registry = get_default_registry()

        with get_session(self.db_url) as session:
            if clear:
                self._clear_cursors(session, annotator)

            if annotator:
                count = registry.run_one(annotator, session)
                results = {annotator: count}
            else:
                results = registry.run_all(session)

        logger.info("Annotation results: {}", results)
        return results

    def list_annotators(self):
        """List all registered annotators with metadata."""
        registry = get_default_registry()
        rows = []
        for cls in registry.list_annotators():
            rows.append({
                "name": cls.__name__,
                "entity_type": cls.ENTITY_TYPE.value if cls.ENTITY_TYPE else "?",
                "key": cls.ANNOTATION_KEY,
                "priority": cls.PRIORITY,
                "version": cls.VERSION,
            })

        print(f"\n{'Name':<30} {'Entity Type':<18} {'Key':<20} {'Priority':>8} {'Version':>8}")
        print("-" * 90)
        for r in rows:
            print(f"{r['name']:<30} {r['entity_type']:<18} {r['key']:<20} {r['priority']:>8} {r['version']:>8}")
        print()
        return rows

    def cursor_status(self):
        """Show status of all annotator cursors."""
        from llm_archive.models.derived import AnnotatorCursor

        with get_session(self.db_url) as session:
            cursors = (
                session.query(AnnotatorCursor)
                .order_by(AnnotatorCursor.annotator_name, AnnotatorCursor.annotator_version)
                .all()
            )

            if not cursors:
                print("No cursors found.")
                return []

            print(f"\n{'Annotator':<30} {'Ver':>5} {'Entity Type':<18} {'HWM':<22} {'Processed':>10} {'Created':>10} {'Runtime':>10}")
            print("-" * 115)
            for c in cursors:
                hwm = c.high_water_mark.strftime("%Y-%m-%d %H:%M") if c.high_water_mark else "epoch"
                runtime = f"{c.cumulative_runtime_seconds:.1f}s"
                print(f"{c.annotator_name:<30} {c.annotator_version:>5} {c.entity_type:<18} {hwm:<22} {c.entities_processed:>10} {c.annotations_created:>10} {runtime:>10}")
            print()

    def _clear_cursors(self, session, annotator_name: str | None = None):
        """Delete cursors to force reprocessing."""
        if annotator_name:
            session.execute(
                text("DELETE FROM derived.annotator_cursors WHERE annotator_name = :name"),
                {"name": annotator_name},
            )
            logger.info("Cleared cursors for {}", annotator_name)
        else:
            session.execute(text("DELETE FROM derived.annotator_cursors"))
            logger.info("Cleared all annotator cursors")
        session.flush()

    # ================================================================
    # Analysis
    # ================================================================

    def stats(self):
        """Show database statistics."""
        with get_session(self.db_url) as session:
            stats = {}

            stats["dialogues"] = session.execute(
                text("SELECT COUNT(*) FROM raw.dialogues")
            ).scalar()

            stats["messages"] = session.execute(
                text("SELECT COUNT(*) FROM raw.messages WHERE deleted_at IS NULL")
            ).scalar()

            stats["content_parts"] = session.execute(
                text("SELECT COUNT(*) FROM raw.content_parts")
            ).scalar()

            sources = session.execute(
                text("SELECT source, COUNT(*) FROM raw.dialogues GROUP BY source")
            ).fetchall()
            stats["by_source"] = {s: c for s, c in sources}

            stats["prompt_responses"] = session.execute(
                text("SELECT COUNT(*) FROM derived.prompt_responses")
            ).scalar()

        print("\n=== LLM Archive Statistics ===\n")
        print("Raw Data:")
        print(f"  Dialogues: {stats['dialogues']}")
        print(f"  Messages: {stats['messages']}")
        print(f"  Content Parts: {stats['content_parts']}")
        print(f"  By Source: {stats['by_source']}")
        print(f"\nDerived Data:")
        print(f"  Prompt-Responses: {stats['prompt_responses']}")

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
            assume_immutable: Skip content hash checks
            incremental: Don't soft-delete missing messages
        """
        results = {}

        if init_db:
            self.init(schema_dir)

        if chatgpt_path or claude_path:
            results["import"] = self.import_all(
                chatgpt_path=chatgpt_path,
                claude_path=claude_path,
                assume_immutable=assume_immutable,
                incremental=incremental,
            )

        results["build"] = self.build_all()
        results["annotate"] = self.annotate()

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
