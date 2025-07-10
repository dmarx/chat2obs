from typing import Any


class Message:
    def __init__(self, data: dict):
        self.data = data
    
    @property
    def content(self):
        return self._get_content()
    
    @property
    def created_date(self):
        return self._get_created_date()
    
    @property
    def author_role(self):
        return self._get_author_role()

    def _get_author_role(self):
        raise NotImplementedError

    def _get_content(self):
        raise NotImplementedError
    
    def _get_created_date(self):
        raise NotImplementedError
    

def get_message_text_chatgpt(message: dict[str, Any]) -> str:
    """Extract text content from a message."""
    content = message.get('content', {})
    text = content.get('text', '')
    parts = content.get('parts', [])
    joined = ' '.join(str(p) for p in parts if isinstance(p, str)).strip()
    if joined:
        text = f"{text} {joined}"
    return text.strip()


class MessageOpenAI(Message):
    def _get_content(self):
        return get_message_text_chatgpt(self.data)
    def _get_created_date(self):
        return self.data.get('create_time', 0.0)
    def _get_author_role(self):
        return self.data.get('author', {}).get('role')

def is_oai_msg(msg):
    return True

def msg_factory(msg):
    if is_oai_msg(msg):
        return MessageOpenAI(data=msg)
    else:
        raise NotImplementedError