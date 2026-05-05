"""Post-processing from verbose parser output to finalized article structure."""

from __future__ import annotations

import json
import re
from typing import Literal

from .schemas import FinalArticle, FinalArticleSection, FinalConversationWrapper, FinalSourceSpan


def _source_span_from_dict(span: dict, *, include_spans: bool) -> FinalSourceSpan | None:
    if not include_spans:
        return None
    if not span.get("present", False):
        return None
    return FinalSourceSpan(start_line=int(span["start_line"]), end_line=int(span["end_line"]))


def _section_id_sort_key(section: dict) -> list[int]:
    return [int(part) for part in section["section_id"].split(".")]


def _article_line_map(parsed: dict) -> dict[int, str]:
    """Map original source line numbers to article_text lines when possible."""
    article_span = parsed.get("article_span", {})
    article_text = str(parsed.get("article_text", ""))
    if not article_span.get("present", False):
        return {}
    start = int(article_span.get("start_line", 1))
    return {start + i: line for i, line in enumerate(article_text.splitlines())}


def _extract_from_article_line_map(line_map: dict[int, str], span: dict) -> str:
    if not span.get("present", False):
        return ""
    if not line_map:
        return ""
    start = int(span["start_line"])
    end = int(span["end_line"])
    return "\n".join(line_map[i] for i in range(start, end + 1) if i in line_map).strip()


def _subtract_child_spans_from_parent(
    *,
    line_map: dict[int, str],
    parent_span: dict,
    child_spans: list[dict],
) -> str:
    """Return parent direct text by removing lines covered by immediate children."""
    if not parent_span.get("present", False):
        return ""
    if not line_map:
        return ""

    start = int(parent_span["start_line"])
    end = int(parent_span["end_line"])
    removed: set[int] = set()

    for child_span in child_spans:
        if not child_span.get("present", False):
            continue
        child_start = max(start, int(child_span["start_line"]))
        child_end = min(end, int(child_span["end_line"]))
        if child_start <= child_end:
            removed.update(range(child_start, child_end + 1))

    kept_lines = [line_map[i] for i in range(start, end + 1) if i in line_map and i not in removed]
    return "\n".join(kept_lines).strip()


def _strip_leading_section_heading(text: str, heading: str) -> str:
    """Remove a duplicated explicit heading line from section content."""
    text = text.strip()
    if not text:
        return ""

    lines = text.splitlines()
    if not lines:
        return ""

    first = lines[0].strip()
    normalized_heading = heading.strip().strip("#").strip()
    normalized_first = first.strip("#").strip()

    if normalized_first == normalized_heading:
        return "\n".join(lines[1:]).strip()

    return text


def _strip_promoted_list_label(text: str, heading: str) -> str:
    """Remove duplicated labels like '1. **Heading**:' from promoted child content."""
    text = text.strip()
    heading = heading.strip()
    if not text or not heading:
        return text

    escaped_heading = re.escape(heading)
    pattern = (
        r"^\s*"
        r"(?:[-*+]\s+|\d+[.)]\s+)?"
        r"(?:\*\*)?"
        + escaped_heading
        + r"(?:\*\*)?\s*:?\s*"
    )
    return re.sub(pattern, "", text, count=1).strip()


def _looks_like_introduction_heading(heading: str) -> bool:
    heading = heading.strip().lower()
    return heading.startswith("intro") or heading in {"overview", "background"}


def _choose_lead_section_heading(
    root_sections: list[dict],
    *,
    preferred_heading: str,
    fallback_heading: str,
) -> str:
    existing = {str(section.get("heading", "")).strip().lower() for section in root_sections}
    if any(_looks_like_introduction_heading(heading) for heading in existing):
        return fallback_heading
    if preferred_heading.strip().lower() in existing:
        return fallback_heading
    return preferred_heading


def _extract_article_lead_text(
    parsed: dict,
    root_sections: list[dict],
    line_map: dict[int, str],
) -> tuple[str, dict]:
    """Extract article-level prose before the first top-level section."""
    article_span = parsed.get("article_span", {})
    if not article_span.get("present", False) or not line_map or not root_sections:
        return "", {"present": False, "start_line": 0, "end_line": 0}

    article_start = int(article_span["start_line"])
    first_section_start = min(
        int(section["content_span"]["start_line"])
        for section in root_sections
        if section.get("content_span", {}).get("present", False)
    )
    lead_end = first_section_start - 1
    if lead_end < article_start:
        return "", {"present": False, "start_line": 0, "end_line": 0}

    content = "\n".join(
        line_map[i]
        for i in range(article_start, lead_end + 1)
        if i in line_map
    ).strip()
    if not content:
        return "", {"present": False, "start_line": 0, "end_line": 0}

    return content, {"present": True, "start_line": article_start, "end_line": lead_end}


def _build_final_section_tree(
    parsed: dict,
    *,
    include_spans: bool = False,
    drop_empty_content: bool = False,
    parent_content_mode: Literal["direct", "full"] = "direct",
    strip_promoted_list_labels: bool = True,
    synthesize_lead_section: bool = True,
    lead_section_heading: str = "Introduction",
    lead_section_fallback_heading: str = "Overview",
) -> list[FinalArticleSection]:
    """Convert parser flat sections into a clean nested article tree.

    parent_content_mode="direct" removes immediate child spans from parent content
    so parent sections do not duplicate all child content. Use "full" to preserve
    every parent section's full span.
    """
    raw_sections = sorted(parsed.get("sections", []), key=_section_id_sort_key)

    raw_by_parent: dict[str, list[dict]] = {}
    for raw in raw_sections:
        raw_by_parent.setdefault(raw.get("parent_id", ""), []).append(raw)

    line_map = _article_line_map(parsed)
    nodes_by_id: dict[str, FinalArticleSection] = {}
    roots: list[FinalArticleSection] = []

    root_raw_sections = raw_by_parent.get("", [])
    if synthesize_lead_section:
        lead_content, lead_span = _extract_article_lead_text(parsed, root_raw_sections, line_map)
        if lead_content:
            roots.append(
                FinalArticleSection(
                    heading=_choose_lead_section_heading(
                        root_raw_sections,
                        preferred_heading=lead_section_heading,
                        fallback_heading=lead_section_fallback_heading,
                    ),
                    content=lead_content,
                    children=[],
                    source_span=_source_span_from_dict(lead_span, include_spans=include_spans),
                )
            )

    for raw in raw_sections:
        section_id = raw["section_id"]
        parent_id = raw.get("parent_id", "")
        heading = str(raw.get("heading", "")).strip()
        span = raw.get("content_span", {})
        child_spans = [child.get("content_span", {}) for child in raw_by_parent.get(section_id, [])]

        if parent_content_mode == "direct" and child_spans:
            content_text = _subtract_child_spans_from_parent(
                line_map=line_map,
                parent_span=span,
                child_spans=child_spans,
            )
        else:
            content_text = _extract_from_article_line_map(line_map, span)
            if not content_text:
                content_text = str(raw.get("content_text", "")).strip()

        content = _strip_leading_section_heading(content_text, heading)
        if strip_promoted_list_labels and parent_id:
            content = _strip_promoted_list_label(content, heading)

        if drop_empty_content and not content and not heading:
            continue

        node = FinalArticleSection(
            heading=heading,
            content=content,
            children=[],
            source_span=_source_span_from_dict(span, include_spans=include_spans),
        )

        nodes_by_id[section_id] = node
        if parent_id and parent_id in nodes_by_id:
            nodes_by_id[parent_id].children.append(node)
        else:
            roots.append(node)

    return roots


def finalize_article_parse(
    parsed: dict,
    *,
    include_spans: bool = False,
    include_conversation: bool = False,
    drop_empty_content: bool = False,
    parent_content_mode: Literal["direct", "full"] = "direct",
    strip_promoted_list_labels: bool = True,
    synthesize_lead_section: bool = True,
    lead_section_heading: str = "Introduction",
    lead_section_fallback_heading: str = "Overview",
) -> dict:
    """Collapse verbose parser output into a finalized article structure.

    Removes parser machinery such as evidence, confidence, refinement signals,
    raw pass-1 sections, validation errors, and parse notes.
    """
    sections = _build_final_section_tree(
        parsed,
        include_spans=include_spans,
        drop_empty_content=drop_empty_content,
        parent_content_mode=parent_content_mode,
        strip_promoted_list_labels=strip_promoted_list_labels,
        synthesize_lead_section=synthesize_lead_section,
        lead_section_heading=lead_section_heading,
        lead_section_fallback_heading=lead_section_fallback_heading,
    )

    conversation = None
    if include_conversation:
        conversation = FinalConversationWrapper(
            preamble=str(parsed.get("conversational_preamble", "")).strip(),
            followup=str(parsed.get("conversational_followup", "")).strip(),
        )

    final = FinalArticle(
        article_present=bool(parsed.get("article_present", False)),
        article_kind=parsed.get("article_kind", "not_article"),
        title=str(parsed.get("title", "")).strip(),
        summary=str(parsed.get("summary", "")).strip(),
        article_text=str(parsed.get("article_text", "")).strip(),
        sections=sections,
        conversation=conversation,
    )

    return final.model_dump(exclude_none=True)


def finalize_parsed_article_json(
    parsed: dict,
    *,
    include_spans: bool = False,
    include_conversation: bool = False,
    drop_empty_content: bool = False,
    parent_content_mode: Literal["direct", "full"] = "direct",
    strip_promoted_list_labels: bool = True,
    synthesize_lead_section: bool = True,
    lead_section_heading: str = "Introduction",
    lead_section_fallback_heading: str = "Overview",
    indent: int = 2,
) -> str:
    """Return finalized article structure as JSON."""
    final = finalize_article_parse(
        parsed,
        include_spans=include_spans,
        include_conversation=include_conversation,
        drop_empty_content=drop_empty_content,
        parent_content_mode=parent_content_mode,
        strip_promoted_list_labels=strip_promoted_list_labels,
        synthesize_lead_section=synthesize_lead_section,
        lead_section_heading=lead_section_heading,
        lead_section_fallback_heading=lead_section_fallback_heading,
    )
    return json.dumps(final, indent=indent, ensure_ascii=False)
