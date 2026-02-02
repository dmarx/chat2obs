# llm_archive/annotators/features.py
"""Feature detection annotators using modular base classes.

Includes:
- Message-level feature detection (code, latex, wiki links, continuations)
- Exchange-level classification (type, coding evidence)
- Dialogue-level statistics (length, prompt stats, first exchange patterns)
"""

import re
import statistics

from llm_archive.annotators.base import (
    MessageTextAnnotator,
    ExchangeAnnotator,
    DialogueAnnotator,
    MessageTextData,
    ExchangeData,
    DialogueData,
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
    """Detect explicit code blocks (```) in messages."""
    
    ANNOTATION_TYPE = 'feature'
    VERSION = '1.1'  # Bumped: now part of granular code detection
    ROLE_FILTER = None
    
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


class FunctionDefinitionAnnotator(MessageTextAnnotator):
    """Detect function/class definition keywords."""
    
    ANNOTATION_TYPE = 'feature'
    VERSION = '1.0'
    ROLE_FILTER = None
    
    # Definition keywords by language family
    KEYWORDS = [
        'def ',       # Python
        'function ',  # JavaScript, PHP
        'class ',     # Many languages
        'fn ',        # Rust
        'func ',      # Go
        'sub ',       # Perl, VB
        'proc ',      # Pascal
    ]
    
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        found = []
        for keyword in self.KEYWORDS:
            if keyword in data.text:
                found.append(keyword.strip())
        
        if found:
            return [AnnotationResult(
                value='has_function_definitions',
                confidence=0.8,
                data={'keywords': found},
            )]
        return []


class ImportStatementAnnotator(MessageTextAnnotator):
    """Detect import/require/include statements."""
    
    ANNOTATION_TYPE = 'feature'
    VERSION = '1.0'
    ROLE_FILTER = None
    
    PATTERNS = [
        re.compile(r'^import\s+\w', re.MULTILINE),       # Python, Java, ES6
        re.compile(r'^from\s+\w+\s+import', re.MULTILINE),  # Python
        re.compile(r'require\s*\('),                      # Node.js, CommonJS
        re.compile(r'^using\s+\w', re.MULTILINE),         # C#
        re.compile(r'^#include\s*[<"]', re.MULTILINE),    # C/C++
    ]
    
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        count = 0
        for pattern in self.PATTERNS:
            count += len(pattern.findall(data.text))
        
        if count > 0:
            return [AnnotationResult(
                value='has_import_statements',
                confidence=0.9,
                data={'count': count},
            )]
        return []


class ScriptHeaderAnnotator(MessageTextAnnotator):
    """Detect script headers and system includes (strong code evidence)."""
    
    ANNOTATION_TYPE = 'feature'
    VERSION = '1.0'
    ROLE_FILTER = None
    
    INDICATORS = [
        '#!/bin/',           # Unix shebang
        '#!/usr/bin/',       # Unix shebang
        '#include <',        # C/C++ system include
        '#include "',        # C/C++ local include
        'using namespace ',  # C++ namespace
        '<?php',             # PHP opening tag
        '<%',                # ASP/JSP
    ]
    
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        found = []
        for indicator in self.INDICATORS:
            if indicator in data.text:
                found.append(indicator.split()[0] if ' ' in indicator else indicator)
        
        if found:
            return [AnnotationResult(
                value='has_script_headers',
                confidence=1.0,
                data={'indicators': list(set(found))},
            )]
        return []


class CodeKeywordDensityAnnotator(MessageTextAnnotator):
    """Detect high density of programming keywords in substantial text."""
    
    ANNOTATION_TYPE = 'feature'
    VERSION = '1.0'
    ROLE_FILTER = None
    
    # Programming keywords to look for
    KEYWORDS = [
        'function', 'class', 'import', 'def ', 'const ', 'let ', 'var ',
        'return', 'if ', 'for ', 'while ', 'else', 'elif', 'switch',
        'case', 'break', 'continue', 'try', 'catch', 'except', 'finally',
        'async', 'await', 'yield', 'lambda', 'struct', 'enum', 'interface',
        'public', 'private', 'protected', 'static', 'void', 'int ', 'str ',
    ]
    
    MIN_TEXT_LENGTH = 500
    MIN_KEYWORD_COUNT = 5
    
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        if len(data.text) < self.MIN_TEXT_LENGTH:
            return []
        
        text_lower = data.text.lower()
        keyword_count = sum(1 for kw in self.KEYWORDS if kw in text_lower)
        
        if keyword_count >= self.MIN_KEYWORD_COUNT:
            density = keyword_count / (len(data.text) / 1000)  # per 1000 chars
            return [AnnotationResult(
                value='has_high_keyword_density',
                confidence=min(0.9, 0.5 + (keyword_count - 5) * 0.1),
                data={
                    'keyword_count': keyword_count,
                    'text_length': len(data.text),
                    'density_per_1k': round(density, 2),
                },
            )]
        return []


class CodeStructureAnnotator(MessageTextAnnotator):
    """Detect actual code structure patterns (syntax combinations)."""
    
    ANNOTATION_TYPE = 'feature'
    VERSION = '1.0'
    ROLE_FILTER = None
    
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        patterns_found = []
        
        # Python function pattern: def name(args): ... return
        if 'def ' in data.text and '(' in data.text and ':' in data.text:
            if 'return' in data.text or 'pass' in data.text:
                patterns_found.append('python_function')
        
        # Python class pattern: class Name: ... def
        if 'class ' in data.text and ':' in data.text and 'def ' in data.text:
            patterns_found.append('python_class')
        
        # JavaScript function pattern: function() { }
        if ('function(' in data.text or 'function ' in data.text):
            if '{' in data.text and '}' in data.text:
                patterns_found.append('js_function')
        
        # Arrow function pattern: => { }
        if '=>' in data.text and ('{' in data.text or 'return' in data.text):
            patterns_found.append('arrow_function')
        
        # Variable declaration pattern: multiple assignments
        if data.text.count('=') >= 3:
            if any(kw in data.text for kw in ['let ', 'const ', 'var ']):
                patterns_found.append('js_declarations')
        
        # C-style function: type name(args) { }
        c_func_pattern = re.compile(r'\w+\s+\w+\s*\([^)]*\)\s*\{')
        if c_func_pattern.search(data.text):
            patterns_found.append('c_style_function')
        
        if patterns_found:
            return [AnnotationResult(
                value='has_code_structure',
                confidence=0.95,
                data={'patterns': patterns_found},
            )]
        return []


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


class CodeEvidenceAnnotator(ExchangeAnnotator):
    """Classify code evidence levels based on indicators."""
    
    ANNOTATION_TYPE = 'feature'
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


# ============================================================
# Dialogue Annotators
# ============================================================

class DialogueLengthAnnotator(DialogueAnnotator):
    """Annotate dialogue length with count and category."""
    
    ANNOTATION_TYPE = 'metadata'
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
        
        # Determine consistency based on variance
        cv = (variance ** 0.5) / mean_wc if mean_wc > 0 else 0  # Coefficient of variation
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
    """Detect if dialogue is likely coding assistance."""
    
    ANNOTATION_TYPE = 'tag'
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