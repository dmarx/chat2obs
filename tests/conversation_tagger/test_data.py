# tests/conversation_tagger/test_data.py
"""
Centralized test data definitions for consistent reuse across tests.
"""

def get_simple_conversation_data():
    """Basic conversation data for both sources."""
    oai_data = {
        'conversation_id': 'simple_oai',
        'title': 'Simple ChatGPT',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1700000000.0,
                    'content': {'text': 'Hello world'},
                    'metadata': {}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 1700000001.0,
                    'content': {'text': 'Hi there!'},
                    'metadata': {}
                }
            }
        }
    }
    
    claude_data = {
        'uuid': 'simple-claude',
        'name': 'Simple Claude',
        'created_at': '2024-01-01T12:00:00Z',
        'updated_at': '2024-01-01T12:00:02Z',
        'account': {'uuid': 'account-uuid'},
        'chat_messages': [
            {
                'uuid': 'msg1-uuid',
                'text': 'Hello world',
                'sender': 'user',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'content': [{'type': 'text', 'text': 'Hello world'}],
                'attachments': [],
                'files': []
            },
            {
                'uuid': 'msg2-uuid',
                'text': 'Hi there!',
                'sender': 'assistant',
                'created_at': '2024-01-01T12:00:01Z',
                'updated_at': '2024-01-01T12:00:01Z',
                'content': [{'type': 'text', 'text': 'Hi there!'}],
                'attachments': [],
                'files': []
            }
        ]
    }
    
    return oai_data, claude_data

def get_code_conversation_data():
    """Code conversation data for both sources."""
    oai_data = {
        'conversation_id': 'code_oai',
        'title': 'Code Help - ChatGPT',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1700000000.0,
                    'content': {'text': 'Help me fix this code:\n```python\ndef hello():\n    print("hello")\n```'},
                    'metadata': {'attachments': []}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 1700000001.0,
                    'content': {'text': 'Here\'s the fix:\n```python\ndef hello():\n    print("Hello, World!")\n```'},
                    'metadata': {}
                }
            }
        }
    }
    
    claude_data = {
        'uuid': 'code-claude',
        'name': 'Code Help - Claude',
        'created_at': '2024-01-01T12:00:00Z',
        'updated_at': '2024-01-01T12:00:02Z',
        'account': {'uuid': 'account-uuid'},
        'chat_messages': [
            {
                'uuid': 'msg1-uuid',
                'text': 'Help me fix this code:\n```python\ndef hello():\n    print("hello")\n```',
                'sender': 'user',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'content': [{'type': 'text', 'text': 'Help me fix this code:\n```python\ndef hello():\n    print("hello")\n```'}],
                'attachments': [],
                'files': []
            },
            {
                'uuid': 'msg2-uuid',
                'text': 'Here\'s the fix:\n```python\ndef hello():\n    print("Hello, World!")\n```',
                'sender': 'assistant',
                'created_at': '2024-01-01T12:00:01Z',
                'updated_at': '2024-01-01T12:00:01Z',
                'content': [{'type': 'text', 'text': 'Here\'s the fix:\n```python\ndef hello():\n    print("Hello, World!")\n```'}],
                'attachments': [],
                'files': []
            }
        ]
    }
    
    return oai_data, claude_data

def get_math_conversation_data():
    """Math conversation data for both sources."""
    oai_data = {
        'conversation_id': 'math_oai',
        'title': 'Math Help - ChatGPT',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1700000000.0,
                    'content': {'text': 'Explain the quadratic formula'},
                    'metadata': {}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 1700000001.0,
                    'content': {'text': 'The quadratic formula is: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$'},
                    'metadata': {}
                }
            }
        }
    }
    
    claude_data = {
        'uuid': 'math-claude',
        'name': 'Math Help - Claude',
        'created_at': '2024-01-01T12:00:00Z',
        'updated_at': '2024-01-01T12:00:02Z',
        'account': {'uuid': 'account-uuid'},
        'chat_messages': [
            {
                'uuid': 'msg1-uuid',
                'text': 'Explain the quadratic formula',
                'sender': 'user',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'content': [{'type': 'text', 'text': 'Explain the quadratic formula'}],
                'attachments': [],
                'files': []
            },
            {
                'uuid': 'msg2-uuid',
                'text': 'The quadratic formula is: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$',
                'sender': 'assistant',
                'created_at': '2024-01-01T12:00:01Z',
                'updated_at': '2024-01-01T12:00:01Z',
                'content': [{'type': 'text', 'text': 'The quadratic formula is: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$'}],
                'attachments': [],
                'files': []
            }
        ]
    }
    
    return oai_data, claude_data

def get_attachment_conversation_data():
    """Attachment conversation data for both sources."""
    oai_data = {
        'conversation_id': 'attach_oai',
        'title': 'File Analysis - ChatGPT',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1700000000.0,
                    'content': {'text': 'Please analyze this Python file'},
                    'metadata': {
                        'attachments': [
                            {'id': 'file1', 'name': 'script.py', 'mime_type': 'text/x-python', 'size': 1024}
                        ]
                    }
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 1700000001.0,
                    'content': {'text': 'I can help analyze your Python script...'},
                    'metadata': {}
                }
            }
        }
    }
    
    claude_data = {
        'uuid': 'attach-claude',
        'name': 'File Analysis - Claude',
        'created_at': '2024-01-01T12:00:00Z',
        'updated_at': '2024-01-01T12:00:02Z',
        'account': {'uuid': 'account-uuid'},
        'chat_messages': [
            {
                'uuid': 'msg1-uuid',
                'text': 'Please analyze this Python file',
                'sender': 'user',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'content': [{'type': 'text', 'text': 'Please analyze this Python file'}],
                'attachments': [
                    {'file_name': 'script.py', 'file_type': 'text/x-python', 'file_size': 1024, 'extracted_content': 'def hello(): pass'}
                ],
                'files': [{'file_name': 'script.py'}]
            },
            {
                'uuid': 'msg2-uuid',
                'text': 'I can help analyze your Python script...',
                'sender': 'assistant',
                'created_at': '2024-01-01T12:00:01Z',
                'updated_at': '2024-01-01T12:00:01Z',
                'content': [{'type': 'text', 'text': 'I can help analyze your Python script...'}],
                'attachments': [],
                'files': []
            }
        ]
    }
    
    return oai_data, claude_data

def get_large_content_conversation_data():
    """Large content conversation data for both sources."""
    large_text = 'x' * 2500  # Over the 2000 char threshold
    
    oai_data = {
        'conversation_id': 'large_oai',
        'title': 'Large Content - ChatGPT',
        'mapping': {
            'msg1': {
                'message': {
                    'author': {'role': 'user'},
                    'create_time': 1700000000.0,
                    'content': {'text': large_text},
                    'metadata': {}
                }
            },
            'msg2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'create_time': 1700000001.0,
                    'content': {'text': 'That\'s a lot of content!'},
                    'metadata': {}
                }
            }
        }
    }
    
    claude_data = {
        'uuid': 'large-claude',
        'name': 'Large Content - Claude',
        'created_at': '2024-01-01T12:00:00Z',
        'updated_at': '2024-01-01T12:00:02Z',
        'account': {'uuid': 'account-uuid'},
        'chat_messages': [
            {
                'uuid': 'msg1-uuid',
                'text': large_text,
                'sender': 'user',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'content': [{'type': 'text', 'text': large_text}],
                'attachments': [],
                'files': []
            },
            {
                'uuid': 'msg2-uuid',
                'text': 'That\'s a lot of content!',
                'sender': 'assistant',
                'created_at': '2024-01-01T12:00:01Z',
                'updated_at': '2024-01-01T12:00:01Z',
                'content': [{'type': 'text', 'text': 'That\'s a lot of content!'}],
                'attachments': [],
                'files': []
            }
        ]
    }
    
    return oai_data, claude_data

# For tests that need to create message objects directly
def create_message_obj(source, sender, text, **kwargs):
    """Helper to create message objects consistently."""
    from conversation_tagger.core.message import MessageOpenAI, MessageClaude
    
    if source == "oai":
        data = {
            'author': {'role': sender},
            'create_time': kwargs.get('create_time', 1700000000.0),
            'content': {'text': text},
            'metadata': kwargs.get('metadata', {})
        }
        return MessageOpenAI(data=data)
    else:
        data = {
            'uuid': kwargs.get('uuid', f'{sender}-{hash(text)}'),
            'text': text,
            'sender': sender,
            'created_at': kwargs.get('created_at', '2024-01-01T12:00:00Z'),
            'updated_at': kwargs.get('updated_at', '2024-01-01T12:00:00Z'),
            'content': [{'type': 'text', 'text': text}],
            'attachments': kwargs.get('attachments', []),
            'files': kwargs.get('files', [])
        }
        return MessageClaude(data=data)