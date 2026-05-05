# utils.py
"""Shared utilities for line numbering, spans, and validation."""

from __future__ import annotations

from .schemas import Pass1ArticleOutline, Span


def number_lines(text: str) -> tuple[str, list[str]]:
    """Return a line-numbered version of text and the original split lines."""
    lines = text.splitlines()
    numbered = "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines))
    return numbered, lines


def span_dict(span: Span | dict) -> dict:
    if isinstance(span, Span):
        return span.model_dump()
    return span


def extract_span(lines: list[str], span: Span | dict) -> str:
    """Extract exact source text for a model-produced span."""
    s = span_dict(span)
    if not s.get("present", False):
        return ""
    start = max(int(s["start_line"]), 1)
    end = min(int(s["end_line"]), len(lines))
    if start > end:
        return ""
    return "\n".join(lines[start - 1 : end]).strip()


def numbered_excerpt(lines: list[str], span: Span | dict) -> str:
    """Return a line-numbered excerpt for a span."""
    s = span_dict(span)
    if not s.get("present", False):
        return ""
    start = max(int(s["start_line"]), 1)
    end = min(int(s["end_line"]), len(lines))
    if start > end:
        return ""
    return "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1))


def span_line_count(span: Span | dict) -> int:
    s = span_dict(span)
    if not s.get("present", False):
        return 0
    return max(0, int(s["end_line"]) - int(s["start_line"]) + 1)


def normalize_pass1_evidence(outline: Pass1ArticleOutline) -> Pass1ArticleOutline:
    """Fill missing evidence line spans from already-validated content spans.

    Some smaller models reliably infer the right structure but omit Evidence.lines.
    Rather than rejecting otherwise usable parses, recover conservative evidence:
    - explicit or inferred title evidence defaults to the article_span start line;
    - explicit section heading evidence defaults to the section content_span start line;
    - missing refinement evidence defaults to the section content_span.
    """
    if outline.article_present and outline.article_span.present:
        if outline.title_source in {"explicit", "inferred"} and not outline.title_evidence.lines:
            line = outline.article_span.start_line
            outline.title_evidence.lines = [Span(present=True, start_line=line, end_line=line)]

    for section in outline.top_sections:
        if section.content_span.present:
            if section.heading_source.startswith("explicit_") and not section.heading_evidence.lines:
                line = section.content_span.start_line
                section.heading_evidence.lines = [Span(present=True, start_line=line, end_line=line)]
            if not section.refinement_evidence.lines:
                section.refinement_evidence.lines = [section.content_span]

    return outline


def section_sort_key(section_id: str) -> list[int]:
    """Sort canonical dotted numeric section IDs like 1, 1.2, 1.2.3."""
    return [int(x) for x in section_id.split(".")]


def validate_result(result: dict, total_lines: int) -> list[str]:
    errors: list[str] = []

    def check_span(name: str, span: dict) -> None:
        if not span.get("present", False):
            return
        start = int(span.get("start_line", 0))
        end = int(span.get("end_line", 0))
        if start < 1:
            errors.append(f"{name}: start_line < 1")
        if end < start:
            errors.append(f"{name}: end_line < start_line")
        if end > total_lines:
            errors.append(f"{name}: end_line exceeds document length")

    for span_name in ["preamble_span", "article_span", "followup_span"]:
        if span_name in result:
            check_span(span_name, result[span_name])

    if "title_evidence" in result:
        for i, ev_span in enumerate(result["title_evidence"].get("lines", [])):
            check_span(f"title_evidence.lines[{i}]", ev_span)

    section_ids = {s["section_id"] for s in result.get("sections", [])}

    for section in result.get("sections", []):
        sid = section["section_id"]
        parent = section.get("parent_id", "")

        if parent and parent not in section_ids:
            errors.append(f"Section {sid} has missing parent {parent}")

        check_span(f"section {sid}.content_span", section["content_span"])

        for i, ev_span in enumerate(section.get("heading_evidence", {}).get("lines", [])):
            check_span(f"section {sid}.heading_evidence.lines[{i}]", ev_span)

        for i, ev_span in enumerate(section.get("refinement_evidence", {}).get("lines", [])):
            check_span(f"section {sid}.refinement_evidence.lines[{i}]", ev_span)

    return errors
