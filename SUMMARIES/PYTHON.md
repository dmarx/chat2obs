# Python Project Structure

## src/conversation_tagger/analysis/faceting.py
```python
def get_facet_value(annotations: Dict[[str, Any]], facet_annotation_name: str, facet_attribute: Optional[str]) -> str
    """Extract facet value from a conversation's annotations."""

def do_facet_conversations(tagged_conversations: List[Dict[[str, Any]]], facet_annotation_name: str, facet_attribute: Optional[str], max_facets: int) -> Dict[[str, List[Dict[[str, Any]]]]]
    """Group conversations by facet values."""

def print_faceted_summary(tagged_conversations: List[Dict[[str, Any]]], facet_annotation_name: str, facet_attribute: Optional[str], show_details: bool, max_facets: int)
    """Print annotation summary broken down by facets."""

```

## src/conversation_tagger/core/conversation.py
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

## src/conversation_tagger/core/detection.py
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

## src/conversation_tagger/core/detection_old.py
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

## src/conversation_tagger/core/exchange.py
```python
@dataclass
class Exchange
    """A sequential conversation exchange with merge capabilities."""

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

## src/conversation_tagger/core/exchange_parser.py
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

    def _create_dyadic_exchanges(self, messages: list[Message], conversation_id: str) -> List[Exchange]
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

## src/conversation_tagger/core/exchange_tagger.py
```python
class ExchangeTagger
    """Tags exchanges with configurable rules using annotations."""

    def __init__(self)

    def add_rule(self, annotation_name: str, rule_function: Callable)
        """Add rule for exchanges."""

    def tag_exchange(self, exchange: Exchange) -> Exchange
        """Tag a single exchange and return the updated exchange."""


```

## src/conversation_tagger/core/generate.py
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

def load_template(template_name: str) -> Template
    """Load a Jinja template from the templates directory."""

def generate_notes(conversation: Conversation, template_name: str, output_dir: str) -> List[str]
    """Generate Obsidian notes from a conversation."""

```

## src/conversation_tagger/core/message.py
```python
class Message

    def __init__(self, data: dict)

    @property
    def content(self)

    @property
    def created_date(self)

    @property
    def author_role(self)

    def _get_author_role(self)

    def _get_content(self)

    def _get_created_date(self)

    def __repr__(self)

    def __str__(self)


def get_message_text_chatgpt(message: dict[[str, Any]]) -> str
    """Extract text content from a message."""

class MessageOpenAI(Message)

    def _get_content(self)

    def _get_created_date(self)

    def _get_author_role(self)


class MessageClaude(Message)

    def _get_content(self)

    def _get_created_date(self)

    def _get_author_role(self)


```

## src/conversation_tagger/core/tag.py
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

## src/conversation_tagger/core/tagger.py
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

## src/conversation_tagger/factory.py
```python
def create_default_tagger(source) -> ConversationTagger
    """Create a basic tagger with example rules for the new exchange design."""

```

## tests/conversation_tagger/conftest.py
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

## tests/conversation_tagger/test_basic_working.py
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

def legacy_tag_rule(exchange)

def false_rule(exchange)

def none_rule(exchange)

```

## tests/conversation_tagger/test_core.py
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

## tests/conversation_tagger/test_detection.py
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

## tests/conversation_tagger/test_integration.py
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

## tests/conversation_tagger/test_parameterized.py
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

## tests/conversation_tagger/test_tagging.py
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
