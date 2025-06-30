# src/conversation_tagger/core/exchange_tagger.py
"""
Tag individual exchanges using the improved exchange structure.
"""
import re
from typing import Dict, Any, List, Callable
from collections import defaultdict
from .tag import Tag
from .exchange import Exchange


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

### Exchange Rules ###

# todo: could extract wikilinks into an annotation.
def has_wiki_links(exchange: Exchange) -> bool:
    """Check for Obsidian-style wiki links [[link text]]."""
    text = exchange.get_assistant_text()
    #return ('[[' in text) and (']]' in text)
    return bool(re.search(r'\[\[.+?\]\]', text))

def has_latex_math(exchange: Exchange) -> bool:
    """Check for LaTeX/MathJax mathematical formulas."""
    text = exchange.get_assistant_text()
    
    # Look for various LaTeX/MathJax patterns
    # these would probably be better as regexes.
    math_indicators = [
        re.search(r'\$\$.+?\$\$', text) is not None,
        re.search(r'\\\((.+?)\\\)', text) is not None,
        re.search(r'\\\[(.+?)\\\]', text) is not None,
        # Common LaTeX commands
        any(cmd in text for cmd in ['\\frac', '\\sum', '\\int', '\\sqrt', '\\alpha', '\\beta', '\\gamma', '\\theta', '\\pi', '\\sigma', '\\infty', '\\partial', '\\nabla']),
    ]
    
    return any(math_indicators)

DEFAULT_EXCHANGE_RULES = {
    'has_wiki_links': has_wiki_links,
    'has_latex_math': has_latex_math,
}