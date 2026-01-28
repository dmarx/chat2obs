from typing import Any
# from datetime import datetime


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

    @property
    def id(self):
        return self._get_id()

    def _get_id(self):
        raise NotImplementedError

    def _get_author_role(self):
        raise NotImplementedError

    def _get_content(self):
        raise NotImplementedError
    
    def _get_created_date(self):
        raise NotImplementedError
    def __repr__(self):
        #return f"Message(author_role={self.author_role}, content={self.content}, created_date={self.created_date})"
        return f"\n{self.created_date} - {self.author_role.upper()}: {self.content[:200].strip()+'...' if len(self.content) > 200 else self.content.strip()}"
    def __str__(self):
        return f"\n{self.created_date} - {self.author_role.upper()}: {self.content.strip()}"


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
    def _get_id(self):
        return self.data.get('id')
    def _get_content(self):
        return get_message_text_chatgpt(self.data)
    def _get_created_date(self):
        return self.data.get('create_time', 0.0)
    def _get_author_role(self):
        return self.data.get('author', {}).get('role')


class MessageClaude(Message):
    def _get_id(self):
        return self.data.get('uuid')
    def _get_content(self):
        return self.data.get('text', '')
    
    def _get_created_date(self):
        # Claude uses ISO format: "2024-01-01T12:00:00Z"
        created_at = self.data.get('created_at')
        # if created_at:
        #     return datetime.fromisoformat(created_at.replace('Z', '+00:00')).timestamp()
        # return 0.0
        return created_at
    
    def _get_author_role(self):
        sender = self.data.get('sender')
        if sender == 'human':
            sender = 'user'
        return sender

# def is_oai_msg(msg):
#     #return True
#     return isinstance(msg, dict) and 'content' in msg and 'create_time' in msg and 'author' in msg

# def is_anthropic_msg(msg):
#     return isinstance(msg, dict) and 'text' in msg and 'created_at' in msg and 'author' in msg

# def msg_factory(msg):
#     if is_oai_msg(msg):
#         return MessageOpenAI(data=msg)
#     else:
#         raise NotImplementedError