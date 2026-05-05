# tests/test_exchange_minimal.py
"""
Minimal tests for exchange-based functionality.
"""

import pytest
from conversation_tagger__complimacated.core.exchange import Exchange
from conversation_tagger__complimacated.core.exchange_parser import ExchangeParser
from conversation_tagger__complimacated.factory.exchange_factory import create_default_exchange_tagger
from conversation_tagger__complimacated.core.conversation_aggregator import ConversationAggregator


def create_test_message(role: str, text: str, create_time: int = 1000):
    """Helper to create test messages."""
    return {
        'id': f'msg_{role}_{create_time}',
        'author': {'role': role},
        'create_time': create_time,
        'content': {
            'content_type': 'text',
            'text': text,
            'parts': []
        },
        'metadata': {}
    }


def create_test_conversation(messages: list, conversation_id: str = 'test_conv'):
    """Helper to create test conversations from message list."""
    mapping = {}
    for i, (role, text, time) in enumerate(messages):
        mapping[f'node_{i}'] = {
            'message': create_test_message(role, text, time)
        }
    
    return {
        'conversation_id': conversation_id,
        'title': 'Test Conversation',
        'mapping': mapping
    }


class TestExchange:
    
    def test_exchange_creation(self):
        user_msg = create_test_message('user', 'Hello')
        assistant_msg = create_test_message('assistant', 'Hi there')
        
        exchange = Exchange(
            exchange_id='test_1',
            conversation_id='test_conv',
            user_messages=[user_msg],
            assistant_messages=[assistant_msg]
        )
        
        assert exchange.get_user_text() == 'Hello'
        assert exchange.get_assistant_text() == 'Hi there'
        assert not exchange.has_continuations()
    
    def test_exchange_with_continuations(self):
        user_msg1 = create_test_message('user', 'Write code')
        user_msg2 = create_test_message('user', 'continue', 2000)
        assistant_msg = create_test_message('assistant', 'Here is more code')
        
        exchange = Exchange(
            exchange_id='test_1',
            conversation_id='test_conv',
            user_messages=[user_msg1, user_msg2],
            assistant_messages=[assistant_msg]
        )
        
        assert 'Write code continue' in exchange.get_user_text()
        assert exchange.has_continuations()


class TestExchangeParser:
    
    def test_simple_exchange_parsing(self):
        conv = create_test_conversation([
            ('user', 'Hello', 1000),
            ('assistant', 'Hi there', 2000),
            ('user', 'How are you?', 3000),
            ('assistant', 'I am fine', 4000)
        ])
        
        parser = ExchangeParser()
        exchanges = parser.parse_conversation(conv)
        
        assert len(exchanges) == 2
        assert exchanges[0].get_user_text() == 'Hello'
        assert exchanges[1].get_user_text() == 'How are you?'
    
    def test_continuation_parsing(self):
        conv = create_test_conversation([
            ('user', 'Write a story', 1000),
            ('assistant', 'Once upon a time...', 2000),
            ('user', 'continue', 3000),
            ('assistant', 'The story continued...', 4000)
        ])
        
        parser = ExchangeParser()
        exchanges = parser.parse_conversation(conv)
        
        assert len(exchanges) == 1  # Should be grouped as one exchange
        assert len(exchanges[0].user_messages) == 2
        assert exchanges[0].has_continuations()
    
    def test_quote_elaborate_pattern(self):
        conv = create_test_conversation([
            ('user', 'Explain AI', 1000),
            ('assistant', 'AI is artificial intelligence', 2000),
            ('user', '> AI is artificial intelligence\n\nelaborate', 3000),
            ('assistant', 'AI involves machine learning...', 4000)
        ])
        
        parser = ExchangeParser()
        exchanges = parser.parse_conversation(conv)
        
        assert len(exchanges) == 1  # Should be grouped as one exchange
        assert exchanges[0].has_continuations()
        
        # Test the detection function directly
        assert parser._is_quote_elaborate_pattern('> AI is artificial intelligence\n\nelaborate')
        assert not parser._is_quote_elaborate_pattern('> AI is artificial intelligence\n\ncontinue')
        assert not parser._is_quote_elaborate_pattern('AI is artificial intelligence\n\nelaborate')


class TestExchangeTagging:
    
    def test_basic_exchange_tagging(self):
        user_msg = create_test_message('user', 'Fix this code:\n```python\nprint("hello")\n```')
        assistant_msg = create_test_message('assistant', 'Here is the fix:\n```python\nprint("Hello, World!")\n```')
        
        exchange = Exchange(
            exchange_id='test_1',
            conversation_id='test_conv',
            user_messages=[user_msg],
            assistant_messages=[assistant_msg]
        )
        
        tagger = create_default_exchange_tagger()
        result = tagger.tag_exchange(exchange)
        
        tag_names = [tag.name for tag in result['tags']]
        assert 'user_has_code_blocks' in tag_names
        assert 'assistant_has_code_blocks' in tag_names
        assert 'coding_exchange' in tag_names
    
    def test_quote_elaborate_tagging(self):
        user_msg1 = create_test_message('user', 'Explain machine learning')
        user_msg2 = create_test_message('user', '> Machine learning is...\n\nelaborate', 2000)
        assistant_msg = create_test_message('assistant', 'Machine learning is a subset of AI...')
        
        exchange = Exchange(
            exchange_id='test_1',
            conversation_id='test_conv',
            user_messages=[user_msg1, user_msg2],
            assistant_messages=[assistant_msg]
        )
        
        tagger = create_default_exchange_tagger()
        result = tagger.tag_exchange(exchange)
        
        tag_names = [tag.name for tag in result['tags']]
        assert 'user_has_quote_elaborate' in tag_names
        assert 'elaboration_exchange' in tag_names
    
    def test_wiki_exchange_tagging(self):
        user_msg = create_test_message('user', 'Write about [[Python Programming]]')
        assistant_msg = create_test_message('assistant', '# Python Programming\n\n[[Python]] is a language...')
        
        exchange = Exchange(
            exchange_id='test_1',
            conversation_id='test_conv',
            user_messages=[user_msg],
            assistant_messages=[assistant_msg]
        )
        
        tagger = create_default_exchange_tagger()
        result = tagger.tag_exchange(exchange)
        
        tag_names = [tag.name for tag in result['tags']]
        assert 'assistant_has_wiki_links' in tag_names
        assert 'wiki_exchange' in tag_names


class TestConversationAggregation:
    
    def test_basic_aggregation(self):
        # Create test exchanges
        exchanges = [
            Exchange('ex1', 'conv1', 
                    [create_test_message('user', 'Hello')],
                    [create_test_message('assistant', 'Hi')]),
            Exchange('ex2', 'conv1',
                    [create_test_message('user', 'Fix this code:\n```python\nprint()\n```')],
                    [create_test_message('assistant', 'Here is the fix:\n```python\nprint("hello")\n```')])
        ]
        
        tagger = create_default_exchange_tagger()
        tagged_exchanges = tagger.tag_exchanges(exchanges)
        
        aggregator = ConversationAggregator()
        conversation = {'conversation_id': 'conv1', 'title': 'Test'}
        result = aggregator.aggregate_to_conversation(tagged_exchanges, conversation)
        
        assert result['exchange_count'] == 2
        assert len(result['tags']) > 0
        
        # Should have aggregated coding activity
        tag_names = [tag.name for tag in result['tags']]
        assert 'has_user_has_code_blocks' in tag_names or 'has_assistant_has_code_blocks' in tag_names


class TestIntegration:
    
    def test_full_pipeline(self):
        """Test the complete exchange analysis pipeline."""
        conv = create_test_conversation([
            ('user', 'Write about [[Python]]', 1000),
            ('assistant', '# Python\n\n[[Python]] is a programming language with $O(n)$ complexity...', 2000),
            ('user', '> Python is a programming language\n\nelaborate', 3000),
            ('assistant', 'Python supports multiple paradigms and has extensive libraries...', 4000),
            ('user', 'Fix this bug:\n```python\nprint("error"\n```', 5000),
            ('assistant', 'Here is the fix:\n```python\nprint("error")\n```', 6000)
        ])
        
        # Parse into exchanges
        parser = ExchangeParser()
        exchanges = parser.parse_conversation(conv)
        
        # Should have 2 exchanges (wiki discussion + code fix)
        assert len(exchanges) == 2
        assert exchanges[0].has_continuations()  # First exchange has quote+elaborate
        
        # Tag exchanges
        tagger = create_default_exchange_tagger()
        tagged_exchanges = tagger.tag_exchanges(exchanges)
        
        # First exchange should be wiki-focused with elaboration
        ex1_tags = [tag.name for tag in tagged_exchanges[0]['tags']]
        assert 'assistant_has_wiki_links' in ex1_tags
        assert 'user_has_quote_elaborate' in ex1_tags
        assert 'elaboration_exchange' in ex1_tags
        
        # Second exchange should be coding-focused
        ex2_tags = [tag.name for tag in tagged_exchanges[1]['tags']]
        assert 'user_has_code_blocks' in ex2_tags
        assert 'assistant_has_code_blocks' in ex2_tags
        assert 'coding_exchange' in ex2_tags
        
        # Aggregate to conversation level
        aggregator = ConversationAggregator()
        result = aggregator.aggregate_to_conversation(tagged_exchanges, conv)
        
        assert result['exchange_count'] == 2
        conversation_tags = [tag.name for tag in result['tags']]
        
        # Should have both wiki and coding activity detected
        assert any('wiki' in tag for tag in conversation_tags)
        assert any('code' in tag for tag in conversation_tags)