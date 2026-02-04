# tests/unit/test_prompt_response.py
"""Unit tests for prompt-response builders and annotators."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from llm_archive.annotators.prompt_response import (
    PromptResponseData,
    WikiCandidateAnnotator,
    NaiveTitleAnnotator,
)


# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def pr_id():
    """Generate a prompt-response ID."""
    return uuid4()


def make_pr_data(
    prompt_text: str,
    response_text: str,
    pr_id: uuid4 = None,
    response_role: str = 'assistant',
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
        prompt_role='user',
        response_role=response_role,
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
        
        assert len(results) == 1
        assert results[0].value == 'wiki_article'
        assert results[0].key == 'exchange_type'
        assert results[0].data['wiki_link_count'] == 2
    
    def test_high_confidence_multiple_links(self, pr_id):
        """Should have higher confidence with 3+ wiki links."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="[[Cats]] are [[mammals]]. They eat [[mice]] and [[birds]].",
            pr_id=pr_id,
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].confidence == 0.95
    
    def test_lower_confidence_single_link(self, pr_id):
        """Should have lower confidence with just 1-2 links."""
        data = make_pr_data(
            prompt_text="Tell me about cats",
            response_text="Cats are [[mammals]].",
            pr_id=pr_id,
        )
        
        annotator = WikiCandidateAnnotator.__new__(WikiCandidateAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].confidence == 0.8
    
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
    
    def test_no_title_preamble(self, pr_id):
        """Should return nothing if first line is preamble."""
        data = make_pr_data(
            prompt_text="Write about cats",
            response_text="Sure, here's an article about cats:\n\n# The Domestic Cat\n\n...",
            pr_id=pr_id,
        )
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        # This is the expected behavior - naive extractor misses the title
        # because first line is a preamble, not a title
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
            response_text=None,
            pr_id=pr_id,
        )
        data.response_text = None  # Override
        
        annotator = NaiveTitleAnnotator.__new__(NaiveTitleAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0


# ============================================================
# Annotation Filter Tests (class attributes)
# ============================================================

class TestAnnotatorFilters:
    """Test REQUIRES_ANNOTATIONS and SKIP_IF_ANNOTATIONS attributes."""
    
    def test_wiki_candidate_has_no_requirements(self):
        """WikiCandidateAnnotator should have no prerequisites."""
        assert WikiCandidateAnnotator.REQUIRES_ANNOTATIONS == []
        assert WikiCandidateAnnotator.SKIP_IF_ANNOTATIONS == []
    
    def test_naive_title_requires_wiki(self):
        """NaiveTitleAnnotator should require wiki_article."""
        assert ('exchange_type', 'wiki_article') in NaiveTitleAnnotator.REQUIRES_ANNOTATIONS
    
    def test_annotator_metadata(self):
        """Check annotator class metadata."""
        assert WikiCandidateAnnotator.ENTITY_TYPE == 'prompt_response'
        assert WikiCandidateAnnotator.ANNOTATION_KEY == 'exchange_type'
        
        assert NaiveTitleAnnotator.ENTITY_TYPE == 'prompt_response'
        assert NaiveTitleAnnotator.ANNOTATION_KEY == 'proposed_title'
        
        # Wiki detection should run before title extraction
        assert WikiCandidateAnnotator.PRIORITY > NaiveTitleAnnotator.PRIORITY