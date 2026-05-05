# parser.py
"""Multi-pass article parsing orchestration."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

from .model_io import DEFAULT_MODEL, call_json_schema, make_client
from .prompts import PASS1_SYSTEM, REFINE_SYSTEM
from .schemas import Pass1ArticleOutline, RefinementSignal, SectionRefinement, Span
from .utils import (
    extract_span,
    normalize_pass1_evidence,
    number_lines,
    numbered_excerpt,
    section_sort_key,
    span_line_count,
    validate_result,
)


def pass1_outline(
    text: str,
    *,
    client: OpenAI,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
    retries: int = 1,
    debug: bool = False,
) -> tuple[Pass1ArticleOutline, list[str]]:
    numbered, lines = number_lines(text)

    messages = [
        {"role": "system", "content": PASS1_SYSTEM},
        {
            "role": "user",
            "content": (
                "PASS 1: Parse the coarse article outline from this line-numbered document.\n\n"
                "<document>\n"
                f"{numbered}\n"
                "</document>"
            ),
        },
    ]

    outline = call_json_schema(
        client=client,
        model=model,
        messages=messages,
        schema_model=Pass1ArticleOutline,
        schema_name="pass1_article_outline",
        max_tokens=max_tokens,
        retries=retries,
        debug=debug,
    )

    outline = normalize_pass1_evidence(outline)
    return outline, lines


def refine_section_once(
    *,
    client: OpenAI,
    model: str,
    article_title: str,
    article_summary: str,
    article_text: str,
    parent_heading: str,
    parent_text_numbered: str,
    max_tokens: int = 2048,
    retries: int = 1,
    debug: bool = False,
) -> SectionRefinement:
    messages = [
        {"role": "system", "content": REFINE_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Article title: {article_title!r}\n"
                f"Article summary: {article_summary}\n\n"
                "Whole article context:\n"
                "<article>\n"
                f"{article_text}\n"
                "</article>\n\n"
                f"Parent heading: {parent_heading!r}\n\n"
                "Parent section with original line numbers:\n"
                "<parent_section>\n"
                f"{parent_text_numbered}\n"
                "</parent_section>"
            ),
        },
    ]

    return call_json_schema(
        client=client,
        model=model,
        messages=messages,
        schema_model=SectionRefinement,
        schema_name="section_refinement",
        max_tokens=max_tokens,
        retries=retries,
        debug=debug,
    )


def should_enqueue_node(
    *,
    refinement_signal: RefinementSignal,
    span: Span | dict,
    min_lines_for_probable: int = 4,
    enqueue_probable: bool = True,
) -> bool:
    if refinement_signal == "definitely_refine":
        return True
    if refinement_signal == "probably_refine" and enqueue_probable:
        return span_line_count(span) >= min_lines_for_probable
    return False


def refine_hierarchy_iteratively(
    *,
    outline: Pass1ArticleOutline,
    lines: list[str],
    client: OpenAI,
    model: str = DEFAULT_MODEL,
    max_depth: int = 5,
    max_nodes: int = 100,
    min_lines_to_refine: int = 3,
    min_lines_for_probable: int = 4,
    enqueue_probable: bool = True,
    retries: int = 1,
    debug: bool = False,
) -> list[dict]:
    article_text = extract_span(lines, outline.article_span)

    sections: list[dict] = []
    queue: list[dict] = []

    for i, top in enumerate(outline.top_sections, start=1):
        section_id = str(i)
        top_span = top.content_span.model_dump()

        node = {
            "section_id": section_id,
            "parent_id": "",
            "level": 1,
            "heading": top.heading,
            "heading_source": top.heading_source,
            "heading_evidence": top.heading_evidence.model_dump(),
            "content_span": top_span,
            "content_text": extract_span(lines, top.content_span),
            "refinement_signal": top.refinement_signal,
            "refinement_evidence": top.refinement_evidence.model_dump(),
            "confidence": top.confidence,
        }
        sections.append(node)

        if should_enqueue_node(
            refinement_signal=top.refinement_signal,
            span=top_span,
            min_lines_for_probable=min_lines_for_probable,
            enqueue_probable=enqueue_probable,
        ):
            queue.append(
                {
                    "section_id": section_id,
                    "level": 1,
                    "heading": top.heading,
                    "content_span": top_span,
                }
            )

    processed = 0

    while queue and processed < max_nodes:
        parent = queue.pop(0)
        processed += 1

        if parent["level"] >= max_depth:
            continue

        if span_line_count(parent["content_span"]) < min_lines_to_refine:
            continue

        parent_span = Span.model_validate(parent["content_span"])
        parent_text_numbered = numbered_excerpt(lines, parent_span)

        refinement = refine_section_once(
            client=client,
            model=model,
            article_title=outline.title,
            article_summary=outline.summary,
            article_text=article_text,
            parent_heading=parent["heading"],
            parent_text_numbered=parent_text_numbered,
            retries=retries,
            debug=debug,
        )

        if not refinement.has_useful_children:
            continue

        child_number = 0
        for child in refinement.children:
            if not child.heading.strip():
                continue
            if not child.content_span.present:
                continue

            child_number += 1
            child_id = f"{parent['section_id']}.{child_number}"
            child_span = child.content_span.model_dump()

            child_node = {
                "section_id": child_id,
                "parent_id": parent["section_id"],
                "level": parent["level"] + 1,
                "heading": child.heading,
                "heading_source": "refinement_child",
                "heading_evidence": {
                    "reason_code": "other",
                    "explanation": "Inferred during refinement pass.",
                    "lines": [child_span],
                },
                "content_span": child_span,
                "content_text": extract_span(lines, child.content_span),
                "refinement_signal": child.refinement_signal,
                "refinement_evidence": {
                    "reason_code": "other",
                    "explanation": "Refinement signal supplied by refinement pass.",
                    "lines": [child_span],
                },
                "confidence": "medium",
            }
            sections.append(child_node)

            if should_enqueue_node(
                refinement_signal=child.refinement_signal,
                span=child_span,
                min_lines_for_probable=min_lines_for_probable,
                enqueue_probable=enqueue_probable,
            ):
                queue.append(
                    {
                        "section_id": child_id,
                        "level": child_node["level"],
                        "heading": child.heading,
                        "content_span": child_span,
                    }
                )

    sections.sort(key=lambda s: section_sort_key(s["section_id"]))
    return sections


def _refine_parent_task(
    *,
    parent: dict,
    outline: Pass1ArticleOutline,
    lines: list[str],
    client: OpenAI,
    model: str,
    article_text: str,
    retries: int,
    debug: bool,
) -> tuple[dict, SectionRefinement]:
    parent_span = Span.model_validate(parent["content_span"])
    parent_text_numbered = numbered_excerpt(lines, parent_span)
    refinement = refine_section_once(
        client=client,
        model=model,
        article_title=outline.title,
        article_summary=outline.summary,
        article_text=article_text,
        parent_heading=parent["heading"],
        parent_text_numbered=parent_text_numbered,
        retries=retries,
        debug=debug,
    )
    return parent, refinement


def refine_hierarchy_concurrently(
    *,
    outline: Pass1ArticleOutline,
    lines: list[str],
    client: OpenAI,
    model: str = DEFAULT_MODEL,
    max_depth: int = 5,
    max_nodes: int = 100,
    min_lines_to_refine: int = 3,
    min_lines_for_probable: int = 4,
    enqueue_probable: bool = True,
    retries: int = 1,
    debug: bool = False,
    max_concurrency: int = 4,
    continue_on_refinement_error: bool = False,
) -> list[dict]:
    """Refine hierarchy with concurrent sibling/frontier requests.

    Pass 1 remains serial. Each refinement frontier is processed concurrently, then
    child nodes are merged in deterministic parent order. This gives vLLM multiple
    independent requests to batch while preserving stable section IDs.
    """
    if max_concurrency <= 1:
        return refine_hierarchy_iteratively(
            outline=outline,
            lines=lines,
            client=client,
            model=model,
            max_depth=max_depth,
            max_nodes=max_nodes,
            min_lines_to_refine=min_lines_to_refine,
            min_lines_for_probable=min_lines_for_probable,
            enqueue_probable=enqueue_probable,
            retries=retries,
            debug=debug,
        )

    article_text = extract_span(lines, outline.article_span)

    sections: list[dict] = []
    frontier: list[dict] = []

    for i, top in enumerate(outline.top_sections, start=1):
        section_id = str(i)
        top_span = top.content_span.model_dump()

        node = {
            "section_id": section_id,
            "parent_id": "",
            "level": 1,
            "heading": top.heading,
            "heading_source": top.heading_source,
            "heading_evidence": top.heading_evidence.model_dump(),
            "content_span": top_span,
            "content_text": extract_span(lines, top.content_span),
            "refinement_signal": top.refinement_signal,
            "refinement_evidence": top.refinement_evidence.model_dump(),
            "confidence": top.confidence,
        }
        sections.append(node)

        if should_enqueue_node(
            refinement_signal=top.refinement_signal,
            span=top_span,
            min_lines_for_probable=min_lines_for_probable,
            enqueue_probable=enqueue_probable,
        ):
            frontier.append(
                {
                    "section_id": section_id,
                    "level": 1,
                    "heading": top.heading,
                    "content_span": top_span,
                }
            )

    processed = 0

    while frontier and processed < max_nodes:
        eligible: list[dict] = []
        for parent in frontier:
            if processed + len(eligible) >= max_nodes:
                break
            if parent["level"] >= max_depth:
                continue
            if span_line_count(parent["content_span"]) < min_lines_to_refine:
                continue
            eligible.append(parent)

        if not eligible:
            break

        next_frontier: list[dict] = []
        results: dict[str, SectionRefinement] = {}
        errors: dict[str, Exception] = {}

        workers = max(1, min(max_concurrency, len(eligible)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_parent = {
                executor.submit(
                    _refine_parent_task,
                    parent=parent,
                    outline=outline,
                    lines=lines,
                    client=client,
                    model=model,
                    article_text=article_text,
                    retries=retries,
                    debug=debug,
                ): parent
                for parent in eligible
            }

            for future in as_completed(future_to_parent):
                parent = future_to_parent[future]
                try:
                    returned_parent, refinement = future.result()
                    results[returned_parent["section_id"]] = refinement
                except Exception as exc:
                    errors[parent["section_id"]] = exc

        if errors and not continue_on_refinement_error:
            first_id = sorted(errors, key=section_sort_key)[0]
            raise RuntimeError(f"Refinement failed for section {first_id}: {errors[first_id]}") from errors[first_id]

        for parent in sorted(eligible, key=lambda p: section_sort_key(p["section_id"])):
            processed += 1
            refinement = results.get(parent["section_id"])
            if refinement is None:
                if debug and parent["section_id"] in errors:
                    print(f"Skipping failed refinement for section {parent['section_id']}: {errors[parent['section_id']]}")
                continue

            if not refinement.has_useful_children:
                continue

            child_number = 0
            for child in refinement.children:
                if not child.heading.strip():
                    continue
                if not child.content_span.present:
                    continue

                child_number += 1
                child_id = f"{parent['section_id']}.{child_number}"
                child_span = child.content_span.model_dump()

                child_node = {
                    "section_id": child_id,
                    "parent_id": parent["section_id"],
                    "level": parent["level"] + 1,
                    "heading": child.heading,
                    "heading_source": "refinement_child",
                    "heading_evidence": {
                        "reason_code": "other",
                        "explanation": "Inferred during refinement pass.",
                        "lines": [child_span],
                    },
                    "content_span": child_span,
                    "content_text": extract_span(lines, child.content_span),
                    "refinement_signal": child.refinement_signal,
                    "refinement_evidence": {
                        "reason_code": "other",
                        "explanation": "Refinement signal supplied by refinement pass.",
                        "lines": [child_span],
                    },
                    "confidence": "medium",
                }
                sections.append(child_node)

                if should_enqueue_node(
                    refinement_signal=child.refinement_signal,
                    span=child_span,
                    min_lines_for_probable=min_lines_for_probable,
                    enqueue_probable=enqueue_probable,
                ):
                    next_frontier.append(
                        {
                            "section_id": child_id,
                            "level": child_node["level"],
                            "heading": child.heading,
                            "content_span": child_span,
                        }
                    )

        frontier = next_frontier

    sections.sort(key=lambda s: section_sort_key(s["section_id"]))
    return sections


def parse_article_multi_pass(
    text: str,
    *,
    client: OpenAI | None = None,
    model: str = DEFAULT_MODEL,
    max_depth: int = 5,
    max_nodes: int = 100,
    retries: int = 1,
    debug: bool = False,
    max_concurrency: int = 1,
    continue_on_refinement_error: bool = False,
) -> dict:
    if client is None:
        client = make_client()

    outline, lines = pass1_outline(
        text,
        client=client,
        model=model,
        retries=retries,
        debug=debug,
    )

    base_result = {
        "article_present": outline.article_present,
        "article_kind": outline.article_kind,
        "title": outline.title,
        "title_source": outline.title_source,
        "title_evidence": outline.title_evidence.model_dump(),
        "summary": outline.summary,
        "preamble_span": outline.preamble_span.model_dump(),
        "article_span": outline.article_span.model_dump(),
        "followup_span": outline.followup_span.model_dump(),
        "conversational_preamble": extract_span(lines, outline.preamble_span),
        "article_text": extract_span(lines, outline.article_span),
        "conversational_followup": extract_span(lines, outline.followup_span),
        "pass1_top_sections_raw": [s.model_dump() for s in outline.top_sections],
        "pass1_parse_notes": outline.parse_notes,
        "confidence": outline.confidence,
    }

    if not outline.article_present:
        result = {**base_result, "sections": []}
        result["validation_errors"] = validate_result(result, total_lines=len(lines))
        return result

    sections = refine_hierarchy_concurrently(
        outline=outline,
        lines=lines,
        client=client,
        model=model,
        max_depth=max_depth,
        max_nodes=max_nodes,
        retries=retries,
        debug=debug,
        max_concurrency=max_concurrency,
        continue_on_refinement_error=continue_on_refinement_error,
    )

    result = {**base_result, "sections": sections}
    result["validation_errors"] = validate_result(result, total_lines=len(lines))
    return result

