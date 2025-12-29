Rerank Modes Comparison
=======================

Lexilux supports two rerank modes: **OpenAI-compatible** and **Chat-based**. This document provides a comprehensive comparison of their data formats, request/response structures, and usage patterns to help you choose the appropriate mode for your use case.

Overview
--------

.. list-table:: Mode Comparison Summary
   :header-rows: 1
   :widths: 30 35 35

   * - Feature
     - OpenAI-Compatible Mode
     - Chat-Based Mode
   * - **Mode Identifier**
     - ``mode="openai"``
     - ``mode="chat"`` (default)
   * - **API Endpoint**
     - ``POST {base_url}/rerank``
     - ``POST {base_url}/chat/completions``
   * - **Request Format**
     - Direct JSON object
     - JSON string in message content
   * - **Response Format**
     - Direct JSON object
     - JSON string in message content
   * - **Parameter Names**
     - ``top_n``, ``return_documents``
     - ``top_k``, ``include_docs``
   * - **Score Field Name**
     - ``relevance_score``
     - ``score`` or ``relevance_score``
   * - **Document Format**
     - Nested object: ``{"text": "..."}``
     - Direct string or nested object
   * - **Use Case**
     - Standard rerank APIs (Cohere, etc.)
     - Custom chat-based rerank services

Request Format Comparison
-------------------------

OpenAI-Compatible Mode
~~~~~~~~~~~~~~~~~~~~~~

**Endpoint:**
.. code-block:: http

   POST {base_url}/rerank

**Request Headers:**
.. code-block:: http

   Content-Type: application/json
   Authorization: Bearer {api_key}

**Request Body:**
.. code-block:: json

   {
     "model": "rerank-english-v3.0",
     "query": "python http library",
     "documents": [
       "urllib is a built-in Python library for HTTP requests",
       "requests is a popular third-party HTTP library for Python",
       "httpx is a modern async HTTP client for Python"
     ],
     "top_n": 3,
     "return_documents": true
   }

**Key Characteristics:**
- Direct JSON object structure
- Uses ``documents`` array (not ``candidates``)
- Uses ``top_n`` parameter (not ``top_k``)
- Uses ``return_documents`` boolean (not ``include_docs``)
- All fields are at the top level

Chat-Based Mode
~~~~~~~~~~~~~~~

**Endpoint:**
.. code-block:: http

   POST {base_url}/chat/completions

**Request Headers:**
.. code-block:: http

   Content-Type: application/json
   Authorization: Bearer {api_key}

**Request Body:**
.. code-block:: json

   {
     "model": "RerankService",
     "messages": [
       {
         "role": "user",
         "content": "{\"query\": \"python http library\", \"candidates\": [\"urllib is a built-in Python library for HTTP requests\", \"requests is a popular third-party HTTP library for Python\", \"httpx is a modern async HTTP client for Python\"], \"top_k\": 3}"
       }
     ],
     "stream": false
   }

**Key Characteristics:**
- Uses standard chat completions endpoint
- Rerank data is JSON string in ``messages[0].content``
- Uses ``candidates`` array (not ``documents``)
- Uses ``top_k`` parameter (not ``top_n``)
- Additional fields can be added to the rerank data JSON string

Side-by-Side Request Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Request Field Mapping
   :header-rows: 1
   :widths: 25 35 40

   * - Field Purpose
     - OpenAI Mode
     - Chat Mode
   * - **Model identifier**
     - ``payload["model"]``
     - ``payload["model"]``
   * - **Query text**
     - ``payload["query"]``
     - ``json.loads(payload["messages"][0]["content"])["query"]``
   * - **Document list**
     - ``payload["documents"]``
     - ``json.loads(payload["messages"][0]["content"])["candidates"]``
   * - **Top results limit**
     - ``payload["top_n"]``
     - ``json.loads(payload["messages"][0]["content"])["top_k"]``
   * - **Include documents**
     - ``payload["return_documents"]``
     - Handled by ``include_docs`` parameter in Lexilux API

Response Format Comparison
---------------------------

OpenAI-Compatible Mode
~~~~~~~~~~~~~~~~~~~~~~

**Response Structure:**
.. code-block:: json

   {
     "results": [
       {
         "index": 1,
         "relevance_score": 0.95,
         "document": {
           "text": "requests is a popular third-party HTTP library for Python"
         }
       },
       {
         "index": 0,
         "relevance_score": 0.80,
         "document": {
           "text": "urllib is a built-in Python library for HTTP requests"
         }
       },
       {
         "index": 2,
         "relevance_score": 0.70,
         "document": {
           "text": "httpx is a modern async HTTP client for Python"
         }
       }
     ],
     "usage": {
       "prompt_tokens": 50,
       "completion_tokens": 10,
       "total_tokens": 60
     }
   }

**Key Characteristics:**
- Direct JSON object at top level
- Results in ``results`` array
- Each result has:
  - ``index``: Original document index (0-based)
  - ``relevance_score``: Relevance score (typically 0.0-1.0)
  - ``document``: Object with ``text`` field containing document content
- Usage statistics at top level

Chat-Based Mode
~~~~~~~~~~~~~~~

**Response Structure:**
.. code-block:: json

   {
     "id": "cmpl-abc123",
     "object": "chat.completion",
     "created": 1234567890,
     "model": "RerankService",
     "choices": [
       {
         "index": 0,
         "message": {
           "role": "assistant",
           "content": "{\"results\": [{\"index\": 1, \"score\": 0.95}, {\"index\": 0, \"score\": 0.80}, {\"index\": 2, \"score\": 0.70}]}"
         },
         "finish_reason": "stop"
       }
     ],
     "usage": {
       "prompt_tokens": 50,
       "completion_tokens": 10,
       "total_tokens": 60
     }
   }

**Key Characteristics:**
- Standard chat completion response structure
- Rerank results in ``choices[0].message.content`` as JSON string
- Multiple result formats supported:
  - Dictionary: ``{"results": [...]}`` or ``{"data": [...]}``
  - Direct list: ``[["doc", score], ...]`` or ``[[index, score], ...]``
- Score field can be ``score`` or ``relevance_score``
- Document can be direct string or nested object

Side-by-Side Response Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Response Field Mapping
   :header-rows: 1
   :widths: 25 35 40

   * - Data Location
     - OpenAI Mode
     - Chat Mode
   * - **Results array**
     - ``response["results"]``
     - ``json.loads(response["choices"][0]["message"]["content"])["results"]``
   * - **Result index**
     - ``result["index"]``
     - ``result["index"]`` or ``result[0]`` (if list format)
   * - **Result score**
     - ``result["relevance_score"]``
     - ``result["score"]`` or ``result["relevance_score"]`` or ``result[1]`` (if list format)
   * - **Document text**
     - ``result["document"]["text"]``
     - ``result["document"]`` (string) or ``result["document"]["text"]`` (object) or ``result[0]`` (if list format)
   * - **Usage stats**
     - ``response["usage"]``
     - ``response["usage"]``

Usage Comparison
----------------

Initialization
~~~~~~~~~~~~~~

**OpenAI-Compatible Mode:**
.. code-block:: python

   from lexilux import Rerank

   rerank = Rerank(
       base_url="https://api.cohere.ai/v1",
       api_key="your-api-key",
       model="rerank-english-v3.0",
       mode="openai"  # Explicit OpenAI mode
   )

**Chat-Based Mode:**
.. code-block:: python

   from lexilux import Rerank

   rerank = Rerank(
       base_url="http://192.168.0.220:20551/v1",
       api_key="your-api-key",
       model="RerankService",
       mode="chat"  # Or omit, chat is default
   )

Basic Rerank Call
~~~~~~~~~~~~~~~~~

**OpenAI-Compatible Mode:**
.. code-block:: python

   query = "python http library"
   docs = [
       "urllib is a built-in Python library for HTTP requests",
       "requests is a popular third-party HTTP library for Python",
       "httpx is a modern async HTTP client for Python"
   ]

   result = rerank(query, docs)
   # result.results: [(1, 0.95), (0, 0.80), (2, 0.70)]

**Chat-Based Mode:**
.. code-block:: python

   query = "python http library"
   docs = [
       "urllib is a built-in Python library for HTTP requests",
       "requests is a popular third-party HTTP library for Python",
       "httpx is a modern async HTTP client for Python"
   ]

   result = rerank(query, docs)
   # result.results: [(1, 0.95), (0, 0.80), (2, 0.70)]

**Note:** The Lexilux API is identical for both modes! The mode selection only affects the underlying HTTP request/response format.

With Top-K Filtering
~~~~~~~~~~~~~~~~~~~~

**OpenAI-Compatible Mode:**
.. code-block:: python

   result = rerank(query, docs, top_k=2)
   # Internally uses "top_n": 2 in request
   # result.results: [(1, 0.95), (0, 0.80)]

**Chat-Based Mode:**
.. code-block:: python

   result = rerank(query, docs, top_k=2)
   # Internally uses "top_k": 2 in rerank data JSON string
   # result.results: [(1, 0.95), (0, 0.80)]

With Document Inclusion
~~~~~~~~~~~~~~~~~~~~~~~

**OpenAI-Compatible Mode:**
.. code-block:: python

   result = rerank(query, docs, include_docs=True)
   # Internally uses "return_documents": true in request
   # result.results: [(1, 0.95, "requests is..."), (0, 0.80, "urllib is...")]

**Chat-Based Mode:**
.. code-block:: python

   result = rerank(query, docs, include_docs=True)
   # Document inclusion handled in response parsing
   # result.results: [(1, 0.95, "requests is..."), (0, 0.80, "urllib is...")]

Mode Override in Call
~~~~~~~~~~~~~~~~~~~~~

You can override the mode for individual calls:

.. code-block:: python

   # Initialize with chat mode
   rerank = Rerank(base_url="...", api_key="...", model="...", mode="chat")

   # Use OpenAI mode for this specific call
   result = rerank(query, docs, mode="openai")

   # Use chat mode for this call (or omit mode parameter)
   result = rerank(query, docs, mode="chat")

Data Format Details
--------------------

Request Data Structure
~~~~~~~~~~~~~~~~~~~~~~

**OpenAI-Compatible Mode Request:**
.. code-block:: json

   {
     "model": "rerank-model",
     "query": "search query",
     "documents": ["doc1", "doc2", "doc3"],
     "top_n": 3,
     "return_documents": true,
     "extra_field": "value"  // Additional fields from 'extra' parameter
   }

**Chat-Based Mode Request:**
.. code-block:: json

   {
     "model": "rerank-model",
     "messages": [
       {
         "role": "user",
         "content": "{\"query\": \"search query\", \"candidates\": [\"doc1\", \"doc2\", \"doc3\"], \"top_k\": 3, \"extra_field\": \"value\"}"
       }
     ],
     "stream": false
   }

Response Data Structure
~~~~~~~~~~~~~~~~~~~~~~~

**OpenAI-Compatible Mode Response:**
.. code-block:: json

   {
     "results": [
       {
         "index": 0,
         "relevance_score": 0.95,
         "document": {"text": "doc1"}
       }
     ],
     "usage": {"total_tokens": 100}
   }

**Chat-Based Mode Response (Format 1 - Dictionary):**
.. code-block:: json

   {
     "choices": [{
       "message": {
         "content": "{\"results\": [{\"index\": 0, \"score\": 0.95}]}"
       }
     }],
     "usage": {"total_tokens": 100}
   }

**Chat-Based Mode Response (Format 2 - Direct List):**
.. code-block:: json

   {
     "choices": [{
       "message": {
         "content": "[[\"doc1\", 0.95], [\"doc2\", 0.80]]"
       }
     }],
     "usage": {"total_tokens": 100}
   }

Field Name Mapping
-------------------

.. list-table:: Field Name Differences
   :header-rows: 1
   :widths: 30 35 35

   * - Purpose
     - OpenAI Mode
     - Chat Mode
   * - **Top results limit**
     - ``top_n``
     - ``top_k``
   * - **Include documents flag**
     - ``return_documents``
     - ``include_docs`` (Lexilux API)
   * - **Document array**
     - ``documents``
     - ``candidates``
   * - **Score field**
     - ``relevance_score``
     - ``score`` or ``relevance_score``
   * - **Results array**
     - ``results``
     - ``results`` or ``data``
   * - **Document text**
     - ``document.text``
     - ``document`` (string) or ``document.text`` (object)

Score Format Handling
----------------------

Both modes support positive and negative scores, but the handling is consistent:

**Positive Scores (e.g., 0.95, 0.80, 0.70):**
- Higher score = Better relevance
- Sorted in descending order: 0.95 > 0.80 > 0.70
- Works the same in both modes

**Negative Scores (e.g., -2.8, -3.2, -4.0):**
- Less negative = Better relevance
- Sorted in descending order: -2.8 > -3.2 > -4.0
- Works the same in both modes

Lexilux automatically detects the score format and applies the correct sorting in both modes.

Error Handling
--------------

Both modes use standard HTTP error codes:

.. list-table:: Error Codes
   :header-rows: 1
   :widths: 20 40 40

   * - Status Code
     - OpenAI Mode
     - Chat Mode
   * - **400 Bad Request**
     - Invalid request format
     - Invalid request format or JSON parsing error
   * - **401 Unauthorized**
     - Invalid or missing API key
     - Invalid or missing API key
   * - **429 Too Many Requests**
     - Rate limit exceeded
     - Rate limit exceeded
   * - **500 Internal Server Error**
     - Server-side error
     - Server-side error

**OpenAI Mode Error Response:**
.. code-block:: json

   {
     "error": {
       "message": "Invalid request format",
       "type": "invalid_request_error"
     }
   }

**Chat Mode Error Response:**
.. code-block:: json

   {
     "error": {
       "message": "Invalid JSON in message content",
       "type": "invalid_request_error"
     }
   }

Or error message in content:
.. code-block:: json

   {
     "choices": [{
       "message": {
         "content": "Error: Invalid query format"
       }
     }]
   }

When to Use Which Mode
----------------------

Use OpenAI-Compatible Mode When:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ✅ You're using a standard rerank API (Cohere, OpenAI-compatible services)
- ✅ You want direct, simple request/response format
- ✅ You prefer standard field names (``top_n``, ``return_documents``)
- ✅ Your service already implements OpenAI-compatible rerank API
- ✅ You need nested document objects (``{"text": "..."}``)

Use Chat-Based Mode When:
~~~~~~~~~~~~~~~~~~~~~~~~~~

- ✅ You're building a custom rerank service
- ✅ You want to leverage existing chat completion infrastructure
- ✅ You need flexible response formats (multiple formats supported)
- ✅ You want to reuse chat API endpoints
- ✅ Your service already implements chat completions API
- ✅ You need to send additional metadata in the rerank request

Migration Guide
---------------

Migrating from OpenAI Mode to Chat Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have an OpenAI-compatible rerank service and want to migrate to chat-based:

1. **Change the endpoint:**
   - From: ``POST /rerank``
   - To: ``POST /chat/completions``

2. **Wrap rerank data in message:**
   - Move all rerank fields into ``messages[0].content`` as JSON string
   - Change ``documents`` to ``candidates``
   - Change ``top_n`` to ``top_k``

3. **Wrap results in chat response:**
   - Put results in ``choices[0].message.content`` as JSON string
   - Keep usage statistics at top level

4. **Update Lexilux client:**
   - Change ``mode="openai"`` to ``mode="chat"``

Migrating from Chat Mode to OpenAI Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have a chat-based rerank service and want to migrate to OpenAI-compatible:

1. **Change the endpoint:**
   - From: ``POST /chat/completions``
   - To: ``POST /rerank``

2. **Flatten request structure:**
   - Extract fields from ``messages[0].content`` JSON string
   - Put them directly in request body
   - Change ``candidates`` to ``documents``
   - Change ``top_k`` to ``top_n``

3. **Flatten response structure:**
   - Extract results from ``choices[0].message.content`` JSON string
   - Put them directly in response body as ``results`` array
   - Ensure ``relevance_score`` field name
   - Ensure nested ``document.text`` structure

4. **Update Lexilux client:**
   - Change ``mode="chat"`` to ``mode="openai"``

Code Examples
-------------

Complete Example: OpenAI Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lexilux import Rerank

   # Initialize
   rerank = Rerank(
       base_url="https://api.cohere.ai/v1",
       api_key="co-xxx",
       model="rerank-english-v3.0",
       mode="openai"
   )

   # Rerank
   query = "machine learning"
   docs = [
       "Neural networks are computational models",
       "Support vector machines are classification algorithms",
       "Random forests combine multiple decision trees"
   ]

   result = rerank(query, docs, top_k=2, include_docs=True)

   # Process results
   for idx, score, doc in result.results:
       print(f"Rank {idx}: {score:.3f} - {doc}")

   print(f"Tokens used: {result.usage.total_tokens}")

Complete Example: Chat Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lexilux import Rerank

   # Initialize
   rerank = Rerank(
       base_url="http://192.168.0.220:20551/v1",
       api_key="sk-123456",
       model="RerankService",
       mode="chat"  # or omit (default)
   )

   # Rerank
   query = "machine learning"
   docs = [
       "Neural networks are computational models",
       "Support vector machines are classification algorithms",
       "Random forests combine multiple decision trees"
   ]

   result = rerank(query, docs, top_k=2, include_docs=True)

   # Process results
   for idx, score, doc in result.results:
       print(f"Rank {idx}: {score:.3f} - {doc}")

   print(f"Tokens used: {result.usage.total_tokens}")

Summary Table
-------------

.. list-table:: Complete Feature Comparison
   :header-rows: 1
   :widths: 25 37 38

   * - Feature
     - OpenAI-Compatible Mode
     - Chat-Based Mode
   * - **Mode Parameter**
     - ``mode="openai"``
     - ``mode="chat"`` (default)
   * - **Endpoint**
     - ``/rerank``
     - ``/chat/completions``
   * - **Request Structure**
     - Direct JSON object
     - JSON string in message
   * - **Query Field**
     - ``payload["query"]``
     - ``content["query"]``
   * - **Documents Field**
     - ``payload["documents"]``
     - ``content["candidates"]``
   * - **Top Results**
     - ``payload["top_n"]``
     - ``content["top_k"]``
   * - **Include Docs**
     - ``payload["return_documents"]``
     - Handled by Lexilux
   * - **Response Structure**
     - Direct JSON object
     - JSON string in message
   * - **Results Location**
     - ``response["results"]``
     - ``content["results"]`` or ``content["data"]``
   * - **Score Field**
     - ``result["relevance_score"]``
     - ``result["score"]`` or ``result["relevance_score"]``
   * - **Document Format**
     - ``{"text": "..."}``
     - String or ``{"text": "..."}``
   * - **Result Formats**
     - Dictionary only
     - Dictionary or list
   * - **Flexibility**
     - Standard format
     - Multiple formats supported

See Also
--------

- :doc:`../chat_rerank_spec` - Detailed specification for implementing chat-based rerank services
- :doc:`api_reference/rerank` - Complete API reference for Rerank class
- :doc:`examples/rerank` - Usage examples for reranking

