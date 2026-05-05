# conversation_tagger/core/__init__.py
"""Core classes for conversation tagging."""

from .tag import Tag
from .tagger import ConversationTagger
from .exchange import Exchange
from .exchange_parser import ExchangeParser
from .exchange_tagger import ExchangeTagger
from .conversation_aggregator import ConversationAggregator

__all__ = [
    'Tag', 'ConversationTagger', 'Exchange', 'ExchangeParser', 
    'ExchangeTagger', 'ConversationAggregator'
]