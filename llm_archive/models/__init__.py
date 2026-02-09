# llm_archive/models/__init__.py
"""SQLAlchemy models for raw and derived schemas."""

from llm_archive.models.raw import (
    Base,
    Source,
    Dialogue,
    Message,
    ContentPart,
    Citation,
    Attachment,
    ChatGPTMessageMeta,
    ChatGPTSearchGroup,
    ChatGPTSearchEntry,
    ChatGPTCodeExecution,
    ChatGPTCodeOutput,
    ChatGPTDalleGeneration,
    ChatGPTCanvasDoc,
    ClaudeMessageMeta,
)

from llm_archive.models.derived import (
    PromptResponse,
    PromptResponseContent,
    AnnotatorCursor,
)

from llm_archive.models.annotations import (
    get_annotation_model,
    get_all_annotation_models,
    ContentPartAnnotationFlag,
    ContentPartAnnotationString,
    PromptResponseAnnotationFlag,
    PromptResponseAnnotationString,
)

__all__ = [
    # Base
    "Base",
    # Raw core
    "Source",
    "Dialogue",
    "Message",
    "ContentPart",
    "Citation",
    "Attachment",
    # Raw ChatGPT extensions
    "ChatGPTMessageMeta",
    "ChatGPTSearchGroup",
    "ChatGPTSearchEntry",
    "ChatGPTCodeExecution",
    "ChatGPTCodeOutput",
    "ChatGPTDalleGeneration",
    "ChatGPTCanvasDoc",
    # Raw Claude extensions
    "ClaudeMessageMeta",
    # Derived
    "PromptResponse",
    "PromptResponseContent",
    "AnnotatorCursor",
    # Annotation model helpers
    "get_annotation_model",
    "get_all_annotation_models",
    # Common annotation models
    "ContentPartAnnotationFlag",
    "ContentPartAnnotationString",
    "PromptResponseAnnotationFlag",
    "PromptResponseAnnotationString",
]
