# schemas.py
"""Pydantic schemas for the multi-pass article parser."""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


Confidence = Literal["high", "medium", "low"]
ArticleKind = Literal["wiki_article", "wiki_fragment", "not_article"]
TitleSource = Literal["explicit", "inferred", "absent"]

HeadingSource = Literal[
    "explicit_markdown_heading",
    "explicit_plaintext_heading",
    "implicit_topic_shift",
    "implicit_list_group",
    "implicit_opening_context",
    "implicit_summary_title",
    "other_inferred",
]

RefinementSignal = Literal[
    "definitely_refine",
    "probably_refine",
    "probably_leaf",
    "definitely_leaf",
]

ReasonCode = Literal[
    "explicit_subheadings_present",
    "multiple_topic_shifts",
    "multiple_coherent_units",
    "nested_list_or_grouping",
    "long_multi_part_section",
    "semantic_substructure",
    "single_coherent_unit",
    "too_short",
    "insufficient_signal",
    "other",
]

OneLineText = Annotated[
    str,
    StringConstraints(
        min_length=0,
        max_length=500,
        pattern=r"^[^\r\n\x00-\x1f]*$",
    ),
]


class Span(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def normalize_span_before_validation(cls, data):
        """Accept common span variants produced by smaller models."""
        if isinstance(data, str):
            nums = [int(x) for x in re.findall("[0-9]+", data)]
            if len(nums) >= 2:
                return {"present": True, "start_line": min(nums), "end_line": max(nums)}
            if len(nums) == 1:
                return {"present": True, "start_line": nums[0], "end_line": nums[0]}
        if isinstance(data, list) and data:
            nums = [int(x) for x in data if isinstance(x, int) or str(x).isdigit()]
            if nums:
                return {"present": True, "start_line": min(nums), "end_line": max(nums)}
        return data

    present: bool
    start_line: int = Field(description="1-indexed inclusive start line. Use 0 if absent.")
    end_line: int = Field(description="1-indexed inclusive end line. Use 0 if absent.")


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_before_validation(cls, data):
        if isinstance(data, str):
            return {"reason_code": "other", "explanation": data, "lines": []}
        if isinstance(data, dict):
            data = dict(data)
            if "explanation" not in data and "evidence" in data:
                data["explanation"] = data.pop("evidence")
            if "lines" not in data:
                if "line_span" in data:
                    data["lines"] = [data.pop("line_span")]
                elif "line_spans" in data:
                    data["lines"] = data.pop("line_spans")
                elif "line_sources" in data:
                    data["lines"] = [data.pop("line_sources")]
                elif "line_soures" in data:
                    data["lines"] = [data.pop("line_soures")]
                else:
                    data["lines"] = []
            if data.get("reason_code") not in ReasonCode.__args__:
                data["reason_code"] = "other"
            if "explanation" not in data:
                data["explanation"] = ""
        return data

    reason_code: ReasonCode
    explanation: OneLineText
    lines: list[Span]


TopLevelSectionId = Annotated[
    str,
    StringConstraints(pattern=r"^[1-9][0-9]*$"),
]


class Pass1TopSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: TopLevelSectionId = Field(description="Top-level numeric ID: '1', '2', '3', etc.")

    heading_evidence: Evidence
    heading_source: HeadingSource
    heading: OneLineText

    content_span: Span = Field(description="Full source span for this coarse top-level section.")

    refinement_evidence: Evidence
    refinement_signal: RefinementSignal = Field(
        description="Whether this top-level section likely deserves a child-refinement pass."
    )

    confidence: Confidence

    @model_validator(mode="after")
    def validate_top_section(self) -> "Pass1TopSection":
        if not self.heading.strip():
            raise ValueError("top section heading must not be empty")
        if not self.content_span.present:
            raise ValueError("top section content_span must be present")
        return self


class Pass1ArticleOutline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def normalize_recoverable_fields_before_validation(cls, data):
        """Repair recoverable Pass 1 inconsistencies before validation.

        Smaller models often infer a useful title from a bold lead phrase but still
        mark title_source as "absent". They may also choose an article_span that
        is too narrow even though their top-section spans identify the true article
        envelope. Normalize those cases rather than rejecting the whole parse.
        """
        if not isinstance(data, dict):
            return data

        data = dict(data)

        title = str(data.get("title", "")).strip()
        title_source = data.get("title_source")
        if title and title_source == "absent":
            data["title_source"] = "inferred"
        elif not title and title_source in {"explicit", "inferred"}:
            data["title_source"] = "absent"

        article_span = data.get("article_span")
        if data.get("article_present") is True and isinstance(article_span, dict):
            starts: list[int] = []
            ends: list[int] = []

            if article_span.get("present"):
                starts.append(int(article_span.get("start_line", 0)))
                ends.append(int(article_span.get("end_line", 0)))

            title_evidence = data.get("title_evidence")
            if isinstance(title_evidence, dict):
                for span in title_evidence.get("lines", []) or []:
                    if isinstance(span, dict) and span.get("present"):
                        starts.append(int(span.get("start_line", 0)))
                        ends.append(int(span.get("end_line", 0)))

            for section in data.get("top_sections", []) or []:
                if not isinstance(section, dict):
                    continue
                span = section.get("content_span")
                if isinstance(span, dict) and span.get("present"):
                    starts.append(int(span.get("start_line", 0)))
                    ends.append(int(span.get("end_line", 0)))

            starts = [x for x in starts if x > 0]
            ends = [x for x in ends if x > 0]
            if starts and ends:
                article_span = dict(article_span)
                article_span["present"] = True
                article_span["start_line"] = min(starts)
                article_span["end_line"] = max(ends)
                data["article_span"] = article_span

        return data

    preamble_span: Span
    article_span: Span
    followup_span: Span

    article_present: bool
    article_kind: ArticleKind

    title_evidence: Evidence
    title_source: TitleSource
    title: OneLineText

    summary: OneLineText
    top_sections: list[Pass1TopSection]

    parse_notes: list[OneLineText]
    confidence: Confidence

    @model_validator(mode="after")
    def validate_outline_consistency(self) -> "Pass1ArticleOutline":
        if self.article_present:
            if self.article_kind == "not_article":
                raise ValueError("article_present=true is inconsistent with article_kind='not_article'")
            if not self.article_span.present:
                raise ValueError("article_present=true requires article_span.present=true")
            if self.title_source == "absent" and self.title.strip():
                raise ValueError("title_source='absent' requires an empty title")
            if self.title_source != "absent" and not self.title.strip():
                raise ValueError("non-absent title_source requires a non-empty title")
            if not self.top_sections:
                raise ValueError("article_present=true requires at least one top-level section")

            article_start = self.article_span.start_line
            article_end = self.article_span.end_line

            for i, span in enumerate(self.title_evidence.lines):
                if span.present and not (article_start <= span.start_line <= span.end_line <= article_end):
                    raise ValueError(f"title_evidence.lines[{i}] must fall inside article_span")

            for section in self.top_sections:
                span = section.content_span
                if span.present and not (article_start <= span.start_line <= span.end_line <= article_end):
                    raise ValueError(
                        f"top section {section.section_id} content_span must fall inside article_span"
                    )
        else:
            if self.article_kind != "not_article":
                raise ValueError("article_present=false requires article_kind='not_article'")
            if self.article_span.present:
                raise ValueError("article_present=false requires article_span.present=false")

        if self.followup_span.present and self.article_span.present:
            if self.followup_span.start_line <= self.article_span.end_line:
                raise ValueError("followup_span must start after article_span ends")

        return self


class ChildSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def normalize_child_before_validation(cls, data):
        """Normalize noisy child-section outputs into the minimal schema.

        Pass 2 should be a lean span-splitting operation. Evidence, confidence,
        heading_source, and recursive child fields are intentionally dropped here;
        the parser/orchestrator can decide whether to refine this child again from
        refinement_signal.
        """
        if not isinstance(data, dict):
            return data
        data = dict(data)

        if "content_span" not in data:
            if "line_span" in data:
                data["content_span"] = data.get("line_span")
            elif "line_spans" in data:
                data["content_span"] = data.get("line_spans")
            elif "lines" in data:
                data["content_span"] = data.get("lines")

        if "refinement_signal" not in data:
            if data.get("has_useful_children") is True:
                data["refinement_signal"] = "probably_refine"
            else:
                data["refinement_signal"] = "probably_leaf"

        keep = {"heading", "content_span", "refinement_signal"}
        return {k: v for k, v in data.items() if k in keep}

    heading: OneLineText = Field(description="A useful normalized heading. Must not be empty.")
    content_span: Span = Field(description="Absolute source-document line span for this child section.")
    refinement_signal: RefinementSignal = Field(
        description="Whether this child likely contains useful lower-level structure."
    )


class SectionRefinement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent_heading: OneLineText

    parse_notes: list[OneLineText]
    parent_refinement_signal: RefinementSignal = Field(
        description="Whether the parent was worth refining after inspection."
    )

    has_useful_children: bool
    children: list[ChildSection]

    confidence: Confidence


class FinalSourceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_line: int
    end_line: int


class FinalArticleSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str
    content: str
    children: list["FinalArticleSection"] = Field(default_factory=list)
    source_span: FinalSourceSpan | None = None


class FinalConversationWrapper(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preamble: str = ""
    followup: str = ""


class FinalArticle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    article_present: bool
    article_kind: ArticleKind
    title: str
    summary: str
    article_text: str
    sections: list[FinalArticleSection]
    conversation: FinalConversationWrapper | None = None


FinalArticleSection.model_rebuild()

