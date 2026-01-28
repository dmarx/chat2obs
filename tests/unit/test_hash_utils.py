# tests/unit/test_hash_utils.py
"""Unit tests for hash computation utilities."""

import pytest
import hashlib

from llm_archive.builders.exchanges import compute_hash


class TestComputeHash:
    """Tests for hash computation."""
    
    def test_simple_hash(self):
        """Test hashing simple text."""
        result = compute_hash("Hello world")
        assert result is not None
        assert len(result) == 64  # SHA-256 hex length
    
    def test_hash_none(self):
        """Test None returns None."""
        assert compute_hash(None) is None
    
    def test_hash_empty_string(self):
        """Test empty string returns None."""
        # Empty string is falsy, so compute_hash returns None
        result = compute_hash("")
        assert result is None
    
    def test_hash_consistency(self):
        """Test same input gives same hash."""
        text = "Test content"
        hash1 = compute_hash(text)
        hash2 = compute_hash(text)
        assert hash1 == hash2
    
    def test_hash_normalization(self):
        """Test whitespace normalization."""
        text1 = "Hello   world"
        text2 = "Hello world"
        text3 = "Hello\n\nworld"
        
        hash1 = compute_hash(text1)
        hash2 = compute_hash(text2)
        hash3 = compute_hash(text3)
        
        # All should produce same hash after normalization
        assert hash1 == hash2
        assert hash2 == hash3
    
    def test_hash_different_content(self):
        """Test different content gives different hash."""
        hash1 = compute_hash("Hello")
        hash2 = compute_hash("World")
        assert hash1 != hash2
    
    def test_hash_unicode(self):
        """Test hashing unicode text."""
        result = compute_hash("Hello 世界 🌍")
        assert result is not None
        assert len(result) == 64
    
    def test_hash_long_text(self):
        """Test hashing long text."""
        long_text = "A" * 100000
        result = compute_hash(long_text)
        assert result is not None
        assert len(result) == 64
    
    def test_hash_matches_direct_sha256(self):
        """Test hash matches direct SHA-256 computation."""
        text = "Hello world"
        normalized = " ".join(text.split())
        expected = hashlib.sha256(normalized.encode()).hexdigest()
        
        result = compute_hash(text)
        assert result == expected
