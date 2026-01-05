Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[0.4.0] - 2026-01-XX
--------------------

Added
~~~~~

* Added ``finish_reason`` field to ``ChatResult`` and ``ChatStreamChunk`` to track why generation stopped
* Added ``proxies`` parameter to ``Chat``, ``Embed``, and ``Rerank`` classes for explicit proxy configuration
* Added comprehensive integration tests for ``finish_reason`` functionality
* Added defensive handling for invalid ``finish_reason`` values from compatible services

Improved
~~~~~~~~

* Enhanced robustness of ``finish_reason`` parsing with normalization function
* Improved error handling for malformed API responses
* Updated test configuration to use new endpoint keys

Fixed
~~~~~

* Fixed test configuration key names to match updated ``test_endpoints.json`` structure
* Fixed potential issues with proxy configuration not being passed to requests

[0.1.0] - 2024-XX-XX
--------------------

Added
~~~~~

* Initial release
* Chat API support with streaming
* Embedding API support
* Rerank API support
* Tokenizer support (optional dependency on transformers)
* Unified Usage and ResultBase classes
* Comprehensive test suite
* Documentation

