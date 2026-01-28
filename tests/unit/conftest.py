# tests/unit/conftest.py
"""Fixtures for unit tests - no database required."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


# ============================================================
# Sample Data Fixtures - ChatGPT Format
# ============================================================

@pytest.fixture
def chatgpt_simple_conversation() -> dict:
    """Simple linear ChatGPT conversation (no branches)."""
    root_id = str(uuid.uuid4())
    msg1_id = str(uuid.uuid4())
    msg2_id = str(uuid.uuid4())
    msg3_id = str(uuid.uuid4())
    msg4_id = str(uuid.uuid4())
    
    return {
        "conversation_id": "conv-simple-001",
        "title": "Simple Test Conversation",
        "create_time": 1700000000.0,
        "update_time": 1700001000.0,
        "mapping": {
            root_id: {
                "id": root_id,
                "parent": None,
                "children": [msg1_id],
                "message": None
            },
            msg1_id: {
                "id": msg1_id,
                "parent": root_id,
                "children": [msg2_id],
                "message": {
                    "id": msg1_id,
                    "author": {"role": "user"},
                    "create_time": 1700000100.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Hello, how are you?"]
                    }
                }
            },
            msg2_id: {
                "id": msg2_id,
                "parent": msg1_id,
                "children": [msg3_id],
                "message": {
                    "id": msg2_id,
                    "author": {"role": "assistant"},
                    "create_time": 1700000200.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["I'm doing well, thank you!"]
                    }
                }
            },
            msg3_id: {
                "id": msg3_id,
                "parent": msg2_id,
                "children": [msg4_id],
                "message": {
                    "id": msg3_id,
                    "author": {"role": "user"},
                    "create_time": 1700000300.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Explain Python decorators."]
                    }
                }
            },
            msg4_id: {
                "id": msg4_id,
                "parent": msg3_id,
                "children": [],
                "message": {
                    "id": msg4_id,
                    "author": {"role": "assistant"},
                    "create_time": 1700000400.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Python decorators are functions that modify other functions.\n\n```python\ndef decorator(func):\n    pass\n```"]
                    }
                }
            }
        }
    }


@pytest.fixture
def claude_simple_conversation() -> dict:
    """Simple Claude conversation."""
    return {
        "uuid": "claude-conv-001",
        "name": "Claude Test Conversation",
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "chat_messages": [
            {
                "uuid": "claude-msg-001",
                "sender": "human",
                "created_at": "2024-01-15T10:00:00Z",
                "content": [
                    {"type": "text", "text": "Hello Claude!"}
                ]
            },
            {
                "uuid": "claude-msg-002",
                "sender": "assistant",
                "created_at": "2024-01-15T10:01:00Z",
                "content": [
                    {"type": "text", "text": "Hello! How can I help you today?"}
                ]
            },
        ]
    }


# ============================================================
# Mock Session Fixture
# ============================================================

@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session for unit tests."""
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.query.return_value.count.return_value = 0
    return session
