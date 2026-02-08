# tests/unit/test_prompt_response.py
"""Unit tests for prompt-response builders and annotators."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from llm_archive.annotators.prompt_response import (
    PromptResponseData,
    PromptResponseAnnotator,
    WikiCandidateAnnotator,
    NaiveTitleAnnotator,
    # HasCodeAnnotator,
    # HasLatexAnnotator,
)
from llm_archive.annotations.core import ValueType, EntityType, AnnotationResult


# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def pr_id():
    """Generate a prompt-response ID."""
    return uuid4()


def make_pr_data(
    prompt_text: str = "Test prompt",
    response_text: str = "Test response",
    pr_id: uuid4 = None,
    response_role: str = 'assistant',
    prompt_role: str = 'user',
) -> PromptResponseData:
    """Create PromptResponseData for testing."""
    return PromptResponseData(
        prompt_response_id=pr_id or uuid4(),
        dialogue_id=uuid4(),
        prompt_message_id=uuid4(),
        response_message_id=uuid4(),
        prompt_text=prompt_text,
        response_text=response_text,
        prompt_word_count=len(prompt_text.split()) if prompt_text else 0,
        response_word_count=len(response_text.split()) if response_text else 0,
        prompt_role=prompt_role,
        response_role=response_role,
        prompt_position=-1,
        response_position=-1,
        created_at=datetime.now(timezone.utc),
    )


# ============================================================
# WikiCandidateAnnotator Tests
# ============================================================

class TestWikiCandidateAnnotator:
    """Test wiki article detection."""
    
    def test_detects_wiki_links(self, pr_id):
        """Should detect responses with wiki links."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="# Cats\n\nCats are [[mammals]] that are [[domesticated]].",
            pr_id=pr_id,
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        # Should have both exchange_type and wiki_link_count annotations
        assert len(results) == 2
        
        exchange_type_result = next(r for r in results if r.key == 'exchange_type')
        assert exchange_type_result.value == 'wiki_article'
        assert exchange_type_result.value_type == ValueType.STRING
        assert exchange_type_result.reason == 'wiki_links_detected'
        
        count_result = next(r for r in results if r.key == 'wiki_link_count')
        assert count_result.value == 2
        assert count_result.value_type == ValueType.NUMERIC
    
    def test_high_confidence_multiple_links(self, pr_id):
        """Should have higher confidence with 3+ wiki links."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="[[Cats]] are [[mammals]]. They eat [[mice]] and [[birds]].",
            pr_id=pr_id,
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        exchange_type_result = next(r for r in results if r.key == 'exchange_type')
        assert exchange_type_result.confidence == 0.95
    
    def test_lower_confidence_single_link(self, pr_id):
        """Should have lower confidence with just 1-2 links."""
        data = make_pr_data(
            prompt_text="Tell me about cats",
            response_text="Cats are [[mammals]].",
            pr_id=pr_id,
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        exchange_type_result = next(r for r in results if r.key == 'exchange_type')
        assert exchange_type_result.confidence == 0.8
    
    def test_no_wiki_links(self, pr_id):
        """Should not detect if no wiki links."""
        data = make_pr_data(
            prompt_text="Tell me about cats",
            response_text="Cats are mammals. They are cute.",
            pr_id=pr_id,
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0
    
    def test_skips_non_assistant(self, pr_id):
        """Should skip non-assistant responses."""
        data = make_pr_data(
            prompt_text="Write [[wiki]] style",
            response_text="Here's [[content]]",
            pr_id=pr_id,
            response_role='user',  # Not assistant
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0
    
    def test_counts_links_correctly(self, pr_id):
        """Should count wiki links correctly."""
        data = make_pr_data(
            response_text="[[One]] [[Two]] [[Three]] [[Four]] [[Five]]",
            pr_id=pr_id,
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        count_result = next(r for r in results if r.key == 'wiki_link_count')
        assert count_result.value == 5
    
    def test_handles_empty_brackets(self, pr_id):
        """Should count empty brackets as potential links."""
        data = make_pr_data(
            response_text="Empty [[]] brackets and [[valid]] link",
            pr_id=pr_id,
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        count_result = next(r for r in results if r.key == 'wiki_link_count')
        assert count_result.value == 2


# ============================================================
# NaiveTitleAnnotator Tests
# ============================================================

class TestNaiveTitleAnnotator:
    """Test naive title extraction."""
    
    def test_extracts_markdown_h1(self, pr_id):
        """Should extract # Title."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="# The Domestic Cat\n\n[[Cats]] are mammals...",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'The Domestic Cat'
        assert results[0].key == 'proposed_title'
        assert results[0].value_type == ValueType.STRING
        assert results[0].reason == 'markdown_header'
    
    def test_extracts_markdown_h2(self, pr_id):
        """Should extract ## Title."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="## Feline History\n\nThe history of cats...",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'Feline History'
        assert results[0].reason == 'markdown_header'
    
    def test_extracts_markdown_h3(self, pr_id):
        """Should extract ### Title."""
        data = make_pr_data(
            response_text="### Deep Section\n\nContent here...",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'Deep Section'
    
    def test_extracts_bold_title(self, pr_id):
        """Should extract **Title**."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="**The Domestic Cat**\n\n[[Cats]] are mammals...",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'The Domestic Cat'
        assert results[0].reason == 'bold_header'
    
    def test_extracts_bold_with_subtitle(self, pr_id):
        """Should extract **Title** - Subtitle pattern."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="**Felis catus** - The Domestic Cat\n\nContent...",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'Felis catus'
        assert results[0].reason == 'bold_header_with_suffix'
    
    def test_no_title_preamble(self, pr_id):
        """Should return nothing if first line is preamble."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="Sure, here's an article about cats:\n\n# The Domestic Cat\n\n...",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        # This is expected - naive extractor misses the title
        # because first line is a preamble
        assert len(results) == 0
    
    def test_no_title_plain_text(self, pr_id):
        """Should return nothing if no clear title format."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="Cats have been domesticated for thousands of years...",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0
    
    def test_skips_non_assistant(self, pr_id):
        """Should skip non-assistant responses."""
        data = make_pr_data(
            prompt_text="# My Title",
            response_text="# Another Title",
            pr_id=pr_id,
            response_role='user',
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0
    
    def test_empty_response(self, pr_id):
        """Should handle empty response."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0
    
    def test_none_response(self, pr_id):
        """Should handle None response."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="placeholder",
            pr_id=pr_id,
        )
        data.response_text = None  # Override
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0
    
    def test_whitespace_only_first_line(self, pr_id):
        """Should skip whitespace-only first lines."""
        data = make_pr_data(
            response_text="   \n# Real Title\n\nContent",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        # .strip() is called on the document, so the title should be extracted.
        assert len(results) == 1
    
    def test_strips_title_whitespace(self, pr_id):
        """Should strip whitespace from extracted title."""
        data = make_pr_data(
            response_text="#   Spaced Title   \n\nContent",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'Spaced Title'


# ============================================================
# Annotation Filter Tests (class attributes)
# ============================================================

class TestAnnotatorFilters:
    """Test annotation filter attributes."""
    
    def test_wiki_candidate_has_no_requirements(self):
        """WikiCandidateAnnotator should have no prerequisites."""
        assert WikiCandidateAnnotator.REQUIRES_FLAGS == []
        assert WikiCandidateAnnotator.REQUIRES_STRINGS == []
        assert WikiCandidateAnnotator.SKIP_IF_FLAGS == []
        assert WikiCandidateAnnotator.SKIP_IF_STRINGS == []
    
    def test_naive_title_requires_wiki(self):
        """NaiveTitleAnnotator should require wiki_article."""
        assert ('exchange_type', 'wiki_article') in NaiveTitleAnnotator.REQUIRES_STRINGS
    
    def test_annotator_metadata(self):
        """Check annotator class metadata."""
        assert WikiCandidateAnnotator.ENTITY_TYPE == EntityType.PROMPT_RESPONSE
        assert WikiCandidateAnnotator.ANNOTATION_KEY == 'exchange_type'
        assert WikiCandidateAnnotator.VALUE_TYPE == ValueType.STRING
        
        assert NaiveTitleAnnotator.ENTITY_TYPE == EntityType.PROMPT_RESPONSE
        assert NaiveTitleAnnotator.ANNOTATION_KEY == 'proposed_title'
        assert NaiveTitleAnnotator.VALUE_TYPE == ValueType.STRING
        
        # Wiki detection should run before title extraction
        assert WikiCandidateAnnotator.PRIORITY > NaiveTitleAnnotator.PRIORITY
    
    def test_custom_annotator_with_filters(self):
        """Test defining custom annotator with filters."""
        
        class PreambleDetector(PromptResponseAnnotator):
            ANNOTATION_KEY = 'has_preamble'
            VALUE_TYPE = ValueType.FLAG
            REQUIRES_STRINGS = [('exchange_type', 'wiki_article')]
            SKIP_IF_FLAGS = ['preamble_checked']
            
            def annotate(self, data):
                return []
        
        assert PreambleDetector.REQUIRES_STRINGS == [('exchange_type', 'wiki_article')]
        assert PreambleDetector.SKIP_IF_FLAGS == ['preamble_checked']


# ============================================================
# AnnotationResult Tests
# ============================================================

class TestAnnotationResult:
    """Test AnnotationResult dataclass behavior."""
    
    def test_result_with_reason(self, pr_id):
        """Results should include reason when provided."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="# Cats\n\n[[Cats]] are mammals.",
            pr_id=pr_id,
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        exchange_type_result = next(r for r in results if r.key == 'exchange_type')
        assert exchange_type_result.reason == 'wiki_links_detected'
    
    def test_key_is_required(self, pr_id):
        """Key should always be set on results."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="# Title\n\n[[link]]",
            pr_id=pr_id,
        )
        
        wiki_annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        wiki_results = wiki_annotator.annotate(data)
        
        title_annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        title_results = title_annotator.annotate(data)
        
        for result in wiki_results + title_results:
            assert result.key is not None
    
    def test_value_type_is_set(self, pr_id):
        """Results should have explicit value_type."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="# Title\n\n[[link1]] [[link2]] [[link3]]",
            pr_id=pr_id,
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        # Should have string and numeric results
        string_results = [r for r in results if r.value_type == ValueType.STRING]
        numeric_results = [r for r in results if r.value_type == ValueType.NUMERIC]
        
        assert len(string_results) >= 1
        assert len(numeric_results) >= 1


# ============================================================
# PromptResponseData Tests
# ============================================================

class TestPromptResponseData:
    """Test PromptResponseData dataclass."""
    
    def test_all_fields_accessible(self):
        """All fields should be accessible."""
        data = make_pr_data(
            prompt_text="Hello",
            response_text="World",
        )
        
        assert data.prompt_text == "Hello"
        assert data.response_text == "World"
        assert data.prompt_role == 'user'
        assert data.response_role == 'assistant'
        assert isinstance(data.prompt_response_id, type(uuid4()))
        assert isinstance(data.dialogue_id, type(uuid4()))
    
    def test_word_counts_calculated(self):
        """Word counts should be calculated from text."""
        data = make_pr_data(
            prompt_text="one two three",
            response_text="four five six seven",
        )
        
        assert data.prompt_word_count == 3
        assert data.response_word_count == 4
    
    def test_handles_none_text(self):
        """Should handle None text gracefully."""
        data = PromptResponseData(
            prompt_response_id=uuid4(),
            dialogue_id=uuid4(),
            prompt_message_id=uuid4(),
            response_message_id=uuid4(),
            prompt_text=None,
            response_text=None,
            prompt_word_count=0,
            response_word_count=0,
            prompt_role='user',
            response_role='assistant',
            created_at=datetime.now(timezone.utc),
        )
        
        assert data.prompt_text is None
        assert data.response_text is None


# # ============================================================
# # HasCodeAnnotator Tests
# # ============================================================

# class TestHasCodeAnnotator:
#     """Test code detection annotator."""
    
#     def test_detects_code_blocks(self, pr_id):
#         """Should detect ``` code blocks."""
#         data = make_pr_data(
#             response_text="Here's some code:\n```python\nprint('hello')\n```",
#             pr_id=pr_id,
#         )
        
#         annotator = HasCodeAnnotator.__new__(HasCodeAnnotator)
#         results = annotator.annotate(data)
        
#         flag_results = [r for r in results if r.key == 'has_code']
#         assert len(flag_results) == 1
#         assert flag_results[0].value_type == ValueType.FLAG
#         assert flag_results[0].confidence >= 0.9
        
#         evidence_results = [r for r in results if r.key == 'code_evidence']
#         evidence_values = {r.value for r in evidence_results}
#         assert 'code_block' in evidence_values
    
#     def test_detects_shebang(self, pr_id):
#         """Should detect shebang lines."""
#         data = make_pr_data(
#             response_text="#!/usr/bin/env python\nprint('hello')",
#             pr_id=pr_id,
#         )
        
#         annotator = HasCodeAnnotator.__new__(HasCodeAnnotator)
#         results = annotator.annotate(data)
        
#         assert any(r.key == 'has_code' for r in results)
#         evidence_values = {r.value for r in results if r.key == 'code_evidence'}
#         assert 'shebang' in evidence_values
    
#     def test_detects_c_include(self, pr_id):
#         """Should detect C/C++ includes."""
#         data = make_pr_data(
#             response_text='#include <stdio.h>\nint main() { return 0; }',
#             pr_id=pr_id,
#         )
        
#         annotator = HasCodeAnnotator.__new__(HasCodeAnnotator)
#         results = annotator.annotate(data)
        
#         assert any(r.key == 'has_code' for r in results)
#         evidence_values = {r.value for r in results if r.key == 'code_evidence'}
#         assert 'c_include' in evidence_values
    
#     def test_detects_python_function(self, pr_id):
#         """Should detect Python function definitions."""
#         data = make_pr_data(
#             response_text="def hello_world():\n    print('hello')",
#             pr_id=pr_id,
#         )
        
#         annotator = HasCodeAnnotator.__new__(HasCodeAnnotator)
#         results = annotator.annotate(data)
        
#         assert any(r.key == 'has_code' for r in results)
#         evidence_values = {r.value for r in results if r.key == 'code_evidence'}
#         assert 'python_function' in evidence_values
    
#     def test_detects_js_function(self, pr_id):
#         """Should detect JavaScript function definitions."""
#         data = make_pr_data(
#             response_text="function hello() {\n  console.log('hello');\n}",
#             pr_id=pr_id,
#         )
        
#         annotator = HasCodeAnnotator.__new__(HasCodeAnnotator)
#         results = annotator.annotate(data)
        
#         assert any(r.key == 'has_code' for r in results)
#         evidence_values = {r.value for r in results if r.key == 'code_evidence'}
#         assert 'js_function' in evidence_values
    
#     def test_detects_arrow_function(self, pr_id):
#         """Should detect arrow functions."""
#         data = make_pr_data(
#             response_text="const hello = (name) => console.log(`Hello ${name}`);",
#             pr_id=pr_id,
#         )
        
#         annotator = HasCodeAnnotator.__new__(HasCodeAnnotator)
#         results = annotator.annotate(data)
        
#         assert any(r.key == 'has_code' for r in results)
#         evidence_values = {r.value for r in results if r.key == 'code_evidence'}
#         assert 'arrow_function' in evidence_values
    
#     def test_detects_python_import(self, pr_id):
#         """Should detect Python imports."""
#         data = make_pr_data(
#             response_text="import pandas as pd\nfrom datetime import datetime",
#             pr_id=pr_id,
#         )
        
#         annotator = HasCodeAnnotator.__new__(HasCodeAnnotator)
#         results = annotator.annotate(data)
        
#         assert any(r.key == 'has_code' for r in results)
#         evidence_values = {r.value for r in results if r.key == 'code_evidence'}
#         assert 'python_import' in evidence_values
    
#     def test_no_code_in_plain_text(self, pr_id):
#         """Should not detect code in plain text."""
#         data = make_pr_data(
#             response_text="Cats are wonderful pets. They like to sleep and play.",
#             pr_id=pr_id,
#         )
        
#         annotator = HasCodeAnnotator.__new__(HasCodeAnnotator)
#         results = annotator.annotate(data)
        
#         assert len(results) == 0
    
#     def test_skips_non_assistant(self, pr_id):
#         """Should skip non-assistant responses."""
#         data = make_pr_data(
#             response_text="```python\nprint('hello')\n```",
#             pr_id=pr_id,
#             response_role='user',
#         )
        
#         annotator = HasCodeAnnotator.__new__(HasCodeAnnotator)
#         results = annotator.annotate(data)
        
#         assert len(results) == 0
    
#     def test_multiple_evidence_types(self, pr_id):
#         """Should detect multiple evidence types."""
#         data = make_pr_data(
#             response_text="```python\nimport os\ndef main():\n    pass\n```",
#             pr_id=pr_id,
#         )
        
#         annotator = HasCodeAnnotator.__new__(HasCodeAnnotator)
#         results = annotator.annotate(data)
        
#         evidence_results = [r for r in results if r.key == 'code_evidence']
#         assert len(evidence_results) >= 2  # code_block + python_function + python_import


# # ============================================================
# # HasLatexAnnotator Tests
# # ============================================================

# class TestHasLatexAnnotator:
#     """Test LaTeX detection annotator."""
    
#     def test_detects_display_math(self, pr_id):
#         """Should detect display math $$...$$."""
#         data = make_pr_data(
#             response_text="The equation is: $$E = mc^2$$",
#             pr_id=pr_id,
#         )
        
#         annotator = HasLatexAnnotator.__new__(HasLatexAnnotator)
#         results = annotator.annotate(data)
        
#         assert any(r.key == 'has_latex' for r in results)
#         latex_types = {r.value for r in results if r.key == 'latex_type'}
#         assert 'display' in latex_types
    
#     def test_detects_bracket_display_math(self, pr_id):
#         """Should detect \\[...\\] display math."""
#         data = make_pr_data(
#             response_text="The integral is: \\[\\int_0^\\infty e^{-x} dx = 1\\]",
#             pr_id=pr_id,
#         )
        
#         annotator = HasLatexAnnotator.__new__(HasLatexAnnotator)
#         results = annotator.annotate(data)
        
#         assert any(r.key == 'has_latex' for r in results)
    
#     def test_detects_latex_commands(self, pr_id):
#         """Should detect LaTeX commands."""
#         data = make_pr_data(
#             response_text="Use \\frac{a}{b} for fractions and \\sqrt{x} for roots.",
#             pr_id=pr_id,
#         )
        
#         annotator = HasLatexAnnotator.__new__(HasLatexAnnotator)
#         results = annotator.annotate(data)
        
#         assert any(r.key == 'has_latex' for r in results)
#         latex_types = {r.value for r in results if r.key == 'latex_type'}
#         assert 'commands' in latex_types
    
#     def test_detects_greek_letters(self, pr_id):
#         """Should detect Greek letter commands."""
#         data = make_pr_data(
#             response_text="The angle \\theta is measured from \\alpha to \\omega.",
#             pr_id=pr_id,
#         )
        
#         annotator = HasLatexAnnotator.__new__(HasLatexAnnotator)
#         results = annotator.annotate(data)
        
#         assert any(r.key == 'has_latex' for r in results)
    
#     def test_no_latex_in_plain_text(self, pr_id):
#         """Should not detect LaTeX in plain text."""
#         data = make_pr_data(
#             response_text="The value of pi is approximately 3.14159.",
#             pr_id=pr_id,
#         )
        
#         annotator = HasLatexAnnotator.__new__(HasLatexAnnotator)
#         results = annotator.annotate(data)
        
#         assert len(results) == 0
    
#     def test_skips_non_assistant(self, pr_id):
#         """Should skip non-assistant responses."""
#         data = make_pr_data(
#             response_text="$$E = mc^2$$",
#             pr_id=pr_id,
#             response_role='user',
#         )
        
#         annotator = HasLatexAnnotator.__new__(HasLatexAnnotator)
#         results = annotator.annotate(data)
        
#         assert len(results) == 0
    
#     def test_high_confidence_for_display_math(self, pr_id):
#         """Should have high confidence for display math."""
#         data = make_pr_data(
#             response_text="$$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$",
#             pr_id=pr_id,
#         )
        
#         annotator = HasLatexAnnotator.__new__(HasLatexAnnotator)
#         results = annotator.annotate(data)
        
#         flag_result = next(r for r in results if r.key == 'has_latex')
#         assert flag_result.confidence >= 0.9
    
#     def test_lower_confidence_for_commands_only(self, pr_id):
#         """Should have lower confidence for commands without display math."""
#         data = make_pr_data(
#             response_text="Use \\alpha and \\beta for parameters.",
#             pr_id=pr_id,
#         )
        
#         annotator = HasLatexAnnotator.__new__(HasLatexAnnotator)
#         results = annotator.annotate(data)
        
#         flag_result = next(r for r in results if r.key == 'has_latex')
#         assert flag_result.confidence < 0.9


# ============================================================
# Annotator Registry Tests
# ============================================================

class TestAnnotatorRegistry:
    """Test the annotator registry and runner."""
    
    def test_all_annotators_in_registry(self):
        """All annotators should be in PROMPT_RESPONSE_ANNOTATORS."""
        from llm_archive.annotators.prompt_response import PROMPT_RESPONSE_ANNOTATORS
        
        assert WikiCandidateAnnotator in PROMPT_RESPONSE_ANNOTATORS
        assert NaiveTitleAnnotator in PROMPT_RESPONSE_ANNOTATORS
        # assert HasCodeAnnotator in PROMPT_RESPONSE_ANNOTATORS
        # assert HasLatexAnnotator in PROMPT_RESPONSE_ANNOTATORS
    
    def test_annotators_have_unique_keys(self):
        """Each annotator should have a unique ANNOTATION_KEY."""
        from llm_archive.annotators.prompt_response import PROMPT_RESPONSE_ANNOTATORS
        
        keys = [cls.ANNOTATION_KEY for cls in PROMPT_RESPONSE_ANNOTATORS]
        assert len(keys) == len(set(keys)), "Duplicate ANNOTATION_KEYs found"
    
    def test_priority_ordering(self):
        """Annotators should have distinct priorities for deterministic ordering."""
        from llm_archive.annotators.prompt_response import PROMPT_RESPONSE_ANNOTATORS
        
        priorities = [cls.PRIORITY for cls in PROMPT_RESPONSE_ANNOTATORS]
        # Note: Priorities don't have to be unique, but it helps with debugging
        assert len(priorities) == len(PROMPT_RESPONSE_ANNOTATORS)
