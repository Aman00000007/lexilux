# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2026-01-06

### Changed
- **BREAKING**: Simplified `Tokenizer` mode parameter from `mode="online"/"offline"/"auto_offline"` to `offline=True/False`
  - Removed `auto_offline` mode (which tried local cache first, then downloaded if not found)
  - Now uses `offline=True` for offline-only mode (fails if model not cached)
  - Now uses `offline=False` (default) for online mode (prioritizes local cache, downloads if needed)
  - Model download logic moved to business code, independent of `AutoTokenizer`
- Renamed exception classes to follow Python naming conventions:
  - `ChatStreamInterrupted` → `ChatStreamInterruptedError`
  - `ChatIncompleteResponse` → `ChatIncompleteResponseError`

### Added
- Added `huggingface-hub>=0.16.0` to `tokenizer` optional dependencies for explicit model downloading support
- `Tokenizer` now automatically downloads models when `offline=False` and model is not cached locally

### Fixed
- Fixed ruff linting configuration warnings by moving `select` and `ignore` to `[tool.ruff.lint]` section

## [0.5.0] - 2026-01-05

### Added
- Added `ChatHistory` class for comprehensive conversation history management
  - Automatic extraction from messages or Chat results (no manual maintenance required)
  - Support for `ChatHistory.from_messages()` and `ChatHistory.from_chat_result()` class methods
  - Token counting and analysis with `analyze_tokens()`, `count_tokens()`, and `count_tokens_per_round()`
  - Truncation by rounds with `truncate_by_rounds()` to fit context windows
  - Serialization to/from JSON with `to_json()` and `from_json()` methods
  - Round-based operations: `get_last_n_rounds()`, `remove_last_round()`, `update_last_assistant()`
  - Multi-format export support (Markdown, HTML, Text, JSON)
- Added `auto_history` feature to `Chat` class for automatic conversation tracking
  - Enable with `Chat(..., auto_history=True)` for zero-maintenance history recording
  - Automatically records all conversations (both streaming and non-streaming)
  - Access recorded history with `chat.get_history()` method
  - Clear history with `chat.clear_history()` method
  - Works seamlessly with streaming responses, updating history in real-time
- Added `ChatContinue` class for continuing cut-off responses
  - `ChatContinue.continue_request()` method to continue generation when `finish_reason == "length"`
  - Support for adding continue prompts (`add_continue_prompt=True`) or direct continuation (`add_continue_prompt=False`)
  - Customizable continue prompt text via `continue_prompt` parameter
  - `ChatContinue.merge_results()` method to merge multiple results into a single complete response
  - Automatically merges text, usage statistics, and metadata from multiple continuation requests

## [0.4.0] - 2026-01-05

### Added
- Added `finish_reason` field to `ChatResult` and `ChatStreamChunk` to track why generation stopped
  - Possible values: `"stop"`, `"length"`, `"content_filter"`, or `None`
  - Helps distinguish between normal completion, token limit, and content filtering
- Added `proxies` parameter to `Chat`, `Embed`, and `Rerank` classes for explicit proxy configuration
  - Supports environment variables (default behavior)
  - Allows explicit proxy configuration via `proxies` parameter
  - Can disable proxies by passing empty dict `{}`
- Added comprehensive integration tests for `finish_reason` functionality
- Added defensive handling for invalid `finish_reason` values from compatible services

### Improved
- Enhanced robustness of `finish_reason` parsing with normalization function
  - Handles empty strings, invalid types, and missing values gracefully
  - Ensures compatibility with services that don't fully implement OpenAI standard
- Improved error handling for malformed API responses
- Updated test configuration to use new endpoint keys (`embedding`, `reranker`, `completion`)

### Fixed
- Fixed test configuration key names to match updated `test_endpoints.json` structure
- Fixed potential issues with proxy configuration not being passed to requests

## [0.3.1] - 2026-01-04

### Changed
- Fixed CI workflow
- Update black tool python version dependencies

## [0.3.0] - 2026-01-03

### Changed
- Updated Python version support to 3.8-3.14
- Integrated CI workflow with uv for automated testing and building

## [0.2.0] - 2026-01-03

### Changed
- **BREAKING**: Removed chat-based rerank mode support. Rerank now only supports OpenAI-compatible and DashScope modes.
- Changed default rerank mode from `"chat"` to `"openai"`.
- Reorganized tests: all real API tests are now marked as `@pytest.mark.integration` and excluded from default test runs.

### Removed
- `ChatBasedHandler` class and chat-based rerank mode (`mode="chat"`).
- `chat_rerank_spec.rst` documentation (no longer needed as chat mode is removed).

### Improved
- Updated test endpoints to use `rerank_local_qwen3` and `embed_local_qwen3` for integration tests.
- Improved test organization following varlord's pattern for integration tests.
- Updated documentation to reflect rerank mode changes.

## [0.1.2] - 2025-12-29

### Added
- Scripts to automatically generate release notes
- Better github action workflow

## [0.1.1] - 2025-12-29

### Added
- Examples
- Comprehensive test suite
- Documentation

## [0.1.0] - 2025-12-28

### Added
- Initial release
- Chat API support with streaming
- Embedding API support
- Rerank API support
- Tokenizer support (optional dependency on transformers)
- Unified Usage and ResultBase classes
- Documentation

