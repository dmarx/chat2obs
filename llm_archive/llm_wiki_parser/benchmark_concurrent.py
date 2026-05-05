# benchmark_concurrency.py
"""Small benchmarking helpers for parser concurrency experiments."""

from __future__ import annotations

import statistics
import time
from collections.abc import Callable
from typing import Any

from .parser import parse_article_multi_pass


def benchmark_parse_concurrency(
    text: str,
    *,
    concurrency_values: list[int] | tuple[int, ...] = (1, 2, 4, 8),
    repeats: int = 1,
    parser_fn: Callable[..., dict] = parse_article_multi_pass,
    parser_kwargs: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Benchmark parse latency for several max_concurrency values.

    Returns a list of dictionaries so the result is easy to display as a DataFrame.
    """
    parser_kwargs = dict(parser_kwargs or {})
    rows: list[dict[str, Any]] = []

    for max_concurrency in concurrency_values:
        durations: list[float] = []
        last_result: dict | None = None
        last_error: str | None = None

        for _ in range(repeats):
            started = time.perf_counter()
            try:
                last_result = parser_fn(
                    text,
                    max_concurrency=max_concurrency,
                    **parser_kwargs,
                )
                last_error = None
            except Exception as exc:  # benchmark should record failures, not hide them
                last_result = None
                last_error = repr(exc)
            durations.append(time.perf_counter() - started)

        rows.append(
            {
                "max_concurrency": max_concurrency,
                "repeats": repeats,
                "mean_seconds": statistics.mean(durations),
                "min_seconds": min(durations),
                "max_seconds": max(durations),
                "success": last_error is None,
                "error": last_error,
                "num_sections": len(last_result.get("sections", [])) if last_result else None,
                "validation_errors": last_result.get("validation_errors", None) if last_result else None,
            }
        )

    return rows
