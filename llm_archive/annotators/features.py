# llm_archive/annotators/features.py
"""Feature detection annotators using modular base classes."""

import re

from llm_archive.annotators.base import (
    MessageTextAnnotator,
    ExchangeAnnotator,
    MessageTextData,
    ExchangeData,
    AnnotationResult,
)


# ============================================================
# Message Feature Annotators
# ============================================================

class WikiLinkAnnotator(MessageTextAnnotator):
    """Detect Obsidian-style [[wiki links]] in assistant messages."""
    
    ANNOTATION_TYPE = 'feature'
    VERSION = '1.0'
    ROLE_FILTER = 'assistant'
    
    PATTERN = re.compile(r'\[\[.+?\]\]')
    
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        if self.PATTERN.search(data.text):
            links = self.PATTERN.findall(data.text)
            return [AnnotationResult(
                value='has_wiki_links',
                confidence=1.0,
                data={'count': len(links)},
            )]
        return []


class CodeBlockAnnotator(MessageTextAnnotator):
    """Detect code blocks (```) in messages."""
    
    ANNOTATION_TYPE = 'feature'
    VERSION = '1.0'
    ROLE_FILTER = None  # All roles
    
    LANGUAGE_PATTERN = re.compile(r'```(\w*)\n')
    
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        if '```' not in data.text:
            return []
        
        languages = self.LANGUAGE_PATTERN.findall(data.text)
        languages = [lang for lang in languages if lang]
        
        results = [AnnotationResult(
            value='has_code_blocks',
            confidence=1.0,
            data={
                'count': data.text.count('```') // 2,
                'languages': list(set(languages)),
            },
        )]
        
        # Add language-specific annotations
        for lang in set(languages):
            results.append(AnnotationResult(
                value=lang,
                key='code_language',
                confidence=1.0,
            ))
        
        return results


class LatexAnnotator(MessageTextAnnotator):
    """Detect LaTeX/MathJax mathematical notation in assistant messages."""
    
    ANNOTATION_TYPE = 'feature'
    VERSION = '1.0'
    ROLE_FILTER = 'assistant'
    
    PATTERNS = [
        re.compile(r'\$\$.+?\$\$', re.DOTALL),
        re.compile(r'\\\(.+?\\\)', re.DOTALL),
        re.compile(r'\\\[.+?\\\]', re.DOTALL),
    ]
    
    COMMANDS = [
        '\\frac', '\\sum', '\\int', '\\sqrt', '\\alpha', '\\beta',
        '\\gamma', '\\theta', '\\pi', '\\sigma', '\\infty', '\\partial',
        '\\nabla', '\\Delta', '\\Omega', '\\lambda', '\\mu',
    ]
    
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        has_latex = False
        found_commands = []
        
        for pattern in self.PATTERNS:
            if pattern.search(data.text):
                has_latex = True
                break
        
        for cmd in self.COMMANDS:
            if cmd in data.text:
                has_latex = True
                found_commands.append(cmd)
        
        if has_latex:
            return [AnnotationResult(
                value='has_latex',
                confidence=1.0,
                data={'commands': found_commands[:10]},
            )]
        return []


class ContinuationAnnotator(MessageTextAnnotator):
    """Detect continuation signals in user messages."""
    
    ANNOTATION_TYPE = 'feature'
    VERSION = '1.0'
    ROLE_FILTER = 'user'
    
    PATTERNS = {
        'continue': ['continue', 'keep going', 'go on', 'carry on'],
        'elaborate': ['elaborate', 'expand', 'tell me more', 'more details'],
        'finish': ['finish', 'complete', 'wrap up'],
        'next': ['next', 'what else', 'and then'],
    }
    
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        text = data.text.strip().lower()
        
        # Skip long messages
        if len(text.split()) > 10:
            return []
        
        # Check quote+elaborate pattern
        if text.startswith('>'):
            lines = text.split('\n')
            last_line = lines[-1].strip()
            if last_line in ('elaborate', 'continue', 'expand', 'more'):
                return [AnnotationResult(
                    value='continuation_signal',
                    key='quote_elaborate',
                    confidence=1.0,
                )]
        
        # Check keyword patterns
        for pattern_name, keywords in self.PATTERNS.items():
            for keyword in keywords:
                if text == keyword or text.startswith(keyword + ' '):
                    return [AnnotationResult(
                        value='continuation_signal',
                        key=pattern_name,
                        confidence=0.9,
                        data={'matched': keyword},
                    )]
        
        return []


# ============================================================
# Exchange Annotators
# ============================================================

class ExchangeTypeAnnotator(ExchangeAnnotator):
    """Classify exchange types based on content patterns."""
    
    ANNOTATION_TYPE = 'tag'
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
