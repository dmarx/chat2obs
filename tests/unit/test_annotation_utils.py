# tests/unit/test_annotation_utils.py
"""Unit tests for annotation utilities and data classes."""

import pytest
from datetime import datetime, timezone

from llm_archive.annotators.base import (
    AnnotationResult,
    MessageTextData,
    ExchangeData,
)


class TestAnnotationResult:
    """Tests for AnnotationResult dataclass."""
    
    def test_minimal_result(self):
        """Test creating result with only required field."""
        result = AnnotationResult(value='test')
        
        assert result.value == 'test'
        assert result.key is None
        assert result.confidence is None
        assert result.data is None
    
    def test_full_result(self):
        """Test creating result with all fields."""
        result = AnnotationResult(
            value='has_code',
            key='feature_type',
            confidence=0.95,
            data={'languages': ['python', 'javascript']},
        )
        
        assert result.value == 'has_code'
        assert result.key == 'feature_type'
        assert result.confidence == 0.95
        assert result.data == {'languages': ['python', 'javascript']}
    
    def test_result_equality(self):
        """Test that identical results are equal."""
        r1 = AnnotationResult(value='test', key='k', confidence=0.5)
        r2 = AnnotationResult(value='test', key='k', confidence=0.5)
        
        assert r1 == r2
    
    def test_result_inequality(self):
        """Test that different results are not equal."""
        r1 = AnnotationResult(value='test1')
        r2 = AnnotationResult(value='test2')
        
        assert r1 != r2


class TestMessageTextData:
    """Tests for MessageTextData dataclass."""
    
    def test_minimal_data(self):
        """Test creating data with required fields."""
        from uuid import uuid4
        
        msg_id = uuid4()
        data = MessageTextData(
            message_id=msg_id,
            text='Hello world',
            created_at=None,
        )
        
        assert data.message_id == msg_id
        assert data.text == 'Hello world'
        assert data.created_at is None
        assert data.role is None
    
    def test_full_data(self):
        """Test creating data with all fields."""
        from uuid import uuid4
        
        msg_id = uuid4()
        ts = datetime.now(timezone.utc)
        
        data = MessageTextData(
            message_id=msg_id,
            text='Test message',
            created_at=ts,
            role='assistant',
        )
        
        assert data.message_id == msg_id
        assert data.text == 'Test message'
        assert data.created_at == ts
        assert data.role == 'assistant'


class TestExchangeData:
    """Tests for ExchangeData dataclass."""
    
    def test_minimal_data(self):
        """Test creating exchange data with minimal fields."""
        from uuid import uuid4
        
        ex_id = uuid4()
        data = ExchangeData(
            exchange_id=ex_id,
            user_text=None,
            assistant_text=None,
            user_word_count=None,
            assistant_word_count=None,
            computed_at=None,
        )
        
        assert data.exchange_id == ex_id
        assert data.user_text is None
    
    def test_full_data(self):
        """Test creating exchange data with all fields."""
        from uuid import uuid4
        
        ex_id = uuid4()
        ts = datetime.now(timezone.utc)
        
        data = ExchangeData(
            exchange_id=ex_id,
            user_text='What is Python?',
            assistant_text='Python is a programming language...',
            user_word_count=3,
            assistant_word_count=5,
            computed_at=ts,
        )
        
        assert data.exchange_id == ex_id
        assert data.user_text == 'What is Python?'
        assert data.assistant_text == 'Python is a programming language...'
        assert data.user_word_count == 3
        assert data.assistant_word_count == 5
        assert data.computed_at == ts


class TestAnnotationResultUsage:
    """Tests for common annotation result patterns."""
    
    def test_return_empty_list_for_no_match(self):
        """Test pattern of returning empty list when no match."""
        def check_for_pattern(text: str) -> list[AnnotationResult]:
            if 'pattern' in text:
                return [AnnotationResult(value='has_pattern')]
            return []
        
        assert check_for_pattern('no match here') == []
        assert len(check_for_pattern('has pattern')) == 1
    
    def test_return_multiple_results(self):
        """Test pattern of returning multiple results."""
        def analyze_text(text: str) -> list[AnnotationResult]:
            results = []
            if '?' in text:
                results.append(AnnotationResult(value='question'))
            if '!' in text:
                results.append(AnnotationResult(value='exclamation'))
            if len(text) > 100:
                results.append(AnnotationResult(value='long'))
            return results
        
        results = analyze_text('Hello? World!')
        assert len(results) == 2
        values = [r.value for r in results]
        assert 'question' in values
        assert 'exclamation' in values
    
    def test_results_with_confidence_gradients(self):
        """Test pattern of assigning different confidence levels."""
        def classify_length(word_count: int) -> list[AnnotationResult]:
            if word_count > 500:
                return [AnnotationResult(value='long', confidence=0.95)]
            elif word_count > 200:
                return [AnnotationResult(value='medium', confidence=0.8)]
            elif word_count > 50:
                return [AnnotationResult(value='short', confidence=0.7)]
            return [AnnotationResult(value='very_short', confidence=0.6)]
        
        long_result = classify_length(600)
        assert long_result[0].confidence == 0.95
        
        short_result = classify_length(100)
        assert short_result[0].confidence == 0.7
