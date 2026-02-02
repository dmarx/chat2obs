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
- metadata: Structural metadata (dialogue_length, prompt_stats)

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

For EXCHANGE annotations based on content, use ExchangeAnnotator:

    class MyExchangeAnnotator(ExchangeAnnotator):
        ANNOTATION_TYPE = 'tag'
        VERSION = '1.0'
        
        def annotate(self, data: ExchangeData) -> list[AnnotationResult]:
            if (data.assistant_word_count or 0) > 1000:
                return [AnnotationResult(value='long_response', key='length')]
            return []

For EXCHANGE annotations based on platform features, use ExchangePlatformAnnotator:

    class MyPlatformAnnotator(ExchangePlatformAnnotator):
        ANNOTATION_TYPE = 'feature'
        VERSION = '1.0'
        
        def annotate(self, data: ExchangePlatformData) -> list[AnnotationResult]:
            # Can query platform tables using data.message_ids
            ...

For DIALOGUE annotations with aggregate statistics, use DialogueAnnotator:

    class MyDialogueAnnotator(DialogueAnnotator):
        ANNOTATION_TYPE = 'metadata'
        VERSION = '1.0'
        
        def annotate(self, data: DialogueData) -> list[AnnotationResult]:
            if data.exchange_count > 10:
                return [AnnotationResult(value='extended', key='length')]
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
    ExchangePlatformAnnotator,
    ExchangePlatformData,
    DialogueAnnotator,
    DialogueData,
)
from llm_archive.annotators.features import (
    # Message-level annotators
    WikiLinkAnnotator,
    CodeBlockAnnotator,
    FunctionDefinitionAnnotator,
    ImportStatementAnnotator,
    ScriptHeaderAnnotator,
    CodeKeywordDensityAnnotator,
    CodeStructureAnnotator,
    LatexAnnotator,
    ContinuationAnnotator,
    QuoteElaborateAnnotator,
    # Exchange content annotators
    ExchangeTypeAnnotator,
    CodeEvidenceAnnotator,
    TitleExtractionAnnotator,
    # Exchange platform annotators
    WebSearchAnnotator,
    CodeExecutionAnnotator,
    CanvasAnnotator,
    GizmoAnnotator,
    AttachmentAnnotator,
    # Dialogue annotators
    DialogueLengthAnnotator,
    PromptStatsAnnotator,
    FirstExchangeAnnotator,
    InteractionPatternAnnotator,
    CodingAssistanceAnnotator,
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
    # Exchange platform annotation
    "ExchangePlatformAnnotator",
    "ExchangePlatformData",
    # Dialogue annotation
    "DialogueAnnotator",
    "DialogueData",
    # Message-level annotators
    "WikiLinkAnnotator",
    "CodeBlockAnnotator",
    "FunctionDefinitionAnnotator",
    "ImportStatementAnnotator",
    "ScriptHeaderAnnotator",
    "CodeKeywordDensityAnnotator",
    "CodeStructureAnnotator",
    "LatexAnnotator",
    "ContinuationAnnotator",
    "QuoteElaborateAnnotator",
    # Exchange content annotators
    "ExchangeTypeAnnotator",
    "CodeEvidenceAnnotator",
    "TitleExtractionAnnotator",
    # Exchange platform annotators
    "WebSearchAnnotator",
    "CodeExecutionAnnotator",
    "CanvasAnnotator",
    "GizmoAnnotator",
    "AttachmentAnnotator",
    # Dialogue annotators
    "DialogueLengthAnnotator",
    "PromptStatsAnnotator",
    "FirstExchangeAnnotator",
    "InteractionPatternAnnotator",
    "CodingAssistanceAnnotator",
]