# llm_archive/annotators/features.py
"""Feature detection annotators."""

import re
from uuid import UUID

from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import Message, ContentPart, Exchange, ExchangeContent
from llm_archive.annotators.base import Annotator


class WikiLinkAnnotator(Annotator):
    """Detect Obsidian-style [[wiki links]] in content."""
    
    ANNOTATION_TYPE = 'feature'
    ENTITY_TYPE = 'message'
    SOURCE = 'heuristic'
    VERSION = '1.0'
    
    PATTERN = re.compile(r'\[\[.+?\]\]')
    
    def compute(self) -> int:
        """Find messages with wiki links."""
        cursor = self.get_cursor()
        
        # Base query
        query = (
            self.session.query(
                ContentPart.message_id, 
                ContentPart.text_content,
                Message.created_at,
            )
            .join(Message)
            .filter(Message.role == 'assistant')
            .filter(Message.deleted_at.is_(None))
            .filter(ContentPart.part_type == 'text')
            .filter(ContentPart.text_content.isnot(None))
        )
        
        # Apply cursor filter
        if cursor:
            query = query.filter(Message.created_at > cursor)
        
        results = query.all()
        
        # Group by message
        message_data: dict[UUID, dict] = {}
        for msg_id, text, created_at in results:
            if msg_id not in message_data:
                message_data[msg_id] = {'texts': [], 'created_at': created_at}
            message_data[msg_id]['texts'].append(text)
        
        count = 0
        for msg_id, data in message_data.items():
            self.track_entity(data['created_at'])
            full_text = '\n'.join(data['texts'])
            
            if self.PATTERN.search(full_text):
                links = self.PATTERN.findall(full_text)
                if self.add_annotation(
                    entity_id=msg_id,
                    value='has_wiki_links',
                    confidence=1.0,
                    data={'count': len(links)},
                ):
                    count += 1
        
        self.finalize_cursor()
        return count


class CodeBlockAnnotator(Annotator):
    """Detect code blocks (```) in content."""
    
    ANNOTATION_TYPE = 'feature'
    ENTITY_TYPE = 'message'
    SOURCE = 'heuristic'
    VERSION = '1.0'
    
    PATTERN = re.compile(r'```(\w*)\n')
    
    def compute(self) -> int:
        """Find messages with code blocks."""
        cursor = self.get_cursor()
        
        query = (
            self.session.query(
                ContentPart.message_id, 
                ContentPart.text_content,
                Message.created_at,
            )
            .join(Message)
            .filter(Message.deleted_at.is_(None))
            .filter(ContentPart.part_type == 'text')
            .filter(ContentPart.text_content.isnot(None))
        )
        
        if cursor:
            query = query.filter(Message.created_at > cursor)
        
        results = query.all()
        
        message_data: dict[UUID, dict] = {}
        for msg_id, text, created_at in results:
            if msg_id not in message_data:
                message_data[msg_id] = {'texts': [], 'created_at': created_at}
            message_data[msg_id]['texts'].append(text)
        
        count = 0
        for msg_id, data in message_data.items():
            self.track_entity(data['created_at'])
            full_text = '\n'.join(data['texts'])
            
            if '```' in full_text:
                languages = self.PATTERN.findall(full_text)
                languages = [l for l in languages if l]
                
                if self.add_annotation(
                    entity_id=msg_id,
                    value='has_code_blocks',
                    confidence=1.0,
                    data={
                        'count': full_text.count('```') // 2,
                        'languages': list(set(languages)),
                    },
                ):
                    count += 1
                
                # Also add language-specific tags
                for lang in set(languages):
                    self.add_annotation(
                        entity_id=msg_id,
                        value=lang,
                        key='code_language',
                        confidence=1.0,
                    )
        
        self.finalize_cursor()
        return count


class LatexAnnotator(Annotator):
    """Detect LaTeX/MathJax mathematical notation."""
    
    ANNOTATION_TYPE = 'feature'
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
        cursor = self.get_cursor()
        
        query = (
            self.session.query(
                ContentPart.message_id, 
                ContentPart.text_content,
                Message.created_at,
            )
            .join(Message)
            .filter(Message.role == 'assistant')
            .filter(Message.deleted_at.is_(None))
            .filter(ContentPart.part_type == 'text')
            .filter(ContentPart.text_content.isnot(None))
        )
        
        if cursor:
            query = query.filter(Message.created_at > cursor)
        
        results = query.all()
        
        message_data: dict[UUID, dict] = {}
        for msg_id, text, created_at in results:
            if msg_id not in message_data:
                message_data[msg_id] = {'texts': [], 'created_at': created_at}
            message_data[msg_id]['texts'].append(text)
        
        count = 0
        for msg_id, data in message_data.items():
            self.track_entity(data['created_at'])
            full_text = '\n'.join(data['texts'])
            
            has_latex = False
            found_commands = []
            
            for pattern in self.PATTERNS:
                if pattern.search(full_text):
                    has_latex = True
                    break
            
            for cmd in self.COMMANDS:
                if cmd in full_text:
                    has_latex = True
                    found_commands.append(cmd)
            
            if has_latex:
                if self.add_annotation(
                    entity_id=msg_id,
                    value='has_latex',
                    confidence=1.0,
                    data={'commands': found_commands[:10]},
                ):
                    count += 1
        
        self.finalize_cursor()
        return count


class ContinuationAnnotator(Annotator):
    """Detect continuation signals in user messages."""
    
    ANNOTATION_TYPE = 'feature'
    ENTITY_TYPE = 'message'
    SOURCE = 'heuristic'
    VERSION = '1.0'
    
    PATTERNS = {
        'continue': ['continue', 'keep going', 'go on', 'carry on'],
        'elaborate': ['elaborate', 'expand', 'tell me more', 'more details'],
        'finish': ['finish', 'complete', 'wrap up'],
        'next': ['next', 'what else', 'and then'],
    }
    
    def compute(self) -> int:
        """Find user messages that are continuation signals."""
        cursor = self.get_cursor()
        
        query = (
            self.session.query(Message.id, ContentPart.text_content, Message.created_at)
            .join(ContentPart)
            .filter(Message.role == 'user')
            .filter(Message.deleted_at.is_(None))
            .filter(ContentPart.part_type == 'text')
            .filter(ContentPart.text_content.isnot(None))
        )
        
        if cursor:
            query = query.filter(Message.created_at > cursor)
        
        results = query.all()
        
        message_data: dict[UUID, dict] = {}
        for msg_id, text, created_at in results:
            if msg_id not in message_data:
                message_data[msg_id] = {'texts': [], 'created_at': created_at}
            message_data[msg_id]['texts'].append(text)
        
        count = 0
        for msg_id, data in message_data.items():
            self.track_entity(data['created_at'])
            full_text = '\n'.join(data['texts']).strip().lower()
            
            if len(full_text.split()) > 10:
                continue
            
            # Check quote+elaborate pattern
            if full_text.startswith('>'):
                lines = full_text.split('\n')
                last_line = lines[-1].strip()
                if last_line in ('elaborate', 'continue', 'expand', 'more'):
                    if self.add_annotation(
                        entity_id=msg_id,
                        value='continuation_signal',
                        key='quote_elaborate',
                        confidence=1.0,
                    ):
                        count += 1
                    continue
            
            # Check keyword patterns
            for pattern_name, keywords in self.PATTERNS.items():
                matched = False
                for keyword in keywords:
                    if full_text == keyword or full_text.startswith(keyword + ' '):
                        if self.add_annotation(
                            entity_id=msg_id,
                            value='continuation_signal',
                            key=pattern_name,
                            confidence=0.9,
                            data={'matched': keyword},
                        ):
                            count += 1
                        matched = True
                        break
                if matched:
                    break
        
        self.finalize_cursor()
        return count


class ExchangeTypeAnnotator(Annotator):
    """Classify exchange types based on content patterns."""
    
    ANNOTATION_TYPE = 'tag'
    ENTITY_TYPE = 'exchange'
    SOURCE = 'heuristic'
    VERSION = '1.0'
    
    def compute(self) -> int:
        """Classify exchanges."""
        cursor = self.get_cursor()
        
        query = (
            self.session.query(Exchange, ExchangeContent)
            .join(ExchangeContent)
        )
        
        if cursor:
            query = query.filter(Exchange.computed_at > cursor)
        
        exchanges = query.all()
        
        count = 0
        for exchange, content in exchanges:
            self.track_entity(exchange.computed_at)
            exchange_type, confidence = self._classify(content)
            
            if exchange_type:
                if self.add_annotation(
                    entity_id=exchange.id,
                    value=exchange_type,
                    key='exchange_type',
                    confidence=confidence,
                ):
                    count += 1
        
        self.finalize_cursor()
        return count
    
    def _classify(self, content: ExchangeContent) -> tuple[str | None, float]:
        """Classify an exchange based on content."""
        user_text = content.user_text or ''
        assistant_text = content.assistant_text or ''
        
        code_blocks = assistant_text.count('```')
        if code_blocks >= 2:
            return 'coding', 0.8
        
        if '[[' in assistant_text and ']]' in assistant_text:
            return 'wiki_article', 0.9
        
        if (content.user_word_count or 0) < 50 and (content.assistant_word_count or 0) > 200:
            return 'qa', 0.6
        
        if (content.assistant_word_count or 0) > 500:
            if assistant_text.startswith('#') or assistant_text.startswith('**'):
                return 'article', 0.7
            return 'generation', 0.5
        
        return 'discussion', 0.4