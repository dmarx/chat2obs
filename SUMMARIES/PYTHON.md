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
    """Supported entity types for annotations."""

class ValueType(str, Enum)
    """Annotation value types."""

@dataclass
class AnnotationResult
    """
    Result from annotation logic.
    For FLAG annotations: only key is required
    For STRING/NUMERIC/JSON: key and value are required
    """

    def __eq__(self, other: object) -> bool
        """Equality check - compares key, value, and value_type."""

    def __hash__(self) -> int
        """Hash based on key, value, and value_type."""

    def __repr__(self) -> str
        """Compact string representation."""


class AnnotationWriter
    """
    Writes annotations to the appropriate typed tables.
    Used by:
    - Extractors during ingestion (source='ingestion')
    - Annotators during processing (source='heuristic', 'model', etc.)
    Handles table routing based on entity_type and value_type.
    Uses upsert semantics (ON CONFLICT DO NOTHING for multi-value,
    ON CONFLICT DO UPDATE for single-value tables).
    """

    def __init__(self, session: Session)

    def _table_name(self, entity_type: EntityType, value_type: ValueType) -> str
        """Get the table name for an entity/value type combination."""

    def write_flag(self, entity_type: EntityType, entity_id: UUID, key: str, confidence: float | None, reason: str | None, source: str, source_version: str | None) -> bool
        """Write a flag annotation (key presence = true)."""

    def write_string(self, entity_type: EntityType, entity_id: UUID, key: str, value: str, confidence: float | None, reason: str | None, source: str, source_version: str | None) -> bool
        """Write a string annotation."""

    def write_numeric(self, entity_type: EntityType, entity_id: UUID, key: str, value: float | int, confidence: float | None, reason: str | None, source: str, source_version: str | None) -> bool
        """Write a numeric annotation."""

    def write_json(self, entity_type: EntityType, entity_id: UUID, key: str, value: dict | list, confidence: float | None, reason: str | None, source: str, source_version: str | None) -> bool
        """Write a JSON annotation (single value per key, upserts)."""

    def write(self, entity_type: EntityType, entity_id: UUID, result: AnnotationResult) -> bool
        """
        Write an annotation from an AnnotationResult.
        Dispatches to the appropriate typed write method.
        """

    def _track(self, table: str, created: bool)
        """Track annotation counts."""

    @property
    def counts(self) -> dict[[str, int]]
        """Get annotation counts by table."""


class AnnotationReader
    """
    Reads annotations from the typed tables.
    Provides methods for:
    - Checking if an annotation exists
    - Getting annotation values
    - Filtering entities by annotations
    """

    def __init__(self, session: Session)

    def _table_name(self, entity_type: EntityType, value_type: ValueType) -> str

    def has_flag(self, entity_type: EntityType, entity_id: UUID, key: str) -> bool
        """Check if entity has a flag annotation."""

    def get_string(self, entity_type: EntityType, entity_id: UUID, key: str) -> list[str]
        """Get all string values for a key (multi-value)."""

    def get_string_single(self, entity_type: EntityType, entity_id: UUID, key: str) -> str | None
        """Get single string value (returns first if multiple)."""

    def get_numeric(self, entity_type: EntityType, entity_id: UUID, key: str) -> list[float]
        """Get all numeric values for a key."""

    def get_json(self, entity_type: EntityType, entity_id: UUID, key: str) -> dict | list | None
        """Get JSON value for a key (single value)."""

    def get_all_keys(self, entity_type: EntityType, entity_id: UUID) -> dict[[str, list[Any]]]
        """Get all annotations for an entity, grouped by key."""

    def find_entities_with_flag(self, entity_type: EntityType, key: str) -> list[UUID]
        """Find all entity IDs that have a specific flag."""

    def find_entities_with_string(self, entity_type: EntityType, key: str, value: str | None) -> list[UUID]
        """Find entity IDs with a string annotation (optionally matching value)."""


```

## llm_archive/annotators/content_part.py
```python
@dataclass
class ContentPartData
    """Data passed to content-part annotation logic."""

class ContentPartAnnotator
    """
    Base class for annotating content parts.
    Iterates over raw.content_parts joined with raw.messages.
    Supports annotation prerequisites and skip conditions.
    """

    def __init__(self, session: Session)

    def compute(self) -> int
        """Run annotation over content parts."""

    def _write_result(self, entity_id: UUID, result: AnnotationResult) -> bool
        """Write an annotation result to the appropriate table."""

    def _iter_content_parts(self) -> Iterator[ContentPartData]
        """Iterate over content parts, respecting filters."""

    @abstractmethod
    def annotate(self, data: ContentPartData) -> list[AnnotationResult]
        """
        Analyze content part and return annotations to create.
        Args:
            data: ContentPartData with content and metadata
        Returns:
            List of AnnotationResult objects (empty list if no match)
        """


class CodeBlockAnnotator(ContentPartAnnotator)
    """
    Detect explicit code blocks (```) in text content parts.
    Highest priority code detector - explicit markdown code blocks
    are the most reliable signal.
    Produces:
    - has_code_block FLAG
    - code_block_count NUMERIC
    - code_languages STRING (multi-value)
    """

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]


class ScriptHeaderAnnotator(ContentPartAnnotator)
    """
    Detect script headers and system includes (strong code evidence).
    Shebangs and #include are unambiguous code markers.
    Produces:
    - has_script_header FLAG
    - script_type STRING
    """

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]


class LatexContentAnnotator(ContentPartAnnotator)
    """
    Detect LaTeX/MathJax mathematical notation in content parts.
    Produces:
    - has_latex FLAG
    - latex_type STRING ('display', 'inline', 'commands')
    """

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]


class WikiLinkContentAnnotator(ContentPartAnnotator)
    """
    Detect Obsidian-style [[wiki links]] in content parts.
    This is a content-part level version for granular detection.
    The prompt-response level WikiCandidateAnnotator aggregates this.
    Produces:
    - has_wiki_links FLAG
    - wiki_link_count NUMERIC
    """

    def annotate(self, data: ContentPartData) -> list[AnnotationResult]


def run_content_part_annotators(session: Session) -> dict[[str, int]]
    """
    Run all content-part annotators in priority order.
    Returns dict mapping annotator name to annotation count.
    """

```

## llm_archive/annotators/prompt_response.py
```python
@dataclass
class PromptResponseData
    """Data passed to prompt-response annotation logic."""

class PromptResponseAnnotator
    """
    Base class for annotating prompt-response pairs.
    Iterates over derived.prompt_response_content_v (view that joins
    content from raw.content_parts - no denormalized storage).
    Supports annotation prerequisites and skip conditions using the
    new typed annotation tables:
    - REQUIRES_FLAGS: Only process entities with ALL of these flag annotations
    - REQUIRES_STRINGS: Only process entities with ALL of these (key, value) string annotations
    - SKIP_IF_FLAGS: Skip entities with ANY of these flag annotations
    - SKIP_IF_STRINGS: Skip entities with ANY of these (key,) or (key, value) string annotations
    Example:
        REQUIRES_STRINGS = [('exchange_type', 'wiki_article')]
        SKIP_IF_FLAGS = ['has_preamble']
    """

    def __init__(self, session: Session)

    def compute(self) -> int
        """Run annotation over prompt-response pairs."""

    def _write_result(self, entity_id: UUID, result: AnnotationResult) -> bool
        """Write an annotation result to the appropriate table."""

    def _iter_prompt_responses(self) -> Iterator[PromptResponseData]
        """Iterate over prompt-responses with content, respecting annotation filters."""

    @abstractmethod
    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]
        """
        Analyze prompt-response pair and return annotations to create.
        Args:
            data: PromptResponseData with texts and metadata
        Returns:
            List of AnnotationResult objects (empty list if no match)
        """


class WikiCandidateAnnotator(PromptResponseAnnotator)
    """
    Detect wiki-style article candidates.
    Looks for [[wiki links]] in assistant responses, which indicate
    the response was likely formatted as a wiki article.
    Produces a STRING annotation: exchange_type = 'wiki_article'
    """

    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]


class NaiveTitleAnnotator(PromptResponseAnnotator)
    """
    Extract title from first line of response.
    Looks for:
    - Markdown headers: # Title
    - Bold headers: **Title**
    Should run AFTER wiki candidate detection.
    Only runs on wiki_article candidates.
    Produces a STRING annotation: proposed_title = '<extracted title>'
    """

    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]

    def _extract_title(self, text: str) -> tuple[[str | None, str | None]]
        """Extract title from first line of text. Returns (title, reason)."""


class HasCodeAnnotator(PromptResponseAnnotator)
    """
    Detect if prompt-response pair involves code.
    Aggregates evidence from multiple sources:
    - Code blocks (```)
    - Script headers (shebang, #include)
    - Function definitions
    - Import statements
    Produces:
    - has_code FLAG
    - code_evidence STRING (multi-value)
    """

    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]


class HasLatexAnnotator(PromptResponseAnnotator)
    """
    Detect if prompt-response pair contains LaTeX/math notation.
    Produces:
    - has_latex FLAG
    - latex_type STRING (multi-value: 'display', 'inline', 'commands')
    """

    def annotate(self, data: PromptResponseData) -> list[AnnotationResult]


def run_prompt_response_annotators(session: Session) -> dict[[str, int]]
    """
    Run all prompt-response annotators in priority order.
    Returns dict mapping annotator name to annotation count.
    """

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
                Faster, but won't detect in-place message edits. Use when
                the provider treats messages as immutable (edits create new IDs).
            incremental: Don't soft-delete messages missing from this import.
                Use when importing partial/delta exports.
        """

    def import_claude(self, path: str, assume_immutable: bool, incremental: bool)
        """
        Import Claude conversations.json export.
        Args:
            path: Path to conversations.json file
            assume_immutable: Skip content hash checks for existing messages.
                Faster, but won't detect in-place message edits. Use when
                the provider treats messages as immutable (edits create new IDs).
            incremental: Don't soft-delete messages missing from this import.
                Use when importing partial/delta exports.
        """

    def import_all(self, chatgpt_path: str | None, claude_path: str | None, assume_immutable: bool, incremental: bool)
        """
        Import from multiple sources.
        Args:
            chatgpt_path: Path to ChatGPT conversations.json
            claude_path: Path to Claude conversations.json
            assume_immutable: Skip content hash checks for existing messages
            incremental: Don't soft-delete messages missing from this import
        """

    def build_prompt_responses(self)
        """Build prompt-response pairs (no tree dependency)."""

    def build_all(self)
        """Build all derived structures."""

    def annotate(self)
        """Run all annotators."""

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
            assume_immutable: Skip content hash checks for existing messages
            incremental: Don't soft-delete messages missing from this import
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
def get_engine(db_url: str)
    """Create database engine."""

def get_session_factory(db_url: str) -> sessionmaker
    """Create a session factory."""

@contextmanager
def get_session(db_url: str)
    """Context manager for database sessions."""

def init_schema(db_url: str, schema_dir: Path | str)
    """Initialize database schema from SQL files."""

def reset_schema(db_url: str, schema_dir: Path | str | None)
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

## llm_archive/models/derived.py
```python
class PromptResponse(Base)
    """
    Direct prompt-response association without tree dependency.
    Each record pairs a user prompt with one of its responses.
    A prompt can have multiple responses (regenerations).
    Each response appears in exactly one record.
    """

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
    """Initialize schemas once per test session."""

def db_session(db_engine, setup_schemas) -> Generator[[Session, None, None]]
    """Create a database session with transaction rollback."""

def clean_db_session(db_session) -> Session
    """Alias for db_session."""

def chatgpt_simple_conversation() -> dict
    """Simple linear ChatGPT conversation."""

def chatgpt_branched_conversation() -> dict
    """ChatGPT conversation: 1 user message with 2 assistant responses that each have continuation messages."""

def chatgpt_conversation_with_code() -> dict
    """ChatGPT conversation with code content - uses nested parts structure."""

def chatgpt_conversation_with_image() -> dict
    """ChatGPT conversation with image content - uses nested parts structure."""

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


class TestScriptHeaderAnnotator
    """Test script header detection."""

    def test_detects_python_shebang(self, content_part_id)
        """Should detect Python shebang."""

    def test_detects_bash_shebang(self, content_part_id)
        """Should detect Bash shebang."""

    def test_detects_c_include(self, content_part_id)
        """Should detect C/C++ includes."""

    def test_detects_c_include_quotes(self, content_part_id)
        """Should detect C includes with quotes."""

    def test_detects_php_tag(self, content_part_id)
        """Should detect PHP opening tag."""

    def test_no_script_header(self, content_part_id)
        """Should not detect in plain text."""


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


class TestContentPartAnnotatorRegistry
    """Test the content-part annotator registry."""

    def test_all_annotators_in_registry(self)
        """All annotators should be in CONTENT_PART_ANNOTATORS."""

    def test_registry_count(self)
        """Registry should have expected number of annotators."""


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

    def test_lower_confidence_single_link(self, pr_id)
        """Should have lower confidence with just 1-2 links."""

    def test_no_wiki_links(self, pr_id)
        """Should not detect if no wiki links."""

    def test_skips_non_assistant(self, pr_id)
        """Should skip non-assistant responses."""

    def test_counts_links_correctly(self, pr_id)
        """Should count wiki links correctly."""

    def test_handles_empty_brackets(self, pr_id)
        """Should count empty brackets as potential links."""


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
        """Should return nothing if first line is preamble."""

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


class TestAnnotatorFilters
    """Test annotation filter attributes."""

    def test_wiki_candidate_has_no_requirements(self)
        """WikiCandidateAnnotator should have no prerequisites."""

    def test_naive_title_requires_wiki(self)
        """NaiveTitleAnnotator should require wiki_article."""

    def test_annotator_metadata(self)
        """Check annotator class metadata."""

    def test_custom_annotator_with_filters(self)
        """Test defining custom annotator with filters."""


class TestAnnotationResult
    """Test AnnotationResult dataclass behavior."""

    def test_result_with_reason(self, pr_id)
        """Results should include reason when provided."""

    def test_key_is_required(self, pr_id)
        """Key should always be set on results."""

    def test_value_type_is_set(self, pr_id)
        """Results should have explicit value_type."""


class TestPromptResponseData
    """Test PromptResponseData dataclass."""

    def test_all_fields_accessible(self)
        """All fields should be accessible."""

    def test_word_counts_calculated(self)
        """Word counts should be calculated from text."""

    def test_handles_none_text(self)
        """Should handle None text gracefully."""


class TestHasCodeAnnotator
    """Test code detection annotator."""

    def test_detects_code_blocks(self, pr_id)
        """Should detect ``` code blocks."""

    def test_detects_shebang(self, pr_id)
        """Should detect shebang lines."""

    def test_detects_c_include(self, pr_id)
        """Should detect C/C++ includes."""

    def test_detects_python_function(self, pr_id)
        """Should detect Python function definitions."""

    def test_detects_js_function(self, pr_id)
        """Should detect JavaScript function definitions."""

    def test_detects_arrow_function(self, pr_id)
        """Should detect arrow functions."""

    def test_detects_python_import(self, pr_id)
        """Should detect Python imports."""

    def test_no_code_in_plain_text(self, pr_id)
        """Should not detect code in plain text."""

    def test_skips_non_assistant(self, pr_id)
        """Should skip non-assistant responses."""

    def test_multiple_evidence_types(self, pr_id)
        """Should detect multiple evidence types."""


class TestHasLatexAnnotator
    """Test LaTeX detection annotator."""

    def test_detects_display_math(self, pr_id)
        """Should detect display math $$...$$."""

    def test_detects_bracket_display_math(self, pr_id)
        """Should detect \[...\] display math."""

    def test_detects_latex_commands(self, pr_id)
        """Should detect LaTeX commands."""

    def test_detects_greek_letters(self, pr_id)
        """Should detect Greek letter commands."""

    def test_no_latex_in_plain_text(self, pr_id)
        """Should not detect LaTeX in plain text."""

    def test_skips_non_assistant(self, pr_id)
        """Should skip non-assistant responses."""

    def test_high_confidence_for_display_math(self, pr_id)
        """Should have high confidence for display math."""

    def test_lower_confidence_for_commands_only(self, pr_id)
        """Should have lower confidence for commands without display math."""


class TestAnnotatorRegistry
    """Test the annotator registry and runner."""

    def test_all_annotators_in_registry(self)
        """All annotators should be in PROMPT_RESPONSE_ANNOTATORS."""

    def test_annotators_have_unique_keys(self)
        """Each annotator should have a unique ANNOTATION_KEY."""

    def test_priority_ordering(self)
        """Annotators should have distinct priorities for deterministic ordering."""


class PreambleDetector(PromptResponseAnnotator)

    def annotate(self, data)


```
