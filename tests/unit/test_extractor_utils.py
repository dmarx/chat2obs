# tests/unit/test_extractor_utils.py
"""Unit tests for extractor utility functions."""

import pytest
from datetime import datetime, timezone

from llm_archive.extractors.base import parse_timestamp, normalize_role, safe_get, compute_content_hash


class TestParseTimestamp:
    """Tests for timestamp parsing."""
    
    def test_parse_epoch_int(self):
        """Test parsing integer epoch timestamp."""
        result = parse_timestamp(1700000000)
        assert result is not None
        assert result.tzinfo is not None
        assert result.year == 2023
    
    def test_parse_epoch_float(self):
        """Test parsing float epoch timestamp."""
        result = parse_timestamp(1700000000.123)
        assert result is not None
        assert result.tzinfo is not None
    
    def test_parse_iso_string(self):
        """Test parsing ISO 8601 string."""
        result = parse_timestamp("2024-01-15T10:00:00Z")
        assert result is not None
        assert result.tzinfo is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_iso_string_with_offset(self):
        """Test parsing ISO 8601 with timezone offset."""
        result = parse_timestamp("2024-01-15T10:00:00+05:00")
        assert result is not None
        assert result.tzinfo is not None
    
    def test_parse_none(self):
        """Test parsing None returns None."""
        result = parse_timestamp(None)
        assert result is None
    
    def test_parse_invalid_string(self):
        """Test parsing invalid string returns None."""
        result = parse_timestamp("not a timestamp")
        assert result is None
    
    def test_parse_negative_epoch(self):
        """Test parsing negative epoch (before 1970)."""
        result = parse_timestamp(-1000000)
        assert result is not None
        assert result.year < 1970


class TestNormalizeRole:
    """Tests for role normalization."""
    
    def test_normalize_user(self):
        """Test 'user' stays 'user'."""
        assert normalize_role("user", "chatgpt") == "user"
    
    def test_normalize_assistant(self):
        """Test 'assistant' stays 'assistant'."""
        assert normalize_role("assistant", "chatgpt") == "assistant"
    
    def test_normalize_human_to_user(self):
        """Test 'human' becomes 'user' (Claude format)."""
        assert normalize_role("human", "claude") == "user"
    
    def test_normalize_human_uppercase(self):
        """Test uppercase 'HUMAN' becomes 'user'."""
        assert normalize_role("HUMAN", "claude") == "user"
    
    def test_normalize_system(self):
        """Test 'system' stays 'system'."""
        assert normalize_role("system", "chatgpt") == "system"
    
    def test_normalize_none(self):
        """Test None becomes 'unknown'."""
        assert normalize_role(None, "chatgpt") == "unknown"


class TestSafeGet:
    """Tests for safe dictionary traversal."""
    
    def test_simple_get(self):
        """Test simple key access."""
        data = {"key": "value"}
        assert safe_get(data, "key") == "value"
    
    def test_nested_get(self):
        """Test nested key access."""
        data = {"level1": {"level2": {"level3": "value"}}}
        assert safe_get(data, "level1", "level2", "level3") == "value"
    
    def test_missing_key(self):
        """Test missing key returns default."""
        data = {"key": "value"}
        assert safe_get(data, "missing") is None
        assert safe_get(data, "missing", default="default") == "default"
    
    def test_missing_nested_key(self):
        """Test missing nested key returns default."""
        data = {"level1": {"level2": "value"}}
        assert safe_get(data, "level1", "level2", "level3") is None
    
    def test_non_dict_intermediate(self):
        """Test non-dict intermediate value returns default."""
        data = {"level1": "not a dict"}
        assert safe_get(data, "level1", "level2") is None
    
    def test_none_intermediate(self):
        """Test None intermediate value returns default."""
        data = {"level1": None}
        assert safe_get(data, "level1", "level2") is None


class TestTimestampEdgeCases:
    """Edge case tests for timestamp parsing."""
    
    def test_zero_epoch(self):
        """Test epoch 0 (1970-01-01)."""
        result = parse_timestamp(0)
        assert result is not None
        assert result.year == 1970
    
    def test_very_large_epoch(self):
        """Test very large epoch value."""
        # Year 2100
        result = parse_timestamp(4102444800)
        assert result is not None
        assert result.year == 2100
    
    def test_iso_without_timezone(self):
        """Test ISO string without timezone gets UTC."""
        result = parse_timestamp("2024-01-15T10:00:00")
        assert result is not None
        assert result.tzinfo is not None


class TestComputeContentHash:
    """Tests for content hash computation."""
    
    def test_hash_dict(self):
        """Test hashing a dictionary."""
        data = {'text': 'Hello world', 'role': 'user'}
        result = compute_content_hash(data)
        
        assert result is not None
        assert len(result) == 64  # SHA-256 hex string
    
    def test_hash_string(self):
        """Test hashing a plain string."""
        result = compute_content_hash('Hello world')
        
        assert result is not None
        assert len(result) == 64
    
    def test_hash_is_deterministic(self):
        """Test that same content produces same hash."""
        data = {'message': 'test', 'value': 123}
        
        hash1 = compute_content_hash(data)
        hash2 = compute_content_hash(data)
        
        assert hash1 == hash2
    
    def test_hash_is_order_independent(self):
        """Test that key order doesn't affect hash."""
        data1 = {'a': 1, 'b': 2}
        data2 = {'b': 2, 'a': 1}
        
        hash1 = compute_content_hash(data1)
        hash2 = compute_content_hash(data2)
        
        assert hash1 == hash2
    
    def test_different_content_different_hash(self):
        """Test that different content produces different hash."""
        data1 = {'text': 'Hello'}
        data2 = {'text': 'World'}
        
        hash1 = compute_content_hash(data1)
        hash2 = compute_content_hash(data2)
        
        assert hash1 != hash2
    
    def test_hash_nested_dict(self):
        """Test hashing nested dictionary."""
        data = {
            'content': {
                'parts': ['Hello', {'type': 'code', 'text': 'print(1)'}]
            },
            'metadata': {'author': 'user'}
        }
        
        result = compute_content_hash(data)
        assert len(result) == 64
    
    def test_hash_list(self):
        """Test hashing a list."""
        data = [{'text': 'message 1'}, {'text': 'message 2'}]
        
        result = compute_content_hash(data)
        assert len(result) == 64
