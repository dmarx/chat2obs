# llm_archive/annotators/registry.py
"""Annotator registry: discovers, registers, and runs annotators in priority order.

Usage:
    from llm_archive.annotators.registry import AnnotatorRegistry

    registry = AnnotatorRegistry()
    # auto-discovers built-in annotators, or register manually:
    registry.register(MyCustomAnnotator)

    with get_session(db_url) as session:
        results = registry.run_all(session)
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy.orm import Session

from llm_archive.annotators.base import BaseAnnotator


class AnnotatorRegistry:
    """Central registry of annotator classes.

    Annotators are sorted by PRIORITY descending (highest priority first).
    """

    def __init__(self) -> None:
        self._annotators: dict[str, type[BaseAnnotator]] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, cls: type[BaseAnnotator]) -> None:
        """Register an annotator class."""
        self._annotators[cls.__name__] = cls

    def register_many(self, classes: list[type[BaseAnnotator]]) -> None:
        for cls in classes:
            self.register(cls)

    def unregister(self, name: str) -> None:
        self._annotators.pop(name, None)

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

    def list_annotators(self) -> list[type[BaseAnnotator]]:
        """Return registered annotators sorted by priority (descending)."""
        return sorted(
            self._annotators.values(),
            key=lambda c: c.PRIORITY,
            reverse=True,
        )

    def get(self, name: str) -> type[BaseAnnotator] | None:
        return self._annotators.get(name)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_all(self, session: Session) -> dict[str, int]:
        """Run every registered annotator in priority order.

        Returns dict mapping annotator name → annotations created.
        """
        results: dict[str, int] = {}
        for cls in self.list_annotators():
            logger.info("Running annotator: {} (priority={})", cls.__name__, cls.PRIORITY)
            annotator = cls(session)
            count = annotator.compute()
            results[cls.__name__] = count
        session.commit()
        return results

    def run_one(self, name: str, session: Session) -> int:
        """Run a single annotator by class name.

        Raises KeyError if not registered.
        """
        cls = self._annotators.get(name)
        if cls is None:
            raise KeyError(
                f"Annotator '{name}' not registered. "
                f"Available: {sorted(self._annotators)}"
            )
        annotator = cls(session)
        count = annotator.compute()
        session.commit()
        return count


def get_default_registry() -> AnnotatorRegistry:
    """Build a registry with all built-in annotators."""
    from llm_archive.annotators.content_part import CONTENT_PART_ANNOTATORS
    from llm_archive.annotators.prompt_response import PROMPT_RESPONSE_ANNOTATORS

    registry = AnnotatorRegistry()
    registry.register_many(CONTENT_PART_ANNOTATORS)
    registry.register_many(PROMPT_RESPONSE_ANNOTATORS)
    return registry
