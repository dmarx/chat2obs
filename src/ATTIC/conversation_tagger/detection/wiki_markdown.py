# conversation_tagger/detection/wiki_markdown.py
"""
Wiki and documentation specific detection functions.
"""

from typing import Dict, Any

from .helpers import get_all_text_from_message


def has_wiki_links(conversation: Dict[str, Any]) -> bool:
    """Check for Obsidian-style wiki links [[link text]]."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        
        # Look for wiki-style links [[...]]
        if '[[' in all_text and ']]' in all_text:
            return True
    
    return False


def has_latex_math(conversation: Dict[str, Any]) -> bool:
    """Check for LaTeX/MathJax mathematical formulas."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        
        # Look for various LaTeX/MathJax patterns
        math_indicators = [
            # Inline math: $formula$
            ('$' in all_text and all_text.count('$') >= 2),
            # Block math: $$formula$$
            '$$' in all_text,
            # LaTeX-style: \(formula\) or \[formula\]
            ('\\(' in all_text and '\\)' in all_text),
            ('\\[' in all_text and '\\]' in all_text),
            # Common LaTeX commands
            any(cmd in all_text for cmd in ['\\frac', '\\sum', '\\int', '\\sqrt', '\\alpha', '\\beta', '\\gamma', '\\theta', '\\pi', '\\sigma', '\\infty', '\\partial', '\\nabla']),
        ]
        
        if any(math_indicators):
            return True
    
    return False


def has_markdown_features(conversation: Dict[str, Any]) -> bool:
    """Check for distinctive markdown features beyond basic formatting."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        
        # Look for markdown features that suggest documentation/wiki content
        markdown_indicators = [
            # Tables (| syntax)
            ('|' in all_text and all_text.count('|') >= 4),
            # Multiple headings (##, ###, etc.)
            (all_text.count('#') >= 3 and '\n#' in all_text),
            # Task lists
            ('- [ ]' in all_text or '- [x]' in all_text),
            # Footnotes
            ('[^' in all_text and ']' in all_text),
            # Multiple links [text](url)
            (all_text.count('[') >= 3 and all_text.count('](') >= 2),
        ]
        
        if any(markdown_indicators):
            return True
    
    return False


def has_documentation_patterns(conversation: Dict[str, Any]) -> bool:
    """Check for patterns typical of documentation or academic writing."""
    mapping = conversation.get('mapping', {})
    
    for node_id, node in mapping.items():
        message = node.get('message')
        if not message:
            continue
        
        all_text = get_all_text_from_message(message)
        
        # Only check substantial text
        if len(all_text) <= 500:
            continue
        
        # Look for documentation/academic language patterns
        doc_keywords = [
            'according to', 'furthermore', 'however', 'therefore', 'moreover', 
            'in conclusion', 'for example', 'such as', 'note that', 'it should be noted',
            'definition', 'theorem', 'proof', 'lemma', 'corollary', 'proposition',
            'see also', 'references', 'bibliography', 'citation', 'figure', 'table',
            'algorithm', 'procedure', 'methodology', 'approach', 'framework'
        ]
        
        keyword_count = sum(1 for keyword in doc_keywords if keyword in all_text.lower())
        
        # High threshold - need multiple academic/documentation indicators
        if keyword_count >= 3:
            return True
    
    return False