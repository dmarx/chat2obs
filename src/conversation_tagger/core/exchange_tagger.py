# src/conversation_tagger/core/exchange_tagger.py
"""
Tag individual exchanges using the improved exchange structure.
"""
import re
from typing import Dict, Any, List, Callable
from collections import defaultdict
from .tag import Tag
from .exchange import Exchange, get_message_text


# we generalize this into a Tagger(ABC) which 
# we can use to tag both exchanges and conversations
## rule adding is the same API
## tagging is the same API
### ... maybe rather than an ExchangeTagger, we have a Tagger that can tag both Exchanges and Conversations
class ExchangeTagger:
    """Tags exchanges with configurable rules."""
    
    def __init__(self):
        self.rules: Dict[str, Callable] = {}
    
    def add_rule(self, tag_name: str, rule_function: Callable):
        """Add rule for exchanges."""
        self.rules[tag_name] = rule_function
    
    def tag_exchange(self, exchange: Exchange) -> Exchange:
        """Tag a single exchange and return the updated exchange."""
        tags = exchange.tags or []
        
        for tag_name, rule_func in self.rules.items():
            try:
                result = rule_func(exchange)
                if result:
                    if isinstance(result, bool):
                        tags.append(Tag(tag_name))
                    elif isinstance(result, Tag):
                        tags.append(result)
                    else:
                        tags.append(Tag(tag_name))
            except Exception as e:
                # Skip failed rules silently for now
                pass
        
        # Update the exchange's tags
        exchange.tags = tags
        return exchange

######################
#   Exchange Rules   #
######################

# todo: could extract wikilinks into an annotation.
def has_wiki_links(exchange: Exchange) -> bool:
    """Check for Obsidian-style wiki links [[link text]]."""
    text = exchange.get_assistant_text()
    return bool(re.search(r'\[\[.+?\]\]', text))

def has_latex_math(exchange: Exchange) -> bool:
    """Check for LaTeX/MathJax mathematical formulas."""
    text = ' '.join(exchange.get_assistant_texts())
    math_indicators = [
        re.search(r'\$\$.+?\$\$', text) is not None,
        re.search(r'\\\((.+?)\\\)', text) is not None,
        re.search(r'\\\[(.+?)\\\]', text) is not None,
        # Common LaTeX commands
        any(cmd in text for cmd in ['\\frac', '\\sum', '\\int', '\\sqrt', '\\alpha', '\\beta', '\\gamma', '\\theta', '\\pi', '\\sigma', '\\infty', '\\partial', '\\nabla']),
    ]
    
    return any(math_indicators)

### User's first message rules ###

def get_first_user_message(exchange: Exchange) -> Dict[str, Any]:
    """Get the first user message from an exchange."""
    user_messages = exchange.get_user_messages()
    if not user_messages:
        return {}
    return user_messages[0]


def first_user_has_large_content(exchange: Exchange, min_length: int = 2000) -> bool:
    """Check if the first user message has large content."""
    first_message = get_first_user_message(exchange)
    if not first_message:
        return False
    first_message_text = get_message_text(first_message)
    return len(first_message_text) > min_length


def first_user_has_code_patterns(conversation: Dict[str, Any]) -> bool:
    """Check if the first user message contains code patterns."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    first_message_text = get_message_text(first_message)
    
    # Strong code indicators
    code_indicators = [
        '```',  # Code blocks
        'def ', 'function ', 'class ',  # Definitions
        'import ', 'from ', 'require(',  # Imports
        '#!/bin/', '#include',  # Script headers
    ]
    
    return any(indicator in first_message_text for indicator in code_indicators)


def first_user_has_attachments(conversation: Dict[str, Any]) -> bool:
    """Check if the first user message has attachments."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    
    metadata = first_message.get('metadata', {})
    attachments = metadata.get('attachments', [])
    return len(attachments) > 0


def first_user_has_code_attachments(conversation: Dict[str, Any]) -> bool:
    """Check if the first user message has code-related attachments."""
    first_message = get_first_user_message(conversation)
    if not first_message:
        return False
    
    metadata = first_message.get('metadata', {})
    attachments = metadata.get('attachments', [])
    
    for attachment in attachments:
        mime_type = attachment.get('mime_type', '').lower()
        name = attachment.get('name', '').lower()
        
        # Check for code file extensions
        code_extensions = ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs', '.ts', '.jsx', '.tsx', '.sql', '.sh', '.rb', '.php']
        if any(ext in name for ext in code_extensions):
            return True
            
        # Check for code-related MIME types
        code_mimes = ['text/x-python', 'text/x-java', 'application/javascript', 'text/x-script']
        if any(mime in mime_type for mime in code_mimes):
            return True
    
    return False

DEFAULT_EXCHANGE_RULES = {
    'has_wiki_links': has_wiki_links,
    'has_latex_math': has_latex_math,
    'first_user_has_large_content': first_user_has_large_content,
    'first_user_has_code_patterns': first_user_has_code_patterns,
    'first_user_has_attachments': first_user_has_attachments,
    'first_user_has_code_attachments': first_user_has_code_attachments,
}
