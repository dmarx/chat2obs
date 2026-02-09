# tests/unit/test_annotator_logic.py
"""Tests for concrete annotator logic.

These tests verify the annotate() methods of ContentPart and PromptResponse
annotators using their respective data classes — no database required.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from llm_archive.annotations.core import AnnotationResult, EntityType, ValueType
from llm_archive.annotators.content_part import (
    ContentPartAnnotator,
    ContentPartData,
    CodeBlockAnnotator,
    LatexContentAnnotator,
    WikiLinkContentAnnotator,
)
from llm_archive.annotators.prompt_response import (
    PromptResponseAnnotator,
    PromptResponseData,
    WikiCandidateAnnotator,
    NaiveTitleAnnotator,
)


# ============================================================
# Helpers
# ============================================================

def _make_content_part(text: str, part_type: str = "text", role: str = "assistant") -> ContentPartData:
    return ContentPartData(
        content_part_id=uuid4(),
        message_id=uuid4(),
        dialogue_id=uuid4(),
        sequence=0,
        part_type=part_type,
        text_content=text,
        language=None,
        role=role,
        created_at=datetime.now(timezone.utc),
    )


def _make_prompt_response(
    response_text: str,
    prompt_text: str = "Tell me something",
    response_word_count: int | None = None,
) -> PromptResponseData:
    if response_word_count is None:
        response_word_count = len(response_text.split()) if response_text else 0
    return PromptResponseData(
        prompt_response_id=uuid4(),
        dialogue_id=uuid4(),
        prompt_message_id=uuid4(),
        response_message_id=uuid4(),
        prompt_text=prompt_text,
        response_text=response_text,
        prompt_word_count=len(prompt_text.split()),
        response_word_count=response_word_count,
        prompt_role="user",
        response_role="assistant",
        created_at=datetime.now(timezone.utc),
    )


# ============================================================
# Content Part Annotator Configuration
# ============================================================

class TestContentPartAnnotatorConfig:

    def test_entity_type(self):
        assert ContentPartAnnotator.ENTITY_TYPE == EntityType.CONTENT_PART

    def test_code_block_filters(self):
        assert CodeBlockAnnotator.PART_TYPE_FILTER == "text"
        assert CodeBlockAnnotator.ROLE_FILTER == "assistant"
        assert CodeBlockAnnotator.PRIORITY == 90

    def test_latex_no_role_filter(self):
        assert LatexContentAnnotator.ROLE_FILTER is None


# ============================================================
# CodeBlockAnnotator
# ============================================================

class TestCodeBlockAnnotator:

    def _annotate(self, text: str) -> list[AnnotationResult]:
        annotator = CodeBlockAnnotator.__new__(CodeBlockAnnotator)
        return annotator.annotate(_make_content_part(text))

    def test_detects_single_code_block(self):
        text = "Here's some code:\n```python\nprint('hello')\n```\nDone."
        results = self._annotate(text)
        keys = {r.key for r in results}
        assert "has_code_block" in keys
        assert "code_block_count" in keys
        assert "code_language" in keys

    def test_counts_multiple_blocks(self):
        text = "```python\nx=1\n```\n\n```javascript\ny=2\n```"
        results = self._annotate(text)
        count_result = [r for r in results if r.key == "code_block_count"][0]
        assert count_result.value == 2

    def test_no_match_returns_empty(self):
        assert self._annotate("no code here") == []

    def test_empty_text_returns_empty(self):
        assert self._annotate("") == []

    def test_none_text_returns_empty(self):
        annotator = CodeBlockAnnotator.__new__(CodeBlockAnnotator)
        data = _make_content_part("")
        data.text_content = None
        assert annotator.annotate(data) == []


# ============================================================
# LatexContentAnnotator
# ============================================================

class TestLatexContentAnnotator:

    def _annotate(self, text: str) -> list[AnnotationResult]:
        annotator = LatexContentAnnotator.__new__(LatexContentAnnotator)
        return annotator.annotate(_make_content_part(text))

    def test_detects_display_math(self):
        results = self._annotate("The equation is $$E = mc^2$$.")
        assert any(r.key == "has_latex" for r in results)
        assert any(r.key == "latex_type" and r.value == "display" for r in results)

    def test_detects_inline_math(self):
        results = self._annotate("The value is $x + y$ here.")
        assert any(r.key == "has_latex" for r in results)

    def test_detects_commands(self):
        results = self._annotate("Use \\frac{a}{b} for fractions.")
        assert any(r.key == "latex_type" and r.value == "commands" for r in results)

    def test_no_latex_returns_empty(self):
        assert self._annotate("plain text") == []


# ============================================================
# WikiLinkContentAnnotator
# ============================================================

class TestWikiLinkContentAnnotator:

    def _annotate(self, text: str) -> list[AnnotationResult]:
        annotator = WikiLinkContentAnnotator.__new__(WikiLinkContentAnnotator)
        return annotator.annotate(_make_content_part(text))

    def test_detects_wiki_links(self):
        results = self._annotate("See [[Python]] and [[JavaScript]]")
        assert any(r.key == "has_wiki_links" for r in results)
        count = [r for r in results if r.key == "wiki_link_count"][0]
        assert count.value == 2

    def test_no_links_returns_empty(self):
        assert self._annotate("no links here") == []


# ============================================================
# Prompt Response Annotator Configuration
# ============================================================

class TestPromptResponseAnnotatorConfig:

    def test_entity_type(self):
        assert PromptResponseAnnotator.ENTITY_TYPE == EntityType.PROMPT_RESPONSE

    def test_naive_title_requires_wiki(self):
        assert NaiveTitleAnnotator.REQUIRES_STRINGS == [("exchange_type", "wiki_article")]

    def test_priority_ordering(self):
        assert WikiCandidateAnnotator.PRIORITY > NaiveTitleAnnotator.PRIORITY


# ============================================================
# WikiCandidateAnnotator
# ============================================================

class TestWikiCandidateAnnotator:

    def _annotate(self, response_text: str, word_count: int | None = None) -> list[AnnotationResult]:
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        data = _make_prompt_response(response_text, response_word_count=word_count)
        return annotator.annotate(data)

    def test_detects_wiki_article(self):
        text = (
            "# Article Title\n\n"
            "## Section One\n\nSee [[Topic A]] for details.\n\n"
            "## Section Two\n\nRelated to [[Topic B]] and [[Topic C]].\n\n"
            "## Section Three\n\nMore info at [[Topic D]].\n"
        )
        results = self._annotate(text, word_count=300)
        assert any(r.key == "wiki_candidate" for r in results)

    def test_no_response_returns_empty(self):
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        data = _make_prompt_response("")
        data.response_text = None
        assert annotator.annotate(data) == []


# ============================================================
# NaiveTitleAnnotator
# ============================================================

class TestNaiveTitleAnnotator:

    def _annotate(self, response_text: str) -> list[AnnotationResult]:
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        return annotator.annotate(_make_prompt_response(response_text))

    def test_extracts_h1_title(self):
        results = self._annotate("# The Great Migration\n\nContent here.")
        assert len(results) == 1
        assert results[0].value == "The Great Migration"
        assert results[0].confidence == 0.9

    # def test_falls_back_to_first_line(self):
    #     results = self._annotate("Understanding the Modern World of Science\n\nParagraph content.")
    #     assert len(results) == 1
    #     assert results[0].value == "Understanding the Modern World of Science"
    #     assert results[0].confidence == 0.6

    # def test_rejects_too_short_first_line(self):
    #     results = self._annotate("Hi\n\nContent here.")
    #     assert results == []

    # def test_rejects_too_long_first_line(self):
    #     long_first = " ".join(["word"] * 15)
    #     results = self._annotate(f"{long_first}\n\nContent here.")
    #     assert results == []
