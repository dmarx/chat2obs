# tests/unit/test_exchange_utils.py
"""Unit tests for exchange building utilities."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from llm_archive.builders.exchanges import (
    is_continuation_prompt,
    CONTINUATION_PATTERNS,
    MessageInfo,
)


class TestIsContinuationPrompt:
    """Tests for continuation prompt detection."""
    
    def test_simple_continue(self):
        """Test 'continue' is detected."""
        assert is_continuation_prompt("continue") is True
    
    def test_continue_with_punctuation(self):
        """Test 'continue?' is detected."""
        assert is_continuation_prompt("continue?") is True
    
    def test_continue_uppercase(self):
        """Test 'CONTINUE' is detected (case insensitive)."""
        assert is_continuation_prompt("CONTINUE") is True
    
    def test_continue_with_whitespace(self):
        """Test '  continue  ' is detected (trimmed)."""
        assert is_continuation_prompt("  continue  ") is True
    
    def test_more(self):
        """Test 'more' is detected."""
        assert is_continuation_prompt("more") is True
    
    def test_keep_going(self):
        """Test 'keep going' is detected."""
        assert is_continuation_prompt("keep going") is True
    
    def test_go_on(self):
        """Test 'go on' is detected."""
        assert is_continuation_prompt("go on") is True
    
    def test_elaborate(self):
        """Test 'elaborate' is detected."""
        assert is_continuation_prompt("elaborate") is True
    
    def test_yes_please(self):
        """Test 'yes please' is detected."""
        assert is_continuation_prompt("yes please") is True
    
    def test_ok(self):
        """Test 'ok' is detected."""
        assert is_continuation_prompt("ok") is True
    
    def test_okay(self):
        """Test 'okay' is detected."""
        assert is_continuation_prompt("okay") is True
    
    def test_please(self):
        """Test 'please' is detected."""
        assert is_continuation_prompt("please") is True
    
    def test_proceed(self):
        """Test 'proceed' is detected."""
        assert is_continuation_prompt("proceed") is True
    
    def test_quote_elaborate_pattern(self):
        """Test quote + elaborate pattern."""
        text = "> some quoted text\n\nelaborate"
        assert is_continuation_prompt(text) is True
    
    def test_quote_continue_pattern(self):
        """Test quote + continue pattern."""
        text = "> quoted\ncontinue"
        assert is_continuation_prompt(text) is True
    
    def test_not_continuation_long_message(self):
        """Test long message is not a continuation."""
        text = "Can you continue the story but add more dragons and make it exciting?"
        assert is_continuation_prompt(text) is False
    
    def test_not_continuation_question(self):
        """Test substantive question is not a continuation."""
        assert is_continuation_prompt("What happened next?") is False
    
    def test_not_continuation_new_topic(self):
        """Test new topic is not a continuation."""
        assert is_continuation_prompt("Now let's talk about something else.") is False
    
    def test_none_text(self):
        """Test None returns False."""
        assert is_continuation_prompt(None) is False
    
    def test_empty_string(self):
        """Test empty string returns False."""
        assert is_continuation_prompt("") is False
    
    def test_whitespace_only(self):
        """Test whitespace only returns False."""
        assert is_continuation_prompt("   ") is False
    
    def test_all_patterns(self):
        """Test all defined continuation patterns are detected."""
        for pattern in CONTINUATION_PATTERNS:
            assert is_continuation_prompt(pattern) is True, f"Pattern '{pattern}' not detected"
    
    def test_continue_with_extra_words(self):
        """Test 'continue please' is detected (starts with pattern)."""
        assert is_continuation_prompt("continue please") is True
    
    def test_pattern_in_middle_not_detected(self):
        """Test pattern in middle of sentence is not detected."""
        # "continue" appears but not at start and message is long
        text = "I would like you to continue with the explanation of neural networks."
        assert is_continuation_prompt(text) is False


class TestMessageInfo:
    """Tests for MessageInfo dataclass."""
    
    def test_create_message_info(self):
        """Test creating MessageInfo."""
        msg_id = uuid4()
        now = datetime.now(timezone.utc)
        
        info = MessageInfo(
            message_id=msg_id,
            role="user",
            created_at=now,
            text_content="Hello",
        )
        
        assert info.message_id == msg_id
        assert info.role == "user"
        assert info.created_at == now
        assert info.text_content == "Hello"
    
    def test_message_info_none_content(self):
        """Test MessageInfo with None content."""
        info = MessageInfo(
            message_id=uuid4(),
            role="assistant",
            created_at=None,
            text_content=None,
        )
        
        assert info.text_content is None
        assert info.created_at is None
