# llm_archive/annotators/message.py
"""Message-level text annotators.

These annotators analyze message text content to detect features like:
- Code patterns (blocks, function definitions, imports)
- Mathematical notation (LaTeX)
- Wiki links
- Continuation signals
"""

import re

from llm_archive.annotators.base import (
    MessageTextAnnotator,
    MessageTextData,
    AnnotationResult,
)


# ============================================================
# Code Detection Annotators
# Strategy hierarchy for ANNOTATION_KEY='code':
#   CodeBlockAnnotator (priority 90) - Explicit ``` blocks
#   ScriptHeaderAnnotator (priority 85) - Shebangs, #include
#   CodeStructureAnnotator (priority 70) - Function/class patterns
#   FunctionDefinitionAnnotator (priority 50) - Keyword detection
#   ImportStatementAnnotator (priority 50) - Import keywords
#   CodeKeywordDensityAnnotator (priority 30) - Keyword density
# ============================================================

class CodeBlockAnnotator(MessageTextAnnotator):
    """Detect explicit code blocks (```) in messages.
    
    Highest priority code detector - explicit markdown code blocks
    are the most reliable signal.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'code'
    PRIORITY = 90
    VERSION = '1.1'
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


class ScriptHeaderAnnotator(MessageTextAnnotator):
    """Detect script headers and system includes (strong code evidence).
    
    High priority - shebangs and #include are unambiguous code markers.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'code'
    PRIORITY = 85
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


class CodeStructureAnnotator(MessageTextAnnotator):
    """Detect actual code structure patterns (syntax combinations).
    
    Medium-high priority - structural patterns are fairly reliable.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'code'
    PRIORITY = 70
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


class FunctionDefinitionAnnotator(MessageTextAnnotator):
    """Detect function/class definition keywords.
    
    Medium priority - keywords alone can produce false positives
    in technical articles.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'code'
    PRIORITY = 50
    VERSION = '1.0'
    ROLE_FILTER = None
    
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
    """Detect import/require/include statements.
    
    Medium priority - import statements are fairly reliable but
    can appear in technical discussions.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'code'
    PRIORITY = 50
    VERSION = '1.0'
    ROLE_FILTER = None
    
    PATTERNS = [
        re.compile(r'^import\s+\w', re.MULTILINE),          # Python, Java, ES6
        re.compile(r'^from\s+\w+\s+import', re.MULTILINE),  # Python
        re.compile(r'require\s*\('),                         # Node.js, CommonJS
        re.compile(r'^using\s+\w', re.MULTILINE),           # C#
        re.compile(r'^#include\s*[<"]', re.MULTILINE),      # C/C++
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


class CodeKeywordDensityAnnotator(MessageTextAnnotator):
    """Detect high density of programming keywords in substantial text.
    
    Low priority - keyword density is the weakest signal and
    most prone to false positives.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'code'
    PRIORITY = 30
    VERSION = '1.0'
    ROLE_FILTER = None
    
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
            density = keyword_count / (len(data.text) / 1000)
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


# ============================================================
# Other Feature Annotators
# ============================================================

class WikiLinkAnnotator(MessageTextAnnotator):
    """Detect Obsidian-style [[wiki links]] in assistant messages."""
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'wiki_links'
    PRIORITY = 50
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


class LatexAnnotator(MessageTextAnnotator):
    """Detect LaTeX/MathJax mathematical notation in assistant messages."""
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'latex'
    PRIORITY = 50
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
    ANNOTATION_KEY = 'continuation'
    PRIORITY = 50
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


class QuoteElaborateAnnotator(MessageTextAnnotator):
    """Detect quote+elaborate continuation pattern in user messages."""
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'continuation'
    PRIORITY = 60  # Higher than ContinuationAnnotator
    VERSION = '1.0'
    ROLE_FILTER = 'user'
    
    ELABORATE_KEYWORDS = ['elaborate', 'continue', 'expand', 'more', 'explain']
    
    def annotate(self, data: MessageTextData) -> list[AnnotationResult]:
        text = data.text.strip()
        
        if not text.startswith('>'):
            return []
        
        lines = text.split('\n')
        if len(lines) < 2:
            return []
        
        # Check if last non-empty line is an elaborate keyword
        last_line = lines[-1].strip().lower()
        
        for keyword in self.ELABORATE_KEYWORDS:
            if last_line == keyword or last_line.startswith(keyword + ' '):
                return [AnnotationResult(
                    value='quote_elaborate',
                    confidence=1.0,
                    data={'keyword': keyword},
                )]
        
        return []