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
    DialogueTree,
    MessagePath,
    LinearSequence,
    SequenceMessage,
    Exchange,
    ExchangeMessage,
    SequenceExchange,
    ExchangeContent,
    Annotation,
    ContentHash,
    PromptResponse,
    PromptResponseContent,
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
    "DialogueTree",
    "MessagePath",
    "LinearSequence",
    "SequenceMessage",
    "Exchange",
    "ExchangeMessage",
    "SequenceExchange",
    "ExchangeContent",
    "Annotation",
    "ContentHash",
    "PromptResponse",
    "PromptResponseContent",
]
