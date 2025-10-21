# conversation_tagger/__init__.py
"""
Database-backed conversation tagging system with exchange-based analysis and incremental processing.
"""

from .core.tagger import ConversationTagger
from .factory import create_default_tagger
from .core.conversation import Conversation
from .core.exchange import Exchange
from .core.message import Message
from .core.exchange_parser import ExchangeParser, ExchangeParserOAI, ExchangeParserClaude
from .core.exchange_tagger import ExchangeTagger
from .core.detection import EXCHANGE_RULES, CONVERSATION_RULES
from .core.generate import generate_notes

# Database layer for incremental processing
from .db import DatabaseManager, IncrementalIngester, ConversationQuery
from .db.tagging import DatabaseTagger, DatabaseBatchProcessor

__all__ = [
    # Core conversation objects
    'ConversationTagger', 'create_default_tagger', 'Conversation', 'Exchange', 'Message', 
    'ExchangeParser', 'ExchangeParserOAI', 'ExchangeParserClaude', 'ExchangeTagger', 
    'EXCHANGE_RULES', 'CONVERSATION_RULES', 'generate_notes',
    
    # Database-backed processing
    'DatabaseManager', 'IncrementalIngester', 'ConversationQuery', 'DatabaseTagger', 'DatabaseBatchProcessor'
]