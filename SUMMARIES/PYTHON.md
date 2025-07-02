# Python Project Structure

## src/conversation_tagger/analysis/faceting.py
```python
def get_facet_value(tags: List[Tag], facet_tag_name: str, facet_attribute: Optional[str]) -> str
    """Extract facet value from a conversation's tags."""

def do_facet_conversations(tagged_conversations: List[Dict[[str, Any]]], facet_tag_name: str, facet_attribute: Optional[str], max_facets: int) -> Dict[[str, List[Dict[[str, Any]]]]]
    """Group conversations by facet values."""

def print_faceted_summary(tagged_conversations: List[Dict[[str, Any]]], facet_tag_name: str, facet_attribute: Optional[str], show_details: bool, max_facets: int)
    """Print tag summary broken down by facets."""

```

## src/conversation_tagger/core/conversation.py
```python
@dataclass
class Conversation
    """A conversation consisting of sequential exchanges."""

    def __post_init__(self)
        """Post-initialization to ensure tags are set."""

    def _add_exchange_tags(self)

    @property
    def _exchange_tags(self) -> List[Tag]
        """Get all tags from exchanges."""

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
def create_conversation_length_tag(conversation: Conversation) -> Tag
    """Create structured tag for conversation length."""

def conversation_feature_summary(conversation: Conversation) -> List[Tag]
    """Aggregate feature usage across all exchanges."""

def conversation_gizmo_plugin_summary(conversation: Conversation) -> List[Tag]
    """Aggregate gizmo/plugin usage across all exchanges."""

def has_github_repos(exchange: Exchange) -> bool
    """Check if GitHub repositories were selected for context in this exchange."""

def has_canvas_operations(exchange: Exchange) -> bool
    """Check for canvas/document operations in this exchange."""

def has_web_search(exchange: Exchange) -> bool
    """Check for web search operations in this exchange."""

def has_reasoning_thoughts(exchange: Exchange) -> bool
    """Check for reasoning/thinking patterns in this exchange."""

def has_code_execution(exchange: Exchange) -> bool
    """Check for code execution artifacts in this exchange."""

def has_code_blocks(exchange: Exchange) -> bool
    """Check for explicit code blocks (``` markdown syntax)."""

def has_script_headers(exchange: Exchange) -> bool
    """Check for script headers and system includes."""

def has_code_structure_patterns(exchange: Exchange) -> bool
    """Check for actual code structure patterns (syntax combinations that suggest real code)."""

def user_has_quote_elaborate(exchange: Exchange) -> bool
    """Check if user messages contain quote+elaborate continuation pattern."""

def user_has_attachments(exchange: Exchange) -> bool
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

def get_gizmo_tags(exchange: Exchange) -> List[Tag]
    """Get tags for specific gizmos used in this exchange."""

def get_plugin_tags(exchange: Exchange) -> List[Tag]
    """Get tags for specific plugins used in this exchange."""

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
def get_message_text(message: Dict[[str, Any]]) -> str
    """Extract text content from a message."""

@dataclass
class Exchange
    """A sequential conversation exchange with merge capabilities."""

    @classmethod
    def create(cls, conversation_id: str, messages: List[Dict[[str, Any]]]) -> 'Exchange'
        """Create a new exchange with a random UUID."""

    @property
    def first_message_time(self) -> float
        """Get the create_time of the first message for ordering."""

    def has_continuations(self) -> bool
        """Check if this exchange has continuation prompts (multiple user messages)."""

    def get_user_messages(self) -> List[Dict[[str, Any]]]
        """Get just the user messages."""

    def get_assistant_messages(self) -> List[Dict[[str, Any]]]
        """Get just the assistant messages."""

    def get_user_texts(self) -> str
        """Get combined text from all user messages."""

    def get_assistant_texts(self) -> str
        """Get combined text from all assistant messages."""

    def __add__(self, other: 'Exchange') -> 'Exchange'
        """Merge two exchanges by combining and time-ordering their messages."""

    def __len__(self) -> int
        """Return number of messages in exchange."""

    def __str__(self) -> str
        """String representation showing message sequence."""


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

    def parse_conversation(self, conversation: Dict[[str, Any]]) -> Conversation
        """Parse a conversation into a Conversation object with fully-tagged exchanges."""

    def _create_dyadic_exchanges(self, messages: List[Dict[[str, Any]]], conversation_id: str) -> List[Exchange]
        """Step 1: Create simple USER-ASSISTANT dyadic exchanges."""

    def _merge_continuations(self, dyadic_exchanges: List[Exchange]) -> List[Exchange]
        """Step 2: Merge exchanges when continuation patterns are detected."""


```

## src/conversation_tagger/core/exchange_tagger.py
```python
class ExchangeTagger
    """Tags exchanges with configurable rules."""

    def __init__(self)

    def add_rule(self, tag_name: str, rule_function: Callable)
        """Add rule for exchanges."""

    def tag_exchange(self, exchange: Exchange) -> Exchange
        """Tag a single exchange and return the updated exchange."""


```

## src/conversation_tagger/core/tag.py
```python
class Tag
    """A tag with optional key-value attributes."""

    def __init__(self, name: str)

    def __str__(self)

    def __repr__(self)

    def __eq__(self, other)

    def __hash__(self)


```

## src/conversation_tagger/core/tagger.py
```python
class ConversationTagger
    """Main tagger that uses exchange-based analysis."""

    def __init__(self, exchange_parser: ExchangeParser | None)

    def add_exchange_rule(self, tag_name: str, rule_function: Callable)
        """Add rule for analyzing exchanges."""

    def add_conversation_rule(self, tag_name: str, rule_function: Callable)
        """Add rule for analyzing entire conversations."""

    def tag_conversation(self, conversation: Dict[[str, Any]]) -> Conversation
        """Tag a conversation using exchange-based analysis."""


```

## src/conversation_tagger/factory.py
```python
def create_default_tagger() -> ConversationTagger
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
def test_tag_functionality()
    """Test that Tag objects work correctly."""

def test_exchange_creation()
    """Test basic exchange creation and message handling."""

def test_exchange_text_api()
    """Test the actual text extraction API to understand what works."""

def test_exchange_tagger_with_correct_api()
    """Test exchange tagger using the correct API."""

def test_conversation_parsing_basic()
    """Test basic conversation parsing without relying on broken methods."""

def test_default_tagger_exists()
    """Test that the default tagger can be created."""

def test_some_default_rules_work()
    """Test that at least some default rules are working."""

def working_rule(exchange)
    """A rule that uses the correct API."""

```

## tests/conversation_tagger/test_core.py
```python
def test_tag_creation()
    """Test tag creation with and without attributes."""

def test_exchange_basic()
    """Test exchange creation and basic operations."""

def test_exchange_merging()
    """Test merging exchanges preserves chronological order."""

def test_conversation_properties()
    """Test conversation aggregation properties."""

def sample_conversation_data()
    """Sample conversation data for parsing tests."""

def test_simple_parsing(sample_conversation_data)
    """Test basic conversation parsing."""

```

## tests/conversation_tagger/test_detection.py
```python
def test_create_conversation_length_tag()
    """Test conversation length categorization."""

def test_conversation_feature_summary()
    """Test feature aggregation across exchanges."""

def test_conversation_gizmo_plugin_summary()
    """Test gizmo/plugin aggregation across exchanges."""

def test_has_github_repos()
    """Test GitHub repository detection."""

def test_has_canvas_operations()
    """Test canvas/document operations detection."""

def test_has_web_search()
    """Test web search detection."""

def test_has_reasoning_thoughts()
    """Test reasoning/thinking pattern detection."""

def test_has_code_execution()
    """Test code execution detection."""

def test_has_code_blocks()
    """Test code block detection."""

def test_has_script_headers()
    """Test script header detection."""

def test_has_code_structure_patterns()
    """Test code structure pattern detection."""

def test_user_has_quote_elaborate()
    """Test quote+elaborate pattern detection."""

def test_user_has_attachments()
    """Test user attachment detection."""

def test_user_is_continuation()
    """Test continuation detection."""

def test_assistant_has_reasoning()
    """Test assistant reasoning detection."""

def test_has_wiki_links()
    """Test wiki link detection."""

def test_has_latex_math()
    """Test LaTeX math detection."""

def test_first_user_has_large_content()
    """Test large content detection in first user message."""

def test_first_user_has_code_patterns()
    """Test code pattern detection in first user message."""

def test_first_user_has_attachments()
    """Test attachment detection in first user message."""

def test_first_user_has_code_attachments()
    """Test code attachment detection in first user message."""

def test_get_gizmo_tags()
    """Test gizmo tag generation."""

def test_get_plugin_tags()
    """Test plugin tag generation."""

def test_extract_proposed_title()
    """Test proposed title extraction from assistant messages."""

def test_naive_title_extraction()
    """Test the helper function directly."""

```

## tests/conversation_tagger/test_integration.py
```python
def sample_coding_conversation()
    """A realistic conversation about coding that should trigger multiple tags."""

def test_default_tagger_creation()
    """Test that default tagger is created with expected rules."""

def test_end_to_end_tagging(sample_coding_conversation)
    """Test complete tagging pipeline with realistic conversation."""

def test_conversation_with_attachments()
    """Test conversation that includes file attachments."""

def test_math_conversation()
    """Test conversation with mathematical content."""

def test_large_content_detection()
    """Test detection of large content messages."""

def test_empty_conversation_handling()
    """Test handling of edge cases like empty conversations."""

def mentions_python(exchange)

```

## tests/conversation_tagger/test_tagging.py
```python
def test_exchange_tagger_basic()
    """Test basic exchange tagging functionality."""

def test_exchange_tagger_with_attributes()
    """Test exchange tagging with tag attributes."""

def test_conversation_tagger()
    """Test conversation-level tagging."""

def test_tagging_error_handling()
    """Test that tagging rules handle errors gracefully."""

def conversation_with_continuation()
    """Conversation data that should trigger continuation merging."""

def test_continuation_detection(conversation_with_continuation)
    """Test that continuation patterns merge exchanges correctly."""

def has_greeting(exchange)

def message_length(exchange)

def is_multi_turn(conversation)

def exchange_count_info(conversation)

def broken_rule(exchange)

def working_rule(exchange)

```
