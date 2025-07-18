"""
Generates Obsidian notes from a conversation.
"""
from typing import List, Dict, Any
from .conversation import Conversation
from .exchange import Exchange
from .message import Message

# Generate Obsidian notes from a conversation using jinja template from templates/article.md.jinja
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2 import Template

from loguru import logger


def load_template(template_name: str) -> Template:
    """Load a Jinja template from the templates directory."""
    templates_dir = Path(__file__).parent.parent / 'templates'
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(['html', 'xml'])
    )
    return env.get_template(template_name)

# before generating the notes, we need to infer some attributes, specifically
# - the title for the preceding note
# - the date of the conversation
# - the title of the proceding note
# notes will generally correspond to a single exchange, so we will generate one note per exchange
# thte title will be associated as an annotation on the exchange
# teh date is an attribute on the exchange object, or the first message in the exchange
# output filename will be the title of the exchange, with spaces replaced by underscores and .md extension
def generate_notes(conversation: Conversation, template_name: str = 'article.md.jinja') -> List[str]:
    """Generate Obsidian notes from a conversation."""
    template = load_template(template_name)
    notes = []

    # need to infer the previous and next note titles before we can generate the notes
    # this is done by iterating through the exchanges and using the annotations
    # we will use the first message's created_date as the date of the exchange
    # and the title from the exchange annotations, or a default title if not present    
    # START BY ASSIGNING DEFAULT TITLES AND FILENAMES SO WE CAN REFER TO THEM WHEN WE NEED THE PREVIOUS AND NEXT TITLES
    for exchange in conversation.exchanges:
        date = exchange.messages[0].created_date if exchange.messages else None
        #title = exchange.annotations.get('title', f'Exchange {exchange.exchange_id}')
        title = exchange.annotations.get('title')
        if not title:
            # If no title is set, use the first user message as the title
            user_messages = exchange.get_user_messages()
            if user_messages:
                title = user_messages[0].content.split('\n')[0]
                if title.startswith('>'):  # Remove blockquote if present
                    title = title[1:].strip()
                
        #output_filename = f"{title.replace(' ', '_')}.md"
        # need to actually sanitize the title to make it a valid filename
        output_filename = f"{title.replace(' ', '_').replace('/', '_').replace('\\', '_').replace(':', '_')[:200]}.md"
        logger.info(f"output_filename: {output_filename}")
        exchange.annotations['output_filename'] = output_filename
        exchange.annotations['date'] = date
        exchange.annotations['title'] = title
        notes.append((exchange, output_filename))       

    # NOW ASSOCIATE PREVIOUS AND NEXT TITLES
    for i, (exchange, output_filename) in enumerate(notes):
        # Set previous title if not the first exchange
        if i > 0:
            previous_exchange = notes[i - 1][0]
            exchange.annotations['previous_title'] = previous_exchange.annotations['title']
            exchange.annotations['previous_filename'] = previous_exchange.annotations['output_filename']
        else:
            exchange.annotations['previous_title'] = None
            exchange.annotations['previous_filename'] = None
        
        # Set next title if not the last exchange
        if i < len(notes) - 1:
            next_exchange = notes[i + 1][0]
            exchange.annotations['next_title'] = next_exchange.annotations['title']
            exchange.annotations['next_filename'] = next_exchange.annotations['output_filename']
        else:
            exchange.annotations['next_title'] = None
            exchange.annotations['next_filename'] = None

    # NOW GENERATE THE NOTES
    for exchange, output_filename in notes: 
        content = template.render(page=exchange)
        with open(output_filename, 'w') as f:
            f.write(content)