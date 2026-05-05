# Python Project Structure

## attic/src/conversation_tagger/analysis/faceting.py
```python
def get_facet_value(annotations: Dict[[str, Any]], facet_annotation_name: str, facet_attribute: Optional[str]) -> str
    """Extract facet value from a conversation's annotations."""

def do_facet_conversations(tagged_conversations: List[Dict[[str, Any]]], facet_annotation_name: str, facet_attribute: Optional[str], max_facets: int) -> Dict[[str, List[Dict[[str, Any]]]]]
    """Group conversations by facet values."""

def print_faceted_summary(tagged_conversations: List[Dict[[str, Any]]], facet_annotation_name: str, facet_attribute: Optional[str], show_details: bool, max_facets: int)
    """Print annotation summary broken down by facets."""

```

## attic/src/conversation_tagger/core/conversation.py
```python
@dataclass
class Conversation
    """A conversation consisting of sequential exchanges with annotations."""

    def __post_init__(self)
        """Post-initialization to ensure annotations are set."""

    def _add_exchange_annotations(self)
        """Aggregate annotations from all exchanges."""

    def add_annotation(self, name: str, value: Any) -> None
        """Add an annotation to this conversation."""

    def has_annotation(self, name: str) -> bool
        """Check if annotation exists."""

    def get_annotation(self, name: str, default: Any) -> Any
        """Get annotation value."""

    @property
    def tags(self) -> List[Tag]
        """Convert annotations back to Tag objects for backward compatibility."""

    def tags(self, tag_list: List[Tag]) -> None
        """Convert Tag objects to annotations for backward compatibility."""

    @property
    def exchange_count(self) -> int

    @property
    def total_message_count(self) -> int

    @property
    def total_user_messages(self) -> int

    @property
    def total_assistant_messages(self) -> int

    @property
    def has_continuations(self) -> bool

    def get_all_user_text(self) -> str

    def get_all_assistant_text(self) -> str


```

## attic/src/conversation_tagger/core/detection.py
```python
def create_conversation_length_annotation(conversation: Conversation) -> Dict[[str, Any]]
    """Create annotation for conversation length."""

def conversation_feature_summary(conversation: Conversation) -> Dict[[str, Any]]
    """Aggregate feature usage across all exchanges."""

def conversation_gizmo_plugin_summary(conversation: Conversation) -> Dict[[str, Any]]
    """Aggregate gizmo/plugin usage across all exchanges."""

def has_github_repos(exchange: Exchange) -> bool

def has_github_repos_oai(exchange: Exchange) -> bool
    """Check if GitHub repositories were selected for context in this exchange."""

def has_canvas_operations(exchange: Exchange) -> bool

def has_canvas_operations_oai(exchange: Exchange) -> bool
    """Check for canvas/document operations in this exchange."""

def has_web_search(exchange: Exchange) -> bool

def has_web_search_oai(exchange: Exchange) -> bool
    """Check for web search operations in this exchange."""

def has_reasoning_thoughts(exchange: Exchange) -> bool

def has_reasoning_thoughts_oai(exchange: Exchange) -> bool
    """Check for reasoning/thinking patterns in this exchange."""

def has_code_execution(exchange: Exchange) -> bool

def has_code_execution_oai(exchange: Exchange) -> bool
    """Check for code execution artifacts in this exchange."""

def has_code_blocks(exchange: Exchange) -> bool

def has_code_blocks_oai(exchange: Exchange) -> bool
    """Check for explicit code blocks (``` markdown syntax)."""

def has_script_headers(exchange: Exchange) -> bool
    """Check for script headers and system includes."""

def has_code_structure_patterns(exchange: Exchange) -> bool
    """Check for actual code structure patterns (syntax combinations that suggest real code)."""

def user_has_quote_elaborate(exchange: Exchange) -> bool
    """Check if user messages contain quote+elaborate continuation pattern."""

def user_has_attachments(exchange: Exchange) -> bool

def user_has_attachments_oai(exchange: Exchange) -> bool
    """Check if user messages have attachments."""

def user_is_continuation(exchange: Exchange) -> bool
    """Check if this exchange started with a continuation prompt."""

def assistant_has_reasoning(exchange: Exchange) -> bool
    """Check if assistant messages contain reasoning/thinking content."""

def has_wiki_links(exchange: Exchange) -> bool
    """Check for Obsidian-style wiki links [[link text]]."""

def has_latex_math(exchange: Exchange) -> bool
    """Check for LaTeX/MathJax mathematical formulas."""

def first_user_has_large_content(exchange: Exchange, min_length: int) -> bool
    """Check if the first user message has large content."""

def first_user_has_code_patterns(exchange: Exchange) -> bool
    """Check if the first user message contains code patterns."""

def first_user_has_attachments(exchange: Exchange) -> bool
    """Check if the first user message has attachments."""

def first_user_has_code_attachments(exchange: Exchange) -> bool
    """Check if the first user message has code-related attachments."""

def get_gizmo_annotations(exchange: Exchange) -> dict[[str, Any]]

def get_gizmo_annotations_oai(exchange: Exchange) -> dict[[str, Any]]
    """Get annotations for specific gizmos used in this exchange."""

def get_plugin_annotations(exchange: Exchange) -> dict[[str, Any]]

def get_plugin_annotations_oai(exchange: Exchange) -> dict[[str, Any]]
    """Get annotations for specific plugins used in this exchange."""

def naive_title_extraction(text)
    """Attempts to detect presence of title in first line of a message."""

def extract_proposed_title(exchange: Exchange) -> str
    """
    Extracts proposed content title from the assistant's response.
    Assumes that an article was generated with a proposed title.
    """

```

## attic/src/conversation_tagger/core/detection_old.py
```python
def has_large_content(conversation: Dict[[str, Any]], min_length: int) -> bool
    """Check if conversation has unusually large content anywhere."""

def has_github_repos(conversation: Dict[[str, Any]]) -> bool
    """Check if GitHub repositories were selected for context."""

def has_canvas_operations(conversation: Dict[[str, Any]]) -> bool
    """Check for canvas/document operations."""

def has_web_search(conversation: Dict[[str, Any]]) -> bool
    """Check for web search operations."""

def has_reasoning_thoughts(conversation: Dict[[str, Any]]) -> bool
    """Check for reasoning/thinking patterns."""

def has_code_execution(conversation: Dict[[str, Any]]) -> bool
    """Check for code execution artifacts."""

def has_code_blocks(conversation: Dict[[str, Any]]) -> bool
    """Check for explicit code blocks (``` markdown syntax)."""

def has_function_definitions(conversation: Dict[[str, Any]]) -> bool
    """Check for function/class definition keywords."""

def has_import_statements(conversation: Dict[[str, Any]]) -> bool
    """Check for import/require statements."""

def has_script_headers(conversation: Dict[[str, Any]]) -> bool
    """Check for script headers and system includes."""

def has_high_keyword_density(conversation: Dict[[str, Any]]) -> bool
    """Check for high density of programming keywords in large text."""

def has_code_structure_patterns(conversation: Dict[[str, Any]]) -> bool
    """Check for actual code structure patterns (syntax combinations that suggest real code)."""

def has_code_patterns(conversation: Dict[[str, Any]]) -> bool
    """Check for any code patterns (combines individual indicators)."""

def user_has_quote_elaborate(exchange: Exchange) -> bool
    """Check if user messages contain quote+elaborate continuation pattern."""

def user_has_code_blocks(exchange: Exchange) -> bool
    """Check if user messages contain code blocks."""

def user_has_attachments(exchange: Exchange) -> bool
    """Check if user messages have attachments."""

def user_has_error_messages(exchange: Exchange) -> bool
    """Check if user messages contain error patterns."""

def user_prompt_length_category(exchange: Exchange) -> Tag
    """Categorize user prompt length."""

def user_is_continuation(exchange: Exchange) -> bool
    """Check if this exchange started with a continuation prompt."""

def assistant_has_code_blocks(exchange: Exchange) -> bool
    """Check if assistant messages contain code blocks."""

def assistant_has_wiki_links(exchange: Exchange) -> bool
    """Check if assistant messages contain wiki-style links."""

def assistant_has_latex_math(exchange: Exchange) -> bool
    """Check if assistant messages contain mathematical formulas."""

def assistant_response_length_category(exchange: Exchange) -> Tag
    """Categorize assistant response length."""

def assistant_has_reasoning(exchange: Exchange) -> bool
    """Check if assistant messages contain reasoning/thinking content."""

def exchange_is_coding_focused(exchange: Exchange) -> bool
    """Check if the entire exchange is focused on coding."""

def exchange_is_wiki_article_focused(exchange: Exchange) -> bool
    """Check if exchange is focused on wiki/documentation content."""

def exchange_has_error_resolution(exchange: Exchange) -> bool
    """Check if exchange involves error troubleshooting."""

def exchange_interaction_pattern(exchange: Exchange) -> Tag
    """Determine the interaction pattern of this exchange."""

def first_user_has_large_content(conversation: Dict[[str, Any]], min_length: int) -> bool
    """Check if the first user message has large content."""

def first_user_has_code_patterns(conversation: Dict[[str, Any]]) -> bool
    """Check if the first user message contains code patterns."""

def first_user_has_attachments(conversation: Dict[[str, Any]]) -> bool
    """Check if the first user message has attachments."""

def first_user_has_code_attachments(conversation: Dict[[str, Any]]) -> bool
    """Check if the first user message has code-related attachments."""

def create_conversation_length_tag(conversation: Dict[[str, Any]]) -> Tag
    """Create structured tag for conversation length."""

def create_prompt_stats_tag(conversation: Dict[[str, Any]]) -> Tag
    """Create structured tag for prompt statistics."""

def create_gizmo_plugin_tags(conversation: Dict[[str, Any]]) -> List[Tag]
    """Create structured tags for gizmos and plugins."""

```

## attic/src/conversation_tagger/core/exchange.py
```python
@dataclass
class Exchange
    """A sequential conversation exchange with merge capabilities."""

    def __post_init__(self)

    @classmethod
    def create(cls, conversation_id: str, messages: List[Message]) -> 'Exchange'
        """Create a new exchange with a random UUID."""

    @property
    def last_message_time(self) -> float
        """Get the create_time of the last message for ordering."""

    @property
    def first_message_time(self) -> float
        """Get the create_time of the first message for ordering."""

    def has_continuations(self) -> bool
        """Check if this exchange has continuation prompts (multiple user messages)."""

    def get_message_ids(self) -> List[str]
        """Get the IDs of all messages in this exchange."""

    def get_user_messages(self) -> List[Dict[[str, Any]]]
        """Get just the user messages."""

    def get_assistant_messages(self) -> List[Dict[[str, Any]]]
        """Get just the assistant messages."""

    def get_user_texts(self) -> List[str]
        """Get text from all user messages."""

    def get_assistant_texts(self) -> List[str]
        """Get text from all assistant messages."""

    def add_annotation(self, name: str, value: Any) -> None
        """Add an annotation to this exchange."""

    def has_annotation(self, name: str) -> bool
        """Check if annotation exists."""

    def get_annotation(self, name: str, default: Any) -> Any
        """Get annotation value."""

    def __add__(self, other: 'Exchange') -> 'Exchange'
        """Merge two exchanges by combining and time-ordering their messages."""

    def __len__(self) -> int
        """Return number of messages in exchange."""

    @property
    def content(self) -> str
        """Get concatenated content of all messages in this exchange."""


```

## attic/src/conversation_tagger/core/exchange_parser.py
```python
def quote_elaborate_rule(previous_exchange: Exchange, current_exchange: Exchange) -> bool
    """Check for quote + elaborate continuation pattern."""

def simple_continuation_rule(previous_exchange: Exchange, current_exchange: Exchange) -> bool
    """Check for simple continuation keywords."""

def short_continuation_rule(previous_exchange: Exchange, current_exchange: Exchange) -> bool
    """Check for short prompts starting with continuation words."""

class ExchangeParser
    """Parses conversations into tagged exchanges."""

    def __init__(self, exchange_tagger: ExchangeTagger | None)

    def add_continuation_rule(self, rule_function: Callable[[Any, bool]])
        """Add a new continuation detection rule."""

    def get_messages(self, conversation: dict)

    def get_conversation_id(self, conversation: dict) -> str

    def get_title(self, conversation: dict) -> str

    def parse_conversation(self, conversation: Dict[[str, Any]]) -> Conversation
        """Parse a conversation into a Conversation object with fully-tagged exchanges."""

    def _create_dyadic_exchanges(self, messages: list[Message | dict], conversation_id: str) -> List[Exchange]
        """Step 1: Create simple USER-ASSISTANT dyadic exchanges."""

    def _merge_continuations(self, dyadic_exchanges: List[Exchange]) -> List[Exchange]
        """Step 2: Merge exchanges when continuation patterns are detected."""


class ExchangeParserOAI(ExchangeParser)

    def get_messages(self, conversation: dict)

    def get_conversation_id(self, conversation: dict) -> str

    def get_title(self, conversation: dict) -> str


class ExchangeParserClaude(ExchangeParser)

    def get_messages(self, conversation: dict)

    def get_conversation_id(self, conversation: dict) -> str

    def get_title(self, conversation: dict) -> str


```

## attic/src/conversation_tagger/core/exchange_tagger.py
```python
class ExchangeTagger
    """Tags exchanges with configurable rules using annotations."""

    def __init__(self)

    def add_rule(self, annotation_name: str, rule_function: Callable)
        """Add rule for exchanges."""

    def tag_exchange(self, exchange: Exchange) -> Exchange
        """Tag a single exchange and return the updated exchange."""


```

## attic/src/conversation_tagger/core/generate.py
```python
def sanitize_filename(title: str, max_length: int) -> str
    """
    Sanitize a title to be safe for use as a filename.
    Args:
        title: The title to sanitize
        max_length: Maximum length of the resulting filename
    Returns:
        A sanitized filename string
    """

def extract_title(exchange: Exchange) -> str

def load_template(template_name: str) -> Template
    """Load a Jinja template from the templates directory."""

def make_metadata(page) -> Dict[[str, object]]
    """Build a dict that python-frontmatter will turn into YAML."""

def generate_notes(conversation: Conversation, template_name: str, output_dir: str) -> List[str]
    """Generate Obsidian notes from a conversation."""

```

## attic/src/conversation_tagger/core/message.py
```python
class Message

    def __init__(self, data: dict)

    @property
    def content(self)

    @property
    def created_date(self)

    @property
    def author_role(self)

    @property
    def id(self)

    def _get_id(self)

    def _get_author_role(self)

    def _get_content(self)

    def _get_created_date(self)

    def __repr__(self)

    def __str__(self)


def get_message_text_chatgpt(message: dict[[str, Any]]) -> str
    """Extract text content from a message."""

class MessageOpenAI(Message)

    def _get_id(self)

    def _get_content(self)

    def _get_created_date(self)

    def _get_author_role(self)


class MessageClaude(Message)

    def _get_id(self)

    def _get_content(self)

    def _get_created_date(self)

    def _get_author_role(self)


```

## attic/src/conversation_tagger/core/tag.py
```python
def create_annotation(name: str, value: Union[[bool, int, float, str, Dict[[str, Any]]]]) -> Dict[[str, Any]]
    """Create a simple annotation as a dictionary entry."""

def merge_annotations() -> Dict[[str, Any]]
    """Merge multiple annotation dictionaries."""

def has_annotation(annotations: Dict[[str, Any]], name: str) -> bool
    """Check if an annotation exists."""

def get_annotation_value(annotations: Dict[[str, Any]], name: str, default: Any) -> Any
    """Get the value of an annotation."""

class Tag
    """A tag with optional key-value attributes - DEPRECATED: Use dictionaries instead."""

    def __init__(self, name: str)

    def to_dict(self) -> Dict[[str, Any]]
        """Convert to dictionary format."""

    def __str__(self)

    def __repr__(self)

    def __eq__(self, other)

    def __hash__(self)


```

## attic/src/conversation_tagger/core/tagger.py
```python
class ConversationTagger
    """Main tagger that uses exchange-based analysis with annotations."""

    def __init__(self, exchange_parser: ExchangeParser | None)

    def add_exchange_rule(self, annotation_name: str, rule_function: Callable)
        """Add rule for analyzing exchanges."""

    def add_conversation_rule(self, annotation_name: str, rule_function: Callable)
        """Add rule for analyzing entire conversations."""

    def tag_conversation(self, conversation: Dict[[str, Any]]) -> Conversation
        """Tag a conversation using exchange-based analysis."""


```

## attic/src/conversation_tagger/factory.py
```python
def create_default_tagger(source) -> ConversationTagger
    """Create a basic tagger with example rules for the new exchange design."""

```

## attic/tests/conversation_tagger/conftest.py
```python
def simple_user_message()
    """A basic user message."""

def simple_assistant_message()
    """A basic assistant message."""

def basic_exchange(simple_user_message, simple_assistant_message)
    """A simple two-message exchange."""

def minimal_conversation_data()
    """Minimal conversation data for parsing tests."""

```

## attic/tests/conversation_tagger/test_basic_working.py
```python
def test_annotation_functionality()
    """Test that annotation helpers work correctly."""

def test_exchange_creation_and_annotations()
    """Test basic exchange creation and annotation handling."""

def test_exchange_text_api_with_annotations()
    """Test the text extraction API and annotation usage."""

def test_exchange_tagger_with_annotations()
    """Test exchange tagger using the annotation system."""

def test_conversation_parsing_with_annotations()
    """Test basic conversation parsing with annotation support."""

def test_default_tagger_with_annotations()
    """Test that the default tagger works with annotation system."""

def test_default_rules_produce_annotations()
    """Test that default rules work and produce annotations."""

def test_annotation_backward_compatibility_workflow()
    """Test complete workflow using both annotations and legacy tags."""

def test_rule_return_value_handling()
    """Test that different rule return value types are handled correctly."""

def analyze_text(texts)

def greeting_detector(exchange)
    """A rule that uses the correct API and returns annotation data."""

def message_counter(exchange)
    """Rule that returns simple numeric annotation."""

def simple_stats(exchange)

def bool_rule(exchange)

def string_rule(exchange)

def number_rule(exchange)

def dict_rule(exchange)

def false_rule(exchange)

def none_rule(exchange)

```

## attic/tests/conversation_tagger/test_core.py
```python
def test_annotation_helpers()
    """Test annotation helper functions."""

def test_tag_backward_compatibility()
    """Test that Tag objects still work and convert properly."""

def test_exchange_annotations()
    """Test exchange annotation functionality."""

def test_exchange_merging_annotations()
    """Test merging exchanges preserves annotations."""

def test_conversation_annotations()
    """Test conversation annotation functionality."""

def sample_conversation_data()
    """Sample conversation data for parsing tests."""

def test_simple_parsing(sample_conversation_data)
    """Test basic conversation parsing with annotations."""

```

## attic/tests/conversation_tagger/test_detection.py
```python
def test_create_conversation_length_annotation()
    """Test conversation length annotation creation."""

def test_conversation_feature_summary()
    """Test feature aggregation across exchanges."""

def test_conversation_gizmo_plugin_summary()
    """Test gizmo/plugin aggregation across exchanges."""

def test_has_github_repos()
    """Test GitHub repository detection."""

def test_get_gizmo_annotations()
    """Test gizmo annotation generation."""

def test_get_plugin_annotations()
    """Test plugin annotation generation."""

def test_has_code_blocks()
    """Test code block detection."""

def test_has_latex_math()
    """Test LaTeX math detection."""

def test_first_user_has_large_content()
    """Test large content detection in first user message."""

def test_user_has_attachments()
    """Test user attachment detection."""

def test_extract_proposed_title()
    """Test proposed title extraction from assistant messages."""

def test_naive_title_extraction()
    """Test the helper function directly."""

```

## attic/tests/conversation_tagger/test_integration.py
```python
def sample_coding_conversation()
    """A realistic conversation about coding that should trigger multiple annotations."""

def test_default_tagger_creation()
    """Test that default tagger is created with expected rules."""

def test_end_to_end_tagging_with_annotations(sample_coding_conversation)
    """Test complete tagging pipeline with realistic conversation."""

def test_conversation_with_attachments()
    """Test conversation that includes file attachments."""

def test_math_conversation()
    """Test conversation with mathematical content."""

def test_large_content_detection()
    """Test detection of large content messages."""

def test_conversation_level_annotations()
    """Test conversation-level annotation aggregation."""

def test_gizmo_plugin_annotations()
    """Test gizmo and plugin annotation detection."""

def test_empty_conversation_handling()
    """Test handling of edge cases like empty conversations."""

def test_claude_conversation_parsing()
    """Test parsing a Claude conversation."""

def mentions_python(exchange)

def count_code_blocks(exchange)
    """Return annotation with count of code blocks."""

```

## attic/tests/conversation_tagger/test_message_ids.py
```python
def test_message_openai_id()
    """Test that OpenAI messages extract IDs correctly."""

def test_message_claude_id()
    """Test that Claude messages extract IDs correctly."""

def test_exchange_get_message_ids()
    """Test that exchanges can return all message IDs."""

def test_exchange_get_message_ids_with_missing_ids()
    """Test exchange message ID extraction with some missing IDs."""

def test_exchange_get_message_ids_empty_exchange()
    """Test get_message_ids with empty exchange."""

def test_exchange_merging_preserves_message_ids()
    """Test that merging exchanges preserves all message IDs."""

def test_mixed_message_types_with_ids()
    """Test exchange with mixed OpenAI and Claude messages (hypothetical scenario)."""

def test_message_id_property_in_existing_tests()
    """Test that existing message objects now have id property."""

```

## attic/tests/conversation_tagger/test_parameterized.py
```python
def get_simple_conversation_data()
    """Return simple conversation data for both sources."""

class TestBasicFunctionality
    """Test basic functionality across both data sources."""

    def test_annotation_functionality(self)
        """Test that annotation helpers work correctly."""

    def test_conversation_parsing_basic(self, source, data)
        """Test basic conversation parsing works for both sources."""

    def test_exchange_annotations(self, source, data)
        """Test exchange annotation handling across sources."""

    def test_default_tagger_creation(self, source)
        """Test that default tagger can be created for both sources."""

    def test_exchange_tagger_rule_handling(self, source)
        """Test exchange tagger rule handling across sources."""


class TestTextExtraction
    """Test text extraction APIs work consistently across sources."""

    def test_user_text_extraction(self, source)
        """Test user text extraction works for both sources."""

    def test_assistant_text_extraction(self, source)
        """Test assistant text extraction works for both sources."""


class TestExchangeMerging
    """Test exchange merging functionality works consistently."""

    def test_exchange_merging_preserves_annotations(self, source)
        """Test that merging exchanges preserves annotations from both."""


def test_empty_conversation_handling(source)
    """Test handling of empty conversations."""

def test_rule_error_handling(source)
    """Test that broken rules don't crash the system."""

def broken_rule(exchange)

def working_rule(exchange)

def greeting_detector(exchange)

def bool_rule(exchange)

def dict_rule(exchange)

def false_rule(exchange)

```

## attic/tests/conversation_tagger/test_tagging.py
```python
def test_exchange_tagger_annotations()
    """Test basic exchange tagging with annotations."""

def test_exchange_tagger_with_string_values()
    """Test exchange tagging with string return values."""

def test_conversation_tagger_annotations()
    """Test conversation-level tagging with annotations."""

def test_tagging_error_handling()
    """Test that tagging rules handle errors gracefully."""

def conversation_with_continuation()
    """Conversation data that should trigger continuation merging."""

def test_continuation_detection_with_annotations(conversation_with_continuation)
    """Test that continuation patterns merge exchanges correctly."""

def has_greeting(exchange)

def message_stats(exchange)
    """Return multiple annotations."""

def get_language(exchange)
    """Return a string value."""

def is_multi_turn(conversation)

def exchange_summary(conversation)
    """Return structured annotation data."""

def broken_rule(exchange)

def working_rule(exchange)

def detect_continuation(exchange)

```

## llm_archive/annotations/core.py
```python
class EntityType(str, Enum)

class ValueType(str, Enum)

@dataclass
class AnnotationResult

    def __eq__(self, other)

    def __hash__(self)

    def __repr__(self)


def _get_model(entity_type: EntityType, value_type: ValueType)
    """Lazy import to avoid circular dependency."""

class AnnotationWriter
    """
    Writes annotations to typed tables using ORM models.
    Uses PostgreSQL upsert (INSERT ... ON CONFLICT) for idempotency:
    - FLAG/JSON: ON CONFLICT (entity_id, key) → single value per key
    - STRING/NUMERIC: ON CONFLICT (entity_id, key, value) → multi-value
    """

    def __init__(self, session: Session)

    def write_flag(self, entity_type: EntityType, entity_id: UUID, key: str, confidence: float | None, reason: str | None, source: str, source_version: str | None) -> bool

    def write_string(self, entity_type: EntityType, entity_id: UUID, key: str, value: str, confidence: float | None, reason: str | None, source: str, source_version: str | None) -> bool

    def write_numeric(self, entity_type: EntityType, entity_id: UUID, key: str, value: float, confidence: float | None, reason: str | None, source: str, source_version: str | None) -> bool

    def write_json(self, entity_type: EntityType, entity_id: UUID, key: str, value: Any, confidence: float | None, reason: str | None, source: str, source_version: str | None) -> bool

    def write(self, entity_type, entity_id, result)
        """Dispatch to the appropriate typed writer."""

    def _track(self, table: str, created: bool) -> None

    @property
    def counts(self)


class AnnotationReader
    """Reads annotations from typed tables using ORM queries."""

    def __init__(self, session: Session)

    def has_flag(self, entity_type: EntityType, entity_id: UUID, key: str) -> bool

    def get_string(self, entity_type: EntityType, entity_id: UUID, key: str) -> list[str]

    def get_string_single(self, entity_type: EntityType, entity_id: UUID, key: str) -> str | None

    def get_numeric(self, entity_type: EntityType, entity_id: UUID, key: str) -> list[float]

    def get_json(self, entity_type: EntityType, entity_id: UUID, key: str) -> dict | list | None

    def has_annotation_key(self, entity_type: EntityType, entity_id: UUID, key: str) -> bool

    def find_entities_with_flag(self, entity_type: EntityType, key: str) -> set[UUID]

    def find_entities_with_string(self, entity_type: EntityType, key: str, value: str | None) -> set[UUID]

    def get_all_keys(self, entity_type: EntityType, entity_id: UUID) -> set[str]
        """Return the set of annotation keys present for an entity (any value type)."""


```

## llm_archive/annotators/base.py
```python
class BaseAnnotator(ABC)
    """
    Abstract base for all annotators.
    Concrete subclasses must define:
        ENTITY_TYPE, ANNOTATION_KEY, and implement
        _iter_entities_after(), _entity_id(), _created_at(), annotate().
    Class attributes (override in subclass):
        ENTITY_TYPE      – EntityType enum member
        ANNOTATION_KEY   – primary annotation key produced
        VALUE_TYPE       – default ValueType for results
        PRIORITY         – higher runs first (descending sort)
        VERSION          – bump to force reprocessing
        SOURCE           – e.g. 'heuristic', 'model', 'ingestion'
    """

    def __init__(self, session: Session) -> None

    def compute(self) -> int
        """
        Run annotation with cursor-based incremental processing.
        Returns the number of annotations created this run.
        """

    def _get_or_create_cursor(self) -> AnnotatorCursor
        """Retrieve or create cursor for this annotator + version + entity_type."""

    def _update_cursor(self, cursor: AnnotatorCursor) -> None
        """Advance cursor state after a run."""

    def _write_result(self, entity_id: UUID, result: AnnotationResult) -> bool
        """Write a single annotation result."""

    @abstractmethod
    def _iter_entities_after(self, after: datetime) -> Iterator[EntityDataT]
        """Yield entities whose created_at > *after*, ordered by created_at."""

    @abstractmethod
    def _entity_id(self, data: EntityDataT) -> UUID
        """Extract the primary-key UUID from entity data."""

    @abstractmethod
    def _created_at(self, data: EntityDataT) -> datetime | None
        """Extract the created_at timestamp from entity data."""

    @abstractmethod
    def annotate(self, data: EntityDataT) -> list[AnnotationResult]
        """
        Produce annotations for a single entity.
        Returns an empty list when no annotation applies.
        """


```

## llm_archive/annotators/content_part.py
```python
@dataclass
class ContentPartData
    """Data passed to content-part annotation logic."""

class ContentPartAnnotator
    """
    Base class for annotating content parts.
    Iterates over ContentPart joined with Message using ORM queries.
    Supports optional content filters (PART_TYPE_FILTER, ROLE_FILTER).
    Subclass and implement ``annotate()`` to create a new content-part
    annotator.  Everything else (cursor tracking, result writing,
    incremental processing) is handled automatically.
    """

    def _iter_entities_after(self, after: datetime) -> Iterator[ContentPartData]
        """Yield content parts whose message.created_at > *after*."""

    def _entity_id(self, data: ContentPartData) -> UUID

    def _created_at(self, data: ContentPartData) -> datetime | None

    @abstractmethod
    def annotate(self, data: ContentPartData) -> list[AnnotationResult]
        """Analyze content part and return annotations to create."""


class CodeBlockAnnotator(ContentPartAnnotator)
    """
    Detect explicit code blocks (```) in text content parts.
    Produces:
    - has_code_block FLAG
    - code_block_count NUMERIC
    - code_language STRING (multi-value, one per detected language)
    """

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]


class LatexContentAnnotator(ContentPartAnnotator)
    """
    Detect LaTeX content in text.
    Produces:
    - has_latex FLAG
    - latex_type STRING ('inline' | 'display' | 'commands')
    """

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]


class WikiLinkContentAnnotator(ContentPartAnnotator)
    """
    Detect [[wiki links]] in content.
    Produces:
    - has_wiki_links FLAG
    - wiki_link_count NUMERIC
    """

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]


```

## llm_archive/annotators/prompt_response.py
```python
@dataclass
class PromptResponseData
    """Data passed to prompt-response annotation logic."""

class PromptResponseAnnotator
    """
    Base class for annotating prompt-response pairs.
    Iterates over PromptResponse joined with PromptResponseContent
    using ORM queries.
    Supports annotation prerequisites and skip conditions via ORM joins:
    - REQUIRES_FLAGS: Only process entities with ALL of these flag annotations
    - REQUIRES_STRINGS: Only process entities with ALL of these (key, value) pairs
    - SKIP_IF_FLAGS: Skip entities with ANY of these flag annotations
    - SKIP_IF_STRINGS: Skip entities with ANY of these (key,) or (key, value) pairs
    Subclass and implement ``annotate()`` to create a new prompt-response
    annotator.
    """

    def _iter_entities_after(self, after: datetime) -> Iterator[PromptResponseData]
        """Yield prompt-response pairs created after *after*."""

    def _apply_annotation_filters(self, query)
        """Apply REQUIRES and SKIP annotation filters using ORM joins."""

    def _entity_id(self, data: PromptResponseData) -> UUID

    def _created_at(self, data: PromptResponseData) -> datetime | None

    @abstractmethod
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]
        """Analyze prompt-response pair and return annotations to create."""


class WikiCandidateAnnotator(PromptResponseAnnotator)
    """
    Detect wiki-style article candidates.
    Looks for [[wiki links]] in assistant responses.
    Produces:
    - exchange_type STRING 'wiki_article'
    """

    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]


def clean_title(text: str)

class NaiveTitleAnnotator(PromptResponseAnnotator)
    """
    Extract potential article title from response.
    Only runs on wiki_article candidates.
    Produces:
    - proposed_title STRING
    """

    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]


```

## llm_archive/annotators/registry.py
```python
class AnnotatorRegistry
    """
    Central registry of annotator classes.
    Annotators are sorted by PRIORITY descending (highest priority first).
    """

    def __init__(self) -> None

    def register(self, cls: type[BaseAnnotator]) -> None
        """Register an annotator class."""

    def register_many(self, classes: list[type[BaseAnnotator]]) -> None

    def unregister(self, name: str) -> None

    def list_annotators(self) -> list[type[BaseAnnotator]]
        """Return registered annotators sorted by priority (descending)."""

    def get(self, name: str) -> type[BaseAnnotator] | None

    def run_all(self, session: Session) -> dict[[str, int]]
        """
        Run every registered annotator in priority order.
        Returns dict mapping annotator name → annotations created.
        """

    def run_one(self, name: str, session: Session) -> int
        """
        Run a single annotator by class name.
        Raises KeyError if not registered.
        """


def get_default_registry() -> AnnotatorRegistry
    """Build a registry with all built-in annotators."""

```

## llm_archive/builders/prompt_response.py
```python
class PromptResponseBuilder
    """
    Builds prompt-response pairs directly from messages.
    Unlike ExchangeBuilder (which depends on tree analysis), this uses:
    1. parent_id relationship when available (ChatGPT)
    2. Sequential fallback (Claude, or when parent_id missing)
    Result: Each non-user message is paired with its eliciting user prompt.
    """

    def __init__(self, session: Session)

    def build_all(self) -> dict[[str, int]]
        """Build prompt-response pairs for all dialogues."""

    def build_for_dialogue(self, dialogue_id: UUID) -> dict[[str, int]]
        """Build prompt-response pairs for a single dialogue."""

    def _find_prompt(self, response_msg: Message, msg_by_id: dict[[UUID, Message]], last_user_msg: Message | None) -> Message | None
        """Find the user prompt that elicited this response."""

    def _create_prompt_response(self, dialogue_id: UUID, prompt_msg: Message, response_msg: Message, prompt_position: int, response_position: int) -> UUID
        """Insert a prompt_response record and return its ID."""

    def _build_content(self, dialogue_id: UUID) -> int
        """Build content records for all prompt-responses in a dialogue."""

    def _clear_existing(self, dialogue_id: UUID)
        """Clear existing prompt-response data for a dialogue."""


```

## llm_archive/cli.py
```python
class CLI
    """LLM Archive - Conversation ingestion and analysis."""

    def __init__(self, db_url: str | None)

    def init(self, schema_dir: str)
        """Initialize database schema."""

    def reset(self, confirm: bool, schema_dir: str)
        """Reset database (drops and recreates schema)."""

    def import_chatgpt(self, path: str, assume_immutable: bool, incremental: bool)
        """
        Import ChatGPT conversations.json export.
        Args:
            path: Path to conversations.json file
            assume_immutable: Skip content hash checks for existing messages.
            incremental: Don't soft-delete messages missing from this import.
        """

    def import_claude(self, path: str, assume_immutable: bool, incremental: bool)
        """
        Import Claude conversations.json export.
        Args:
            path: Path to conversations.json file
            assume_immutable: Skip content hash checks for existing messages.
            incremental: Don't soft-delete messages missing from this import.
        """

    def import_all(self, chatgpt_path: str | None, claude_path: str | None, assume_immutable: bool, incremental: bool)
        """Import from multiple sources."""

    def build_prompt_responses(self)
        """Build prompt-response pairs (no tree dependency)."""

    def build_all(self)
        """Build all derived structures."""

    def annotate(self, annotator: str | None, clear: bool)
        """
        Run annotators with cursor-based incremental processing.
        Args:
            annotator: Run only this annotator (by class name). Omit for all.
            clear: Delete cursors before running so all entities are reprocessed.
        """

    def list_annotators(self)
        """List all registered annotators with metadata."""

    def cursor_status(self)
        """Show status of all annotator cursors."""

    def _clear_cursors(self, session, annotator_name: str | None)
        """Delete cursors to force reprocessing."""

    def annotation_counts(self)
        """
        Query annotation tables and return counts by annotation_key, entity_type, and value_type.
        Provides visibility into all annotations including those applied during raw archive ingestion.
        Returns:
            List of dicts with keys: annotation_key, entity_type, value_type, count
        """

    def stats(self)
        """Show database statistics."""

    def run(self, chatgpt_path: str | None, claude_path: str | None, init_db: bool, schema_dir: str, assume_immutable: bool, incremental: bool)
        """
        Run full pipeline: import, build, annotate.
        Args:
            chatgpt_path: Path to ChatGPT conversations.json
            claude_path: Path to Claude conversations.json
            init_db: Initialize database schema before import
            schema_dir: Directory containing schema files
            assume_immutable: Skip content hash checks
            incremental: Don't soft-delete missing messages
        """

    def _load_json(self, path: str) -> list[dict]
        """Load JSON file."""


def main()
    """Entry point."""

```

## llm_archive/config.py
```python
def get_database_url() -> str
    """Construct database URL from environment variables."""

```

## llm_archive/db.py
```python
def get_engine(db_url: str) -> Engine
    """Create database engine."""

def get_session_factory(db_url: str) -> sessionmaker
    """Create a session factory."""

@contextmanager
def get_session(db_url: str)
    """Context manager for database sessions."""

def create_pg_schemas(engine: Engine) -> None
    """Create PostgreSQL schema namespaces and extensions."""

def create_tables(engine: Engine) -> None
    """Create all ORM-defined tables via Base.metadata.create_all."""

def seed_sources(engine: Engine) -> None
    """Seed raw.sources if empty."""

def create_annotation_union_views(engine: Engine) -> None
    """Generate *_annotations_all union views for each entity type."""

def execute_view_files(engine: Engine, schema_dir: Path) -> None
    """
    Execute SQL files that contain view definitions.
    Skips files with only tables/extensions/seeds (handled by ORM).
    """

def drop_schemas(engine: Engine) -> None
    """Drop raw and derived schemas (destructive!)."""

def init_schema_with_engine(engine: Engine, schema_dir: Path | None) -> None
    """
    Initialize database schema using an existing engine.
    1. Create PostgreSQL schema namespaces + extensions
    2. Create all ORM-defined tables
    3. Seed raw.sources lookup table
    4. Create annotation union views (*_annotations_all)
    5. Execute additional view SQL files from schema_dir
    """

def init_schema(db_url: str, schema_dir: Path | str | None) -> None
    """Initialize database schema from a URL string."""

def reset_schema(db_url: str, schema_dir: Path | str | None) -> None
    """Drop and recreate schemas (destructive!)."""

```

## llm_archive/extractors/base.py
```python
def parse_timestamp(value: int | float | str | None) -> datetime | None
    """
    Parse timestamp from various formats to timezone-aware datetime.
    Handles:
    - Epoch floats/ints (ChatGPT)
    - ISO 8601 strings (Claude)
    """

def normalize_role(role: str, source: str) -> str
    """
    Normalize role/sender to standard vocabulary.
    Standard roles: 'user', 'assistant', 'system', 'tool'
    """

def safe_get(data: dict[[str, Any]]) -> Any
    """Safely traverse nested dict."""

def compute_content_hash(source_json: dict | list | str) -> str
    """Compute a stable hash of message content for change detection."""

class BaseExtractor(ABC)
    """
    Base class for source extractors.
    Supports idempotent ingestion with incremental updates:
    - Skip dialogues that haven't changed (by updated_at timestamp)
    - Preserve message UUIDs for unchanged messages
    - Soft-delete messages removed from source (unless incremental=True)
    - Only rebuild content_parts for actually changed messages
    Args:
        session: SQLAlchemy session
        assume_immutable: If True, assume message content never changes once created.
            This skips content hash comparison for existing messages, which is faster
            but won't detect in-place edits. Use for providers where edits create new
            message UUIDs rather than modifying existing ones. Default: False.
        incremental: If True, treat the import as a delta/partial update. Messages
            not present in the current import will NOT be soft-deleted. Use when
            importing partial exports or streaming updates. Default: False.
    """

    def __init__(self, session: Session, assume_immutable: bool, incremental: bool)

    def _increment_count(self, key: str, amount: int)
        """Safely increment a count (no-op if counts not initialized)."""

    @abstractmethod
    def extract_dialogue(self, raw: dict[[str, Any]]) -> str | None
        """
        Extract a single dialogue and all its contents.
        Returns:
            'new' - new dialogue created
            'updated' - existing dialogue updated  
            'skipped' - existing dialogue unchanged
            None - extraction failed
        """

    def extract_all(self, data: list[dict[[str, Any]]]) -> dict[[str, int]]
        """Extract all dialogues from a data list."""

    def get_existing_dialogue(self, source_id: str) -> Dialogue | None
        """Check if dialogue already exists."""

    def get_existing_messages(self, dialogue_id: UUID) -> dict[[str, Message]]
        """Get all existing messages for a dialogue, keyed by source_id."""

    def should_update(self, existing: Dialogue, new_updated_at: datetime | None) -> bool
        """Determine if existing dialogue should be updated."""

    def register_message_id(self, source_id: str, native_id: UUID)
        """Register a mapping from source message ID to native UUID."""

    def resolve_message_id(self, source_id: str | None) -> UUID | None
        """Resolve a source message ID to native UUID."""

    def _delete_message_content(self, message_id: UUID)
        """Delete content parts and related data for a message."""

    def _soft_delete_messages(self, messages: list[Message]) -> int
        """Soft delete messages that are no longer in source."""

    def _restore_message(self, message: Message)
        """Restore a soft-deleted message."""


```

## llm_archive/extractors/chatgpt.py
```python
class ChatGPTExtractor(BaseExtractor)
    """Extracts ChatGPT conversations into the raw schema."""

    def __init__(self, session: Session, assume_immutable: bool, incremental: bool)

    def extract_dialogue(self, raw: dict[[str, Any]]) -> str | None
        """
        Extract a complete ChatGPT conversation with incremental updates.
        Returns:
            'new' - new dialogue created
            'updated' - existing dialogue updated
            'skipped' - existing dialogue unchanged
            None - extraction failed
        """

    def _sync_messages(self, dialogue_id: UUID, mapping: dict[[str, Any]])
        """
        Incrementally sync messages - preserve UUIDs for unchanged messages.
        This method:
        1. Compares existing messages with new data (unless assume_immutable=True)
        2. Updates changed messages in place
        3. Creates new messages
        4. Soft-deletes messages removed from source
        When assume_immutable=True, existing messages are assumed unchanged and
        skipped without hash comparison. This is faster but won't detect edits.
        """

    def _update_message(self, message: Message, msg_data: dict[[str, Any]], content_hash: str)
        """Update an existing message in place."""

    def _delete_message_metadata(self, message_id: UUID)
        """Delete ChatGPT-specific metadata for a message."""

    def _delete_message_annotations(self, message_id: UUID)
        """Delete annotations for a message (for re-extraction)."""

    def _create_message(self, dialogue_id: UUID, msg_data: dict[[str, Any]], content_hash: str) -> UUID | None
        """Create a new message."""

    def _extract_messages_new(self, dialogue_id: UUID, mapping: dict[[str, Any]])
        """Extract all messages for a new dialogue."""

    def _extract_content_parts(self, message_id: UUID, msg_data: dict[[str, Any]])
        """Extract content parts from a message."""

    def _classify_content_part(self, part: str | dict[[str, Any]]) -> dict[[str, Any]]
        """
        Classify a content part and extract all relevant fields.
        Returns dict with: part_type, text_content, language, media_type, url, source_json
        """

    def _extract_citations(self, content_part_id: UUID, citations: list[dict[[str, Any]]])
        """Extract citations from metadata."""

    def _extract_attachments(self, message_id: UUID, msg_data: dict[[str, Any]])
        """Extract attachments from message metadata."""

    def _extract_chatgpt_meta(self, message_id: UUID, msg_data: dict[[str, Any]])
        """
        Extract ChatGPT-specific metadata and write annotations.
        Writes:
        - gizmo_id as message string annotation
        - has_gizmo as message flag annotation
        - model_slug as message string annotation
        Also creates ChatGPTMessageMeta record for backwards compatibility.
        """

    def _extract_search_group(self, message_id: UUID, group_data: dict[[str, Any]])
        """Extract a search result group and its entries."""

    def _extract_code_execution(self, message_id: UUID, agg_result: dict[[str, Any]])
        """Extract code execution data."""

    def _extract_dalle_generation(self, content_part_id: UUID, part: dict[[str, Any]])
        """Extract DALL-E generation data from a content part."""

    def _extract_canvas_doc(self, message_id: UUID, canvas: dict[[str, Any]])
        """
        Extract canvas document as content_part + annotations.
        Creates:
        - content_part with part_type='canvas' containing the canvas content
        - String annotation for canvas title
        - String annotation for textdoc_id (for version tracking)
        - Numeric annotation for version number
        - ChatGPTCanvasDoc record for backwards compatibility
        """


def mark_latest_canvas_versions(session: Session) -> int
    """
    Mark the latest version of each canvas document.
    Run this after extraction is complete. For each textdoc_id,
    finds the content_part with the highest version number and
    marks it with 'is_latest_canvas_version' flag.
    Returns:
        Count of canvas documents marked as latest.
    Usage:
        extractor.extract_all(data)
        session.commit()
        mark_latest_canvas_versions(session)
    """

def find_wiki_gizmo_messages(session: Session, gizmo_id: str) -> list[UUID]
    """
    Find all message IDs that used a specific gizmo.
    Useful for identifying likely wiki article candidates
    if you know which gizmo was used to generate them.
    Args:
        session: Database session
        gizmo_id: The gizmo ID to search for (e.g., 'g-xxxxx')
    Returns:
        List of message UUIDs
    """

```

## llm_archive/extractors/claude.py
```python
class ClaudeExtractor(BaseExtractor)
    """Extracts Claude conversations into the raw schema."""

    def __init__(self, session: Session, assume_immutable: bool, incremental: bool)

    def extract_dialogue(self, raw: dict[[str, Any]]) -> str | None
        """
        Extract a complete Claude conversation with incremental updates.
        Returns:
            'new' - new dialogue created
            'updated' - existing dialogue updated
            'skipped' - existing dialogue unchanged
            None - extraction failed
        """

    def _sync_messages(self, dialogue_id: UUID, chat_messages: list[dict[[str, Any]]])
        """
        Incrementally sync messages - preserve UUIDs for unchanged messages.
        Claude conversations are linear, so we maintain the chain structure.
        When assume_immutable=True, existing messages are assumed unchanged and
        skipped without hash comparison. This is faster but won't detect edits.
        """

    def _update_message(self, message: Message, msg_data: dict[[str, Any]], content_hash: str, parent_id: UUID | None)
        """Update an existing message in place."""

    def _delete_message_metadata(self, message_id: UUID)
        """Delete Claude-specific metadata for a message."""

    def _create_message(self, dialogue_id: UUID, msg_data: dict[[str, Any]], content_hash: str, parent_id: UUID | None) -> UUID | None
        """Create a new message."""

    def _extract_messages_new(self, dialogue_id: UUID, chat_messages: list[dict[[str, Any]]])
        """Extract all messages for a new dialogue."""

    def _extract_content_parts(self, message_id: UUID, msg_data: dict[[str, Any]])
        """Extract content parts from a Claude message."""

    def _classify_content_part(self, part: dict[[str, Any]]) -> dict[[str, Any]]
        """
        Classify a Claude content part and extract all relevant fields.
        Returns dict with: part_type, text_content, tool_name, tool_use_id, tool_input, media_type, url
        """

    def _extract_citations(self, content_part_id: UUID, citations: list[dict[[str, Any]]])
        """Extract citations from a content part."""

    def _extract_attachments(self, message_id: UUID, msg_data: dict[[str, Any]])
        """Extract attachments from a Claude message."""

    def _extract_claude_meta(self, message_id: UUID, msg_data: dict[[str, Any]])
        """Extract Claude-specific metadata."""


```

## llm_archive/models/annotations.py
```python
def _common_columns(entity_fk: str) -> dict

def _value_columns_and_args(entity_type: EntityType, value_type: ValueType) -> tuple[[dict, tuple]]
    """Return (extra_columns, __table_args__) for a value type."""

def _class_name(entity_type: EntityType, value_type: ValueType) -> str
    """Generate a PascalCase class name: e.g. ContentPartAnnotationFlag."""

def _make_annotation_model(entity_type: EntityType, value_type: ValueType) -> type
    """Generate an ORM model class for one annotation table."""

def get_annotation_model(entity_type: EntityType, value_type: ValueType) -> type
    """Look up the ORM model for a (entity_type, value_type) pair."""

def get_all_annotation_models() -> list[type]
    """Return all 16 annotation model classes (for schema creation)."""

```

## llm_archive/models/derived.py
```python
class PromptResponse(Base)
    """
    Direct prompt-response association without tree dependency.
    Each record pairs a user prompt with one of its responses.
    A prompt can have multiple responses (regenerations).
    Each response appears in exactly one record.
    """

    @property
    def prompt_text(self) -> str | None
        """Aggregate text content from prompt message content_parts."""

    @property
    def response_text(self) -> str | None
        """Aggregate text content from response message content_parts."""

    @property
    def prompt_word_count(self) -> int

    @property
    def response_word_count(self) -> int


class PromptResponseContent(Base)
    """
    Denormalized text content for annotation/search without joins.
    NOTE: This table is maintained for backward compatibility with views.
    Prefer PromptResponse.prompt_text / .response_text properties which
    derive content from the source-of-truth content_parts table.
    """

class AnnotatorCursor(Base)
    """
    Tracks processing state for an annotator version.
    Each (annotator_name, annotator_version, entity_type) triple gets its
    own cursor.  Bumping VERSION in annotator code creates a fresh cursor,
    triggering full reprocessing.
    """

    def __repr__(self) -> str


```

## llm_archive/models/raw.py
```python
class Source(Base)
    """Registry of dialogue sources."""

class Dialogue(Base)
    """Universal dialogue container."""

class Message(Base)
    """Universal message with tree structure support."""

class ContentPart(Base)
    """Content segments within a message."""

class Citation(Base)
    """Citations within content parts."""

class Attachment(Base)
    """File attachments on messages."""

class ChatGPTMessageMeta(Base)
    """ChatGPT-specific message metadata."""

class ChatGPTSearchGroup(Base)
    """ChatGPT search result groups."""

class ChatGPTSearchEntry(Base)
    """ChatGPT search result entries."""

class ChatGPTCodeExecution(Base)
    """ChatGPT code execution records."""

class ChatGPTCodeOutput(Base)
    """ChatGPT code execution outputs."""

class ChatGPTDalleGeneration(Base)
    """ChatGPT DALL-E image generations."""

class ChatGPTCanvasDoc(Base)
    """ChatGPT canvas document operations."""

class ClaudeMessageMeta(Base)
    """Claude-specific message metadata."""

```

## src/ATTIC/chat2obs/graph.py
```python
def conversation_to_graph(conv)

def process_conversation_graph__prompt_and_title(G)

def link_prompts_back_to_source_spans(G)

def subgraphs_to_articles(subgraphs)

```

## src/ATTIC/chat2obs/misc.py
```python
def naive_title_extraction(text)
    """Returns title if first line is just a title suggestion and can be removed"""

def extract_proposed_title(text)
    """
    Assumes that an article was generated with a proposed title. If present, proposed title
    expected to present (on the first line) as:
    * title/section header
      - preceded by several #'s
    * emphasized content
      - encapsulated in **bold**, *emph*, _emph_, [[link]]...
    * prompt = title --> top line contains prompt
    """

def get_links(content)

```

## src/ATTIC/chat2obs/process_chatgpt.py
```python
def load_conversations(root)

def process_conv(conv)

def convs_to_articles(convs, filter_func)

```

## src/ATTIC/chat2obs/vault.py
```python
def read_yaml(txt)

def extract_frontmatter(doc)

def get_wikilinks(text)

def clean_links(wikilinks, collect_aliases)
    """canonicalize aliases, standardize case"""

class ObsDoc

    def __init__(self, title, raw)

    @property
    def node_name(self)
        """canonicalized title"""

    @classmethod
    def from_path(cls, fpath)


def load_vault(obs_root)

def obs_docs_to_graph(corpus)

def identify_candidates(G)
    """Gets nodes in graph that correspond to hyperlinks to non-existent pages in the vault"""

```

## src/ATTIC/conversation_tagger/analysis/comparison.py
```python
def compare_facets(tagged_conversations: List[Dict[[str, Any]]], facet_tag_name: str, facet_attribute: Optional[str], comparison_tags: List[str], min_facet_size: int) -> None
    """Compare specific tags across facets."""

```

## src/ATTIC/conversation_tagger/analysis/debugging.py
```python
def debug_code_detection(tagged_conversations: List[Dict[[str, Any]]], facet_tag_name: str, facet_value: str, max_examples: int)
    """Debug why conversations are being tagged as having code patterns."""

def print_summary(tagged_conversations: List[Dict[[str, Any]]], show_details: bool)
    """Print comprehensive summary with all tag types and optional details."""

```

## src/ATTIC/conversation_tagger/analysis/faceting.py
```python
def get_facet_value(tags: List[Tag], facet_tag_name: str, facet_attribute: Optional[str]) -> str
    """Extract facet value from a conversation's tags."""

def do_facet_conversations(tagged_conversations: List[Dict[[str, Any]]], facet_tag_name: str, facet_attribute: Optional[str], max_facets: int)
    """Group conversations by facet values."""

def print_faceted_summary(tagged_conversations: List[Dict[[str, Any]]], facet_tag_name: str, facet_attribute: Optional[str], show_details: bool, max_facets: int)
    """Print tag summary broken down by facets."""

```

## src/ATTIC/conversation_tagger/core/conversation_aggregator.py
```python
class ConversationAggregator
    """Aggregates exchange tags into conversation-level tags."""

    def aggregate_to_conversation(self, tagged_exchanges: List[Dict[[str, Any]]], conversation: Dict[[str, Any]]) -> Dict[[str, Any]]
        """Aggregate exchange tags to conversation level."""

    def _aggregate_presence_tags(self, all_exchange_tags: List[Tag]) -> List[Tag]
        """Create conversation tags based on presence of exchange tags."""

    def _aggregate_frequency_tags(self, all_exchange_tags: List[Tag], exchange_count: int) -> List[Tag]
        """Create tags based on frequency of exchange tags."""

    def _aggregate_statistical_tags(self, all_exchange_tags: List[Tag]) -> List[Tag]
        """Create statistical aggregation tags."""

    def _aggregate_conversation_structure_tags(self, tagged_exchanges: List[Dict[[str, Any]]]) -> List[Tag]
        """Create tags about conversation structure."""

    def _aggregate_gizmo_plugin_tags(self, conversation: Dict[[str, Any]]) -> List[Tag]
        """Add gizmo/plugin tags from conversation metadata."""

    def _calculate_aggregation_stats(self, tagged_exchanges: List[Dict[[str, Any]]], all_exchange_tags: List[Tag]) -> Dict[[str, Any]]
        """Calculate detailed aggregation statistics."""


```

## src/ATTIC/conversation_tagger/core/exchange.py
```python
@dataclass
class Exchange
    """
    Represents a complete user-assistant exchange, including continuations.
    An exchange consists of:
    - Initial user prompt
    - Assistant response(s) 
    - Any continuation prompts ("more", "continue") and their responses
    """

    def get_user_text(self) -> str
        """Get combined text from all user messages in this exchange."""

    def get_assistant_text(self) -> str
        """Get combined text from all assistant messages in this exchange."""

    def get_total_text(self) -> str
        """Get all text from this exchange."""

    def has_continuations(self) -> bool
        """Check if this exchange has continuation prompts."""

    def is_code_focused(self) -> bool
        """Quick check if this exchange seems code-focused (for optimization)."""

    def get_user_prompt_stats(self) -> Dict[[str, Any]]
        """Get statistics about user prompts in this exchange."""

    def get_assistant_response_stats(self) -> Dict[[str, Any]]
        """Get statistics about assistant responses in this exchange."""


```

## src/ATTIC/conversation_tagger/core/exchange_parser.py
```python
class ExchangeParser
    """Parses conversations into exchanges."""

    def __init__(self)

    def parse_conversation(self, conversation: Dict[[str, Any]]) -> List[Exchange]
        """Parse a conversation into a list of exchanges."""

    def _group_into_exchanges(self, messages: List[Dict[[str, Any]]], conversation_id: str) -> List[Exchange]
        """Group messages into exchanges."""

    def _is_continuation_prompt(self, message: Dict[[str, Any]]) -> bool
        """Check if a user message is a continuation prompt."""

    def _is_quote_elaborate_pattern(self, text: str) -> bool
        """Check if text follows the quote + elaborate pattern."""

    def _create_exchange(self, user_messages: List[Dict[[str, Any]]], assistant_messages: List[Dict[[str, Any]]], conversation_id: str, exchange_index: int) -> Exchange
        """Create an Exchange object from messages."""


```

## src/ATTIC/conversation_tagger/core/exchange_rules.py
```python
def user_has_code_blocks(exchange: Exchange) -> bool
    """Check if user messages contain code blocks."""

def user_has_attachments(exchange: Exchange) -> bool
    """Check if user messages have attachments."""

def user_has_error_messages(exchange: Exchange) -> bool
    """Check if user messages contain error patterns."""

def user_prompt_length_category(exchange: Exchange) -> Tag
    """Categorize user prompt length."""

def user_is_continuation(exchange: Exchange) -> bool
    """Check if this exchange started with a continuation prompt."""

def assistant_has_code_blocks(exchange: Exchange) -> bool
    """Check if assistant messages contain code blocks."""

def assistant_has_wiki_links(exchange: Exchange) -> bool
    """Check if assistant messages contain wiki-style links."""

def assistant_has_latex_math(exchange: Exchange) -> bool
    """Check if assistant messages contain mathematical formulas."""

def assistant_response_length_category(exchange: Exchange) -> Tag
    """Categorize assistant response length."""

def assistant_has_reasoning(exchange: Exchange) -> bool
    """Check if assistant messages contain reasoning/thinking content."""

def exchange_is_coding_focused(exchange: Exchange) -> bool
    """Check if the entire exchange is focused on coding."""

def exchange_is_wiki_article_focused(exchange: Exchange) -> bool
    """Check if exchange is focused on wiki/documentation content."""

def exchange_has_error_resolution(exchange: Exchange) -> bool
    """Check if exchange involves error troubleshooting."""

def exchange_interaction_pattern(exchange: Exchange) -> Tag
    """Determine the interaction pattern of this exchange."""

```

## src/ATTIC/conversation_tagger/core/exchange_tagger.py
```python
class ExchangeTagger
    """Tags individual exchanges with rules specific to exchange-level analysis."""

    def __init__(self)

    def add_user_rule(self, tag_name: str, rule_function: Callable, description: str)
        """Add rule that analyzes user messages in the exchange."""

    def add_assistant_rule(self, tag_name: str, rule_function: Callable, description: str)
        """Add rule that analyzes assistant messages in the exchange."""

    def add_exchange_rule(self, tag_name: str, rule_function: Callable, description: str)
        """Add rule that analyzes the entire exchange."""

    def add_supplemental_rule(self, tag_name: str, rule_function: Callable, description: str)
        """Add rule that depends on existing tags."""

    def tag_exchange(self, exchange: Exchange) -> Dict[[str, Any]]
        """Apply all tagging rules to an exchange."""

    def tag_exchanges(self, exchanges: List[Exchange]) -> List[Dict[[str, Any]]]
        """Tag multiple exchanges."""

    def _normalize_tag(self, result: Union[[bool, str, Tag]], tag_name: str) -> Tag
        """Convert rule results to Tag objects."""


```

## src/ATTIC/conversation_tagger/core/tag.py
```python
class Tag
    """Represents a tag with optional key-value attributes."""

    def __init__(self, name: str)

    def __str__(self)

    def __repr__(self)

    def __eq__(self, other)

    def __hash__(self)

    def matches(self, name: str) -> bool
        """Check if tag matches name and optional attribute criteria."""


```

## src/ATTIC/conversation_tagger/core/tagger.py
```python
class ConversationTagger
    """
    Enhanced tagging system that analyzes conversations at both exchange and conversation levels.
    Flow:
    1. Parse conversation into exchanges
    2. Tag each exchange with exchange-level rules
    3. Aggregate exchange tags to conversation-level tags
    4. Apply conversation-level supplemental rules
    """

    def __init__(self, use_exchange_analysis: bool)

    def add_user_rule(self, tag_name: str, rule_function: Callable, description: str)
        """Add rule that analyzes user messages in exchanges."""

    def add_assistant_rule(self, tag_name: str, rule_function: Callable, description: str)
        """Add rule that analyzes assistant messages in exchanges."""

    def add_exchange_rule(self, tag_name: str, rule_function: Callable, description: str)
        """Add rule that analyzes entire exchanges."""

    def add_exchange_supplemental_rule(self, tag_name: str, rule_function: Callable, description: str)
        """Add exchange-level supplemental rule."""

    def add_base_rule(self, tag_name: str, rule_function: Callable, description: str)
        """Add a conversation-level base rule (legacy API)."""

    def add_multi_tag_rule(self, rule_name: str, rule_function: Callable, description: str)
        """Add a conversation-level multi-tag rule (legacy API)."""

    def add_supplemental_rule(self, tag_name: str, rule_function: Callable, description: str)
        """Add a conversation-level supplemental rule (legacy API)."""

    def tag_conversation(self, conversation: Dict[[str, Any]]) -> Dict[[str, Any]]
        """Tag a conversation using exchange-based analysis."""

    def _tag_conversation_exchange_based(self, conversation: Dict[[str, Any]]) -> Dict[[str, Any]]
        """Tag conversation using exchange-based analysis."""

    def _tag_conversation_legacy(self, conversation: Dict[[str, Any]]) -> Dict[[str, Any]]
        """Tag conversation using legacy conversation-level analysis."""

    def tag_conversations(self, conversations: List[Dict[[str, Any]]]) -> List[Dict[[str, Any]]]
        """Tag multiple conversations."""

    def get_exchange_analysis(self, conversation: Dict[[str, Any]]) -> List[Dict[[str, Any]]]
        """Get detailed exchange-level analysis for a conversation."""

    def filter_by_tags(self, tagged_conversations: List[Dict[[str, Any]]], include_tags: List[Union[[str, Dict]]], exclude_tags: List[Union[[str, Dict]]]) -> List[Dict[[str, Any]]]
        """Filter conversations by tags with attribute support."""

    def _matches_criterion(self, tags: List[Tag], criterion: Union[[str, Dict]]) -> bool
        """Check if any tag matches the given criterion."""

    def _normalize_tag(self, tag: Union[[str, Tag]]) -> Tag
        """Convert string tags to Tag objects."""


```

## src/ATTIC/conversation_tagger/detection/code_indicators.py
```python
def has_code_blocks(conversation: Dict[[str, Any]]) -> bool
    """Check for explicit code blocks (``` markdown syntax)."""

def has_function_definitions(conversation: Dict[[str, Any]]) -> bool
    """Check for function/class definition keywords."""

def has_import_statements(conversation: Dict[[str, Any]]) -> bool
    """Check for import/require statements."""

def has_script_headers(conversation: Dict[[str, Any]]) -> bool
    """Check for script headers and system includes."""

def has_high_keyword_density(conversation: Dict[[str, Any]]) -> bool
    """Check for high density of programming keywords in large text."""

def has_code_structure_patterns(conversation: Dict[[str, Any]]) -> bool
    """Check for actual code structure patterns (syntax combinations that suggest real code)."""

def has_code_patterns(conversation: Dict[[str, Any]]) -> bool
    """Check for any code patterns (combines individual indicators)."""

```

## src/ATTIC/conversation_tagger/detection/content.py
```python
def has_large_content(conversation: Dict[[str, Any]], min_length: int) -> bool
    """Check if conversation has unusually large content anywhere."""

def has_github_repos(conversation: Dict[[str, Any]]) -> bool
    """Check if GitHub repositories were selected for context."""

def has_canvas_operations(conversation: Dict[[str, Any]]) -> bool
    """Check for canvas/document operations."""

def has_web_search(conversation: Dict[[str, Any]]) -> bool
    """Check for web search operations."""

def has_reasoning_thoughts(conversation: Dict[[str, Any]]) -> bool
    """Check for reasoning/thinking patterns."""

def has_code_execution(conversation: Dict[[str, Any]]) -> bool
    """Check for code execution artifacts."""

```

## src/ATTIC/conversation_tagger/detection/exchange_rules.py
```python
def user_has_quote_elaborate(exchange: Exchange) -> bool
    """Check if user messages contain quote+elaborate continuation pattern."""

```

## src/ATTIC/conversation_tagger/detection/first_user.py
```python
def first_user_has_large_content(conversation: Dict[[str, Any]], min_length: int) -> bool
    """Check if the first user message has large content."""

def first_user_has_code_patterns(conversation: Dict[[str, Any]]) -> bool
    """Check if the first user message contains code patterns."""

def first_user_has_attachments(conversation: Dict[[str, Any]]) -> bool
    """Check if the first user message has attachments."""

def first_user_has_code_attachments(conversation: Dict[[str, Any]]) -> bool
    """Check if the first user message has code-related attachments."""

```

## src/ATTIC/conversation_tagger/detection/helpers.py
```python
def get_all_user_messages(conversation: Dict[[str, Any]]) -> List[Dict[[str, Any]]]
    """Get all user messages in chronological order."""

def get_first_user_message(conversation: Dict[[str, Any]]) -> Dict[[str, Any]]
    """Find the first user message in the conversation."""

def get_all_text_from_message(message: Dict[[str, Any]]) -> str
    """Extract all text content from a message."""

def get_all_conversation_text(conversation: Dict[[str, Any]]) -> str
    """Extract all text content from a conversation."""

```

## src/ATTIC/conversation_tagger/detection/structured_tags.py
```python
def create_conversation_length_tag(conversation: Dict[[str, Any]]) -> Tag
    """Create structured tag for conversation length."""

def create_prompt_stats_tag(conversation: Dict[[str, Any]]) -> Tag
    """Create structured tag for prompt statistics."""

def create_gizmo_plugin_tags(conversation: Dict[[str, Any]]) -> List[Tag]
    """Create structured tags for gizmos and plugins."""

```

## src/ATTIC/conversation_tagger/detection/wiki_markdown.py
```python
def has_wiki_links(conversation: Dict[[str, Any]]) -> bool
    """Check for Obsidian-style wiki links [[link text]]."""

def has_latex_math(conversation: Dict[[str, Any]]) -> bool
    """Check for LaTeX/MathJax mathematical formulas."""

def has_markdown_features(conversation: Dict[[str, Any]]) -> bool
    """Check for distinctive markdown features beyond basic formatting."""

def has_documentation_patterns(conversation: Dict[[str, Any]]) -> bool
    """Check for patterns typical of documentation or academic writing."""

```

## src/ATTIC/conversation_tagger/factory.py
```python
def create_default_tagger() -> ConversationTagger
    """
    Create a conversation tagger with all default rules.
    Args:
        use_exchange_analysis: If True, uses exchange-based analysis (recommended).
                              If False, uses legacy conversation-level analysis only.
    """

def _configure_exchange_based_tagger(tagger: ConversationTagger)
    """Configure tagger with exchange-based rules."""

def has_code_blocks_conversation_level(conversation: Dict[[str, Any]]) -> bool
    """Legacy conversation-level code block detection."""

```

## src/ATTIC/conversation_tagger/tests/test_exchange_minimal.py
```python
def create_test_message(role: str, text: str, create_time: int)
    """Helper to create test messages."""

def create_test_conversation(messages: list, conversation_id: str)
    """Helper to create test conversations from message list."""

class TestExchange

    def test_exchange_creation(self)

    def test_exchange_with_continuations(self)


class TestExchangeParser

    def test_simple_exchange_parsing(self)

    def test_continuation_parsing(self)

    def test_quote_elaborate_pattern(self)


class TestExchangeTagging

    def test_basic_exchange_tagging(self)

    def test_quote_elaborate_tagging(self)

    def test_wiki_exchange_tagging(self)


class TestConversationAggregation

    def test_basic_aggregation(self)


class TestIntegration

    def test_full_pipeline(self)
        """Test the complete exchange analysis pipeline."""


```

## tests/conftest.py
```python
def pytest_configure(config)
    """Configure pytest markers."""

def pytest_collection_modifyitems(config, items)
    """Automatically mark tests in integration folder."""

```

## tests/integration/conftest.py
```python
def get_test_db_url() -> str
    """Get test database URL from environment."""

def db_engine() -> Generator[[Engine, None, None]]
    """Create database engine for tests."""

def setup_schemas(db_engine)
    """Initialize schemas once per test session via ORM."""

def db_session(db_engine, setup_schemas) -> Generator[[Session, None, None]]
    """Create a database session with transaction rollback."""

def clean_db_session(db_session) -> Session
    """Alias for db_session."""

def chatgpt_simple_conversation() -> dict
    """Simple linear ChatGPT conversation."""

def chatgpt_branched_conversation() -> dict
    """ChatGPT conversation with branching (regenerated response)."""

def chatgpt_conversation_with_code() -> dict
    """ChatGPT conversation with code content — nested parts structure."""

def chatgpt_conversation_with_image() -> dict
    """ChatGPT conversation with image content — multimodal parts."""

def chatgpt_conversations(chatgpt_simple_conversation, chatgpt_branched_conversation) -> list[dict]
    """List of ChatGPT test conversations."""

def claude_simple_conversation() -> dict
    """Simple Claude conversation."""

def claude_conversation_with_thinking() -> dict
    """Claude conversation with thinking blocks."""

def claude_conversation_with_tool_use() -> dict
    """Claude conversation with tool use."""

def claude_conversations(claude_simple_conversation, claude_conversation_with_thinking, claude_conversation_with_tool_use) -> list[dict]
    """List of Claude test conversations."""

def populated_chatgpt_db(clean_db_session, chatgpt_simple_conversation)
    """Database with a single ChatGPT conversation imported."""

def populated_claude_db(clean_db_session, claude_simple_conversation)
    """Database with a single Claude conversation imported."""

def fully_populated_db(clean_db_session, chatgpt_simple_conversation, chatgpt_branched_conversation, claude_simple_conversation)
    """Database with multiple conversations and derived data."""

```

## tests/integration/test_annotations.py
```python
class TestAnnotationWriterIntegration
    """Integration tests for AnnotationWriter."""

    def test_write_flag_creates_record(self, clean_db_session, chatgpt_simple_conversation)
        """Writing a flag creates a record in flag table."""

    def test_write_string_creates_record(self, clean_db_session, chatgpt_simple_conversation)
        """Writing a string creates a record in string table."""

    def test_write_numeric_creates_record(self, clean_db_session, chatgpt_simple_conversation)
        """Writing a numeric creates a record in numeric table."""

    def test_write_json_creates_record(self, clean_db_session, chatgpt_simple_conversation)
        """Writing JSON creates a record in json table."""

    def test_write_duplicate_flag_returns_false(self, clean_db_session, chatgpt_simple_conversation)
        """Writing duplicate flag returns False (no new record)."""

    def test_write_multi_value_string(self, clean_db_session, chatgpt_simple_conversation)
        """Can write multiple values for same string key."""

    def test_write_from_annotation_result(self, clean_db_session, chatgpt_simple_conversation)
        """Can write from AnnotationResult object."""


class TestAnnotationReaderIntegration
    """Integration tests for AnnotationReader."""

    def test_find_entities_with_flag(self, clean_db_session, chatgpt_simple_conversation)
        """Can find all entities with a specific flag."""

    def test_find_entities_with_string_value(self, clean_db_session, chatgpt_simple_conversation)
        """Can find entities with specific string value."""

    def test_get_all_keys(self, clean_db_session, chatgpt_simple_conversation)
        """Can get all annotations for an entity."""


class TestPromptResponseAnnotatorIntegration
    """Integration tests for prompt-response annotators."""

    def wiki_conversation(self)
        """Conversation with wiki-style content."""

    def test_wiki_candidate_annotator_end_to_end(self, clean_db_session, wiki_conversation)
        """Test WikiCandidateAnnotator with real database."""

    def test_naive_title_annotator_end_to_end(self, clean_db_session, wiki_conversation)
        """Test NaiveTitleAnnotator with real database."""

    def test_annotator_prerequisite_filtering(self, clean_db_session, chatgpt_simple_conversation)
        """Test that NaiveTitleAnnotator respects REQUIRES_STRINGS."""


class TestGizmoAnnotationIntegration
    """Integration tests for gizmo annotation writing during extraction."""

    def test_gizmo_annotation_written_during_extraction(self, clean_db_session)
        """Test that gizmo_id is written as annotation during extraction."""


```

## tests/integration/test_extraction_diagnostics.py
```python
def test_branched_conversation_diagnostic(db_session, chatgpt_branched_conversation)
    """Diagnostic test to see what's actually extracted."""

def test_simple_parent_child_relationship(db_session)
    """Test if parent-child relationships work at all."""

def test_branched_extraction_step_by_step(db_session)
    """Test extraction with a known branched structure."""

```

## tests/integration/test_extractors.py
```python
class TestChatGPTExtractor
    """Tests for ChatGPT extractor."""

    def test_extract_simple_conversation(self, db_session, chatgpt_simple_conversation)
        """Test extracting a simple linear conversation."""

    def test_extract_messages(self, db_session, chatgpt_simple_conversation)
        """Test that messages are extracted correctly."""

    def test_extract_content_parts(self, db_session, chatgpt_simple_conversation)
        """Test that content parts are extracted."""

    def test_extract_branched_conversation(self, db_session, chatgpt_branched_conversation)
        """Test extracting a conversation with branches."""

    def test_extract_code_content(self, db_session, chatgpt_conversation_with_code)
        """Test extracting code execution content with language."""

    def test_extract_image_content(self, db_session, chatgpt_conversation_with_image)
        """Test extracting image content with media type and URL."""

    def test_missing_conversation_id(self, db_session)
        """Test handling of conversation without ID."""

    def test_extract_all(self, db_session, chatgpt_conversations)
        """Test extracting multiple conversations."""


class TestClaudeExtractor
    """Tests for Claude extractor."""

    def test_extract_simple_conversation(self, db_session, claude_simple_conversation)
        """Test extracting a simple Claude conversation."""

    def test_extract_messages_linear(self, db_session, claude_simple_conversation)
        """Test that Claude messages form a linear chain."""

    def test_role_normalization(self, db_session, claude_simple_conversation)
        """Test that 'human' role is normalized to 'user'."""

    def test_extract_thinking_blocks(self, db_session, claude_conversation_with_thinking)
        """Test extracting thinking content."""

    def test_extract_tool_use(self, db_session, claude_conversation_with_tool_use)
        """Test extracting tool use content with all fields."""

    def test_extract_tool_result(self, db_session, claude_conversation_with_tool_use)
        """Test extracting tool result content with linked tool_use_id."""

    def test_missing_uuid(self, db_session)
        """Test handling of conversation without UUID."""

    def test_extract_all(self, db_session, claude_conversations)
        """Test extracting multiple Claude conversations."""


class TestExtractorTimestamps
    """Tests for timestamp parsing."""

    def test_chatgpt_epoch_timestamps(self, db_session, chatgpt_simple_conversation)
        """Test parsing ChatGPT epoch timestamps."""

    def test_claude_iso_timestamps(self, db_session, claude_simple_conversation)
        """Test parsing Claude ISO timestamps."""


```

## tests/integration/test_idempotency.py
```python
class TestChatGPTIdempotency
    """Tests for ChatGPT idempotent import."""

    def test_reimport_unchanged_skips(self, clean_db_session, chatgpt_simple_conversation)
        """Test that reimporting unchanged conversation is skipped."""

    def test_reimport_updated_updates(self, clean_db_session, chatgpt_simple_conversation)
        """Test that reimporting updated conversation updates it."""

    def test_reimport_messages_refreshed(self, clean_db_session, chatgpt_simple_conversation)
        """Test that messages are refreshed on update."""

    def test_extract_all_mixed_results(self, clean_db_session, chatgpt_simple_conversation)
        """Test extract_all with mix of new, updated, and skipped."""


class TestClaudeIdempotency
    """Tests for Claude idempotent import."""

    def test_reimport_unchanged_skips(self, clean_db_session, claude_simple_conversation)
        """Test that reimporting unchanged conversation is skipped."""

    def test_reimport_updated_updates(self, clean_db_session, claude_simple_conversation)
        """Test that reimporting updated conversation updates it."""


class TestCrossSourceIdempotency
    """Tests for idempotency across sources."""

    def test_same_content_different_sources(self, clean_db_session)
        """Test that same content from different sources creates separate records."""


class TestPartialUpdate
    """Tests for partial update scenarios."""

    def test_conversation_extended(self, clean_db_session, chatgpt_simple_conversation)
        """Test handling of conversation that has been extended."""


class TestUUIDPreservation
    """Tests for message UUID preservation during updates."""

    def test_unchanged_messages_keep_uuids(self, clean_db_session, chatgpt_simple_conversation)
        """Test that unchanged messages keep their UUIDs."""

    def test_changed_message_keeps_uuid_updates_content(self, clean_db_session, chatgpt_simple_conversation)
        """Test that changed messages keep their UUID but update content."""

    def test_claude_unchanged_messages_keep_uuids(self, clean_db_session, claude_simple_conversation)
        """Test UUID preservation for Claude extractor."""


class TestSoftDelete
    """Tests for soft-delete behavior when messages are removed from source."""

    def test_removed_message_soft_deleted(self, clean_db_session, chatgpt_simple_conversation)
        """Test that messages removed from source are soft-deleted."""

    def test_soft_deleted_message_restored_on_reappear(self, clean_db_session, chatgpt_simple_conversation)
        """Test that soft-deleted message is restored if it reappears."""

    def test_content_hash_detects_changes(self, clean_db_session, chatgpt_simple_conversation)
        """Test that content hash correctly detects changed messages."""


class TestAssumeImmutableFlag
    """Tests for assume_immutable optimization flag."""

    def test_immutable_mode_skips_hash_check(self, clean_db_session, chatgpt_simple_conversation)
        """Test that immutable mode skips content hash comparison."""

    def test_mutable_mode_detects_changes(self, clean_db_session, chatgpt_simple_conversation)
        """Test that mutable mode (default) detects content changes."""

    def test_immutable_mode_still_creates_new_messages(self, clean_db_session, chatgpt_simple_conversation)
        """Test that immutable mode still creates new messages properly."""

    def test_immutable_mode_still_soft_deletes(self, clean_db_session, chatgpt_simple_conversation)
        """Test that immutable mode still soft-deletes removed messages."""

    def test_immutable_mode_restores_soft_deleted(self, clean_db_session, chatgpt_simple_conversation)
        """Test that immutable mode restores soft-deleted messages without re-hashing."""

    def test_claude_immutable_mode(self, clean_db_session, claude_simple_conversation)
        """Test that assume_immutable works for Claude extractor too."""


class TestIncrementalMode
    """Tests for incremental (delta import) mode."""

    def test_incremental_mode_skips_soft_delete(self, clean_db_session, chatgpt_simple_conversation)
        """Test that incremental mode doesn't soft-delete missing messages."""

    def test_non_incremental_mode_does_soft_delete(self, clean_db_session, chatgpt_simple_conversation)
        """Test that non-incremental mode (default) does soft-delete missing messages."""

    def test_incremental_mode_still_adds_new_messages(self, clean_db_session, chatgpt_simple_conversation)
        """Test that incremental mode still adds new messages."""

    def test_incremental_mode_still_updates_changed_messages(self, clean_db_session, chatgpt_simple_conversation)
        """Test that incremental mode still updates changed messages."""

    def test_claude_incremental_mode(self, clean_db_session, claude_simple_conversation)
        """Test that incremental mode works for Claude extractor."""

    def test_combined_immutable_and_incremental(self, clean_db_session, chatgpt_simple_conversation)
        """Test combining immutable and incremental modes for fastest delta imports."""


```

## tests/integration/test_models.py
```python
class TestRawModels
    """Tests for raw schema models with database persistence."""

    def test_create_dialogue(self, db_session)
        """Test creating and persisting a dialogue."""

    def test_create_message_with_parent(self, db_session)
        """Test creating messages with parent relationship."""

    def test_create_content_part(self, db_session)
        """Test creating content parts."""

    def test_dialogue_messages_relationship(self, db_session)
        """Test dialogue to messages relationship."""


class TestCascadeDeletes
    """Tests for cascade delete behavior."""

    def test_delete_dialogue_cascades_to_messages(self, db_session)
        """Test that deleting dialogue deletes messages."""

    def test_delete_message_cascades_to_content(self, db_session)
        """Test that deleting message deletes content parts."""


```

## tests/integration/test_prompt_response_builder.py
```python
class TestPromptResponseBuilderBasic
    """Basic tests for PromptResponseBuilder."""

    def test_build_for_simple_conversation(self, clean_db_session, chatgpt_simple_conversation)
        """Test building prompt-responses for a simple conversation."""

    def test_pairs_user_with_assistant(self, clean_db_session, chatgpt_simple_conversation)
        """Test that user messages are paired with assistant responses."""

    def test_response_position_ordering(self, clean_db_session, chatgpt_simple_conversation)
        """Test that response_position reflects message order."""


class TestPromptResponseBuilderClaude
    """Tests specific to Claude conversations."""

    def test_build_for_claude_conversation(self, clean_db_session, claude_simple_conversation)
        """Test building prompt-responses for Claude conversation."""

    def test_linear_chain_pairing(self, clean_db_session, claude_simple_conversation)
        """Test that linear chains are paired correctly."""


class TestPromptResponseBuilderBranched
    """Tests for branched conversations."""

    def test_build_for_branched_conversation(self, clean_db_session, chatgpt_branched_conversation)
        """Test building prompt-responses for branched conversation."""

    def test_uses_parent_id_for_pairing(self, clean_db_session, chatgpt_branched_conversation)
        """Test that parent_id is used to find the correct prompt."""


class TestPromptResponseBuilderIdempotency
    """Tests for idempotent building."""

    def test_rebuild_clears_existing(self, clean_db_session, chatgpt_simple_conversation)
        """Test that rebuilding clears and recreates records."""

    def test_build_for_single_dialogue(self, clean_db_session, chatgpt_simple_conversation, chatgpt_branched_conversation)
        """Test building for a single dialogue doesn't affect others."""


class TestPromptResponseBuilderEdgeCases
    """Edge case tests."""

    def test_handles_system_messages(self, clean_db_session)
        """Test handling of conversations with system messages."""

    def test_handles_empty_dialogue(self, clean_db_session)
        """Test handling of dialogue with no messages."""

    def test_handles_user_only_dialogue(self, clean_db_session)
        """Test handling of dialogue with only user messages."""


```

## tests/unit/conftest.py
```python
def chatgpt_simple_conversation() -> dict
    """Simple linear ChatGPT conversation (no branches)."""

def claude_simple_conversation() -> dict
    """Simple Claude conversation."""

def mock_session()
    """Create a mock SQLAlchemy session for unit tests."""

```

## tests/unit/test_annotation_models.py
```python
class TestAnnotationModelFactory
    """Verify the factory generates all expected models."""

    def test_generates_16_models(self)

    def test_all_entity_value_combinations_exist(self)

    def test_each_entity_type_has_config(self)


class TestAnnotationModelTableNames
    """Verify table names follow the convention."""

    def test_table_name(self, et, vt, expected)

    def test_all_tables_in_derived_schema(self)


class TestAnnotationModelClassNames
    """Verify generated class names are PascalCase."""

    def test_class_name(self, et, vt, expected)


class TestAnnotationModelColumns
    """Verify column presence varies correctly by value type."""

    def _column_names(self, model) -> set[str]

    def test_all_models_have_common_columns(self)

    def test_flag_model_has_no_annotation_value(self)

    def test_valued_models_have_annotation_value(self, vt)

    def test_entity_id_is_not_nullable(self)


class TestAnnotationModelForeignKeys
    """Verify FK references point to the correct entity tables."""

    def _get_fk_target(self, model) -> str

    def test_fk_target(self, et, expected_target)


class TestAnnotationModelConstraints
    """Verify unique constraints vary by value type."""

    def _unique_columns(self, model) -> list[tuple[[str, Ellipsis]]]
        """Extract unique constraint column sets."""

    def test_flag_unique_on_entity_and_key(self)

    def test_string_unique_on_entity_key_value(self)

    def test_numeric_unique_on_entity_key_value(self)

    def test_json_unique_on_entity_and_key(self)


class TestConvenienceAliases
    """Verify module-level aliases resolve to the right models."""

    def test_content_part_flag_alias(self)

    def test_content_part_string_alias(self)

    def test_prompt_response_flag_alias(self)

    def test_prompt_response_string_alias(self)


class TestAnnotationModelExtensibility
    """Verify adding entity types only requires config changes."""

    def test_entity_config_covers_all_entity_types(self)
        """Every EntityType has an FK target configured."""


```

## tests/unit/test_annotations.py
```python
class TestAnnotationResult
    """Test AnnotationResult dataclass."""

    def test_create_flag_result(self)
        """Flag results only need key."""

    def test_create_string_result(self)
        """String results need key and value."""

    def test_create_numeric_result(self)
        """Numeric results need key and numeric value."""

    def test_create_json_result(self)
        """JSON results can store complex data."""

    def test_default_value_type_is_string(self)
        """Default value_type should be STRING."""

    def test_default_source_is_heuristic(self)
        """Default source should be 'heuristic'."""


class TestEnums
    """Test EntityType and ValueType enums."""

    def test_entity_types(self)
        """All expected entity types exist."""

    def test_value_types(self)
        """All expected value types exist."""


class TestAnnotationWriterInterface
    """Test AnnotationWriter interface without database."""

    def test_table_name_generation(self)
        """Test table name generation for entity/value type combos."""


def db_session()
    """
    Create a database session for integration tests.
    This fixture is a placeholder - actual implementation would
    need a test database setup.
    """

class TestAnnotationWriterIntegration
    """Integration tests for AnnotationWriter (require database)."""

    def test_write_flag_creates_record(self, db_session)
        """Writing a flag creates a record in flag table."""

    def test_write_string_creates_record(self, db_session)
        """Writing a string creates a record in string table."""

    def test_write_duplicate_flag_returns_false(self, db_session)
        """Writing duplicate flag returns False (no new record)."""

    def test_write_multi_value_string(self, db_session)
        """Can write multiple values for same string key."""


class TestAnnotationReaderIntegration
    """Integration tests for AnnotationReader (require database)."""

    def test_find_entities_with_flag(self, db_session)
        """Can find all entities with a specific flag."""

    def test_find_entities_with_string_value(self, db_session)
        """Can find entities with specific string value."""


```

## tests/unit/test_annotator_logic.py
```python
def _make_content_part(text: str, part_type: str, role: str) -> ContentPartData

def _make_prompt_response(response_text: str, prompt_text: str, response_word_count: int | None) -> PromptResponseData

class TestContentPartAnnotatorConfig

    def test_entity_type(self)

    def test_code_block_filters(self)

    def test_latex_no_role_filter(self)


class TestCodeBlockAnnotator

    def _annotate(self, text: str) -> list[AnnotationResult]

    def test_detects_single_code_block(self)

    def test_counts_multiple_blocks(self)

    def test_no_match_returns_empty(self)

    def test_empty_text_returns_empty(self)

    def test_none_text_returns_empty(self)


class TestLatexContentAnnotator

    def _annotate(self, text: str) -> list[AnnotationResult]

    def test_detects_display_math(self)

    def test_detects_inline_math(self)

    def test_detects_commands(self)

    def test_no_latex_returns_empty(self)


class TestWikiLinkContentAnnotator

    def _annotate(self, text: str) -> list[AnnotationResult]

    def test_detects_wiki_links(self)

    def test_no_links_returns_empty(self)


class TestWikiCandidateAnnotator

    def _annotate(self, response_text: str, word_count: int | None) -> list[AnnotationResult]

    def test_detects_wiki_article(self)

    def test_no_response_returns_empty(self)


class TestNaiveTitleAnnotator

    def _annotate(self, response_text: str) -> list[AnnotationResult]

    def test_extracts_h1_title(self)


```

## tests/unit/test_base_annotator.py
```python
class StubAnnotator(BaseAnnotator)
    """Minimal concrete annotator for testing BaseAnnotator mechanics."""

    def __init__(self, session, entities)

    def _iter_entities_after(self, after)

    def _entity_id(self, data)

    def _created_at(self, data)

    def annotate(self, data)


def _make_entity(created_at: datetime, should_annotate: bool)

def _make_cursor(name: str, version: str, hwm: datetime | None) -> AnnotatorCursor

class TestBaseAnnotatorCursorCreation
    """Test cursor creation on first run."""

    def test_creates_cursor_when_none_exists(self)
        """First call to _get_or_create_cursor creates a new cursor."""

    def test_returns_existing_cursor(self)
        """Returns existing cursor if one matches."""


class TestBaseAnnotatorCursorUpdate
    """Test cursor update after processing."""

    def test_update_advances_hwm(self)

    def test_update_accumulates_stats(self)
        """Stats are cumulative across runs."""


class TestBaseAnnotatorCompute
    """Test the compute() orchestration."""

    def test_compute_processes_entities_after_hwm(self)
        """Only entities newer than HWM are processed."""

    def test_compute_updates_hwm_to_latest(self)
        """HWM advances to the latest entity's created_at."""

    def test_compute_returns_annotation_count(self)
        """compute() returns number of annotations created."""

    def test_compute_tracks_runtime(self)
        """cumulative_runtime_seconds increases after compute()."""

    def test_compute_noop_when_no_new_entities(self)
        """compute() returns 0 and HWM unchanged when nothing new."""


class TestBaseAnnotatorVersioning
    """Test that version changes create separate cursors."""

    def test_different_versions_get_different_cursors(self)
        """Changing VERSION should query for a new cursor key."""


class TestBaseAnnotatorWriteResult
    """Test _write_result dispatch."""

    def test_dispatches_flag(self)

    def test_dispatches_string(self)

    def test_dispatches_numeric(self)

    def test_dispatches_json(self)


class V1(StubAnnotator)

class V2(StubAnnotator)

```

## tests/unit/test_chatgpt_extractor_annotations.py
```python
def make_message_data(msg_id: str, role: str, content: str, gizmo_id: str, model_slug: str, canvas: dict) -> dict
    """Create mock ChatGPT message data."""

def make_canvas_data(textdoc_id: str, version: int, title: str, textdoc_type: str, content: str) -> dict
    """Create mock canvas data."""

class TestMessageDataConstruction
    """Test message data fixture construction."""

    def test_basic_message_data(self)
        """Basic message data should have required fields."""

    def test_message_with_gizmo(self)
        """Message with gizmo_id should have it in metadata."""

    def test_message_with_model(self)
        """Message with model_slug should have it in metadata."""

    def test_message_with_canvas(self)
        """Message with canvas should have canvas in metadata."""


class TestCanvasDataConstruction
    """Test canvas data fixture construction."""

    def test_basic_canvas_data(self)
        """Basic canvas data should have required fields."""

    def test_canvas_version_tracking(self)
        """Canvas with version > 1 should have from_version."""

    def test_canvas_first_version(self)
        """First version canvas should have from_version=None."""


def db_session()
    """
    Create a database session for integration tests.
    This fixture is a placeholder - actual implementation would
    need a test database setup with schema applied.
    """

class TestChatGPTExtractorGizmoAnnotations
    """Test gizmo annotation writing during extraction."""

    def test_extracts_gizmo_id_annotation(self, db_session)
        """Gizmo ID should be written as message string annotation."""

    def test_extracts_has_gizmo_flag(self, db_session)
        """has_gizmo flag should be written for messages with gizmo."""

    def test_no_gizmo_annotation_when_missing(self, db_session)
        """Messages without gizmo should not have gizmo annotations."""


class TestChatGPTExtractorCanvasAnnotations
    """Test canvas annotation writing during extraction."""

    def test_extracts_canvas_as_content_part(self, db_session)
        """Canvas should be created as content_part with type='canvas'."""

    def test_canvas_title_annotation(self, db_session)
        """Canvas title should be written as content_part annotation."""

    def test_canvas_version_annotation(self, db_session)
        """Canvas version should be written as numeric annotation."""


class TestMarkLatestCanvasVersions
    """Test the mark_latest_canvas_versions utility."""

    def test_marks_single_version_as_latest(self, db_session)
        """Single canvas version should be marked as latest."""

    def test_marks_highest_version_as_latest(self, db_session)
        """With multiple versions, only highest should be marked latest."""


class TestFindWikiGizmoMessages
    """Test the find_wiki_gizmo_messages utility."""

    def test_finds_messages_by_gizmo(self, db_session)
        """Should find all messages with specific gizmo_id."""

    def test_returns_empty_for_unknown_gizmo(self, db_session)
        """Should return empty list for unknown gizmo_id."""


```

## tests/unit/test_cli.py
```python
class TestCLIInit
    """Tests for CLI initialization."""

    def test_cli_default_db_url(self)
        """Test CLI uses default database URL."""

    def test_cli_custom_db_url(self)
        """Test CLI accepts custom database URL."""


class TestCLILoadJSON
    """Tests for JSON loading."""

    def test_load_json_valid(self)
        """Test loading valid JSON file."""

    def test_load_json_missing_file(self)
        """Test loading missing file raises error."""

    def test_load_json_invalid_format(self)
        """Test loading non-array JSON raises error."""

    def test_load_json_empty_array(self)
        """Test loading empty array."""

    def test_load_json_multiple_items(self)
        """Test loading array with multiple items."""


```

## tests/unit/test_content_classification.py
```python
class TestChatGPTClassifyContentPart
    """Tests for ChatGPT content part classification."""

    def extractor(self, mock_session)
        """Create extractor with mock session."""

    def test_classify_string_text(self, extractor)
        """Test classifying a plain string as text."""

    def test_classify_dict_text(self, extractor)
        """Test classifying a dict with text."""

    def test_classify_image(self, extractor)
        """Test classifying image content."""

    def test_classify_image_with_url(self, extractor)
        """Test classifying image with direct URL."""

    def test_classify_audio(self, extractor)
        """Test classifying audio content."""

    def test_classify_video(self, extractor)
        """Test classifying video content."""

    def test_classify_code(self, extractor)
        """Test classifying code content."""

    def test_classify_code_by_language(self, extractor)
        """Test classifying code by presence of language field."""

    def test_classify_unknown_type(self, extractor)
        """Test classifying unknown content type."""

    def test_classify_non_dict(self, extractor)
        """Test classifying non-dict, non-string content."""


class TestClaudeClassifyContentPart
    """Tests for Claude content part classification."""

    def extractor(self, mock_session)
        """Create extractor with mock session."""

    def test_classify_text(self, extractor)
        """Test classifying text content."""

    def test_classify_thinking(self, extractor)
        """Test classifying thinking content."""

    def test_classify_tool_use(self, extractor)
        """Test classifying tool_use content."""

    def test_classify_tool_use_text_input(self, extractor)
        """Test classifying tool_use with text input."""

    def test_classify_tool_result_string(self, extractor)
        """Test classifying tool_result with string content."""

    def test_classify_tool_result_list(self, extractor)
        """Test classifying tool_result with list content."""

    def test_classify_tool_result_mixed_list(self, extractor)
        """Test classifying tool_result with mixed list content."""

    def test_classify_tool_result_error(self, extractor)
        """Test classifying tool_result with error flag."""

    def test_classify_image(self, extractor)
        """Test classifying image content."""

    def test_classify_image_base64(self, extractor)
        """Test classifying base64 image (no URL)."""

    def test_classify_unknown_type(self, extractor)
        """Test classifying unknown content type."""


```

## tests/unit/test_content_part_annotators.py
```python
def content_part_id()
    """Generate a content-part ID."""

def make_content_part_data(text_content: str, part_type: str, language: str | None, role: str, content_part_id: uuid4) -> ContentPartData
    """Create ContentPartData for testing."""

class TestCodeBlockAnnotator
    """Test code block detection at content-part level."""

    def test_detects_simple_code_block(self, content_part_id)
        """Should detect basic code blocks."""

    def test_detects_code_block_with_language(self, content_part_id)
        """Should detect code blocks with language specification."""

    def test_counts_multiple_code_blocks(self, content_part_id)
        """Should count multiple code blocks."""

    def test_no_code_blocks(self, content_part_id)
        """Should return empty for text without code blocks."""

    def test_skips_non_text_parts(self, content_part_id)
        """Should only process text part_type."""

    def test_empty_text_content(self, content_part_id)
        """Should handle empty text content."""

    def test_none_text_content(self, content_part_id)
        """Should handle None text content."""


class TestLatexContentAnnotator
    """Test LaTeX detection at content-part level."""

    def test_detects_display_math(self, content_part_id)
        """Should detect $$ display math."""

    def test_detects_inline_math(self, content_part_id)
        """Should detect inline $ math."""

    def test_detects_latex_commands(self, content_part_id)
        """Should detect LaTeX commands."""

    def test_multiple_latex_types(self, content_part_id)
        """Should detect multiple LaTeX types."""

    def test_no_latex(self, content_part_id)
        """Should not detect in plain text."""


class TestWikiLinkContentAnnotator
    """Test wiki link detection at content-part level."""

    def test_detects_wiki_links(self, content_part_id)
        """Should detect [[wiki links]]."""

    def test_counts_many_wiki_links(self, content_part_id)
        """Should count multiple wiki links."""

    def test_no_wiki_links(self, content_part_id)
        """Should not detect in plain text."""


class TestContentPartAnnotatorBase
    """Test base class attributes and behavior."""

    def test_entity_type(self)
        """All content-part annotators should use CONTENT_PART entity type."""

    def test_annotators_have_annotation_key(self)
        """All annotators should have ANNOTATION_KEY defined."""

    def test_annotators_have_priority(self)
        """All annotators should have PRIORITY defined."""


```

## tests/unit/test_extractor_utils.py
```python
class TestParseTimestamp
    """Tests for timestamp parsing."""

    def test_parse_epoch_int(self)
        """Test parsing integer epoch timestamp."""

    def test_parse_epoch_float(self)
        """Test parsing float epoch timestamp."""

    def test_parse_iso_string(self)
        """Test parsing ISO 8601 string."""

    def test_parse_iso_string_with_offset(self)
        """Test parsing ISO 8601 with timezone offset."""

    def test_parse_none(self)
        """Test parsing None returns None."""

    def test_parse_invalid_string(self)
        """Test parsing invalid string returns None."""

    def test_parse_negative_epoch(self)
        """Test parsing negative epoch (before 1970)."""


class TestNormalizeRole
    """Tests for role normalization."""

    def test_normalize_user(self)
        """Test 'user' stays 'user'."""

    def test_normalize_assistant(self)
        """Test 'assistant' stays 'assistant'."""

    def test_normalize_human_to_user(self)
        """Test 'human' becomes 'user' (Claude format)."""

    def test_normalize_human_uppercase(self)
        """Test uppercase 'HUMAN' becomes 'user'."""

    def test_normalize_system(self)
        """Test 'system' stays 'system'."""

    def test_normalize_none(self)
        """Test None becomes 'unknown'."""


class TestSafeGet
    """Tests for safe dictionary traversal."""

    def test_simple_get(self)
        """Test simple key access."""

    def test_nested_get(self)
        """Test nested key access."""

    def test_missing_key(self)
        """Test missing key returns default."""

    def test_missing_nested_key(self)
        """Test missing nested key returns default."""

    def test_non_dict_intermediate(self)
        """Test non-dict intermediate value returns default."""

    def test_none_intermediate(self)
        """Test None intermediate value returns default."""


class TestTimestampEdgeCases
    """Edge case tests for timestamp parsing."""

    def test_zero_epoch(self)
        """Test epoch 0 (1970-01-01)."""

    def test_very_large_epoch(self)
        """Test very large epoch value."""

    def test_iso_without_timezone(self)
        """Test ISO string without timezone gets UTC."""


class TestComputeContentHash
    """Tests for content hash computation."""

    def test_hash_dict(self)
        """Test hashing a dictionary."""

    def test_hash_string(self)
        """Test hashing a plain string."""

    def test_hash_is_deterministic(self)
        """Test that same content produces same hash."""

    def test_hash_is_order_independent(self)
        """Test that key order doesn't affect hash."""

    def test_different_content_different_hash(self)
        """Test that different content produces different hash."""

    def test_hash_nested_dict(self)
        """Test hashing nested dictionary."""

    def test_hash_list(self)
        """Test hashing a list."""


```

## tests/unit/test_models.py
```python
class TestDialogueModel
    """Tests for Dialogue model instantiation."""

    def test_create_dialogue_instance(self)
        """Test creating a Dialogue instance."""

    def test_dialogue_with_timestamps(self)
        """Test Dialogue with timestamp fields."""

    def test_dialogue_minimal_fields(self)
        """Test Dialogue with only required fields."""


class TestMessageModel
    """Tests for Message model instantiation."""

    def test_create_message_instance(self)
        """Test creating a Message instance."""

    def test_message_with_parent(self)
        """Test Message with parent reference."""

    def test_message_with_author(self)
        """Test Message with author fields."""

    def test_message_with_content_hash(self)
        """Test Message with content hash for change detection."""

    def test_message_with_deleted_at(self)
        """Test Message with soft delete timestamp."""

    def test_message_not_deleted_by_default(self)
        """Test that deleted_at is None by default."""


class TestContentPartModel
    """Tests for ContentPart model instantiation."""

    def test_create_text_content_part(self)
        """Test creating a text ContentPart."""

    def test_create_code_content_part(self)
        """Test creating a code ContentPart with language."""

    def test_create_image_content_part(self)
        """Test creating an image ContentPart with media type and URL."""

    def test_create_tool_use_content_part(self)
        """Test creating a tool_use ContentPart."""

    def test_create_tool_result_content_part(self)
        """Test creating a tool_result ContentPart."""


class TestModelTableNames
    """Tests for model table name configuration."""

    def test_dialogue_table_name(self)
        """Test Dialogue uses raw schema."""

    def test_message_table_name(self)
        """Test Message uses raw schema."""

    def test_content_part_table_name(self)
        """Test ContentPart uses raw schema."""


```

## tests/unit/test_prompt_response.py
```python
def pr_id()
    """Generate a prompt-response ID."""

def make_pr_data(prompt_text: str, response_text: str, pr_id: uuid4, response_role: str, prompt_role: str) -> PromptResponseData
    """Create PromptResponseData for testing."""

class TestWikiCandidateAnnotator
    """Test wiki article detection."""

    def test_detects_wiki_links(self, pr_id)
        """Should detect responses with wiki links."""

    def test_high_confidence_multiple_links(self, pr_id)
        """Should have higher confidence with 3+ wiki links."""

    def test_no_wiki_links(self, pr_id)
        """Should not detect if no wiki links."""


class TestNaiveTitleAnnotator
    """Test naive title extraction."""

    def test_extracts_markdown_h1(self, pr_id)
        """Should extract # Title."""

    def test_extracts_markdown_h2(self, pr_id)
        """Should extract ## Title."""

    def test_extracts_markdown_h3(self, pr_id)
        """Should extract ### Title."""

    def test_extracts_bold_title(self, pr_id)
        """Should extract **Title**."""

    def test_extracts_bold_with_subtitle(self, pr_id)
        """Should extract **Title** - Subtitle pattern."""

    def test_no_title_preamble(self, pr_id)
        """~~Should return nothing if first line is preamble.~~ Actually, now we check for any header in the first 5 lines"""

    def test_no_title_plain_text(self, pr_id)
        """Should return nothing if no clear title format."""

    def test_skips_non_assistant(self, pr_id)
        """Should skip non-assistant responses."""

    def test_empty_response(self, pr_id)
        """Should handle empty response."""

    def test_none_response(self, pr_id)
        """Should handle None response."""

    def test_whitespace_only_first_line(self, pr_id)
        """Should skip whitespace-only first lines."""

    def test_strips_title_whitespace(self, pr_id)
        """Should strip whitespace from extracted title."""


class TestPromptResponseData
    """Test PromptResponseData dataclass."""

    def test_all_fields_accessible(self)
        """All fields should be accessible."""

    def test_handles_none_text(self)
        """Should handle None text gracefully."""


```

## tests/unit/test_registry.py
```python
class HighPriorityAnnotator(BaseAnnotator)

    def _iter_entities_after(self, after)

    def _entity_id(self, data)

    def _created_at(self, data)

    def annotate(self, data)


class LowPriorityAnnotator(BaseAnnotator)

    def _iter_entities_after(self, after)

    def _entity_id(self, data)

    def _created_at(self, data)

    def annotate(self, data)


class MediumPriorityAnnotator(BaseAnnotator)

    def _iter_entities_after(self, after)

    def _entity_id(self, data)

    def _created_at(self, data)

    def annotate(self, data)


class TestRegistryRegistration
    """Test registration mechanics."""

    def test_register_single(self)

    def test_register_many(self)

    def test_unregister(self)

    def test_get_returns_none_for_missing(self)


class TestRegistryOrdering
    """Test priority-based ordering."""

    def test_list_sorted_by_priority_descending(self)


class TestRegistryExecution
    """Test run_all and run_one."""

    def test_run_one_raises_for_unknown(self)


class TestDefaultRegistry
    """Test the default registry factory."""

    def test_default_registry_has_builtins(self)

    def test_default_registry_sorted_by_priority(self)


```
