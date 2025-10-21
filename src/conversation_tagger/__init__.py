# conversation_tagger/__init__.py
"""
Minimal conversation tagging system with exchange-based analysis.
Now includes database-backed incremental processing.
"""

# Tag import removed - using dictionary-based annotations
from .core.tagger import ConversationTagger
from .factory import create_default_tagger
from .core.conversation import Conversation
from .core.exchange import Exchange
from .core.message import Message
from .core.exchange_parser import ExchangeParser, ExchangeParserOAI, ExchangeParserClaude
from .core.exchange_tagger import ExchangeTagger
from .core.detection import EXCHANGE_RULES, CONVERSATION_RULES
from .core.generate import generate_notes

# Data loading and processing (file-based)
from .data import ConversationLoader, load_conversations, DataSourceConfig, get_default_config
from .processing import ProcessingPipeline, BatchProcessor, ConversationFilter, FilterCriteria
from .processing.pipeline import ProcessingConfig

# Database layer (incremental processing)
from .db import DatabaseManager, IncrementalIngester, ConversationQuery
from .db.tagging import DatabaseTagger, DatabaseBatchProcessor

__all__ = [
    # Core conversation objects
    'ConversationTagger', 'create_default_tagger', 'Conversation', 'Exchange', 'Message', 
    'ExchangeParser', 'ExchangeParserOAI', 'ExchangeParserClaude', 'ExchangeTagger', 
    'EXCHANGE_RULES', 'CONVERSATION_RULES', 'generate_notes',
    
    # File-based processing (legacy)
    'ConversationLoader', 'load_conversations', 'DataSourceConfig', 'get_default_config',
    'ProcessingPipeline', 'BatchProcessor', 'ConversationFilter', 'FilterCriteria', 'ProcessingConfig',
    
    # Database-backed processing (recommended)
    'DatabaseManager', 'IncrementalIngester', 'ConversationQuery', 'DatabaseTagger', 'DatabaseBatchProcessor'
]