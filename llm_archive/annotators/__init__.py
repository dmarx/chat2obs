# llm_archive/annotators/__init__.py
"""Annotation infrastructure for entities.

Annotators analyze entities and produce annotations stored in derived.annotations.

Architecture Overview:
---------------------

**Annotation Keys vs Annotators (Strategy Pattern)**

An ANNOTATION_KEY identifies what we're trying to detect (e.g., 'code', 'latex').
Multiple annotators can target the same key using different strategies.
Higher PRIORITY annotators run first; lower-priority ones can be skipped
if the key is already satisfied.

Example: Detecting code in an exchange
  - ChatGPTCodeExecutionAnnotator (priority=100): Platform ground truth
  - CodeBlockAnnotator (priority=90): Explicit ``` blocks  
  - CodeStructureAnnotator (priority=70): Function/class patterns
  - CodeKeywordDensityAnnotator (priority=30): Keyword density

If code execution is detected (priority 100), lower-priority heuristics
can check has_annotation_key() to skip redundant work.

**Annotation Types**
- tag: For filtering (topic:physics, quality:high)
- feature: Detected features (has_code_blocks, has_latex)
- metadata: Structural data (dialogue_length, prompt_stats)
- title: Generated titles
- summary: Brief descriptions

**Entity Types**
- message: Individual messages
- exchange: User prompt + assistant response pair
- dialogue: Entire conversation

Creating Custom Annotators:
--------------------------

For MESSAGE annotations based on text content:

    class MyMessageAnnotator(MessageTextAnnotator):
        ANNOTATION_TYPE = 'feature'
        ANNOTATION_KEY = 'my_feature'  # What we're detecting
        PRIORITY = 50                   # When to run (higher = first)
        VERSION = '1.0'
        ROLE_FILTER = 'assistant'       # or 'user' or None for all
        
        def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
            if 'keyword' in data.text:
                return [AnnotationResult(value='has_keyword', confidence=0.9)]
            return []

For EXCHANGE annotations based on content:

    class MyExchangeAnnotator(ExchangeAnnotator):
        ANNOTATION_TYPE = 'tag'
        ANNOTATION_KEY = 'my_tag'
        PRIORITY = 50
        VERSION = '1.0'
        
        def annotate(self, data: ExchangeData) -> list[AnnotationResult]:
            if (data.assistant_word_count or 0) > 1000:
                return [AnnotationResult(value='long_response', key='length')]
            return []

For EXCHANGE annotations based on platform features (e.g., ChatGPT):

    class MyChatGPTAnnotator(ExchangePlatformAnnotator):
        ANNOTATION_TYPE = 'feature'
        ANNOTATION_KEY = 'platform_feature'
        PRIORITY = 100  # Platform = ground truth
        VERSION = '1.0'
        
        def annotate(self, data: ExchangePlatformData) -> list[AnnotationResult]:
            # Query platform tables using data.message_ids
            ...

For DIALOGUE annotations with aggregate statistics:

    class MyDialogueAnnotator(DialogueAnnotator):
        ANNOTATION_TYPE = 'metadata'
        ANNOTATION_KEY = 'my_stats'
        PRIORITY = 50
        VERSION = '1.0'
        
        def annotate(self, data: DialogueData) -> list[AnnotationResult]:
            if data.exchange_count > 10:
                return [AnnotationResult(value='extended', key='length')]
            return []

Priority Guidelines:
- 100: Platform features (ground truth from database)
- 90: Explicit syntax (```, shebangs)
- 70: Structural patterns (function definitions)
- 50: Keyword detection (default)
- 30: Density/heuristic analysis

Bump VERSION to reprocess all entities with new logic.
"""

from llm_archive.annotators.base import (
    # Base classes
    Annotator,
    AnnotationManager,
    AnnotationResult,
    # Message annotation
    MessageTextAnnotator,
    MessageTextData,
    # Exchange annotation  
    ExchangeAnnotator,
    ExchangeData,
    ExchangePlatformAnnotator,
    ExchangePlatformData,
    # Dialogue annotation
    DialogueAnnotator,
    DialogueData,
)

from llm_archive.annotators.message import (
    # Code detection (priority order)
    CodeBlockAnnotator,
    ScriptHeaderAnnotator,
    CodeStructureAnnotator,
    FunctionDefinitionAnnotator,
    ImportStatementAnnotator,
    CodeKeywordDensityAnnotator,
    # Other message features
    WikiLinkAnnotator,
    LatexAnnotator,
    ContinuationAnnotator,
    QuoteElaborateAnnotator,
)

from llm_archive.annotators.exchange import (
    ExchangeTypeAnnotator,
    CodeEvidenceAnnotator,
    TitleExtractionAnnotator,
)

from llm_archive.annotators.dialogue import (
    DialogueLengthAnnotator,
    PromptStatsAnnotator,
    FirstExchangeAnnotator,
    InteractionPatternAnnotator,
    CodingAssistanceAnnotator,
)

from llm_archive.annotators.chatgpt import (
    ChatGPTWebSearchAnnotator,
    ChatGPTCodeExecutionAnnotator,
    ChatGPTCanvasAnnotator,
    ChatGPTGizmoAnnotator,
    ChatGPTAttachmentAnnotator,
    ChatGPTDalleAnnotator,
)

__all__ = [
    # Base classes
    "Annotator",
    "AnnotationManager",
    "AnnotationResult",
    # Message annotation base
    "MessageTextAnnotator",
    "MessageTextData",
    # Exchange annotation base
    "ExchangeAnnotator",
    "ExchangeData",
    "ExchangePlatformAnnotator",
    "ExchangePlatformData",
    # Dialogue annotation base
    "DialogueAnnotator",
    "DialogueData",
    # Message annotators - Code detection
    "CodeBlockAnnotator",
    "ScriptHeaderAnnotator",
    "CodeStructureAnnotator",
    "FunctionDefinitionAnnotator",
    "ImportStatementAnnotator",
    "CodeKeywordDensityAnnotator",
    # Message annotators - Other features
    "WikiLinkAnnotator",
    "LatexAnnotator",
    "ContinuationAnnotator",
    "QuoteElaborateAnnotator",
    # Exchange annotators
    "ExchangeTypeAnnotator",
    "CodeEvidenceAnnotator",
    "TitleExtractionAnnotator",
    # Dialogue annotators
    "DialogueLengthAnnotator",
    "PromptStatsAnnotator",
    "FirstExchangeAnnotator",
    "InteractionPatternAnnotator",
    "CodingAssistanceAnnotator",
    # ChatGPT-specific annotators
    "ChatGPTWebSearchAnnotator",
    "ChatGPTCodeExecutionAnnotator",
    "ChatGPTCanvasAnnotator",
    "ChatGPTGizmoAnnotator",
    "ChatGPTAttachmentAnnotator",
    "ChatGPTDalleAnnotator",
]