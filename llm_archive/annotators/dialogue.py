# llm_archive/annotators/dialogue.py
"""Dialogue-level annotators for aggregate statistics.

These annotators analyze entire dialogues to compute:
- Length metrics (exchange count, message count)
- Prompt statistics (length, consistency)
- First exchange patterns (context dump detection)
- Interaction patterns (brief, extended, interactive)
- Coding assistance classification
"""

import statistics

from llm_archive.annotators.base import (
    DialogueAnnotator,
    DialogueData,
    AnnotationResult,
)


class DialogueLengthAnnotator(DialogueAnnotator):
    """Annotate dialogue length with count and category."""
    
    ANNOTATION_TYPE = 'metadata'
    ANNOTATION_KEY = 'dialogue_length'
    PRIORITY = 50
    VERSION = '1.0'
    
    def annotate(self, data: DialogueData) -> list[AnnotationResult]:
        count = data.exchange_count
        
        # Determine category
        if count == 0:
            category = 'empty'
        elif count == 1:
            category = 'single'
        elif count <= 3:
            category = 'short'
        elif count <= 10:
            category = 'medium'
        elif count <= 25:
            category = 'long'
        else:
            category = 'very_long'
        
        return [AnnotationResult(
            value=category,
            key='dialogue_length',
            confidence=1.0,
            data={
                'exchange_count': count,
                'message_count': data.message_count,
                'user_message_count': data.user_message_count,
                'assistant_message_count': data.assistant_message_count,
            },
        )]


class PromptStatsAnnotator(DialogueAnnotator):
    """Compute user prompt statistics across the dialogue."""
    
    ANNOTATION_TYPE = 'metadata'
    ANNOTATION_KEY = 'prompt_stats'
    PRIORITY = 50
    VERSION = '1.0'
    
    def annotate(self, data: DialogueData) -> list[AnnotationResult]:
        if not data.user_word_counts:
            return [AnnotationResult(
                value='none',
                key='prompt_stats',
                confidence=1.0,
                data={'count': 0},
            )]
        
        counts = data.user_word_counts
        n = len(counts)
        
        # Calculate statistics
        mean_wc = statistics.mean(counts)
        median_wc = statistics.median(counts)
        variance = statistics.variance(counts) if n > 1 else 0
        
        # Determine length category based on mean
        if mean_wc < 10:
            length_category = 'very_short'
        elif mean_wc < 50:
            length_category = 'short'
        elif mean_wc < 200:
            length_category = 'medium'
        elif mean_wc < 500:
            length_category = 'long'
        else:
            length_category = 'very_long'
        
        # Determine consistency based on coefficient of variation
        cv = (variance ** 0.5) / mean_wc if mean_wc > 0 else 0
        if cv < 0.3:
            consistency = 'consistent'
        elif cv < 0.7:
            consistency = 'mixed'
        else:
            consistency = 'variable'
        
        return [AnnotationResult(
            value=f'{length_category}_{consistency}',
            key='prompt_stats',
            confidence=1.0,
            data={
                'count': n,
                'mean': round(mean_wc, 1),
                'median': round(median_wc, 1),
                'variance': round(variance, 1),
                'length_category': length_category,
                'consistency': consistency,
            },
        )]


class FirstExchangeAnnotator(DialogueAnnotator):
    """Analyze first exchange patterns (context dump detection)."""
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'first_exchange'
    PRIORITY = 50
    VERSION = '1.0'
    
    LARGE_CONTENT_THRESHOLD = 2000  # characters
    
    # Code indicators to check in first message
    CODE_INDICATORS = ['```', 'def ', 'function ', 'class ', 'import ', '#include']
    
    def annotate(self, data: DialogueData) -> list[AnnotationResult]:
        results = []
        first_text = data.first_user_text or ''
        
        # Check for large initial content
        if len(first_text) > self.LARGE_CONTENT_THRESHOLD:
            results.append(AnnotationResult(
                value='starts_large_content',
                confidence=1.0,
                data={'char_count': len(first_text)},
            ))
        
        # Check for code patterns in first message
        code_found = [ind for ind in self.CODE_INDICATORS if ind in first_text]
        if code_found:
            results.append(AnnotationResult(
                value='starts_with_code',
                confidence=0.9,
                data={'indicators': code_found},
            ))
        
        # Context dump detection: short dialogue + large first message
        if data.exchange_count <= 3 and len(first_text) > self.LARGE_CONTENT_THRESHOLD:
            results.append(AnnotationResult(
                value='context_dump',
                confidence=0.85,
                data={
                    'exchange_count': data.exchange_count,
                    'first_message_chars': len(first_text),
                },
            ))
        
        return results


class InteractionPatternAnnotator(DialogueAnnotator):
    """Classify dialogue interaction patterns."""
    
    ANNOTATION_TYPE = 'tag'
    ANNOTATION_KEY = 'interaction_pattern'
    PRIORITY = 40  # After length/stats computed
    VERSION = '1.0'
    
    def annotate(self, data: DialogueData) -> list[AnnotationResult]:
        results = []
        
        # Brief interaction (1-3 exchanges)
        if data.exchange_count <= 3:
            results.append(AnnotationResult(
                value='brief_interaction',
                confidence=1.0,
            ))
        
        # Extended conversation (10+ exchanges)
        elif data.exchange_count >= 10:
            results.append(AnnotationResult(
                value='extended_conversation',
                confidence=1.0,
            ))
        
        # Check for consistency patterns in longer dialogues
        if data.exchange_count >= 5 and len(data.user_word_counts) >= 5:
            mean_wc = statistics.mean(data.user_word_counts)
            if mean_wc > 0:
                cv = (statistics.stdev(data.user_word_counts) / mean_wc)
                
                if cv < 0.3:
                    results.append(AnnotationResult(
                        value='interactive_session',
                        confidence=0.8,
                        data={'cv': round(cv, 2), 'exchanges': data.exchange_count},
                    ))
                elif cv > 0.7:
                    results.append(AnnotationResult(
                        value='evolving_discussion',
                        confidence=0.8,
                        data={'cv': round(cv, 2), 'exchanges': data.exchange_count},
                    ))
        
        return results


class CodingAssistanceAnnotator(DialogueAnnotator):
    """Detect if dialogue is likely coding assistance.
    
    Lower priority than platform-specific code execution detection.
    Uses text pattern analysis across the entire dialogue.
    """
    
    ANNOTATION_TYPE = 'tag'
    ANNOTATION_KEY = 'coding_assistance'
    PRIORITY = 40  # Lower than platform-specific detectors
    VERSION = '1.0'
    
    # Strong code indicators
    STRONG_INDICATORS = ['```', '#!/', '#include <', '#include "']
    
    # Moderate indicators
    MODERATE_INDICATORS = ['def ', 'function ', 'class ', 'import ', 'from ']
    
    def annotate(self, data: DialogueData) -> list[AnnotationResult]:
        all_user = ' '.join(data.user_texts)
        all_assistant = ' '.join(data.assistant_texts)
        all_text = all_user + ' ' + all_assistant
        
        # Count indicators
        strong_count = sum(1 for ind in self.STRONG_INDICATORS if ind in all_text)
        moderate_count = sum(1 for ind in self.MODERATE_INDICATORS if ind in all_text)
        
        # Conservative detection (high confidence)
        if strong_count >= 2:
            return [AnnotationResult(
                value='coding_assistance',
                confidence=0.95,
                data={
                    'evidence': 'strong',
                    'strong_indicators': strong_count,
                    'moderate_indicators': moderate_count,
                },
            )]
        
        # Likely coding (moderate confidence)
        if strong_count >= 1 or moderate_count >= 3:
            return [AnnotationResult(
                value='coding_assistance',
                confidence=0.7,
                data={
                    'evidence': 'moderate',
                    'strong_indicators': strong_count,
                    'moderate_indicators': moderate_count,
                },
            )]
        
        return []