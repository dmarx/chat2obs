# tests/conversation_tagger/test_basic_working_parameterized.py
"""
Updated basic tests using streamlined parameterization approach.
"""

import pytest
from conversation_tagger import create_default_tagger
from conversation_tagger.core.exchange import Exchange
from conversation_tagger.core.exchange_tagger import ExchangeTagger
from conversation_tagger.core.tag import Tag, create_annotation, merge_annotations
from conversation_tagger.core.message import MessageOpenAI, MessageClaude


def get_simple_conversation_data():
    """Return simple conversation data for both sources."""
    oai_data = {
        'conversation_id': 'test_oai',
        'title': 'Test ChatGPT',
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
        'uuid': 'test-claude',
        'name': 'Test Claude',
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


class TestBasicFunctionality:
    """Test basic functionality across both data sources."""
    
    def test_annotation_functionality(self):
        """Test that annotation helpers work correctly."""
        # Simple annotation
        simple = create_annotation('test_annotation', True)
        assert simple == {'test_annotation': True}
        
        # Valued annotation
        valued = create_annotation('count', 42)
        assert valued == {'count': 42}
        
        # Complex annotation
        complex_data = {'type': 'test', 'score': 0.95}
        complex_ann = create_annotation('analysis', complex_data)
        assert complex_ann == {'analysis': complex_data}
        
        # Merge annotations
        merged = merge_annotations(simple, valued, complex_ann)
        assert 'test_annotation' in merged
        assert 'count' in merged
        assert 'analysis' in merged
        assert merged['count'] == 42

    @pytest.mark.parametrize("source,data", [
        ("oai", get_simple_conversation_data()[0]),
        ("claude", get_simple_conversation_data()[1])
    ])
    def test_conversation_parsing_basic(self, source, data):
        """Test basic conversation parsing works for both sources."""
        tagger = create_default_tagger(source=source)
        result = tagger.tag_conversation(data)
        
        # Basic structure checks
        assert result.conversation_id in ['test_oai', 'test-claude']
        assert 'Test' in result.title
        assert result.exchange_count == 1
        assert result.total_message_count == 2
        
        # Text extraction works
        user_text = result.get_all_user_text()
        assistant_text = result.get_all_assistant_text()
        assert 'Hello world' in user_text
        assert 'Hi there!' in assistant_text

    @pytest.mark.parametrize("source,data", [
        ("oai", get_simple_conversation_data()[0]),
        ("claude", get_simple_conversation_data()[1])
    ])
    def test_exchange_annotations(self, source, data):
        """Test exchange annotation handling across sources."""
        tagger = create_default_tagger(source=source)
        
        # Add custom annotation rule
        def greeting_detector(exchange):
            user_texts = exchange.get_user_texts()
            if user_texts:
                text = ' '.join(user_texts).lower()
                if any(greeting in text for greeting in ['hello', 'hi', 'hey']):
                    return {
                        'has_greeting': True,
                        'greeting_type': 'informal' if 'hi' in text or 'hey' in text else 'formal'
                    }
            return False
        
        tagger.add_exchange_rule('greeting_analysis', greeting_detector)
        
        result = tagger.tag_conversation(data)
        exchange = result.exchanges[0]
        
        # Check that annotations were applied
        assert exchange.has_annotation('has_greeting')
        assert exchange.get_annotation('has_greeting') is True
        assert exchange.get_annotation('greeting_type') == 'formal'  # "hello" is formal

    @pytest.mark.parametrize("source", ["oai", "claude"])
    def test_default_tagger_creation(self, source):
        """Test that default tagger can be created for both sources."""
        tagger = create_default_tagger(source=source)
        assert tagger is not None
        assert hasattr(tagger, 'exchange_parser')
        assert hasattr(tagger.exchange_parser, 'exchange_tagger')
        
        # Should have some default rules
        assert len(tagger.exchange_parser.exchange_tagger.rules) > 0

    @pytest.mark.parametrize("source", ["oai", "claude"])
    def test_exchange_tagger_rule_handling(self, source):
        """Test exchange tagger rule handling across sources."""
        tagger = ExchangeTagger()
        
        def bool_rule(exchange):
            return True
        
        def dict_rule(exchange):
            return {
                'message_count': len(exchange.messages),
                'has_user': len(exchange.get_user_messages()) > 0
            }
        
        def false_rule(exchange):
            return False
        
        tagger.add_rule('bool_test', bool_rule)
        tagger.add_rule('dict_test', dict_rule)
        tagger.add_rule('false_test', false_rule)
        
        # Create message object based on source
        if source == "oai":
            message_data = {
                'author': {'role': 'user'},
                'create_time': 1700000000.0,
                'content': {'text': 'test'},
                'metadata': {}
            }
            message_obj = MessageOpenAI(data=message_data)
        else:
            message_data = {
                'uuid': 'test-uuid',
                'text': 'test',
                'sender': 'user',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'content': [{'type': 'text', 'text': 'test'}],
                'attachments': [],
                'files': []
            }
            message_obj = MessageClaude(data=message_data)
        
        exchange = Exchange.create('test', [message_obj])
        tagged = tagger.tag_exchange(exchange)
        
        # Check annotations
        assert tagged.get_annotation('bool_test') is True
        assert tagged.get_annotation('message_count') == 1
        assert tagged.get_annotation('has_user') is True
        assert not tagged.has_annotation('false_test')  # False shouldn't create annotation


class TestTextExtraction:
    """Test text extraction APIs work consistently across sources."""
    
    @pytest.mark.parametrize("source", ["oai", "claude"])
    def test_user_text_extraction(self, source):
        """Test user text extraction works for both sources."""
        if source == "oai":
            message_data = {
                'author': {'role': 'user'},
                'create_time': 1700000000.0,
                'content': {'text': 'This is a test message'},
                'metadata': {}
            }
            message_obj = MessageOpenAI(data=message_data)
        else:
            message_data = {
                'uuid': 'user-text-uuid',
                'text': 'This is a test message',
                'sender': 'user',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'content': [{'type': 'text', 'text': 'This is a test message'}],
                'attachments': [],
                'files': []
            }
            message_obj = MessageClaude(data=message_data)
        
        exchange = Exchange.create('test', [message_obj])
        user_texts = exchange.get_user_texts()
        
        assert isinstance(user_texts, list)
        assert len(user_texts) == 1
        assert 'This is a test message' in user_texts[0]

    @pytest.mark.parametrize("source", ["oai", "claude"])
    def test_assistant_text_extraction(self, source):
        """Test assistant text extraction works for both sources."""
        if source == "oai":
            message_data = {
                'author': {'role': 'assistant'},
                'create_time': 1700000000.0,
                'content': {'text': 'This is an assistant response'},
                'metadata': {}
            }
            message_obj = MessageOpenAI(data=message_data)
        else:
            message_data = {
                'uuid': 'assistant-text-uuid',
                'text': 'This is an assistant response',
                'sender': 'assistant',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'content': [{'type': 'text', 'text': 'This is an assistant response'}],
                'attachments': [],
                'files': []
            }
            message_obj = MessageClaude(data=message_data)
        
        exchange = Exchange.create('test', [message_obj])
        assistant_texts = exchange.get_assistant_texts()
        
        assert isinstance(assistant_texts, list)
        assert len(assistant_texts) == 1
        assert 'This is an assistant response' in assistant_texts[0]


class TestExchangeMerging:
    """Test exchange merging functionality works consistently."""
    
    @pytest.mark.parametrize("source", ["oai", "claude"])
    def test_exchange_merging_preserves_annotations(self, source):
        """Test that merging exchanges preserves annotations from both."""
        if source == "oai":
            msg1_data = {
                'author': {'role': 'user'},
                'create_time': 1700000000.0,
                'content': {'text': 'First'},
                'metadata': {}
            }
            msg2_data = {
                'author': {'role': 'assistant'},
                'create_time': 1700000001.0,
                'content': {'text': 'Response 1'},
                'metadata': {}
            }
            msg3_data = {
                'author': {'role': 'user'},
                'create_time': 1700000002.0,
                'content': {'text': 'Second'},
                'metadata': {}
            }
            msg4_data = {
                'author': {'role': 'assistant'},
                'create_time': 1700000003.0,
                'content': {'text': 'Response 2'},
                'metadata': {}
            }
            
            msg1_obj = MessageOpenAI(data=msg1_data)
            msg2_obj = MessageOpenAI(data=msg2_data)
            msg3_obj = MessageOpenAI(data=msg3_data)
            msg4_obj = MessageOpenAI(data=msg4_data)
        else:
            msg1_data = {
                'uuid': 'msg1-uuid',
                'text': 'First',
                'sender': 'user',
                'created_at': '2024-01-01T12:00:00Z',
                'updated_at': '2024-01-01T12:00:00Z',
                'content': [{'type': 'text', 'text': 'First'}],
                'attachments': [],
                'files': []
            }
            msg2_data = {
                'uuid': 'msg2-uuid',
                'text': 'Response 1',
                'sender': 'assistant',
                'created_at': '2024-01-01T12:00:01Z',
                'updated_at': '2024-01-01T12:00:01Z',
                'content': [{'type': 'text', 'text': 'Response 1'}],
                'attachments': [],
                'files': []
            }
            msg3_data = {
                'uuid': 'msg3-uuid',
                'text': 'Second',
                'sender': 'user',
                'created_at': '2024-01-01T12:00:02Z',
                'updated_at': '2024-01-01T12:00:02Z',
                'content': [{'type': 'text', 'text': 'Second'}],
                'attachments': [],
                'files': []
            }
            msg4_data = {
                'uuid': 'msg4-uuid',
                'text': 'Response 2',
                'sender': 'assistant',
                'created_at': '2024-01-01T12:00:03Z',
                'updated_at': '2024-01-01T12:00:03Z',
                'content': [{'type': 'text', 'text': 'Response 2'}],
                'attachments': [],
                'files': []
            }
            
            msg1_obj = MessageClaude(data=msg1_data)
            msg2_obj = MessageClaude(data=msg2_data)
            msg3_obj = MessageClaude(data=msg3_data)
            msg4_obj = MessageClaude(data=msg4_data)
        
        exchange1 = Exchange.create('test', [msg1_obj, msg2_obj])
        exchange1.add_annotation('first_exchange', True)
        exchange1.add_annotation('part', 1)
        
        exchange2 = Exchange.create('test', [msg3_obj, msg4_obj])
        exchange2.add_annotation('second_exchange', True)
        exchange2.add_annotation('part', 2)
        
        merged = exchange1 + exchange2
        
        # Check basic structure
        assert len(merged.messages) == 4
        
        # Check annotations were merged
        assert merged.has_annotation('first_exchange')
        assert merged.has_annotation('second_exchange')
        assert merged.get_annotation('part') == 2  # Second exchange wins
        
        # Check message ordering is preserved
        user_texts = merged.get_user_texts()
        assert 'First' in user_texts[0]
        assert 'Second' in user_texts[1]


# Test error handling
@pytest.mark.parametrize("source", ["oai", "claude"])
def test_empty_conversation_handling(source):
    """Test handling of empty conversations."""
    if source == "oai":
        empty_data = {
            'conversation_id': 'empty_oai',
            'title': 'Empty',
            'mapping': {}
        }
    else:
        empty_data = {
            'uuid': 'empty-claude',
            'name': 'Empty',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'account': {'uuid': 'account-uuid'},
            'chat_messages': []
        }
    
    tagger = create_default_tagger(source=source)
    result = tagger.tag_conversation(empty_data)
    
    assert result.exchange_count == 0
    assert result.total_message_count == 0


@pytest.mark.parametrize("source", ["oai", "claude"])
def test_rule_error_handling(source):
    """Test that broken rules don't crash the system."""
    tagger = create_default_tagger(source=source)
    
    def broken_rule(exchange):
        raise ValueError("This rule always fails")
    
    def working_rule(exchange):
        return True
    
    tagger.add_exchange_rule('broken', broken_rule)
    tagger.add_exchange_rule('working', working_rule)
    
    if source == "oai":
        data = {
            'conversation_id': 'test',
            'title': 'Test',
            'mapping': {
                'msg1': {
                    'message': {
                        'author': {'role': 'user'},
                        'create_time': 1700000000.0,
                        'content': {'text': 'Hello'},
                        'metadata': {}
                    }
                }
            }
        }
    else:
        data = {
            'uuid': 'test-uuid',
            'name': 'Test',
            'created_at': '2024-01-01T12:00:00Z',
            'updated_at': '2024-01-01T12:00:00Z',
            'account': {'uuid': 'account-uuid'},
            'chat_messages': [
                {
                    'uuid': 'msg1-uuid',
                    'text': 'Hello',
                    'sender': 'user',
                    'created_at': '2024-01-01T12:00:00Z',
                    'updated_at': '2024-01-01T12:00:00Z',
                    'content': [{'type': 'text', 'text': 'Hello'}],
                    'attachments': [],
                    'files': []
                }
            ]
        }
    
    # Should not raise exception
    result = tagger.tag_conversation(data)
    
    exchange = result.exchanges[0]
    # Working rule should apply, broken rule should be skipped
    assert exchange.has_annotation('working')
    assert not exchange.has_annotation('broken')