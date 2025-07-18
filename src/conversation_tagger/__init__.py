# conversation_tagger/__init__.py
"""
Minimal conversation tagging system with exchange-based analysis.
"""

from .core.tag import Tag
from .core.tagger import ConversationTagger
from .factory import create_default_tagger
from .core.conversation import Conversation
from .core.exchange import Exchange
from .core.message import Message
from .core.exchange_parser import ExchangeParser, ExchangeParserOAI, ExchangeParserClaude
from .core.exchange_tagger import ExchangeTagger
from .core.detection import EXCHANGE_RULES, CONVERSATION_RULES
from .core.generate import generate_notes   

__all__ = ['Tag', 'ConversationTagger', 'create_default_tagger', 'Conversation', 'Exchange', 'Message', 'ExchangeParser', 'ExchangeParserOAI', 'ExchangeParserClaude', 'ExchangeTagger', 'EXCHANGE_RULES', 'CONVERSATION_RULES' ]