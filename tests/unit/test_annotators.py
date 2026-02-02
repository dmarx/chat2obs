# tests/unit/test_annotators.py
"""Unit tests for annotator logic.

Tests the annotate() method of each annotator class by constructing
data objects directly, without requiring a database.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from llm_archive.annotators import (
    # Data classes
    MessageTextData,
    ExchangeData,
    DialogueData,
    AnnotationResult,
    # Message annotators
    CodeBlockAnnotator,
    ScriptHeaderAnnotator,
    CodeStructureAnnotator,
    FunctionDefinitionAnnotator,
    ImportStatementAnnotator,
    CodeKeywordDensityAnnotator,
    WikiLinkAnnotator,
    LatexAnnotator,
    ContinuationAnnotator,
    QuoteElaborateAnnotator,
    # Exchange annotators
    ExchangeTypeAnnotator,
    CodeEvidenceAnnotator,
    TitleExtractionAnnotator,
    # Dialogue annotators
    DialogueLengthAnnotator,
    PromptStatsAnnotator,
    FirstExchangeAnnotator,
    InteractionPatternAnnotator,
    CodingAssistanceAnnotator,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def message_id():
    return uuid4()


@pytest.fixture
def exchange_id():
    return uuid4()


@pytest.fixture
def dialogue_id():
    return uuid4()


def make_message_data(text: str, role: str = 'assistant', message_id=None) -> MessageTextData:
    """Helper to create MessageTextData for testing."""
    return MessageTextData(
        message_id=message_id or uuid4(),
        text=text,
        created_at=datetime.now(timezone.utc),
        role=role,
    )


def make_exchange_data(
    user_text: str | None = None,
    assistant_text: str | None = None,
    exchange_id=None,
) -> ExchangeData:
    """Helper to create ExchangeData for testing."""
    return ExchangeData(
        exchange_id=exchange_id or uuid4(),
        user_text=user_text,
        assistant_text=assistant_text,
        user_word_count=len(user_text.split()) if user_text else None,
        assistant_word_count=len(assistant_text.split()) if assistant_text else None,
        created_at=datetime.now(timezone.utc),
    )


def make_dialogue_data(
    exchange_count: int = 5,
    user_texts: list[str] | None = None,
    assistant_texts: list[str] | None = None,
    dialogue_id=None,
) -> DialogueData:
    """Helper to create DialogueData for testing."""
    if user_texts is None:
        user_texts = [f"User message {i}" for i in range(exchange_count)]
    if assistant_texts is None:
        assistant_texts = [f"Assistant response {i}" for i in range(exchange_count)]
    
    user_word_counts = [len(t.split()) for t in user_texts]
    assistant_word_counts = [len(t.split()) for t in assistant_texts]
    
    return DialogueData(
        dialogue_id=dialogue_id or uuid4(),
        source='chatgpt',
        title='Test Dialogue',
        exchange_count=exchange_count,
        message_count=exchange_count * 2,
        user_message_count=exchange_count,
        assistant_message_count=exchange_count,
        user_texts=user_texts,
        assistant_texts=assistant_texts,
        user_word_counts=user_word_counts,
        assistant_word_counts=assistant_word_counts,
        created_at=datetime.now(timezone.utc),
        first_user_text=user_texts[0] if user_texts else None,
        first_assistant_text=assistant_texts[0] if assistant_texts else None,
    )


# ============================================================
# Message Annotator Tests - Code Detection
# ============================================================

class TestCodeBlockAnnotator:
    """Test CodeBlockAnnotator (priority 90)."""
    
    def test_detects_code_block_without_language(self, message_id):
        """Should detect basic code blocks."""
        text = "Here's the code:\n```\nprint('hello')\n```"
        data = make_message_data(text, message_id=message_id)
        
        # Create instance without session (we only test annotate())
        annotator = CodeBlockAnnotator.__new__(CodeBlockAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) >= 1
        assert results[0].value == 'has_code_blocks'
        assert results[0].confidence == 1.0
        assert results[0].data['count'] == 1
    
    def test_detects_code_block_with_language(self, message_id):
        """Should detect code blocks with language specification."""
        text = "```python\ndef hello():\n    print('world')\n```"
        data = make_message_data(text, message_id=message_id)
        
        annotator = CodeBlockAnnotator.__new__(CodeBlockAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) >= 1
        assert 'python' in results[0].data['languages']
        # Should also have language-specific annotation
        lang_results = [r for r in results if r.key == 'code_language']
        assert len(lang_results) == 1
        assert lang_results[0].value == 'python'
    
    def test_counts_multiple_code_blocks(self, message_id):
        """Should count multiple code blocks."""
        text = "```python\ncode1\n```\n\nMore text\n\n```javascript\ncode2\n```"
        data = make_message_data(text, message_id=message_id)
        
        annotator = CodeBlockAnnotator.__new__(CodeBlockAnnotator)
        results = annotator.annotate(data)
        
        assert results[0].data['count'] == 2
        languages = results[0].data['languages']
        assert 'python' in languages
        assert 'javascript' in languages
    
    def test_no_code_blocks(self, message_id):
        """Should return empty for text without code blocks."""
        text = "This is just regular text without any code."
        data = make_message_data(text, message_id=message_id)
        
        annotator = CodeBlockAnnotator.__new__(CodeBlockAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0


class TestScriptHeaderAnnotator:
    """Test ScriptHeaderAnnotator (priority 85)."""
    
    def test_detects_shebang(self, message_id):
        """Should detect Unix shebang."""
        text = "#!/bin/bash\necho 'hello'"
        data = make_message_data(text, message_id=message_id)
        
        annotator = ScriptHeaderAnnotator.__new__(ScriptHeaderAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'has_script_headers'
        assert '#!/bin/' in results[0].data['indicators']
    
    def test_detects_include(self, message_id):
        """Should detect C/C++ includes."""
        text = '#include <stdio.h>\nint main() {}'
        data = make_message_data(text, message_id=message_id)
        
        annotator = ScriptHeaderAnnotator.__new__(ScriptHeaderAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert '#include' in results[0].data['indicators']
    
    def test_detects_php(self, message_id):
        """Should detect PHP opening tag."""
        text = "<?php\necho 'hello';\n?>"
        data = make_message_data(text, message_id=message_id)
        
        annotator = ScriptHeaderAnnotator.__new__(ScriptHeaderAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1


class TestCodeStructureAnnotator:
    """Test CodeStructureAnnotator (priority 70)."""
    
    def test_detects_python_function(self, message_id):
        """Should detect Python function pattern."""
        text = "def hello(name):\n    return f'Hello {name}'"
        data = make_message_data(text, message_id=message_id)
        
        annotator = CodeStructureAnnotator.__new__(CodeStructureAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert 'python_function' in results[0].data['patterns']
    
    def test_detects_javascript_function(self, message_id):
        """Should detect JavaScript function pattern."""
        text = "function greet(name) { return 'Hello ' + name; }"
        data = make_message_data(text, message_id=message_id)
        
        annotator = CodeStructureAnnotator.__new__(CodeStructureAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert 'js_function' in results[0].data['patterns']
    
    def test_detects_arrow_function(self, message_id):
        """Should detect arrow function pattern."""
        text = "const greet = (name) => { return 'Hello ' + name; }"
        data = make_message_data(text, message_id=message_id)
        
        annotator = CodeStructureAnnotator.__new__(CodeStructureAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert 'arrow_function' in results[0].data['patterns']


class TestFunctionDefinitionAnnotator:
    """Test FunctionDefinitionAnnotator (priority 50)."""
    
    def test_detects_def_keyword(self, message_id):
        """Should detect 'def' keyword."""
        text = "We define a function using def in Python."
        data = make_message_data(text, message_id=message_id)
        
        annotator = FunctionDefinitionAnnotator.__new__(FunctionDefinitionAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert 'def' in results[0].data['keywords']


class TestImportStatementAnnotator:
    """Test ImportStatementAnnotator (priority 50)."""
    
    def test_detects_python_import(self, message_id):
        """Should detect Python import statements."""
        text = "import os\nfrom pathlib import Path"
        data = make_message_data(text, message_id=message_id)
        
        annotator = ImportStatementAnnotator.__new__(ImportStatementAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].data['count'] >= 2


class TestCodeKeywordDensityAnnotator:
    """Test CodeKeywordDensityAnnotator (priority 30)."""
    
    def test_detects_high_density(self, message_id):
        """Should detect high keyword density in long text."""
        # Create text with many programming keywords
        text = """
        function processData() {
            if (data != null) {
                for (let i = 0; i < data.length; i++) {
                    try {
                        const result = await process(data[i]);
                        return result;
                    } catch (e) {
                        break;
                    }
                }
            } else {
                while (true) {
                    continue;
                }
            }
        }
        """ + " padding" * 100  # Make it long enough
        data = make_message_data(text, message_id=message_id)
        
        annotator = CodeKeywordDensityAnnotator.__new__(CodeKeywordDensityAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'has_high_keyword_density'
    
    def test_ignores_short_text(self, message_id):
        """Should not trigger on short text."""
        text = "function if for while return"
        data = make_message_data(text, message_id=message_id)
        
        annotator = CodeKeywordDensityAnnotator.__new__(CodeKeywordDensityAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0


# ============================================================
# Message Annotator Tests - Other Features
# ============================================================

class TestWikiLinkAnnotator:
    """Test WikiLinkAnnotator."""
    
    def test_detects_wiki_links(self, message_id):
        """Should detect [[wiki links]]."""
        text = "See [[Python]] for more info on [[programming]]."
        data = make_message_data(text, role='assistant', message_id=message_id)
        
        annotator = WikiLinkAnnotator.__new__(WikiLinkAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'has_wiki_links'
        assert results[0].data['count'] == 2
    
    def test_no_wiki_links(self, message_id):
        """Should return empty for text without wiki links."""
        text = "Regular text with [markdown](links) but no wiki links."
        data = make_message_data(text, role='assistant', message_id=message_id)
        
        annotator = WikiLinkAnnotator.__new__(WikiLinkAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0


class TestLatexAnnotator:
    """Test LatexAnnotator."""
    
    def test_detects_display_math(self, message_id):
        """Should detect display math $$...$$."""
        text = "The formula is $$E = mc^2$$"
        data = make_message_data(text, role='assistant', message_id=message_id)
        
        annotator = LatexAnnotator.__new__(LatexAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'has_latex'
    
    def test_detects_latex_commands(self, message_id):
        """Should detect LaTeX commands."""
        text = "The integral is \\int_0^1 f(x) dx and \\frac{1}{2}"
        data = make_message_data(text, role='assistant', message_id=message_id)
        
        annotator = LatexAnnotator.__new__(LatexAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert '\\frac' in results[0].data['commands']


class TestContinuationAnnotator:
    """Test ContinuationAnnotator."""
    
    def test_detects_continue_keyword(self, message_id):
        """Should detect 'continue' keyword."""
        text = "continue"
        data = make_message_data(text, role='user', message_id=message_id)
        
        annotator = ContinuationAnnotator.__new__(ContinuationAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'continuation_signal'
    
    def test_ignores_long_messages(self, message_id):
        """Should ignore continuation keywords in long messages."""
        text = "Please continue with the analysis of the data and tell me more about it."
        data = make_message_data(text, role='user', message_id=message_id)
        
        annotator = ContinuationAnnotator.__new__(ContinuationAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0


class TestQuoteElaborateAnnotator:
    """Test QuoteElaborateAnnotator."""
    
    def test_detects_quote_elaborate(self, message_id):
        """Should detect quote+elaborate pattern."""
        text = "> Some quoted text here\nelaborate"
        data = make_message_data(text, role='user', message_id=message_id)
        
        annotator = QuoteElaborateAnnotator.__new__(QuoteElaborateAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'quote_elaborate'
        assert results[0].data['keyword'] == 'elaborate'
    
    def test_not_detected_without_quote(self, message_id):
        """Should not detect if not starting with quote."""
        text = "elaborate on this topic"
        data = make_message_data(text, role='user', message_id=message_id)
        
        annotator = QuoteElaborateAnnotator.__new__(QuoteElaborateAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0


# ============================================================
# Exchange Annotator Tests
# ============================================================

class TestExchangeTypeAnnotator:
    """Test ExchangeTypeAnnotator."""
    
    def test_classifies_coding_exchange(self, exchange_id):
        """Should classify as coding when multiple code blocks present."""
        user = "How do I reverse a string?"
        assistant = "Here's how:\n```python\ns[::-1]\n```\nOr:\n```python\nreversed(s)\n```"
        data = make_exchange_data(user, assistant, exchange_id=exchange_id)
        
        annotator = ExchangeTypeAnnotator.__new__(ExchangeTypeAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'coding'
    
    def test_classifies_wiki_article(self, exchange_id):
        """Should classify as wiki_article when wiki links present."""
        user = "Tell me about Python"
        assistant = "[[Python]] is a [[programming language]] created by [[Guido van Rossum]]."
        data = make_exchange_data(user, assistant, exchange_id=exchange_id)
        
        annotator = ExchangeTypeAnnotator.__new__(ExchangeTypeAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'wiki_article'


class TestCodeEvidenceAnnotator:
    """Test CodeEvidenceAnnotator."""
    
    def test_strong_evidence_code_blocks(self, exchange_id):
        """Should detect strong evidence with code blocks."""
        user = "Show me code"
        assistant = "```python\nprint('hello')\n```"
        data = make_exchange_data(user, assistant, exchange_id=exchange_id)
        
        annotator = CodeEvidenceAnnotator.__new__(CodeEvidenceAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'strong_code_evidence'
        assert results[0].confidence == 0.95
    
    def test_moderate_evidence_keywords(self, exchange_id):
        """Should detect moderate evidence with function keywords."""
        user = "How do I define a function?"
        assistant = "You use def to define a function, then import what you need."
        data = make_exchange_data(user, assistant, exchange_id=exchange_id)
        
        annotator = CodeEvidenceAnnotator.__new__(CodeEvidenceAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'moderate_code_evidence'


class TestTitleExtractionAnnotator:
    """Test TitleExtractionAnnotator."""
    
    def test_extracts_markdown_title(self, exchange_id):
        """Should extract markdown header title."""
        user = "Write an article"
        assistant = "# The Art of Python Programming\n\nPython is a versatile language..."
        data = make_exchange_data(user, assistant, exchange_id=exchange_id)
        
        annotator = TitleExtractionAnnotator.__new__(TitleExtractionAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'The Art of Python Programming'
        assert results[0].key == 'proposed_title'
    
    def test_extracts_bold_title(self, exchange_id):
        """Should extract bold header title."""
        user = "Write an article"
        assistant = "**Introduction to Machine Learning**\n\nML is a branch..."
        data = make_exchange_data(user, assistant, exchange_id=exchange_id)
        
        annotator = TitleExtractionAnnotator.__new__(TitleExtractionAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'Introduction to Machine Learning'


# ============================================================
# Dialogue Annotator Tests
# ============================================================

class TestDialogueLengthAnnotator:
    """Test DialogueLengthAnnotator."""
    
    def test_single_exchange(self, dialogue_id):
        """Should classify single exchange."""
        data = make_dialogue_data(exchange_count=1, dialogue_id=dialogue_id)
        
        annotator = DialogueLengthAnnotator.__new__(DialogueLengthAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'single'
    
    def test_short_dialogue(self, dialogue_id):
        """Should classify short dialogue (2-3 exchanges)."""
        data = make_dialogue_data(exchange_count=3, dialogue_id=dialogue_id)
        
        annotator = DialogueLengthAnnotator.__new__(DialogueLengthAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'short'
    
    def test_medium_dialogue(self, dialogue_id):
        """Should classify medium dialogue (4-10 exchanges)."""
        data = make_dialogue_data(exchange_count=7, dialogue_id=dialogue_id)
        
        annotator = DialogueLengthAnnotator.__new__(DialogueLengthAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'medium'
    
    def test_long_dialogue(self, dialogue_id):
        """Should classify long dialogue (11-25 exchanges)."""
        data = make_dialogue_data(exchange_count=20, dialogue_id=dialogue_id)
        
        annotator = DialogueLengthAnnotator.__new__(DialogueLengthAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'long'
    
    def test_very_long_dialogue(self, dialogue_id):
        """Should classify very long dialogue (>25 exchanges)."""
        data = make_dialogue_data(exchange_count=30, dialogue_id=dialogue_id)
        
        annotator = DialogueLengthAnnotator.__new__(DialogueLengthAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'very_long'


class TestPromptStatsAnnotator:
    """Test PromptStatsAnnotator."""
    
    def test_computes_statistics(self, dialogue_id):
        """Should compute mean, median, variance."""
        user_texts = ["Short", "A bit longer message", "Short again"]
        data = make_dialogue_data(
            exchange_count=3,
            user_texts=user_texts,
            dialogue_id=dialogue_id,
        )
        
        annotator = PromptStatsAnnotator.__new__(PromptStatsAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert 'mean' in results[0].data
        assert 'median' in results[0].data
        assert 'variance' in results[0].data
    
    def test_empty_dialogue(self, dialogue_id):
        """Should handle empty dialogue."""
        data = make_dialogue_data(
            exchange_count=0,
            user_texts=[],
            assistant_texts=[],
            dialogue_id=dialogue_id,
        )
        
        annotator = PromptStatsAnnotator.__new__(PromptStatsAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'none'


class TestFirstExchangeAnnotator:
    """Test FirstExchangeAnnotator."""
    
    def test_detects_large_first_message(self, dialogue_id):
        """Should detect large first message."""
        large_message = "x " * 1500  # >2000 chars
        data = make_dialogue_data(
            exchange_count=3,
            user_texts=[large_message, "short", "short"],
            dialogue_id=dialogue_id,
        )
        
        annotator = FirstExchangeAnnotator.__new__(FirstExchangeAnnotator)
        results = annotator.annotate(data)
        
        values = [r.value for r in results]
        assert 'starts_large_content' in values
    
    def test_detects_code_in_first_message(self, dialogue_id):
        """Should detect code in first message."""
        data = make_dialogue_data(
            exchange_count=3,
            user_texts=["```python\ncode here\n```", "follow up", "another"],
            dialogue_id=dialogue_id,
        )
        
        annotator = FirstExchangeAnnotator.__new__(FirstExchangeAnnotator)
        results = annotator.annotate(data)
        
        values = [r.value for r in results]
        assert 'starts_with_code' in values
    
    def test_detects_context_dump(self, dialogue_id):
        """Should detect context dump (short dialogue + large first message)."""
        large_message = "x " * 1500
        data = make_dialogue_data(
            exchange_count=2,
            user_texts=[large_message, "short"],
            dialogue_id=dialogue_id,
        )
        
        annotator = FirstExchangeAnnotator.__new__(FirstExchangeAnnotator)
        results = annotator.annotate(data)
        
        values = [r.value for r in results]
        assert 'context_dump' in values


class TestInteractionPatternAnnotator:
    """Test InteractionPatternAnnotator."""
    
    def test_detects_brief_interaction(self, dialogue_id):
        """Should detect brief interaction (1-3 exchanges)."""
        data = make_dialogue_data(exchange_count=2, dialogue_id=dialogue_id)
        
        annotator = InteractionPatternAnnotator.__new__(InteractionPatternAnnotator)
        results = annotator.annotate(data)
        
        values = [r.value for r in results]
        assert 'brief_interaction' in values
    
    def test_detects_extended_conversation(self, dialogue_id):
        """Should detect extended conversation (10+ exchanges)."""
        data = make_dialogue_data(exchange_count=15, dialogue_id=dialogue_id)
        
        annotator = InteractionPatternAnnotator.__new__(InteractionPatternAnnotator)
        results = annotator.annotate(data)
        
        values = [r.value for r in results]
        assert 'extended_conversation' in values


class TestCodingAssistanceAnnotator:
    """Test CodingAssistanceAnnotator."""
    
    def test_strong_coding_evidence(self, dialogue_id):
        """Should detect strong coding evidence."""
        user_texts = ["```python\ncode\n```", "#!/bin/bash\nscript"]
        assistant_texts = ["```python\nmore code\n```", "Here's the fix"]
        data = make_dialogue_data(
            exchange_count=2,
            user_texts=user_texts,
            assistant_texts=assistant_texts,
            dialogue_id=dialogue_id,
        )
        
        annotator = CodingAssistanceAnnotator.__new__(CodingAssistanceAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 1
        assert results[0].value == 'coding_assistance'
        assert results[0].confidence >= 0.9
    
    def test_no_coding_evidence(self, dialogue_id):
        """Should not detect coding in regular conversation."""
        data = make_dialogue_data(
            exchange_count=3,
            user_texts=["Hello", "How are you?", "Thanks!"],
            assistant_texts=["Hi there!", "I'm doing well.", "You're welcome!"],
            dialogue_id=dialogue_id,
        )
        
        annotator = CodingAssistanceAnnotator.__new__(CodingAssistanceAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) == 0


# ============================================================
# Annotation Strategy Tests
# ============================================================

class TestAnnotatorMetadata:
    """Test annotator class metadata."""
    
    def test_code_annotators_have_key(self):
        """All code annotators should have ANNOTATION_KEY='code'."""
        code_annotators = [
            CodeBlockAnnotator,
            ScriptHeaderAnnotator,
            CodeStructureAnnotator,
            FunctionDefinitionAnnotator,
            ImportStatementAnnotator,
            CodeKeywordDensityAnnotator,
        ]
        for annotator_cls in code_annotators:
            assert annotator_cls.ANNOTATION_KEY == 'code', \
                f"{annotator_cls.__name__} should have ANNOTATION_KEY='code'"
    
    def test_code_annotators_have_priority_order(self):
        """Code annotators should be ordered by priority."""
        # Expected order (highest to lowest)
        expected_order = [
            (CodeBlockAnnotator, 90),
            (ScriptHeaderAnnotator, 85),
            (CodeStructureAnnotator, 70),
            (FunctionDefinitionAnnotator, 50),
            (ImportStatementAnnotator, 50),
            (CodeKeywordDensityAnnotator, 30),
        ]
        
        for annotator_cls, expected_priority in expected_order:
            assert annotator_cls.PRIORITY == expected_priority, \
                f"{annotator_cls.__name__} should have PRIORITY={expected_priority}"
    
    def test_all_annotators_have_version(self):
        """All annotators should have VERSION defined."""
        annotators = [
            CodeBlockAnnotator,
            WikiLinkAnnotator,
            LatexAnnotator,
            ExchangeTypeAnnotator,
            DialogueLengthAnnotator,
        ]
        for annotator_cls in annotators:
            assert annotator_cls.VERSION is not None
            assert isinstance(annotator_cls.VERSION, str)