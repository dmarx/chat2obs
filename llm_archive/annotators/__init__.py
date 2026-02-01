# llm_archive/annotators/__init__.py
"""Annotation infrastructure for entities.

Annotators analyze entities and produce annotations stored in derived.annotations.

Annotation Types:
- tag: For filtering (topic:physics, quality:high)
- title: For generation (wiki article titles)
- summary: Brief description
- feature: Detected features (has_code_blocks, has_latex)
- topic: Subject classification
- quality: Quality assessment

Creating Custom Annotators:
--------------------------

For MESSAGE annotations based on text content, use MessageTextAnnotator:

    class MyMessageAnnotator(MessageTextAnnotator):
        ANNOTATION_TYPE = 'feature'
        VERSION = '1.0'
        ROLE_FILTER = 'assistant'  # or 'user' or None for all
        
        def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
            if 'keyword' in data.text:
                return [AnnotationResult(value='has_keyword', confidence=0.9)]
            return []

For EXCHANGE annotations, use ExchangeAnnotator:

    class MyExchangeAnnotator(ExchangeAnnotator):
        ANNOTATION_TYPE = 'tag'
        VERSION = '1.0'
        
        def annotate(self, data: ExchangeData) -> list[AnnotationResult]:
            if (data.assistant_word_count or 0) > 1000:
                return [AnnotationResult(value='long_response', key='length')]
            return []

The base classes handle:
- Cursor-based incremental processing (only new entities)
- Querying and iterating over entities
- Grouping content parts by message
- Tracking entities and finalizing cursors

Bump VERSION to reprocess all entities with new logic.
"""

from llm_archive.annotators.base import (
    Annotator,
    AnnotationManager,
    AnnotationResult,
    MessageTextAnnotator,
    MessageTextData,
    ExchangeAnnotator,
    ExchangeData,
)
from llm_archive.annotators.features import (
    WikiLinkAnnotator,
    CodeBlockAnnotator,
    LatexAnnotator,
    ContinuationAnnotator,
    ExchangeTypeAnnotator,
)

__all__ = [
    # Base classes
    "Annotator",
    "AnnotationManager",
    "AnnotationResult",
    # Message annotation
    "MessageTextAnnotator",
    "MessageTextData",
    # Exchange annotation
    "ExchangeAnnotator",
    "ExchangeData",
    # Built-in annotators
    "WikiLinkAnnotator",
    "CodeBlockAnnotator",
    "LatexAnnotator",
    "ContinuationAnnotator",
    "ExchangeTypeAnnotator",
]
