# conversation_tagger/cli/__init__.py
"""
Command-line interface for conversation processing.
Supports both file-based and database-backed processing.
"""

from .main import main as console_main
from .discovery import discover_and_configure

__all__ = ['console_main', 'discover_and_configure']