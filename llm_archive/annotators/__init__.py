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

**Cursor-Based Incremental Processing**

All annotators extend BaseAnnotator which manages cursor state.
On each run only entities with created_at > high_water_mark are processed.
Changing VERSION creates a new cursor, forcing full reprocessing.

**Creating a Custom Annotator**

    from llm_archive.annotators.prompt_response import (
        PromptResponseAnnotator, PromptResponseData,
    )
    from llm_archive.annotations.core import AnnotationResult, ValueType

    class MyAnnotator(PromptResponseAnnotator):
        ANNOTATION_KEY = 'my_tag'
        VALUE_TYPE = ValueType.STRING
        PRIORITY = 50
        VERSION = '1.0'

        def annotate(self, data: PromptResponseData) -> list[AnnotationResult]:
            if some_condition(data):
                return [AnnotationResult(key='my_tag', value='detected')]
            return []

Then register it:

    from llm_archive.annotators.registry import get_default_registry

    registry = get_default_registry()
    registry.register(MyAnnotator)
    results = registry.run_all(session)
"""

from llm_archive.annotators.base import BaseAnnotator
from llm_archive.annotators.registry import AnnotatorRegistry, get_default_registry

from llm_archive.annotators.content_part import (
    ContentPartAnnotator,
    ContentPartData,
    CodeBlockAnnotator,
    LatexContentAnnotator,
    WikiLinkContentAnnotator,
    CONTENT_PART_ANNOTATORS,
)

from llm_archive.annotators.prompt_response import (
    PromptResponseAnnotator,
    PromptResponseData,
    WikiCandidateAnnotator,
    NaiveTitleAnnotator,
    PROMPT_RESPONSE_ANNOTATORS,
)

__all__ = [
    # Base
    "BaseAnnotator",
    # Registry
    "AnnotatorRegistry",
    "get_default_registry",
    # Content-part annotators
    "ContentPartAnnotator",
    "ContentPartData",
    "CodeBlockAnnotator",
    "ScriptHeaderAnnotator",
    "LatexContentAnnotator",
    "WikiLinkContentAnnotator",
    "CONTENT_PART_ANNOTATORS",
    # Prompt-response annotators
    "PromptResponseAnnotator",
    "PromptResponseData",
    "WikiCandidateAnnotator",
    "NaiveTitleAnnotator",
    "PROMPT_RESPONSE_ANNOTATORS",
]
