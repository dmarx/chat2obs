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

## llm_archive/annotators/base.py
```python
class Annotator(ABC)
    """
    Base class for annotation generators.
    Annotators analyze entities and produce annotations stored in
    the derived.annotations table.
    Supports incremental processing via cursor tracking:
    - Each annotator+version tracks a "high water mark" (cursor)
    - Only entities created after the cursor are processed
    - Bump VERSION to force reprocessing all entities
    Subclass and implement:
    - ANNOTATION_TYPE: Type of annotation ('tag', 'title', 'feature', etc.)
    - ENTITY_TYPE: Target entity type ('message', 'exchange', 'dialogue')
    - SOURCE: Provenance ('heuristic', 'model', 'manual')
    - VERSION: Version string - bump this to reprocess all entities
    - compute(): Main logic to generate annotations
    """

    def __init__(self, session: Session)

    @property
    def name(self) -> str
        """Annotator name for cursor tracking."""

    def get_cursor(self) -> datetime | None
        """
        Get the high water mark for this annotator version.
        Returns the timestamp of the last processed entity, or None if
        this annotator version hasn't run before.
        """

    def update_cursor(self, high_water_mark: datetime, entities_processed: int, annotations_created: int)
        """
        Update the cursor position after processing.
        Args:
            high_water_mark: The max created_at timestamp seen
            entities_processed: Number of entities processed in this run
            annotations_created: Number of annotations created in this run
        """

    def track_entity(self, created_at: datetime | None)
        """Track an entity being processed for cursor update."""

    def finalize_cursor(self)
        """Finalize cursor update after processing."""

    @abstractmethod
    def compute(self) -> int
        """
        Compute and persist annotations.
        Implementations should:
        1. Call get_cursor() to get the high water mark
        2. Query only entities with created_at > cursor (or all if cursor is None)
        3. Call track_entity(created_at) for each entity processed
        4. Call add_annotation() for each annotation
        5. Call finalize_cursor() at the end
        Returns count of annotations created/updated.
        """

    def add_annotation(self, entity_id: UUID, value: str, key: str | None, confidence: float | None, data: dict | None) -> bool
        """
        Add or update an annotation.
        Args:
            entity_id: Target entity UUID
            value: Annotation value (required)
            key: Optional sub-key for namespacing
            confidence: Optional confidence score (0.0-1.0)
            data: Optional additional structured data
        Returns:
            True if a new annotation was created, False if existing.
        """

    def supersede_annotation(self, entity_id: UUID, value: str, key: str | None, new_annotation_id: UUID | None)
        """Mark an existing annotation as superseded."""


class AnnotationManager
    """Manages annotation operations and annotator execution."""

    def __init__(self, session: Session)

    def register(self, annotator_class: type[Annotator])
        """Register an annotator class."""

    def run_all(self) -> dict[[str, int]]
        """Run all registered annotators."""

    def get_annotations(self, entity_type: str | None, entity_id: UUID | None, annotation_type: str | None, active_only: bool) -> list[Annotation]
        """Query annotations with filters."""

    def get_entity_annotations(self, entity_type: str, entity_id: UUID) -> dict[[str, Any]]
        """Get all active annotations for an entity as a dict."""

    def get_tags(self, entity_type: str, entity_id: UUID) -> list[str]
        """Get tag values for an entity."""

    def get_title(self, entity_type: str, entity_id: UUID) -> str | None
        """Get title annotation for an entity."""

    def clear_annotations(self, entity_type: str | None, annotation_type: str | None, source: str | None)
        """Clear annotations matching filters (hard delete)."""


```

## llm_archive/annotators/features.py
```python
class WikiLinkAnnotator(Annotator)
    """Detect Obsidian-style [[wiki links]] in content."""

    def compute(self) -> int
        """Find messages with wiki links."""


class CodeBlockAnnotator(Annotator)
    """Detect code blocks (```) in content."""

    def compute(self) -> int
        """Find messages with code blocks."""


class LatexAnnotator(Annotator)
    """Detect LaTeX/MathJax mathematical notation."""

    def compute(self) -> int
        """Find messages with LaTeX content."""


class ContinuationAnnotator(Annotator)
    """Detect continuation signals in user messages."""

    def compute(self) -> int
        """Find user messages that are continuation signals."""


class ExchangeTypeAnnotator(Annotator)
    """Classify exchange types based on content patterns."""

    def compute(self) -> int
        """Classify exchanges."""

    def _classify(self, content: ExchangeContent) -> tuple[[str | None, float]]
        """Classify an exchange based on content."""


```

## llm_archive/builders/chunks.py
```python
@dataclass
class ChunkRecord

class MessageChunkBuilder

    def __init__(self, session: Session)

    def build_all(self, name: str | None, params: dict | None) -> dict[[str, int]]

    def _chunk_message(self, message_id, run_id) -> int

    def _get_message_text(self, message_id) -> str | None

    def _parse_markdown(self, text_in: str) -> Iterable[ChunkRecord]


def line_to_char(line_no: int) -> int

def grab_text_for_map(map_pair)

```

## llm_archive/builders/exchanges.py
```python
@dataclass
class MessageInfo
    """Lightweight message info for exchange building."""

def is_continuation_prompt(text: str | None) -> bool
    """Check if text is a continuation prompt."""

def compute_hash(text: str | None) -> str | None
    """Compute SHA-256 hash of text."""

class ExchangeBuilder
    """
    Builds exchanges from dialogue trees.
    An exchange is a dyadic unit:
    - USER message(s) followed by ASSISTANT response(s)
    - Ends when next USER message starts a new topic (not a continuation)
    Exchanges are built from the TREE and identified by 
    (dialogue_id, first_message_id, last_message_id).
    Sequences then REFERENCE exchanges via sequence_exchanges join table.
    This avoids duplicate exchange creation for shared prefixes.
    """

    def __init__(self, session: Session)

    def build_all(self) -> dict[[str, int]]
        """Build exchanges for all dialogues."""

    def build_for_dialogue(self, dialogue_id: UUID) -> dict[[str, int]]
        """Build exchanges for a single dialogue."""

    def _build_for_sequence(self, sequence: LinearSequence) -> dict[[str, int]]
        """Build/link exchanges for a single sequence."""

    def _load_sequence_messages(self, sequence_id: UUID) -> list[MessageInfo]
        """Load message info for a sequence in order."""

    def _get_message_text(self, message_id: UUID) -> str | None
        """Get concatenated text content for a message."""

    def _create_dyadic_groups(self, messages: list[MessageInfo]) -> list[list[MessageInfo]]
        """
        Group messages into dyadic exchanges.
        A dyadic exchange starts with USER message(s) and includes
        all following ASSISTANT message(s) until the next USER message.
        """

    def _merge_continuations(self, groups: list[list[MessageInfo]]) -> list[tuple[[list[MessageInfo], bool]]]
        """
        Merge groups when USER message is a continuation signal.
        Returns list of (messages, is_continuation) tuples.
        The is_continuation flag indicates the exchange contains merged continuation prompts.
        """

    def _get_or_create_exchange(self, dialogue_id: UUID, messages: list[MessageInfo], is_continuation: bool) -> tuple[[UUID, bool, int]]
        """
        Get existing exchange or create new one.
        Returns (exchange_id, was_newly_created, message_count).
        """

    def _create_exchange_content(self, exchange_id: UUID, messages: list[MessageInfo])
        """Create aggregated content for an exchange."""

    def _clear_sequence_links(self, dialogue_id: UUID)
        """Clear existing sequence_exchanges for this dialogue."""


```

## llm_archive/builders/hashes.py
```python
def normalize_whitespace(text: str) -> str
    """Normalize whitespace in text."""

def normalize_for_comparison(text: str) -> str
    """Normalize text for fuzzy comparison."""

def compute_sha256(text: str) -> str
    """Compute SHA-256 hash."""

class HashBuilder
    """
    Builds content hashes for deduplication.
    Creates hashes at multiple levels:
    - Message level: individual message content
    - Exchange level: aggregated exchange content
    Supports multiple normalizations:
    - none: raw text
    - whitespace: normalized whitespace
    - normalized: lowercase, no punctuation, normalized whitespace
    """

    def __init__(self, session: Session)

    def build_all(self) -> dict[[str, int]]
        """Build hashes for all entities."""

    def _hash_messages(self) -> tuple[[int, int]]
        """Hash all message content."""

    def _hash_exchanges(self) -> tuple[[int, int]]
        """Hash all exchange content."""

    def _create_hashes(self, entity_type: str, entity_id: UUID, text: str, scope: str) -> int
        """Create hashes with multiple normalizations."""

    def find_duplicates(self, entity_type: str | None, scope: str | None, normalization: str) -> list[dict]
        """Find duplicate content by hash."""


```

## llm_archive/builders/trees.py
```python
@dataclass
class TreeNode
    """In-memory representation of a message in the tree."""

    @property
    def is_leaf(self) -> bool

    @property
    def timestamp(self) -> float


@dataclass
class TreeAnalysis
    """Results of analyzing a dialogue tree."""

class TreeBuilder
    """
    Analyzes dialogue trees and materializes derived structures.
    Works uniformly across all sources:
    - Linear dialogues (Claude) produce degenerate trees (branch_count=0)
    - Branched dialogues (ChatGPT) produce full tree analysis
    """

    def __init__(self, session: Session)

    def build_all(self) -> dict[[str, int]]
        """Build tree analysis for all dialogues."""

    def build_for_dialogue(self, dialogue_id: UUID) -> dict[[str, int]]
        """Build tree analysis for a single dialogue."""

    def _analyze_tree(self, dialogue_id: UUID, messages: list[Message]) -> TreeAnalysis
        """Analyze the tree structure of a dialogue."""

    def _build_tree(self, messages: list[Message]) -> tuple[[dict[[UUID, TreeNode]], list[TreeNode]]]
        """Build in-memory tree from messages."""

    def _compute_depths(self, root: TreeNode) -> dict[[UUID, int]]
        """Compute depth for each node starting from root."""

    def _select_primary_leaf(self, leaves: list[TreeNode], nodes: dict[[UUID, TreeNode]]) -> TreeNode | None
        """Select primary leaf (longest path, then most recent)."""

    def _get_ancestor_ids(self, node: TreeNode, nodes: dict[[UUID, TreeNode]]) -> list[UUID]
        """Get ancestor IDs from root to parent (excluding node)."""

    def _get_path_ids(self, node: TreeNode, nodes: dict[[UUID, TreeNode]]) -> set[UUID]
        """Get all IDs on path from root to node (inclusive)."""

    def _classify_branches(self, nodes: dict[[UUID, TreeNode]]) -> tuple[[bool, bool]]
        """Determine if tree has regenerations and/or edits."""

    def _persist_dialogue_tree(self, analysis: TreeAnalysis)
        """Persist dialogue tree record."""

    def _persist_message_paths(self, analysis: TreeAnalysis) -> int
        """Persist message path records."""

    def _compute_sibling_indices(self, nodes: dict[[UUID, TreeNode]]) -> dict[[UUID, int]]
        """Compute sibling index for each node."""

    def _persist_linear_sequences(self, analysis: TreeAnalysis) -> tuple[[int, int]]
        """Persist linear sequences for each leaf."""

    def _clear_derived(self, dialogue_id: UUID)
        """Clear existing derived data for a dialogue."""


def traverse(node: TreeNode, depth: int)

def score(leaf: TreeNode) -> tuple[[int, float]]

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

    def build_trees(self)
        """Build dialogue tree analysis."""

    def build_exchanges(self)
        """Build exchanges from dialogue trees."""

    def build_hashes(self)
        """Build content hashes for deduplication."""

    def build_chunks(self, name: str | None)
        """Chunk messages into derived.message_chunks (markdown-aware)."""

    def build_all(self)
        """Build all derived structures."""

    def annotate(self)
        """Run all annotators."""

    def find_duplicates(self, entity_type: str, scope: str)
        """Find duplicate content."""

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
        """Extract ChatGPT-specific metadata."""

    def _extract_search_group(self, message_id: UUID, group_data: dict[[str, Any]])
        """Extract a search result group and its entries."""

    def _extract_code_execution(self, message_id: UUID, agg_result: dict[[str, Any]])
        """Extract code execution data."""

    def _extract_dalle_generation(self, content_part_id: UUID, part: dict[[str, Any]])
        """Extract DALL-E generation data from a content part."""

    def _extract_canvas_doc(self, message_id: UUID, canvas: dict[[str, Any]])
        """Extract canvas document data."""


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
class DialogueTree(Base)
    """Tree analysis results for a dialogue."""

class MessagePath(Base)
    """Materialized path for a message in the tree."""

class LinearSequence(Base)
    """A root-to-leaf path as a linear sequence."""

class SequenceMessage(Base)
    """Message membership in a linear sequence."""

class Exchange(Base)
    """Logical interaction unit (user prompt + assistant response)."""

class ExchangeMessage(Base)
    """Message membership in an exchange."""

class SequenceExchange(Base)
    """Links sequences to exchanges (many-to-many)."""

class ExchangeContent(Base)
    """Aggregated content for an exchange."""

class Annotation(Base)
    """Polymorphic annotation for any entity."""

class ContentHash(Base)
    """Content hash for deduplication."""

class AnnotatorCursor(Base)
    """
    Tracks processing state for incremental annotation.
    Each annotator+version+entity_type combination has a cursor pointing to
    the last processed entity (by created_at). This allows incremental
    annotation without re-processing old entities or storing "no match" records.
    """

class PipelineRun(Base)

class MessageChunk(Base)

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
    """Get test database URL from environment or use default."""

def db_engine()
    """Create database engine for test session."""

def setup_schemas(db_engine)
    """Initialize schemas once per test session."""

def db_session(db_engine, setup_schemas) -> Generator[[Session, None, None]]
    """Create a database session with transaction rollback."""

def clean_db_session(db_engine, setup_schemas) -> Generator[[Session, None, None]]
    """
    Create a database session that commits changes.
    Use when you need data to persist across operations within the test.
    Cleans up data at the end.
    """

def chatgpt_simple_conversation() -> dict
    """Simple linear ChatGPT conversation (no branches)."""

def chatgpt_branched_conversation() -> dict
    """ChatGPT conversation with branches (regeneration)."""

def chatgpt_conversation_with_code() -> dict
    """ChatGPT conversation with code blocks including language."""

def chatgpt_conversation_with_image() -> dict
    """ChatGPT conversation with image content."""

def chatgpt_conversations(chatgpt_simple_conversation, chatgpt_branched_conversation, chatgpt_conversation_with_code) -> list[dict]
    """List of all ChatGPT test conversations."""

def claude_simple_conversation() -> dict
    """Simple Claude conversation."""

def claude_conversation_with_thinking() -> dict
    """Claude conversation with thinking blocks."""

def claude_conversation_with_tool_use() -> dict
    """Claude conversation with tool use."""

def claude_conversations(claude_simple_conversation, claude_conversation_with_thinking, claude_conversation_with_tool_use) -> list[dict]
    """List of all Claude test conversations."""

def conversation_with_continuation() -> dict
    """ChatGPT conversation with continuation prompts."""

def populated_chatgpt_db(clean_db_session, chatgpt_simple_conversation)
    """Database with a single ChatGPT conversation imported."""

def populated_claude_db(clean_db_session, claude_simple_conversation)
    """Database with a single Claude conversation imported."""

def fully_populated_db(clean_db_session, chatgpt_simple_conversation, chatgpt_branched_conversation, claude_simple_conversation)
    """Database with multiple conversations and derived data."""

```

## tests/integration/test_annotators.py
```python
class TestAnnotatorBase
    """Tests for base annotator functionality."""

    def test_add_annotation(self, db_session)
        """Test adding a simple annotation."""

    def test_annotation_with_key(self, db_session)
        """Test adding annotation with a key."""

    def test_annotation_deduplication(self, db_session)
        """Test that duplicate annotations are not created."""

    def test_supersede_annotation(self, db_session)
        """Test superseding an annotation."""


class TestAnnotationManager
    """Tests for annotation manager."""

    def test_register_annotator(self, db_session)
        """Test registering an annotator."""

    def test_run_all(self, db_session)
        """Test running all annotators."""

    def test_get_annotations(self, db_session)
        """Test querying annotations."""

    def test_get_tags(self, db_session)
        """Test getting tags for an entity."""


class TestFeatureAnnotators
    """Tests for feature detection annotators."""

    def conversation_with_features(self)
        """Conversation with various detectable features."""

    def test_wiki_link_annotator(self, clean_db_session, conversation_with_features)
        """Test wiki link detection."""

    def test_code_block_annotator(self, clean_db_session, conversation_with_features)
        """Test code block detection."""

    def test_latex_annotator(self, clean_db_session, conversation_with_features)
        """Test LaTeX detection."""

    def test_continuation_annotator(self, clean_db_session, conversation_with_features)
        """Test continuation signal detection."""

    def test_exchange_type_annotator(self, clean_db_session, conversation_with_features)
        """Test exchange type classification."""


class TestCustomAnnotator
    """Tests for creating custom annotators."""

    def test_custom_annotator_interface(self, db_session)
        """Test that custom annotators work correctly."""


class TestAnnotator(Annotator)

    def compute(self)


class TestAnnotator(Annotator)

    def compute(self)


class TestAnnotator(Annotator)

    def compute(self)


class TestAnnotator(Annotator)

    def compute(self)


class DummyAnnotator(Annotator)

    def compute(self)


class CountingAnnotator(Annotator)

    def compute(self)


class TopicAnnotator(Annotator)
    """Custom annotator that tags exchanges with topics."""

    def compute(self) -> int


```

## tests/integration/test_builders.py
```python
class TestTreeBuilder
    """Tests for dialogue tree builder."""

    def test_build_linear_tree(self, clean_db_session, chatgpt_simple_conversation)
        """Test building tree for linear conversation."""

    def test_build_branched_tree(self, clean_db_session, chatgpt_branched_conversation)
        """Test building tree for branched conversation."""

    def test_message_paths(self, clean_db_session, chatgpt_simple_conversation)
        """Test that message paths are created correctly."""

    def test_linear_sequences(self, clean_db_session, chatgpt_simple_conversation)
        """Test that linear sequences are created."""

    def test_multiple_sequences_for_branches(self, clean_db_session, chatgpt_branched_conversation)
        """Test that branched conversations get multiple sequences."""

    def test_sequence_messages_order(self, clean_db_session, chatgpt_simple_conversation)
        """Test that sequence messages are ordered correctly."""


class TestExchangeBuilder
    """Tests for exchange builder."""

    def test_build_exchanges_simple(self, clean_db_session, chatgpt_simple_conversation)
        """Test building exchanges from simple conversation."""

    def test_exchange_dyadic_structure(self, clean_db_session, chatgpt_simple_conversation)
        """Test that exchanges have user->assistant structure."""

    def test_exchange_deduplication(self, clean_db_session, chatgpt_branched_conversation)
        """Test that shared prefix exchanges are not duplicated."""

    def test_exchange_content_created(self, clean_db_session, chatgpt_simple_conversation)
        """Test that exchange content is created."""

    def test_continuation_detection(self, clean_db_session, conversation_with_continuation)
        """Test that continuation prompts are detected."""


class TestHashBuilder
    """Tests for content hash builder."""

    def test_build_hashes(self, fully_populated_db)
        """Test building content hashes."""

    def test_message_hashes(self, fully_populated_db)
        """Test that message hashes are created."""

    def test_exchange_hashes(self, fully_populated_db)
        """Test that exchange hashes are created."""

    def test_multiple_normalizations(self, fully_populated_db)
        """Test that multiple normalizations are created."""

    def test_find_duplicates(self, clean_db_session)
        """Test finding duplicate content."""


```

## tests/integration/test_chunk_builder.py
```python
class TestMessageChunkBuilder

    def test_build_chunks_creates_runs_and_chunks(self, clean_db_session, chatgpt_simple_conversation)

    def test_second_run_creates_new_run_and_new_chunks(self, clean_db_session, chatgpt_simple_conversation)

    def test_views_exist_and_return_rows(self, clean_db_session, chatgpt_simple_conversation)


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


class TestDerivedModels
    """Tests for derived schema models with database persistence."""

    def test_create_dialogue_tree(self, db_session)
        """Test creating a dialogue tree."""

    def test_create_exchange(self, db_session)
        """Test creating an exchange."""

    def test_exchange_content_relationship(self, db_session)
        """Test exchange to content relationship."""

    def test_create_annotation(self, db_session)
        """Test creating an annotation."""

    def test_annotation_with_data(self, db_session)
        """Test annotation with JSONB data."""


class TestCascadeDeletes
    """Tests for cascade delete behavior."""

    def test_delete_dialogue_cascades_to_messages(self, db_session)
        """Test that deleting dialogue deletes messages."""

    def test_delete_message_cascades_to_content(self, db_session)
        """Test that deleting message deletes content parts."""


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

## tests/unit/test_exchange_utils.py
```python
class TestIsContinuationPrompt
    """Tests for continuation prompt detection."""

    def test_simple_continue(self)
        """Test 'continue' is detected."""

    def test_continue_with_punctuation(self)
        """Test 'continue?' is detected."""

    def test_continue_uppercase(self)
        """Test 'CONTINUE' is detected (case insensitive)."""

    def test_continue_with_whitespace(self)
        """Test '  continue  ' is detected (trimmed)."""

    def test_more(self)
        """Test 'more' is detected."""

    def test_keep_going(self)
        """Test 'keep going' is detected."""

    def test_go_on(self)
        """Test 'go on' is detected."""

    def test_elaborate(self)
        """Test 'elaborate' is detected."""

    def test_yes_please(self)
        """Test 'yes please' is detected."""

    def test_ok(self)
        """Test 'ok' is detected."""

    def test_okay(self)
        """Test 'okay' is detected."""

    def test_please(self)
        """Test 'please' is detected."""

    def test_proceed(self)
        """Test 'proceed' is detected."""

    def test_quote_elaborate_pattern(self)
        """Test quote + elaborate pattern."""

    def test_quote_continue_pattern(self)
        """Test quote + continue pattern."""

    def test_not_continuation_long_message(self)
        """Test long message is not a continuation."""

    def test_not_continuation_question(self)
        """Test substantive question is not a continuation."""

    def test_not_continuation_new_topic(self)
        """Test new topic is not a continuation."""

    def test_none_text(self)
        """Test None returns False."""

    def test_empty_string(self)
        """Test empty string returns False."""

    def test_whitespace_only(self)
        """Test whitespace only returns False."""

    def test_all_patterns(self)
        """Test all defined continuation patterns are detected."""

    def test_continue_with_extra_words(self)
        """Test 'continue please' is detected (starts with pattern)."""

    def test_pattern_in_middle_not_detected(self)
        """Test pattern in middle of sentence is not detected."""


class TestMessageInfo
    """Tests for MessageInfo dataclass."""

    def test_create_message_info(self)
        """Test creating MessageInfo."""

    def test_message_info_none_content(self)
        """Test MessageInfo with None content."""


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

## tests/unit/test_hash_utils.py
```python
class TestComputeHash
    """Tests for hash computation."""

    def test_simple_hash(self)
        """Test hashing simple text."""

    def test_hash_none(self)
        """Test None returns None."""

    def test_hash_empty_string(self)
        """Test empty string returns None."""

    def test_hash_consistency(self)
        """Test same input gives same hash."""

    def test_hash_normalization(self)
        """Test whitespace normalization."""

    def test_hash_different_content(self)
        """Test different content gives different hash."""

    def test_hash_unicode(self)
        """Test hashing unicode text."""

    def test_hash_long_text(self)
        """Test hashing long text."""

    def test_hash_matches_direct_sha256(self)
        """Test hash matches direct SHA-256 computation."""


```

## tests/unit/test_markdown_chunking.py
```python
def builder(mock_session)

def test_parse_markdown_heading_paragraph_and_fence(builder)

def test_parse_markdown_blockquote_and_list(builder)

def test_parse_markdown_hr(builder)

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


class TestDerivedModels
    """Tests for derived schema model instantiation."""

    def test_create_dialogue_tree(self)
        """Test creating a DialogueTree."""

    def test_dialogue_tree_boolean_flags(self)
        """Test DialogueTree boolean flags."""

    def test_create_exchange(self)
        """Test creating an Exchange."""

    def test_exchange_continuation_flag(self)
        """Test Exchange continuation flag."""

    def test_create_exchange_content(self)
        """Test creating ExchangeContent."""


class TestAnnotationModel
    """Tests for Annotation model instantiation."""

    def test_create_tag_annotation(self)
        """Test creating a tag annotation."""

    def test_annotation_with_key(self)
        """Test annotation with key for namespacing."""

    def test_annotation_with_data(self)
        """Test annotation with JSONB data."""

    def test_annotation_with_confidence(self)
        """Test annotation with confidence score."""


class TestContentHashModel
    """Tests for ContentHash model instantiation."""

    def test_create_message_hash(self)
        """Test creating a message content hash."""

    def test_create_exchange_hash(self)
        """Test creating an exchange content hash."""


class TestModelTableNames
    """Tests for model table name configuration."""

    def test_dialogue_table_name(self)
        """Test Dialogue uses raw schema."""

    def test_message_table_name(self)
        """Test Message uses raw schema."""

    def test_content_part_table_name(self)
        """Test ContentPart uses raw schema."""

    def test_exchange_table_name(self)
        """Test Exchange uses derived schema."""

    def test_annotation_table_name(self)
        """Test Annotation uses derived schema."""


```
