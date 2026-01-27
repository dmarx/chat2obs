# tests/conftest.py
"""Pytest fixtures for llm_archive tests."""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from llm_archive.models import Base


# ============================================================
# Database Fixtures
# ============================================================

def get_test_db_url() -> str:
    """Get test database URL from environment or use default."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/llm_archive_test"
    )


@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for test session."""
    url = get_test_db_url()
    engine = create_engine(url, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def setup_schemas(db_engine):
    """Initialize schemas once per test session."""
    from pathlib import Path
    
    schema_dir = Path(__file__).parent.parent / "schema"
    
    with db_engine.connect() as conn:
        # Drop and recreate schemas
        conn.execute(text("DROP SCHEMA IF EXISTS derived CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS raw CASCADE"))
        conn.commit()
        
        # Execute schema files in order
        for sql_file in sorted(schema_dir.glob("*.sql")):
            sql = sql_file.read_text()
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                except Exception:
                    pass  # Ignore errors (e.g., extension already exists)
            conn.commit()
    
    yield
    
    # Cleanup after all tests
    with db_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS derived CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS raw CASCADE"))
        conn.commit()


@pytest.fixture
def db_session(db_engine, setup_schemas) -> Generator[Session, None, None]:
    """Create a database session with transaction rollback."""
    connection = db_engine.connect()
    transaction = connection.begin()
    
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def clean_db_session(db_engine, setup_schemas) -> Generator[Session, None, None]:
    """
    Create a database session that commits changes.
    Use when you need data to persist across operations within the test.
    Cleans up data at the end.
    """
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    
    yield session
    
    # Cleanup: delete all data from tables
    session.execute(text("DELETE FROM derived.annotations"))
    session.execute(text("DELETE FROM derived.content_hashes"))
    session.execute(text("DELETE FROM derived.exchange_content"))
    session.execute(text("DELETE FROM derived.exchange_messages"))
    session.execute(text("DELETE FROM derived.sequence_exchanges"))
    session.execute(text("DELETE FROM derived.exchanges"))
    session.execute(text("DELETE FROM derived.sequence_messages"))
    session.execute(text("DELETE FROM derived.linear_sequences"))
    session.execute(text("DELETE FROM derived.message_paths"))
    session.execute(text("DELETE FROM derived.dialogue_trees"))
    session.execute(text("DELETE FROM raw.chatgpt_canvas_docs"))
    session.execute(text("DELETE FROM raw.chatgpt_dalle_generations"))
    session.execute(text("DELETE FROM raw.chatgpt_code_outputs"))
    session.execute(text("DELETE FROM raw.chatgpt_code_executions"))
    session.execute(text("DELETE FROM raw.chatgpt_search_entries"))
    session.execute(text("DELETE FROM raw.chatgpt_search_groups"))
    session.execute(text("DELETE FROM raw.chatgpt_message_meta"))
    session.execute(text("DELETE FROM raw.claude_message_meta"))
    session.execute(text("DELETE FROM raw.citations"))
    session.execute(text("DELETE FROM raw.attachments"))
    session.execute(text("DELETE FROM raw.content_parts"))
    session.execute(text("DELETE FROM raw.messages"))
    session.execute(text("DELETE FROM raw.dialogues"))
    session.commit()
    session.close()


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
                        "parts": ["I'm doing well, thank you! How can I help you today?"]
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
                        "parts": ["Can you explain Python decorators?"]
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
                        "parts": ["Python decorators are functions that modify other functions.\n\n```python\ndef my_decorator(func):\n    def wrapper():\n        print('Before')\n        func()\n        print('After')\n    return wrapper\n```"]
                    }
                }
            }
        }
    }


@pytest.fixture
def chatgpt_branched_conversation() -> dict:
    """ChatGPT conversation with branches (regeneration and edit)."""
    root_id = str(uuid.uuid4())
    msg1_id = str(uuid.uuid4())
    msg2a_id = str(uuid.uuid4())  # First assistant response
    msg2b_id = str(uuid.uuid4())  # Regenerated assistant response
    msg3_id = str(uuid.uuid4())
    msg4_id = str(uuid.uuid4())
    
    return {
        "conversation_id": "conv-branched-001",
        "title": "Branched Conversation",
        "create_time": 1700000000.0,
        "update_time": 1700002000.0,
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
                "children": [msg2a_id, msg2b_id],  # Two children = branch
                "message": {
                    "id": msg1_id,
                    "author": {"role": "user"},
                    "create_time": 1700000100.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["What is machine learning?"]
                    }
                }
            },
            msg2a_id: {
                "id": msg2a_id,
                "parent": msg1_id,
                "children": [],
                "message": {
                    "id": msg2a_id,
                    "author": {"role": "assistant"},
                    "create_time": 1700000200.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Machine learning is a subset of AI."]
                    }
                }
            },
            msg2b_id: {
                "id": msg2b_id,
                "parent": msg1_id,
                "children": [msg3_id],
                "message": {
                    "id": msg2b_id,
                    "author": {"role": "assistant"},
                    "create_time": 1700000250.0,  # Later = regeneration
                    "content": {
                        "content_type": "text",
                        "parts": ["Machine learning is a branch of artificial intelligence that enables computers to learn from data without explicit programming."]
                    }
                }
            },
            msg3_id: {
                "id": msg3_id,
                "parent": msg2b_id,
                "children": [msg4_id],
                "message": {
                    "id": msg3_id,
                    "author": {"role": "user"},
                    "create_time": 1700000300.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Give me an example."]
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
                        "parts": ["A common example is spam detection in email."]
                    }
                }
            }
        }
    }


@pytest.fixture
def chatgpt_conversation_with_code() -> dict:
    """ChatGPT conversation with code execution."""
    root_id = str(uuid.uuid4())
    msg1_id = str(uuid.uuid4())
    msg2_id = str(uuid.uuid4())
    
    return {
        "conversation_id": "conv-code-001",
        "title": "Code Execution Test",
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
                        "parts": ["Calculate 2+2"]
                    }
                }
            },
            msg2_id: {
                "id": msg2_id,
                "parent": msg1_id,
                "children": [],
                "message": {
                    "id": msg2_id,
                    "author": {"role": "assistant"},
                    "create_time": 1700000200.0,
                    "content": {
                        "content_type": "code",
                        "language": "python",
                        "text": "result = 2 + 2\nprint(result)"
                    },
                    "metadata": {
                        "aggregate_result": {
                            "code": "result = 2 + 2\nprint(result)",
                            "final_expression_output": "4",
                            "run_id": "run-123",
                            "status": "success"
                        }
                    }
                }
            }
        }
    }


# ============================================================
# Sample Data Fixtures - Claude Format
# ============================================================

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
            {
                "uuid": "claude-msg-003",
                "sender": "human",
                "created_at": "2024-01-15T10:02:00Z",
                "content": [
                    {"type": "text", "text": "Explain quantum computing."}
                ]
            },
            {
                "uuid": "claude-msg-004",
                "sender": "assistant",
                "created_at": "2024-01-15T10:03:00Z",
                "content": [
                    {"type": "text", "text": "Quantum computing uses quantum mechanics principles like superposition and entanglement to process information."}
                ]
            }
        ]
    }


@pytest.fixture
def claude_conversation_with_thinking() -> dict:
    """Claude conversation with thinking blocks."""
    return {
        "uuid": "claude-conv-002",
        "name": "Claude Thinking Test",
        "created_at": "2024-01-15T11:00:00Z",
        "updated_at": "2024-01-15T11:10:00Z",
        "chat_messages": [
            {
                "uuid": "claude-msg-005",
                "sender": "human",
                "created_at": "2024-01-15T11:00:00Z",
                "content": [
                    {"type": "text", "text": "What is 15 * 23?"}
                ]
            },
            {
                "uuid": "claude-msg-006",
                "sender": "assistant",
                "created_at": "2024-01-15T11:01:00Z",
                "content": [
                    {"type": "thinking", "thinking": "Let me calculate: 15 * 23 = 15 * 20 + 15 * 3 = 300 + 45 = 345"},
                    {"type": "text", "text": "15 multiplied by 23 equals 345."}
                ]
            }
        ]
    }


@pytest.fixture
def claude_conversation_with_tool_use() -> dict:
    """Claude conversation with tool use."""
    return {
        "uuid": "claude-conv-003",
        "name": "Claude Tool Use Test",
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2024-01-15T12:10:00Z",
        "chat_messages": [
            {
                "uuid": "claude-msg-007",
                "sender": "human",
                "created_at": "2024-01-15T12:00:00Z",
                "content": [
                    {"type": "text", "text": "Search for recent news about AI."}
                ]
            },
            {
                "uuid": "claude-msg-008",
                "sender": "assistant",
                "created_at": "2024-01-15T12:01:00Z",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool-001",
                        "name": "web_search",
                        "input": {"query": "recent AI news 2024"}
                    }
                ]
            },
            {
                "uuid": "claude-msg-009",
                "sender": "human",
                "created_at": "2024-01-15T12:02:00Z",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool-001",
                        "content": "AI advances in 2024 include..."
                    }
                ]
            },
            {
                "uuid": "claude-msg-010",
                "sender": "assistant",
                "created_at": "2024-01-15T12:03:00Z",
                "content": [
                    {"type": "text", "text": "Based on my search, here are the recent developments in AI..."}
                ]
            }
        ]
    }


# ============================================================
# Continuation Pattern Fixtures
# ============================================================

@pytest.fixture
def conversation_with_continuation() -> dict:
    """ChatGPT conversation with continuation prompts."""
    root_id = str(uuid.uuid4())
    msg1_id = str(uuid.uuid4())
    msg2_id = str(uuid.uuid4())
    msg3_id = str(uuid.uuid4())
    msg4_id = str(uuid.uuid4())
    msg5_id = str(uuid.uuid4())
    msg6_id = str(uuid.uuid4())
    
    return {
        "conversation_id": "conv-continuation-001",
        "title": "Continuation Test",
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
                        "parts": ["Write a story about a robot."]
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
                        "parts": ["Once upon a time, there was a robot named Alex..."]
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
                        "parts": ["continue"]  # Continuation signal
                    }
                }
            },
            msg4_id: {
                "id": msg4_id,
                "parent": msg3_id,
                "children": [msg5_id],
                "message": {
                    "id": msg4_id,
                    "author": {"role": "assistant"},
                    "create_time": 1700000400.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Alex wandered through the abandoned factory..."]
                    }
                }
            },
            msg5_id: {
                "id": msg5_id,
                "parent": msg4_id,
                "children": [msg6_id],
                "message": {
                    "id": msg5_id,
                    "author": {"role": "user"},
                    "create_time": 1700000500.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["What happened next?"]  # New topic
                    }
                }
            },
            msg6_id: {
                "id": msg6_id,
                "parent": msg5_id,
                "children": [],
                "message": {
                    "id": msg6_id,
                    "author": {"role": "assistant"},
                    "create_time": 1700000600.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Alex found a mysterious door..."]
                    }
                }
            }
        }
    }


# ============================================================
# Multi-conversation Fixtures
# ============================================================

@pytest.fixture
def chatgpt_conversations(
    chatgpt_simple_conversation,
    chatgpt_branched_conversation,
    chatgpt_conversation_with_code,
) -> list[dict]:
    """List of all ChatGPT test conversations."""
    return [
        chatgpt_simple_conversation,
        chatgpt_branched_conversation,
        chatgpt_conversation_with_code,
    ]


@pytest.fixture
def claude_conversations(
    claude_simple_conversation,
    claude_conversation_with_thinking,
    claude_conversation_with_tool_use,
) -> list[dict]:
    """List of all Claude test conversations."""
    return [
        claude_simple_conversation,
        claude_conversation_with_thinking,
        claude_conversation_with_tool_use,
    ]


# ============================================================
# Pre-populated Database Fixtures
# ============================================================

@pytest.fixture
def populated_chatgpt_db(clean_db_session, chatgpt_simple_conversation):
    """Database with a single ChatGPT conversation imported."""
    from llm_archive.extractors import ChatGPTExtractor
    
    extractor = ChatGPTExtractor(clean_db_session)
    extractor.extract_dialogue(chatgpt_simple_conversation)
    clean_db_session.commit()
    
    return clean_db_session


@pytest.fixture
def populated_claude_db(clean_db_session, claude_simple_conversation):
    """Database with a single Claude conversation imported."""
    from llm_archive.extractors import ClaudeExtractor
    
    extractor = ClaudeExtractor(clean_db_session)
    extractor.extract_dialogue(claude_simple_conversation)
    clean_db_session.commit()
    
    return clean_db_session


@pytest.fixture
def fully_populated_db(
    clean_db_session,
    chatgpt_simple_conversation,
    chatgpt_branched_conversation,
    claude_simple_conversation,
):
    """Database with multiple conversations and derived data."""
    from llm_archive.extractors import ChatGPTExtractor, ClaudeExtractor
    from llm_archive.builders import TreeBuilder, ExchangeBuilder
    
    # Import conversations
    chatgpt_extractor = ChatGPTExtractor(clean_db_session)
    chatgpt_extractor.extract_dialogue(chatgpt_simple_conversation)
    chatgpt_extractor.extract_dialogue(chatgpt_branched_conversation)
    
    claude_extractor = ClaudeExtractor(clean_db_session)
    claude_extractor.extract_dialogue(claude_simple_conversation)
    
    clean_db_session.commit()
    
    # Build derived data
    tree_builder = TreeBuilder(clean_db_session)
    tree_builder.build_all()
    
    exchange_builder = ExchangeBuilder(clean_db_session)
    exchange_builder.build_all()
    
    clean_db_session.commit()
    
    return clean_db_session
