# tests/integration/conftest.py
"""Pytest configuration for integration tests - CORRECTED FIXTURES."""

import os
from typing import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def get_test_db_url() -> str:
    """Get test database URL from environment."""
    url = os.getenv('TEST_DATABASE_URL', 'postgresql://localhost:5432/llm_archive_test')
    return url


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """Create database engine for tests."""
    url = get_test_db_url()
    engine = create_engine(url, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def setup_schemas(db_engine):
    """Initialize schemas once per test session."""
    from pathlib import Path
    
    # Find schema directory relative to this file
    tests_dir = Path(__file__).parent.parent
    project_dir = tests_dir.parent
    schema_dir = project_dir / "schema"
    
    with db_engine.connect() as conn:
        # Drop and recreate schemas
        conn.execute(text("DROP SCHEMA IF EXISTS derived CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS raw CASCADE"))
        conn.commit()
        
        # Execute schema files in order
        for sql_file in sorted(schema_dir.glob("*.sql")):
            print(f"Executing {sql_file.name}")
            sql = sql_file.read_text()
            
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception as e:
                if "already exists" in str(e).lower():
                    conn.rollback()
                    print(f"Note: {sql_file.name} - {e}")
                else:
                    print(f"ERROR in {sql_file.name}: {e}")
                    conn.rollback()
                    raise
    
    yield
    
    # Cleanup
    with db_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS derived CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS raw CASCADE"))
        conn.commit()


@pytest.fixture
def db_session(db_engine, setup_schemas) -> Generator[Session, None, None]:
    """Create a database session with transaction rollback."""
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionFactory = sessionmaker(bind=connection)
    session = SessionFactory()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def clean_db_session(db_session) -> Session:
    """Alias for db_session."""
    return db_session


# ============================================================
# ChatGPT Test Fixtures
# ============================================================

@pytest.fixture
def chatgpt_simple_conversation() -> dict:
    """Simple linear ChatGPT conversation."""
    return {
        "conversation_id": "conv-simple-001",
        "title": "Simple Test Conversation",
        "create_time": 1700000000.0,
        "update_time": 1700001000.0,
        "mapping": {
            "root": {
                "id": "root",
                "parent": None,
                "children": ["node-1"],
                "message": None,
            },
            "node-1": {
                "id": "node-1",
                "parent": "root",
                "children": ["node-2"],
                "message": {
                    "id": "msg-1",
                    "author": {"role": "user"},
                    "create_time": 1700000100.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Hello, how are you?"]
                    }
                }
            },
            "node-2": {
                "id": "node-2",
                "parent": "node-1",
                "children": ["node-3"],
                "message": {
                    "id": "msg-2",
                    "author": {"role": "assistant"},
                    "create_time": 1700000200.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["I'm doing well, thank you!"]
                    }
                }
            },
            "node-3": {
                "id": "node-3",
                "parent": "node-2",
                "children": ["node-4"],
                "message": {
                    "id": "msg-3",
                    "author": {"role": "user"},
                    "create_time": 1700000300.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["What's the weather like?"]
                    }
                }
            },
            "node-4": {
                "id": "node-4",
                "parent": "node-3",
                "children": [],
                "message": {
                    "id": "msg-4",
                    "author": {"role": "assistant"},
                    "create_time": 1700000400.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["It's sunny and warm today."]
                    }
                }
            }
        }
    }


@pytest.fixture
def chatgpt_branched_conversation() -> dict:
    """ChatGPT conversation: 1 user message with 2 assistant responses that each have continuation messages."""
    return {
        "conversation_id": "conv-branched-001",
        "title": "Branched Test Conversation",
        "create_time": 1700000000.0,
        "update_time": 1700002000.0,
        "mapping": {
            "root": {
                "id": "root",
                "parent": None,
                "children": ["user1"],
                "message": None,
            },
            # THE ONLY USER MESSAGE - has 2 assistant children (regenerations)
            "user1": {
                "id": "user1",
                "parent": "root",
                "children": ["asst1a", "asst1b"],  # BRANCH POINT
                "message": {
                    "id": "msg-user1",
                    "author": {"role": "user"},
                    "create_time": 1700000100.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Tell me a story"]
                    }
                }
            },
            # First branch
            "asst1a": {
                "id": "asst1a",
                "parent": "user1",
                "children": ["asst2a"],
                "message": {
                    "id": "msg-asst1a",
                    "author": {"role": "assistant"},
                    "create_time": 1700000200.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Once upon a time..."]
                    }
                }
            },
            "asst2a": {
                "id": "asst2a",
                "parent": "asst1a",
                "children": [],
                "message": {
                    "id": "msg-asst2a",
                    "author": {"role": "assistant"},
                    "create_time": 1700000300.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["There was a brave knight..."]
                    }
                }
            },
            # Second branch  
            "asst1b": {
                "id": "asst1b",
                "parent": "user1",
                "children": ["asst2b"],
                "message": {
                    "id": "msg-asst1b",
                    "author": {"role": "assistant"},
                    "create_time": 1700000250.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["In a galaxy far away..."]
                    }
                }
            },
            "asst2b": {
                "id": "asst2b",
                "parent": "asst1b",
                "children": [],
                "message": {
                    "id": "msg-asst2b",
                    "author": {"role": "assistant"},
                    "create_time": 1700000350.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["A spaceship landed..."]
                    }
                }
            }
        }
    }


@pytest.fixture
def chatgpt_conversation_with_code() -> dict:
    """ChatGPT conversation with code content - uses nested parts structure."""
    return {
        "conversation_id": "conv-code-001",
        "title": "Code Example",
        "create_time": 1700000000.0,
        "update_time": 1700001000.0,
        "mapping": {
            "root": {
                "id": "root",
                "parent": None,
                "children": ["node-1"],
                "message": None,
            },
            "node-1": {
                "id": "node-1",
                "parent": "root",
                "children": ["node-2"],
                "message": {
                    "id": "msg-1",
                    "author": {"role": "user"},
                    "create_time": 1700000100.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Write a Python function to calculate fibonacci numbers"]
                    }
                }
            },
            "node-2": {
                "id": "node-2",
                "parent": "node-1",
                "children": [],
                "message": {
                    "id": "msg-2",
                    "author": {"role": "assistant"},
                    "create_time": 1700000200.0,
                    "content": {
                        "content_type": "text",
                        "parts": [
                            "Here's a Python function:",
                            {
                                "content_type": "code",
                                "language": "python",
                                "text": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
                            },
                            "This is a recursive implementation."
                        ]
                    }
                }
            }
        }
    }


@pytest.fixture
def chatgpt_conversation_with_image() -> dict:
    """ChatGPT conversation with image content - uses nested parts structure."""
    return {
        "conversation_id": "conv-image-001",
        "title": "Image Example",
        "create_time": 1700000000.0,
        "update_time": 1700001000.0,
        "mapping": {
            "root": {
                "id": "root",
                "parent": None,
                "children": ["node-1"],
                "message": None,
            },
            "node-1": {
                "id": "node-1",
                "parent": "root",
                "children": ["node-2"],
                "message": {
                    "id": "msg-1",
                    "author": {"role": "user"},
                    "create_time": 1700000100.0,
                    "content": {
                        "content_type": "multimodal_text",
                        "parts": [
                            "What's in this image?",
                            {
                                "content_type": "image/png",
                                "asset_pointer": "file-service://dalle-gen-abc123"
                            }
                        ]
                    }
                }
            },
            "node-2": {
                "id": "node-2",
                "parent": "node-1",
                "children": [],
                "message": {
                    "id": "msg-2",
                    "author": {"role": "assistant"},
                    "create_time": 1700000200.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["This image shows a cat."]
                    }
                }
            }
        }
    }


@pytest.fixture
def chatgpt_conversations(
    chatgpt_simple_conversation,
    chatgpt_branched_conversation,
) -> list[dict]:
    """List of ChatGPT test conversations."""
    third_conversation = {
        "conversation_id": "conv-third-001",
        "title": "Third Conversation",
        "create_time": 1700003000.0,
        "update_time": 1700003000.0,
        "mapping": {
            "root": {
                "id": "root",
                "parent": None,
                "children": ["node-1"],
                "message": None,
            },
            "node-1": {
                "id": "node-1",
                "parent": "root",
                "children": [],
                "message": {
                    "id": "msg-third-1",
                    "author": {"role": "user"},
                    "create_time": 1700003100.0,
                    "content": {
                        "content_type": "text",
                        "parts": ["Hello"]
                    }
                }
            }
        }
    }
    return [
        chatgpt_simple_conversation,
        chatgpt_branched_conversation,
        third_conversation,
    ]


# ============================================================
# Claude Test Fixtures
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
                    {"type": "text", "text": "Hello Claude"}
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
                "created_at": "2024-01-15T10:05:00Z",
                "content": [
                    {"type": "text", "text": "What's 5 + 3?"}
                ]
            },
            {
                "uuid": "claude-msg-004",
                "sender": "assistant",
                "created_at": "2024-01-15T10:06:00Z",
                "content": [
                    {"type": "text", "text": "5 + 3 = 8"}
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
        "updated_at": "2024-01-15T11:05:00Z",
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
                    {"type": "thinking", "thinking": "Let me calculate: 15 * 23 = 345"},
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


@pytest.fixture
def claude_conversations(
    claude_simple_conversation,
    claude_conversation_with_thinking,
    claude_conversation_with_tool_use,
) -> list[dict]:
    """List of Claude test conversations."""
    return [
        claude_simple_conversation,
        claude_conversation_with_thinking,
        claude_conversation_with_tool_use,
    ]


# ============================================================
# Populated Database Fixtures
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
    from llm_archive.builders.prompt_response import PromptResponseBuilder
    
    chatgpt_extractor = ChatGPTExtractor(clean_db_session)
    chatgpt_extractor.extract_dialogue(chatgpt_simple_conversation)
    chatgpt_extractor.extract_dialogue(chatgpt_branched_conversation)
    
    claude_extractor = ClaudeExtractor(clean_db_session)
    claude_extractor.extract_dialogue(claude_simple_conversation)
    
    clean_db_session.commit()
    
    pr_builder = PromptResponseBuilder(clean_db_session)
    pr_builder.build_all()
    
    clean_db_session.commit()
    
    return clean_db_session
