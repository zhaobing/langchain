# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Monorepo context

This is the `langchain-core` package within the larger LangChain monorepo. It defines the base abstractions that other packages build upon:
- **`langchain`**: Concrete implementations and high-level utilities
- **`partners/`**: Third-party integrations (OpenAI, Anthropic, etc.)
- **`langchain-text-splitters`**: Document chunking utilities
- **`langchain-tests`**: Standard test suite

These are linked via local paths in `[tool.uv.sources]` for development.

## Package overview

`langchain-core` contains the foundational abstractions and interfaces for the LangChain ecosystem. This is the **base layer** - no third-party integrations or concrete implementations of models/providers. The package defines interfaces, protocols, and base classes that the rest of the LangChain ecosystem builds upon.

## Development commands

This package uses `uv` for dependency management and `make` for task automation.

```bash
# Run unit tests (no network calls allowed)
make test

# Run specific test file
make test TEST_FILE=tests/unit_tests/test_runnables.py

# Run tests in watch mode (auto-rerun on changes)
make test_watch

# Run extended tests
make extended_tests

# Lint and type check
make lint

# Format code
make format

# Run specific test with pytest directly
uv run --group test pytest tests/unit_tests/test_runnables/test_base.py -v

# Check imports
make check_imports

# Run benchmarks
make benchmark
```

## Package architecture

### Core abstractions

The package is organized around several key abstractions that form the foundation of LangChain:

#### 1. **Runnable Protocol** (`langchain_core/runnables/`)
The central abstraction that defines a unified interface for all components:
- **Base class**: [`Runnable`](langchain_core/runnables/base.py) - All components inherit from this
- **Universal interface**: `invoke()`, `batch()`, `stream()`, plus async variants (`ainvoke()`, `abatch()`, `astream()`)
- **Composition**: Use the `|` operator to chain Runnables together (LCEL - LangChain Expression Language)
- **Configuration**: [`RunnableConfig`](langchain_core/runnables/config.py) for runtime behavior (callbacks, metadata, tags)
- **Event streaming**: `astream_events()` for granular execution events

**Key runnable modules**:
- `base.py`: Core Runnable class and LCEL implementation
- `config.py`: Configuration management and config propagation
- `branch.py`: `RunnableBranch` for conditional routing
- `fallbacks.py`: Error handling with fallback mechanisms
- `passthrough.py`: `RunnablePassthrough`, `RunnableLambda`, `RunnableParallel` for data manipulation
- `configurable.py`: Dynamic configuration at runtime
- `graph.py`: Runnable graph visualization and representation
- `history.py`: Message history management for conversations
- `retry.py`: Automatic retry logic with configurable policies

#### 2. **Language Models** (`langchain_core/language_models/`)
Base abstractions for different types of language models:
- **`BaseLanguageModel`**: Root abstraction for all language models (extends `Runnable`)
- **`BaseChatModel`**: For chat-based models (takes messages, returns messages)
- **`BaseLLM`**: Legacy string-in/string-out models
- **`fake/`**: Mock implementations for testing

#### 3. **Messages** (`langchain_core/messages/`)
Rich message system with multimodal support:
- **`BaseMessage`**: Foundation for all message types
- **Message types**: `HumanMessage`, `AIMessage`, `SystemMessage`, `ToolMessage`
- **`content/`**: Content blocks (text, images, audio, video, reasoning, tool calls)
- **`block_translators/`**: Provider-specific format adapters (OpenAI, Anthropic, Google, etc.)

#### 4. **Tools** (`langchain_core/tools/`)
Abstractions for agent tools:
- **`BaseTool`**: Base class for all tools
- **`tool` decorator**: Convert functions to tools
- **`StructuredTool`**: Tools with argument schemas
- **`convert_to_tool()`**: Convert Runnables to tools

#### 5. **Prompts** (`langchain_core/prompts/`)
Flexible templating system:
- **`BasePromptTemplate`**: Abstract prompt interface
- **`ChatPromptTemplate`**: For chat-based message templates
- **`FewShotPromptTemplate`**: Few-shot learning prompts
- **`MessagesPlaceholder`**: Placeholder for message lists in templates

#### 6. **Output Parsers** (`langchain_core/output_parsers/`)
Parse structured outputs from models:
- **`BaseOutputParser`**: Base interface
- **`StrOutputParser`**: Parse to string
- **`JsonOutputParser`**: Parse to JSON/dict
- **`PydanticOutputParser`**: Parse to Pydantic models

#### 7. **Other Key Modules**
- **`callbacks/`**: Event handling and callbacks during execution
- **`tracers/`**: Execution tracing and observability (LangSmith integration)
- **`documents/`**: Document abstractions for RAG applications
- **`embeddings/`**: Text embedding interfaces
- **`vectorstores/`**: Vector database interfaces
- **`retrievers/`**: Data retrieval abstractions
- **`stores/`**: Key-value storage interfaces
- **`load/`**: Serialization system ([`Serializable`](langchain_core/load/serializable.py) base class)

### Design patterns

#### Pydantic Integration
All major classes inherit from `Pydantic`'s `BaseModel`:
- Automatic validation
- JSON serialization/deserialization
- Schema generation
- Type safety with strict mode enabled

#### Serialization System
The [`Serializable`](langchain_core/load/serializable.py) base class provides:
- Save/load functionality for LangChain objects
- Safe serialization (secrets are not serialized)
- Custom serialization logic for complex objects
- Used by the `Runnable` protocol

#### Configuration Propagation
[`RunnableConfig`](langchain_core/runnables/config.py) flows through the entire chain:
- Callbacks for observability
- Metadata for tracking
- Tags for filtering
- Configurable fields for runtime behavior

#### Async/Sync Parallelism
All operations support both sync and async:
- `invoke()` / `ainvoke()`
- `batch()` / `abatch()`
- `stream()` / `astream()`
- Async operations use `asyncio` for concurrent execution

#### LCEL (LangChain Expression Language)
Declarative syntax for combining components:
```python
chain = prompt | model | parser
result = chain.invoke({"input": "hello"})
```
The `|` operator creates a `RunnableSequence` that automatically:
- Passes config through the chain
- Supports streaming
- Handles errors gracefully
- Provides observability

### API Stability Mechanisms

#### Beta Decorator
Use `@beta()` to mark experimental features:
```python
from langchain_core._api import beta

@beta()
class MyExperimentalFeature:
    pass
```
Beta features emit warnings when used, signaling they may change.

#### Deprecation System
Use `@deprecated()` to mark deprecated APIs:
```python
from langchain_core._api import deprecated

@deprecated("0.1.0", removal="1.0.0", alternative="new_function")
def old_function():
    pass
```

### Testing conventions

Tests mirror the source structure in `tests/`:
- **Unit tests**: `tests/unit_tests/` - No network calls allowed (enforced by `pytest-socket`)
- **Integration tests**: `tests/integration_tests/` - Network calls permitted
- **Benchmarks**: `tests/benchmarks/` - Performance tests

**Key testing practices**:
- Use `pytest` markers: `@pytest.mark.requires("library")`
- Use freezegun for time-dependent tests
- Use syrupy for snapshot testing
- Test both sync and async variants
- Mock external dependencies

### Common patterns

#### Creating a custom Runnable
```python
from langchain_core.runnables import RunnableSerializable

class MyComponent(RunnableSerializable[str, str]):
    def invoke(self, input: str, config: RunnableConfig | None = None) -> str:
        # Your implementation
        return input.upper()

    # Optionally implement stream, batch, etc.
```

#### Creating a custom tool
```python
from langchain_core.tools import tool

@tool
def my_tool(input: str) -> str:
    """Tool description."""
    return f"Processed: {input}"
```

#### Working with messages
```python
from langchain_core.messages import HumanMessage, AIMessage

message = HumanMessage(content="Hello")
# or with multimodal content
message = HumanMessage(content=[
    {"type": "text", "text": "Hello"},
    {"type": "image_url", "image_url": {"url": "..."}}
])
```

### Code quality standards

**CRITICAL: Maintain stable public interfaces**

Before making ANY changes to public APIs:
- Check if the function/class is exported in `__init__.py`
- Look for existing usage patterns in tests and examples
- Use keyword-only arguments for new parameters: `*, new_param: str = "default"`
- Mark experimental features with `@beta()` decorator

Ask: "Would this change break someone's code if they used it last week?"

**Type hints and docstrings:**

All Python code MUST include type hints and return types. Use Google-style docstrings:

```python
def filter_unknown_users(users: list[str], known_users: set[str]) -> list[str]:
    """Single line description of the function.

    Any additional context about the function can go here.

    Args:
        users: List of user identifiers to filter.
        known_users: Set of known/valid user identifiers.

    Returns:
        List of users that are not in the known_users set.

    Raises:
        ValueError: If users list is empty.
    """
```

- Types go in function signatures, NOT in docstrings
- If a default is present, DO NOT repeat it in the docstring unless there is post-processing
- Focus on "why" rather than "what" in descriptions
- Use American English spelling (e.g., "behavior", not "behaviour")

**Security considerations:**
- No `eval()`, `exec()`, or `pickle` on user-controlled input
- Proper exception handling (no bare `except:`)
- Remove unreachable/commented code before committing

### Related packages

- **`langchain`**: Concrete implementations and high-level utilities
- **`langchain-text-splitters`**: Document chunking (linked via local path in `[tool.uv.sources]`)
- **`langchain-tests`**: Standard test suite (linked via local path)
