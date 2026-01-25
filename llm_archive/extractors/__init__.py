# llm_archive/extractors/__init__.py
"""Source-specific extractors for importing dialogue data."""

from llm_archive.extractors.base import BaseExtractor, parse_timestamp, normalize_role
from llm_archive.extractors.chatgpt import ChatGPTExtractor
from llm_archive.extractors.claude import ClaudeExtractor

__all__ = [
    "BaseExtractor",
    "parse_timestamp",
    "normalize_role",
    "ChatGPTExtractor",
    "ClaudeExtractor",
]