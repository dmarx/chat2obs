# docs/testing.md
# Testing Guide

## Overview

The test suite validates all components of LLM Archive across multiple layers:

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions with a real database

## Test Organization

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── conftest.py             # Unit test fixtures
│   ├── test_annotators.py      # Annotator logic tests
│   ├── test_annotation_utils.py
│   ├── test_cli.py             # CLI tests
│   ├── test_content_classification.py
│   ├── test_exchange_utils.py
│   ├── test_extractor_utils.py
│   ├── test_hash_utils.py
│   └── test_models.py          # Model tests
└── integration/
    ├── conftest.py             # Database fixtures
    ├── test_annotators.py      # Annotator integration
    ├── test_builders.py        # Builder integration
    ├── test_extractors.py      # Extractor integration
    ├── test_idempotency.py     # Incremental import tests
    └── test_models.py          # Model persistence tests
```

## Running Tests

### All Tests

```bash
# Run all tests
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=llm_archive --cov-report=html
```

### Unit Tests Only

```bash
# Unit tests don't require database
pytest tests/unit/ -v
```

### Integration Tests Only

```bash
# Requires PostgreSQL running
pytest tests/integration/ -v
```

### Specific Test File

```bash
pytest tests/unit/test_annotators.py -v
```

### Specific Test Class or Function

```bash
# Specific class
pytest tests/unit/test_annotators.py::TestCodeBlockAnnotator -v

# Specific test
pytest tests/unit/test_annotators.py::TestCodeBlockAnnotator::test_detects_code_block_with_language -v
```

---

## Unit Tests

Unit tests verify component logic without database dependencies.

### Annotator Tests

Tests validate the `annotate()` method by constructing data objects directly:

```python
# tests/unit/test_annotators.py

class TestCodeBlockAnnotator:
    """Test CodeBlockAnnotator (priority 90)."""
    
    def test_detects_code_block_with_language(self, message_id):
        """Should detect code blocks with language specification."""
        text = "```python\ndef hello():\n    print('world')\n```"
        data = make_message_data(text, message_id=message_id)
        
        # Create instance without session (we only test annotate())
        annotator = CodeBlockAnnotator.__new__(CodeBlockAnnotator)
        results = annotator.annotate(data)
        
        assert len(results) >= 1
        assert 'python' in results[0].data['languages']
```

### Helper Functions

```python
def make_message_data(text: str, role: str = 'assistant', message_id=None) -> MessageTextData:
    """Helper to create MessageTextData for testing."""
    return MessageTextData(
        message_id=message_id or uuid4(),
        text=text,
        created_at=datetime.now(timezone.utc),
        role=role,
    )

def make_exchange_data(
    user_text: str | None = None,
    assistant_text: str | None = None,
) -> ExchangeData:
    """Helper to create ExchangeData for testing."""
    return ExchangeData(
        exchange_id=uuid4(),
        user_text=user_text,
        assistant_text=assistant_text,
        user_word_count=len(user_text.split()) if user_text else None,
        assistant_word_count=len(assistant_text.split()) if assistant_text else None,
        created_at=datetime.now(timezone.utc),
    )
```

### Model Tests

Test SQLAlchemy model instantiation and field defaults:

```python
class TestDialogueModel:
    def test_create_dialogue_instance(self):
        """Test creating a Dialogue model instance."""
        dialogue = Dialogue(
            source='chatgpt',
            source_id='test-123',
            title='Test Dialogue',
            source_json={'key': 'value'},
        )
        
        assert dialogue.source == 'chatgpt'
        assert dialogue.source_id == 'test-123'
        assert dialogue.id is None  # Set by database
```

---

## Integration Tests

Integration tests verify component interactions with a real PostgreSQL database.

### Database Fixtures

```python
# tests/integration/conftest.py

@pytest.fixture(scope='session')
def database():
    """Create test database."""
    # Create database
    create_test_database()
    
    yield
    
    # Cleanup
    drop_test_database()

@pytest.fixture
def session(database):
    """Create database session with rollback."""
    engine = create_engine(TEST_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()
```

### Extractor Tests

```python
class TestChatGPTExtractor:
    def test_import_simple_conversation(self, session, sample_chatgpt_export):
        """Test importing a simple ChatGPT conversation."""
        extractor = ChatGPTExtractor(session)
        
        count = extractor.extract(sample_chatgpt_export)
        
        assert count == 1
        
        dialogue = session.query(Dialogue).first()
        assert dialogue is not None
        assert dialogue.source == 'chatgpt'
        assert len(dialogue.messages) > 0
```

### Builder Tests

```python
class TestTreeBuilder:
    def test_build_linear_tree(self, session, dialogue_with_messages):
        """Test tree analysis for linear conversation."""
        builder = TreeBuilder(session)
        
        results = builder.build(dialogue_with_messages.id)
        
        tree = session.query(DialogueTree).get(dialogue_with_messages.id)
        assert tree is not None
        assert tree.branch_count == 0  # Linear
        assert tree.is_linear  # Generated column
```

### Annotator Integration Tests

```python
class TestAnnotatorIntegration:
    def test_full_annotation_pipeline(self, session, populated_database):
        """Test running full annotation pipeline."""
        manager = AnnotationManager(session)
        manager.register(CodeBlockAnnotator)
        manager.register(WikiLinkAnnotator)
        manager.register(ExchangeTypeAnnotator)
        
        results = manager.run_all()
        
        assert all(count >= 0 for count in results.values())
        
        # Verify annotations were created
        annotations = session.query(Annotation).count()
        assert annotations > 0
```

---

## Test Fixtures

### Sample Data Fixtures

```python
# tests/conftest.py

@pytest.fixture
def sample_chatgpt_conversation():
    """Sample ChatGPT conversation data."""
    return {
        'id': 'test-conv-123',
        'title': 'Test Conversation',
        'create_time': 1699900000.0,
        'update_time': 1699900100.0,
        'mapping': {
            'root': {
                'id': 'root',
                'parent': None,
                'children': ['msg-1'],
                'message': {
                    'id': 'root-msg',
                    'author': {'role': 'system'},
                    'content': {'content_type': 'text', 'parts': ['']},
                }
            },
            'msg-1': {
                'id': 'msg-1',
                'parent': 'root',
                'children': ['msg-2'],
                'message': {
                    'id': 'user-msg-1',
                    'author': {'role': 'user'},
                    'content': {'content_type': 'text', 'parts': ['Hello!']},
                }
            },
            'msg-2': {
                'id': 'msg-2',
                'parent': 'msg-1',
                'children': [],
                'message': {
                    'id': 'asst-msg-1',
                    'author': {'role': 'assistant'},
                    'content': {'content_type': 'text', 'parts': ['Hi! How can I help?']},
                }
            },
        },
        'current_node': 'msg-2',
    }

@pytest.fixture
def sample_code_message():
    """Sample message with code block."""
    return MessageTextData(
        message_id=uuid4(),
        text='Here is the code:\n```python\nprint("hello")\n```',
        created_at=datetime.now(timezone.utc),
        role='assistant',
    )
```

### Database Population Fixtures

```python
@pytest.fixture
def populated_database(session):
    """Database with sample dialogues, messages, and exchanges."""
    # Create dialogue
    dialogue = Dialogue(
        source='chatgpt',
        source_id='test-1',
        title='Test',
        source_json={},
    )
    session.add(dialogue)
    session.flush()
    
    # Create messages
    messages = create_test_messages(dialogue.id, session)
    
    # Build derived structures
    tree_builder = TreeBuilder(session)
    tree_builder.build(dialogue.id)
    
    exchange_builder = ExchangeBuilder(session)
    exchange_builder.build(dialogue.id)
    
    session.commit()
    
    yield dialogue
```

---

## Test Patterns

### Testing Annotator Logic

```python
def test_annotator_logic():
    """Test annotator without database."""
    # 1. Create data object
    data = MessageTextData(...)
    
    # 2. Create annotator without session
    annotator = MyAnnotator.__new__(MyAnnotator)
    
    # 3. Call annotate directly
    results = annotator.annotate(data)
    
    # 4. Assert on results
    assert len(results) == 1
    assert results[0].value == 'expected'
```

### Testing Incremental Processing

```python
def test_incremental_import(session):
    """Test that incremental import updates correctly."""
    extractor = ChatGPTExtractor(session)
    
    # First import
    count1 = extractor.extract(file_path, mode='full')
    
    # Modify export file
    modify_export_file(file_path)
    
    # Incremental import
    count2 = extractor.extract(file_path, mode='incremental')
    
    # Should detect changes
    assert count2 > 0
```

### Testing Strategy Priority

```python
def test_strategy_priority():
    """Test that annotators run in priority order."""
    manager = AnnotationManager(session)
    
    # Register in random order
    manager.register(LowPriorityAnnotator)    # priority=30
    manager.register(HighPriorityAnnotator)   # priority=90
    manager.register(MedPriorityAnnotator)    # priority=50
    
    # Verify sorted order
    sorted_annotators = manager._sorted_annotators()
    priorities = [a.PRIORITY for a in sorted_annotators]
    
    assert priorities == sorted(priorities, reverse=True)
```

---

## Mocking

### Mock Database Session

```python
from unittest.mock import MagicMock, patch

def test_with_mock_session():
    """Test with mocked session."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.all.return_value = []
    
    annotator = MyAnnotator(mock_session)
    result = annotator.compute()
    
    assert result == 0
```

### Mock File System

```python
def test_import_with_mock_file(tmp_path):
    """Test import with temporary file."""
    # Create temp file
    export_file = tmp_path / "conversations.json"
    export_file.write_text(json.dumps([sample_conversation]))
    
    # Import
    extractor = ChatGPTExtractor(session)
    count = extractor.extract(export_file)
    
    assert count == 1
```

---

## Coverage

### Running with Coverage

```bash
# Generate coverage report
pytest --cov=llm_archive --cov-report=html

# View report
open htmlcov/index.html
```

### Coverage Requirements

- Unit tests: High coverage for business logic
- Integration tests: Cover happy paths and edge cases
- Minimum target: 80% line coverage

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: test_llm_archive
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_llm_archive
        run: |
          pytest --cov=llm_archive --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

---

## Related Documentation

- [Architecture Overview](architecture.md)
- [Annotators](annotators.md) - Annotator testing patterns
- [CLI Reference](cli.md) - CLI testing