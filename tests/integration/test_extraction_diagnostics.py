# tests/integration/test_extraction_diagnostics.py
"""Diagnostic tests to understand what's happening during extraction."""

import pytest
from llm_archive.extractors import ChatGPTExtractor
from llm_archive.models import Message


def test_branched_conversation_diagnostic(db_session, chatgpt_branched_conversation):
    """Diagnostic test to see what's actually extracted."""
    extractor = ChatGPTExtractor(db_session)
    result = extractor.extract_dialogue(chatgpt_branched_conversation)
    
    print(f"\n=== EXTRACTION RESULT: {result} ===")
    
    # Get all messages
    messages = db_session.query(Message).order_by(Message.created_at).all()
    
    print(f"\n=== TOTAL MESSAGES: {len(messages)} ===")
    for i, msg in enumerate(messages):
        print(f"{i+1}. source_id={msg.source_id}, role={msg.role}, parent_id={msg.parent_id}")
    
    # Check the mapping structure
    mapping = chatgpt_branched_conversation['mapping']
    print(f"\n=== MAPPING STRUCTURE ===")
    for node_id, node in mapping.items():
        msg_data = node.get('message')
        if msg_data:
            msg_id = msg_data.get('id')
            role = msg_data.get('author', {}).get('role')
            parent_node = node.get('parent')
            children = node.get('children', [])
            print(f"Node: {node_id}, msg_id: {msg_id}, role: {role}, parent: {parent_node}, children: {children}")
    
    # Find the user message
    user_msg = db_session.query(Message).filter(Message.role == 'user').first()
    print(f"\n=== USER MESSAGE ===")
    print(f"source_id: {user_msg.source_id}")
    print(f"parent_id: {user_msg.parent_id}")
    
    # Find children
    children = db_session.query(Message).filter(Message.parent_id == user_msg.id).all()
    print(f"\n=== CHILDREN OF USER MESSAGE ===")
    print(f"Count: {len(children)}")
    for child in children:
        print(f"  - source_id={child.source_id}, role={child.role}")
    
    # Check if parent_id is set at all
    messages_with_parent = db_session.query(Message).filter(Message.parent_id.isnot(None)).all()
    print(f"\n=== MESSAGES WITH PARENT_ID SET ===")
    print(f"Count: {len(messages_with_parent)}")
    for msg in messages_with_parent:
        parent = db_session.get(Message, msg.parent_id)
        parent_source = parent.source_id if parent else "NOT FOUND"
        print(f"  - {msg.source_id} -> parent: {parent_source}")
    
    # The actual assertion
    assert len(children) == 2, f"Expected 2 children, found {len(children)}"


def test_simple_parent_child_relationship(db_session):
    """Test if parent-child relationships work at all."""
    simple_conv = {
        "conversation_id": "test-parent-child",
        "title": "Parent Child Test",
        "create_time": 1700000000.0,
        "update_time": 1700000000.0,
        "mapping": {
            "root": {
                "id": "root",
                "parent": None,
                "children": ["node1"],
                "message": None
            },
            "node1": {
                "id": "node1", 
                "parent": "root",
                "children": ["node2"],
                "message": {
                    "id": "msg1",
                    "author": {"role": "user"},
                    "create_time": 1700000100.0,
                    "content": {"content_type": "text", "parts": ["Hello"]}
                }
            },
            "node2": {
                "id": "node2",
                "parent": "node1",
                "children": [],
                "message": {
                    "id": "msg2",
                    "author": {"role": "assistant"},
                    "create_time": 1700000200.0,
                    "content": {"content_type": "text", "parts": ["Hi"]}
                }
            }
        }
    }
    
    extractor = ChatGPTExtractor(db_session)
    extractor.extract_dialogue(simple_conv)
    
    msg1 = db_session.query(Message).filter(Message.source_id == "msg1").first()
    msg2 = db_session.query(Message).filter(Message.source_id == "msg2").first()
    
    print(f"\n=== SIMPLE TEST ===")
    print(f"msg1 (user): source_id={msg1.source_id}, id={msg1.id}, parent_id={msg1.parent_id}")
    print(f"msg2 (asst): source_id={msg2.source_id}, id={msg2.id}, parent_id={msg2.parent_id}")
    
    # Check if msg2's parent_id points to msg1's id
    if msg2.parent_id:
        print(f"msg2.parent_id == msg1.id? {msg2.parent_id == msg1.id}")
    else:
        print("msg2.parent_id is None!")
    
    assert msg2.parent_id == msg1.id, "Child should have parent_id pointing to parent"


def test_branched_extraction_step_by_step(db_session):
    """Test extraction with a known branched structure."""
    conv = {
        "conversation_id": "test-branch",
        "title": "Branch Test",
        "create_time": 1700000000.0,
        "update_time": 1700000000.0,
        "mapping": {
            "root": {
                "id": "root",
                "parent": None,
                "children": ["user1"],
                "message": None
            },
            "user1": {
                "id": "user1",
                "parent": "root", 
                "children": ["asst1", "asst2"],  # TWO CHILDREN
                "message": {
                    "id": "msg-user1",
                    "author": {"role": "user"},
                    "create_time": 1700000100.0,
                    "content": {"content_type": "text", "parts": ["Question"]}
                }
            },
            "asst1": {
                "id": "asst1",
                "parent": "user1",
                "children": [],
                "message": {
                    "id": "msg-asst1",
                    "author": {"role": "assistant"},
                    "create_time": 1700000200.0,
                    "content": {"content_type": "text", "parts": ["Answer 1"]}
                }
            },
            "asst2": {
                "id": "asst2",
                "parent": "user1",
                "children": [],
                "message": {
                    "id": "msg-asst2",
                    "author": {"role": "assistant"},
                    "create_time": 1700000250.0,
                    "content": {"content_type": "text", "parts": ["Answer 2"]}
                }
            }
        }
    }
    
    extractor = ChatGPTExtractor(db_session)
    extractor.extract_dialogue(conv)
    
    user_msg = db_session.query(Message).filter(Message.source_id == "msg-user1").first()
    asst1 = db_session.query(Message).filter(Message.source_id == "msg-asst1").first()
    asst2 = db_session.query(Message).filter(Message.source_id == "msg-asst2").first()
    
    print(f"\n=== BRANCHED TEST ===")
    print(f"user: id={user_msg.id}, source_id={user_msg.source_id}")
    print(f"asst1: id={asst1.id}, parent_id={asst1.parent_id}")
    print(f"asst2: id={asst2.id}, parent_id={asst2.parent_id}")
    
    # Both assistants should have user as parent
    assert asst1.parent_id == user_msg.id, "asst1 parent should be user"
    assert asst2.parent_id == user_msg.id, "asst2 parent should be user"
    
    # User should have 2 children
    children = db_session.query(Message).filter(Message.parent_id == user_msg.id).all()
    print(f"Children count: {len(children)}")
    
    assert len(children) == 2, f"User should have 2 children, got {len(children)}"
