# llm_archive/annotators/exchange.py
"""Exchange-level annotators based on text content.

These annotators analyze exchange content (user + assistant text) to:
- Classify exchange types (coding, qa, article, etc.)
- Assess code evidence levels
- Extract metadata like proposed titles
"""

from llm_archive.annotators.base import (
    ExchangeAnnotator,
    ExchangeData,
    AnnotationResult,
)


class ExchangeTypeAnnotator(ExchangeAnnotator):
    """Classify exchange types based on content patterns."""
    
    ANNOTATION_TYPE = 'tag'
    ANNOTATION_KEY = 'exchange_type'
    PRIORITY = 50
    VERSION = '1.0'
    
    def annotate(self, data: ExchangeData) -> list[AnnotationResult]:
        exchange_type, confidence = self._classify(data)
        
        if exchange_type:
            return [AnnotationResult(
                value=exchange_type,
                key='exchange_type',
                confidence=confidence,
            )]
        return []
    
    def _classify(self, data: ExchangeData) -> tuple[str | None, float]:
        """Classify an exchange based on content."""
        user_text = data.user_text or ''
        assistant_text = data.assistant_text or ''
        
        # Coding exchanges
        code_blocks = assistant_text.count('```')
        if code_blocks >= 2:
            return 'coding', 0.8
        
        # Wiki-style articles
        if '[[' in assistant_text and ']]' in assistant_text:
            return 'wiki_article', 0.9
        
        # Q&A (short question, long answer)
        if (data.user_word_count or 0) < 50 and (data.assistant_word_count or 0) > 200:
            return 'qa', 0.6
        
        # Long-form generation
        if (data.assistant_word_count or 0) > 500:
            if assistant_text.startswith('#') or assistant_text.startswith('**'):
                return 'article', 0.7
            return 'generation', 0.5
        
        return 'discussion', 0.4


class CodeEvidenceAnnotator(ExchangeAnnotator):
    """Classify code evidence levels based on text indicators.
    
    This annotator analyzes text patterns to determine the strength
    of evidence that the exchange involves coding assistance.
    
    Evidence levels:
    - strong: Explicit code blocks, shebangs, #include
    - moderate: Function definitions, imports (could be in articles)
    - weak: High keyword density only
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'code_evidence'
    PRIORITY = 40  # Runs after platform-level code detection
    VERSION = '1.0'
    
    # Strong indicators (very reliable)
    STRONG_INDICATORS = ['```', '#!/', '#include']
    
    # Moderate indicators (could be false positives in articles)
    MODERATE_KEYWORDS = ['def ', 'function ', 'class ', 'import ', 'from ']
    
    # Programming keywords for density check
    DENSITY_KEYWORDS = [
        'function', 'class', 'import', 'return', 'if ', 'for ', 'while ',
        'const ', 'let ', 'var ', 'async', 'await', 'try', 'catch',
    ]
    
    def annotate(self, data: ExchangeData) -> list[AnnotationResult]:
        all_text = (data.user_text or '') + ' ' + (data.assistant_text or '')
        results = []
        
        # Check strong indicators
        strong_count = sum(1 for ind in self.STRONG_INDICATORS if ind in all_text)
        
        # Check moderate indicators
        moderate_count = sum(1 for kw in self.MODERATE_KEYWORDS if kw in all_text)
        
        # Check keyword density
        keyword_count = sum(1 for kw in self.DENSITY_KEYWORDS if kw in all_text.lower())
        has_high_density = len(all_text) > 500 and keyword_count >= 5
        
        # Determine evidence level
        if strong_count > 0:
            results.append(AnnotationResult(
                value='strong_code_evidence',
                confidence=0.95,
                data={'strong_indicators': strong_count, 'moderate_keywords': moderate_count},
            ))
        elif moderate_count >= 2:
            results.append(AnnotationResult(
                value='moderate_code_evidence',
                confidence=0.7,
                data={'moderate_keywords': moderate_count, 'keyword_density': keyword_count},
            ))
        elif has_high_density:
            results.append(AnnotationResult(
                value='weak_code_evidence',
                confidence=0.5,
                data={'keyword_density': keyword_count, 'text_length': len(all_text)},
            ))
        
        return results


class TitleExtractionAnnotator(ExchangeAnnotator):
    """Extract proposed title from assistant responses.
    
    Detects titles in markdown format (# Title) or bold format (**Title**).
    """
    
    ANNOTATION_TYPE = 'metadata'
    ANNOTATION_KEY = 'proposed_title'
    PRIORITY = 50
    VERSION = '1.0'
    
    def annotate(self, data: ExchangeData) -> list[AnnotationResult]:
        if not data.assistant_text:
            return []
        
        title = self._extract_title(data.assistant_text)
        if title:
            return [AnnotationResult(
                value=title,
                key='proposed_title',
                confidence=0.8,
            )]
        return []
    
    def _extract_title(self, text: str) -> str | None:
        """Extract title from first line of assistant response."""
        lines = text.strip().split('\n')
        if not lines:
            return None
        
        first_line = lines[0].strip()
        
        # Markdown header: # Title
        if first_line.startswith('#'):
            title = first_line.lstrip('#').strip()
            if title:
                return title
        
        # Bold header: **Title**
        if first_line.startswith('**') and first_line.endswith('**'):
            title = first_line.strip('*').strip()
            if title:
                return title
        
        return None