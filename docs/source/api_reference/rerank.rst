Rerank Module
=============

The Rerank module provides document reranking functionality with support for three provider modes:
OpenAI-compatible, DashScope, and Chat-based custom format.

The module uses a strategy pattern with separate handlers for each mode, ensuring a unified interface
while hiding provider-specific differences.

Supported Modes
---------------

- **openai**: OpenAI-compatible standard rerank API
- **dashscope**: Alibaba Cloud DashScope rerank API
- **chat**: Chat-based custom rerank API (default)

All modes return the same ``RerankResult`` format, hiding provider differences from users.

.. automodule:: lexilux.rerank
   :members:
   :undoc-members:
   :show-inheritance:

See Also
--------

- :doc:`../rerank_modes_comparison` - Comprehensive comparison of rerank modes
- :doc:`../chat_rerank_spec` - Detailed specification for implementing custom chat-based rerank services

