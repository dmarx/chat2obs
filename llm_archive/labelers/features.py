# llm_archive/labelers/features.py
"""Feature detection labelers."""

import re
from uuid import UUID

from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import (
    Message, ContentPart, Exchange, ExchangeContent,
)
from llm_archive.labelers.base import Labeler


class WikiLinkLabeler(Labeler):
    """Detect Obsidian-style [[wiki links]] in content."""
    
    LABEL_TYPE = 'feature'
    ENTITY_TYPE = 'message'
    SOURCE = 'heuristic'
    VERSION = '1.0'
    
    PATTERN = re.compile(r'\[\[.+?\]\]')
    
    def compute(self) -> int:
        """Find messages with wiki links."""
        # Query assistant messages with text content
        results = (
            self.session.query(ContentPart.message_id, ContentPart.text_content)
            .join(Message)
            .filter(Message.role == 'assistant')
            .filter(ContentPart.part_type == 'text')
            .filter(ContentPart.text_content.isnot(None))
            .all()
        )
        
        # Group by message
        message_texts: dict[UUID, list[str]] = {}
        for msg_id, text in results:
            if msg_id not in message_texts:
                message_texts[msg_id] = []
            message_texts[msg_id].append(text)
        
        count = 0
        for msg_id, texts in message_texts.items():
            full_text = '\n'.join(texts)
            
            if self.PATTERN.search(full_text):
                # Count links
                links = self.PATTERN.findall(full_text)
                if self.add_label(
                    entity_id=msg_id,
                    label_value='has_wiki_links',
                    confidence=1.0,
                    label_data={'count': len(links)},
                ):
                    count += 1
        
        return count


class CodeBlockLabeler(Labeler):
    """Detect code blocks (```) in content."""
    
    LABEL_TYPE = 'feature'
    ENTITY_TYPE = 'message'
    SOURCE = 'heuristic'
    VERSION = '1.0'
    
    # Match ``` with optional language
    PATTERN = re.compile(r'```(\w*)\n')
    
    def compute(self) -> int:
        """Find messages with code blocks."""
        results = (
            self.session.query(ContentPart.message_id, ContentPart.text_content)
            .filter(ContentPart.part_type == 'text')
            .filter(ContentPart.text_content.isnot(None))
            .all()
        )
        
        message_texts: dict[UUID, list[str]] = {}
        for msg_id, text in results:
            if msg_id not in message_texts:
                message_texts[msg_id] = []
            message_texts[msg_id].append(text)
        
        count = 0
        for msg_id, texts in message_texts.items():
            full_text = '\n'.join(texts)
            
            if '```' in full_text:
                # Detect languages
                languages = self.PATTERN.findall(full_text)
                languages = [l for l in languages if l]  # Filter empty
                
                if self.add_label(
                    entity_id=msg_id,
                    label_value='has_code_blocks',
                    confidence=1.0,
                    label_data={
                        'count': full_text.count('```') // 2,
                        'languages': list(set(languages)),
                    },
                ):
                    count += 1
        
        return count


class LatexLabeler(Labeler):
    """Detect LaTeX/MathJax mathematical notation."""
    
    LABEL_TYPE = 'feature'
    ENTITY_TYPE = 'message'
    SOURCE = 'heuristic'
    VERSION = '1.0'
    
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
    
    def compute(self) -> int:
        """Find messages with LaTeX content."""
        results = (
            self.session.query(ContentPart.message_id, ContentPart.text_content)
            .join(Message)
            .filter(Message.role == 'assistant')
            .filter(ContentPart.part_type == 'text')
            .filter(ContentPart.text_content.isnot(None))
            .all()
        )
        
        message_texts: dict[UUID, list[str]] = {}
        for msg_id, text in results:
            if msg_id not in message_texts:
                message_texts[msg_id] = []
            message_texts[msg_id].append(text)
        
        count = 0
        for msg_id, texts in message_texts.items():
            full_text = '\n'.join(texts)
            
            has_latex = False
            matched_patterns = []
            
            # Check patterns
            for pattern in self.PATTERNS:
                if pattern.search(full_text):
                    has_latex = True
                    matched_patterns.append(pattern.pattern[:20])
            
            # Check commands
            found_commands = []
            for cmd in self.COMMANDS:
                if cmd in full_text:
                    has_latex = True
                    found_commands.append(cmd)
            
            if has_latex:
                if self.add_label(
                    entity_id=msg_id,
                    label_value='has_latex',
                    confidence=1.0,
                    label_data={
                        'commands': found_commands[:10],  # Limit
                    },
                ):
                    count += 1
        
        return count


class ContinuationLabeler(Labeler):
    """Detect continuation signals in user messages."""
    
    LABEL_TYPE = 'continuation_signal'
    ENTITY_TYPE = 'message'
    SOURCE = 'heuristic'
    VERSION = '1.0'
    
    PATTERNS = [
        ('continue', ['continue', 'keep going', 'go on', 'carry on']),
        ('elaborate', ['elaborate', 'expand', 'tell me more', 'more details']),
        ('finish', ['finish', 'complete', 'wrap up']),
        ('next', ['next', 'what else', 'and then']),
        ('quote_elaborate', None),  # Special handling
    ]
    
    def compute(self) -> int:
        """Find user messages that are continuation signals."""
        results = (
            self.session.query(Message.id, ContentPart.text_content)
            .join(ContentPart)
            .filter(Message.role == 'user')
            .filter(ContentPart.part_type == 'text')
            .filter(ContentPart.text_content.isnot(None))
            .all()
        )
        
        message_texts: dict[UUID, list[str]] = {}
        for msg_id, text in results:
            if msg_id not in message_texts:
                message_texts[msg_id] = []
            message_texts[msg_id].append(text)
        
        count = 0
        for msg_id, texts in message_texts.items():
            full_text = '\n'.join(texts).strip().lower()
            
            # Skip long messages
            if len(full_text.split()) > 10:
                continue
            
            # Check quote+elaborate pattern
            if full_text.startswith('>'):
                lines = full_text.split('\n')
                last_line = lines[-1].strip()
                if last_line in ('elaborate', 'continue', 'expand', 'more'):
                    if self.add_label(
                        entity_id=msg_id,
                        label_value='quote_elaborate',
                        confidence=1.0,
                    ):
                        count += 1
                    continue
            
            # Check keyword patterns
            for pattern_name, keywords in self.PATTERNS:
                if keywords is None:
                    continue
                
                for keyword in keywords:
                    if full_text == keyword or full_text.startswith(keyword + ' '):
                        if self.add_label(
                            entity_id=msg_id,
                            label_value=pattern_name,
                            confidence=0.9,
                            label_data={'matched': keyword},
                        ):
                            count += 1
                        break
        
        return count


class ExchangeTypeLabeler(Labeler):
    """Classify exchange types based on content patterns."""
    
    LABEL_TYPE = 'exchange_type'
    ENTITY_TYPE = 'exchange'
    SOURCE = 'heuristic'
    VERSION = '1.0'
    
    def compute(self) -> int:
        """Classify exchanges."""
        exchanges = (
            self.session.query(Exchange, ExchangeContent)
            .join(ExchangeContent)
            .all()
        )
        
        count = 0
        for exchange, content in exchanges:
            exchange_type, confidence = self._classify(content)
            
            if exchange_type:
                if self.add_label(
                    entity_id=exchange.id,
                    label_value=exchange_type,
                    confidence=confidence,
                ):
                    count += 1
        
        return count
    
    def _classify(self, content: ExchangeContent) -> tuple[str | None, float]:
        """Classify an exchange based on content."""
        user_text = content.user_text or ''
        assistant_text = content.assistant_text or ''
        
        # Check for code-heavy exchanges
        code_blocks = assistant_text.count('```')
        if code_blocks >= 2:
            return 'coding', 0.8
        
        # Check for wiki-style content
        if '[[' in assistant_text and ']]' in assistant_text:
            return 'wiki_article', 0.9
        
        # Check for Q&A pattern (short question, longer answer)
        if (content.user_word_count or 0) < 50 and (content.assistant_word_count or 0) > 200:
            return 'qa', 0.6
        
        # Check for long-form generation
        if (content.assistant_word_count or 0) > 500:
            # Look for article indicators
            if assistant_text.startswith('#') or assistant_text.startswith('**'):
                return 'article', 0.7
            return 'generation', 0.5
        
        # Default to discussion
        return 'discussion', 0.4