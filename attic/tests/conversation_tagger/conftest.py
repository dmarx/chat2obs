# tests/conftest.py
"""
Shared test fixtures and configuration.
"""
from pathlib import Path
import sys
#PATH=str((Path().cwd().parent /'src').absolute())
PATH=str((Path().cwd() /'src').absolute())
print(PATH)
if PATH not in sys.path:
    sys.path.append(PATH)

import pytest
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.message import Message


@pytest.fixture
def simple_user_message():
    """A basic user message."""
    return Message(**{
        'author': {'role': 'user'},
        'create_time': 1000,
        'content': {'text': 'Hello, how are you?'}
    })


@pytest.fixture
def simple_assistant_message():
    """A basic assistant message."""
    return {
        'author': {'role': 'assistant'},
        'create_time': 2000,
        'content': {'text': 'I am doing well, thank you!'}
    }


@pytest.fixture
def basic_exchange(simple_user_message, simple_assistant_message):
    """A simple two-message exchange."""
    return Exchange.create('test_conv', [simple_user_message, simple_assistant_message])


@pytest.fixture
def minimal_conversation_data():
    """Minimal conversation data for parsing tests."""
    return {
        'conversation_id': 'test_conv',
        'title': 'Test Conversation',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1000,
                    'content': {'text': 'Test question'}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 2000,
                    'content': {'text': 'Test answer'}
                }
            }
        }
    }
