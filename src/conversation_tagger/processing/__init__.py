# conversation_tagger/processing/__init__.py
"""
Processing pipeline machinery for batch conversation processing.
"""

from .pipeline import ProcessingPipeline, BatchProcessor
from .filters import ConversationFilter, FilterCriteria

__all__ = [
    'ProcessingPipeline',
    'BatchProcessor', 
    'ConversationFilter',
    'FilterCriteria'
]
