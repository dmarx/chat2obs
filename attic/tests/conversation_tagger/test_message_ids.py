# tests/conversation_tagger/test_message_ids.py
"""
Tests for message ID functionality.
"""

import pytest
from conversation_tagger.core.message import MessageOpenAI, MessageClaude
from conversation_tagger.core.exchange import Exchange


def test_message_openai_id():
    """Test that OpenAI messages extract IDs correctly."""
    msg_data = {
        'id': 'msg-12345',
        'author': {'role': 'user'},
        'create_time': 1700000000.0,
        'content': {'text': 'Hello world'},
        'metadata': {}
    }
    
    message = MessageOpenAI(data=msg_data)
    assert message.id == 'msg-12345'
    
    # Test missing ID
    msg_data_no_id = {
        'author': {'role': 'user'},
        'create_time': 1700000000.0,
        'content': {'text': 'Hello world'},
        'metadata': {}
    }
    
    message_no_id = MessageOpenAI(data=msg_data_no_id)
    assert message_no_id.id is None


def test_message_claude_id():
    """Test that Claude messages extract IDs correctly."""
    msg_data = {
        'uuid': 'claude-msg-67890',
        'text': 'Hello world',
        'sender': 'user',
        'created_at': '2024-01-01T12:00:00Z',
        'updated_at': '2024-01-01T12:00:00Z',
        'content': [{'type': 'text', 'text': 'Hello world'}],
        'attachments': [],
        'files': []
    }
    
    message = MessageClaude(data=msg_data)
    assert message.id == 'claude-msg-67890'
    
    # Test missing UUID
    msg_data_no_uuid = {
        'text': 'Hello world',
        'sender': 'user',
        'created_at': '2024-01-01T12:00:00Z',
        'updated_at': '2024-01-01T12:00:00Z',
        'content': [{'type': 'text', 'text': 'Hello world'}],
        'attachments': [],
        'files': []
    }
    
    message_no_uuid = MessageClaude(data=msg_data_no_uuid)
    assert message_no_uuid.id is None


def test_exchange_get_message_ids():
    """Test that exchanges can return all message IDs."""
    # Create messages with IDs
    msg1_data = {
        'id': 'user-msg-1',
        'author': {'role': 'user'},
        'create_time': 1700000000.0,
        'content': {'text': 'Question'},
        'metadata': {}
    }
    
    msg2_data = {
        'id': 'assistant-msg-1',
        'author': {'role': 'assistant'},
        'create_time': 1700000001.0,
        'content': {'text': 'Answer'},
        'metadata': {}
    }
    
    msg3_data = {
        'id': 'user-msg-2',
        'author': {'role': 'user'},
        'create_time': 1700000002.0,
        'content': {'text': 'Follow up'},
        'metadata': {}
    }
    
    messages = [
        MessageOpenAI(data=msg1_data),
        MessageOpenAI(data=msg2_data),
        MessageOpenAI(data=msg3_data)
    ]
    
    exchange = Exchange.create('test_conv', messages)
    message_ids = exchange.get_message_ids()
    
    assert len(message_ids) == 3
    assert 'user-msg-1' in message_ids
    assert 'assistant-msg-1' in message_ids
    assert 'user-msg-2' in message_ids
    assert message_ids == ['user-msg-1', 'assistant-msg-1', 'user-msg-2']


def test_exchange_get_message_ids_with_missing_ids():
    """Test exchange message ID extraction with some missing IDs."""
    # Mix of messages with and without IDs
    msg1_data = {
        'id': 'msg-with-id',
        'author': {'role': 'user'},
        'create_time': 1700000000.0,
        'content': {'text': 'Question'},
        'metadata': {}
    }
    
    msg2_data = {
        # No ID field
        'author': {'role': 'assistant'},
        'create_time': 1700000001.0,
        'content': {'text': 'Answer'},
        'metadata': {}
    }
    
    messages = [
        MessageOpenAI(data=msg1_data),
        MessageOpenAI(data=msg2_data)
    ]
    
    exchange = Exchange.create('test_conv', messages)
    message_ids = exchange.get_message_ids()
    
    # Should only include messages with non-empty IDs
    assert len(message_ids) == 1
    assert 'msg-with-id' in message_ids


def test_exchange_get_message_ids_empty_exchange():
    """Test get_message_ids with empty exchange."""
    exchange = Exchange.create('test_conv', [])
    message_ids = exchange.get_message_ids()
    
    assert message_ids == []


def test_exchange_merging_preserves_message_ids():
    """Test that merging exchanges preserves all message IDs."""
    # First exchange
    msg1_data = {
        'id': 'msg-1',
        'author': {'role': 'user'},
        'create_time': 1700000000.0,
        'content': {'text': 'First question'},
        'metadata': {}
    }
    
    msg2_data = {
        'id': 'msg-2',
        'author': {'role': 'assistant'},
        'create_time': 1700000001.0,
        'content': {'text': 'First answer'},
        'metadata': {}
    }
    
    exchange1 = Exchange.create('test_conv', [
        MessageOpenAI(data=msg1_data),
        MessageOpenAI(data=msg2_data)
    ])
    
    # Second exchange
    msg3_data = {
        'id': 'msg-3',
        'author': {'role': 'user'},
        'create_time': 1700000002.0,
        'content': {'text': 'Continue'},
        'metadata': {}
    }
    
    msg4_data = {
        'id': 'msg-4',
        'author': {'role': 'assistant'},
        'create_time': 1700000003.0,
        'content': {'text': 'Continued answer'},
        'metadata': {}
    }
    
    exchange2 = Exchange.create('test_conv', [
        MessageOpenAI(data=msg3_data),
        MessageOpenAI(data=msg4_data)
    ])
    
    # Merge exchanges
    merged = exchange1 + exchange2
    message_ids = merged.get_message_ids()
    
    assert len(message_ids) == 4
    assert 'msg-1' in message_ids
    assert 'msg-2' in message_ids
    assert 'msg-3' in message_ids
    assert 'msg-4' in message_ids
    
    # Should be in chronological order
    assert message_ids == ['msg-1', 'msg-2', 'msg-3', 'msg-4']


def test_mixed_message_types_with_ids():
    """Test exchange with mixed OpenAI and Claude messages (hypothetical scenario)."""
    # This tests the interface consistency between message types
    oai_msg_data = {
        'id': 'oai-msg-1',
        'author': {'role': 'user'},
        'create_time': 1700000000.0,
        'content': {'text': 'OpenAI question'},
        'metadata': {}
    }
    
    claude_msg_data = {
        'uuid': 'claude-msg-1',
        'text': 'Claude response',
        'sender': 'assistant',
        'created_at': '2024-01-01T12:00:01Z',
        'updated_at': '2024-01-01T12:00:01Z',
        'content': [{'type': 'text', 'text': 'Claude response'}],
        'attachments': [],
        'files': []
    }
    
    # In practice, exchanges would typically have one message type,
    # but this tests interface consistency
    oai_message = MessageOpenAI(data=oai_msg_data)
    claude_message = MessageClaude(data=claude_msg_data)
    
    assert oai_message.id == 'oai-msg-1'
    assert claude_message.id == 'claude-msg-1'
    
    # Both implement the same id interface
    assert hasattr(oai_message, 'id')
    assert hasattr(claude_message, 'id')


# Add to existing test files as needed
def test_message_id_property_in_existing_tests():
    """Test that existing message objects now have id property."""
    # From existing test patterns
    simple_user_message = {
        'id': 'test-user-msg',
        'author': {'role': 'user'},
        'create_time': 1000,
        'content': {'text': 'Hello, how are you?'}
    }
    
    simple_assistant_message = {
        'id': 'test-assistant-msg', 
        'author': {'role': 'assistant'},
        'create_time': 2000,
        'content': {'text': 'I am doing well, thank you!'}
    }
    
    user_msg = MessageOpenAI(data=simple_user_message)
    assistant_msg = MessageOpenAI(data=simple_assistant_message)
    
    assert user_msg.id == 'test-user-msg'
    assert assistant_msg.id == 'test-assistant-msg'
    
    exchange = Exchange.create('test_conv', [user_msg, assistant_msg])
    message_ids = exchange.get_message_ids()
    
    assert message_ids == ['test-user-msg', 'test-assistant-msg']