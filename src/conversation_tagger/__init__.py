# src/conversation_tagger/__init__.py
"""
Simplified conversation tagger with dict-based annotations.
"""

from .core.models import Exchange, Conversation
from .core.annotator import Annotator, AnnotationPipeline
from .core.parser import ExchangeParser, ConversationProcessor
from .factory import (
    create_default_annotator,
    create_basic_annotator, 
    create_code_focused_annotator,
    create_default_parser,
    create_basic_parser,
    create_default_processor,
    create_custom_processor,
    create_pipeline_processor,
    quick_annotate,
    batch_annotate,
    create_default_tagger  # Legacy compatibility
)

__version__ = "0.2.0"

__all__ = [
    # Core classes
    'Exchange',
    'Conversation', 
    'Annotator',
    'AnnotationPipeline',
    'ExchangeParser',
    'ConversationProcessor',
    
    # Factory functions
    'create_default_annotator',
    'create_basic_annotator',
    'create_code_focused_annotator', 
    'create_default_parser',
    'create_basic_parser',
    'create_default_processor',
    'create_custom_processor',
    'create_pipeline_processor',
    
    # Convenience functions
    'quick_annotate',
    'batch_annotate',
    
    # Legacy compatibility
    'create_default_tagger'
]
