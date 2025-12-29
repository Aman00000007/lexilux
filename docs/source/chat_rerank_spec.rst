Chat-Based Rerank API Specification
====================================

This document describes the data exchange standard for implementing a custom chat-based rerank service compatible with Lexilux. This specification enables you to build your own rerank service that works seamlessly with Lexilux's chat-based rerank mode.

Overview
--------

The chat-based rerank API uses the standard chat completions endpoint (`/chat/completions`) to perform document reranking. The rerank request data is sent as a JSON string within the message content, and the rerank results are returned as a JSON string in the response message content.

This approach allows rerank services to leverage existing chat completion infrastructure while maintaining a flexible data format.

Request Format
--------------

Endpoint
~~~~~~~~

**POST** ``{base_url}/chat/completions``

Where ``{base_url}`` is the base URL of your API service (e.g., ``http://192.168.0.220:20551/v1``).

Headers
~~~~~~~

Required headers:

.. code-block:: http

   Content-Type: application/json
   Authorization: Bearer {api_key}

Request Body
~~~~~~~~~~~~

The request body follows the standard chat completions format:

.. code-block:: json

   {
     "model": "rerank-model-name",
     "messages": [
       {
         "role": "user",
         "content": "{rerank_data_json_string}"
       }
     ],
     "stream": false
   }

**Fields:**

- **`model`** (string, required): The rerank model identifier.
- **`messages`** (array, required): Array containing a single message object.
  - **`role`** (string, required): Must be `"user"`.
  - **`content`** (string, required): JSON string containing the rerank request data.
- **`stream`** (boolean, optional): Should be `false` for rerank requests (default: `false`).

Rerank Data JSON String
~~~~~~~~~~~~~~~~~~~~~~~

The `content` field contains a JSON string with the following structure:

.. code-block:: json

   {
     "query": "search query text",
     "candidates": [
       "document text 1",
       "document text 2",
       "document text 3"
     ],
     "top_k": 3,
     "prompt": "optional prompt text",
     "batch_size": 10
   }

**Fields:**

- **`query`** (string, required): The search query to rank documents against.
- **`candidates`** (array of strings, required): List of document texts to be reranked.
- **`top_k`** (integer, optional): Number of top results to return. If not specified, all results are returned.
- **`prompt`** (string, optional): Additional prompt text to guide the reranking process.
- **`batch_size`** (integer, optional): Batch size for processing (if supported by the service).

**Example JSON string:**

.. code-block:: json

   "{\"query\": \"python http library\", \"candidates\": [\"urllib is a built-in library\", \"requests is popular\", \"httpx is modern\"], \"top_k\": 3}"

**Note:** The JSON string must be properly escaped when embedded in the message content.

Complete Request Example
~~~~~~~~~~~~~~~~~~~~~~~~~

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

Response Format
---------------

Response Structure
~~~~~~~~~~~~~~~~~~

The response follows the standard chat completions format:

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
           "content": "{rerank_results_json_string}"
         },
         "finish_reason": "stop"
       }
     ],
     "usage": {
       "prompt_tokens": 100,
       "completion_tokens": 50,
       "total_tokens": 150
     }
   }

**Fields:**

- **`id`** (string, optional): Unique identifier for the completion.
- **`object`** (string, optional): Object type, typically `"chat.completion"`.
- **`created`** (integer, optional): Unix timestamp of creation.
- **`model`** (string, optional): Model identifier used.
- **`choices`** (array, required): Array containing a single choice object.
  - **`index`** (integer, optional): Index of the choice (typically 0).
  - **`message`** (object, required): Message object containing results.
    - **`role`** (string, required): Must be `"assistant"`.
    - **`content`** (string, required): JSON string containing rerank results.
  - **`finish_reason`** (string, optional): Reason for completion (typically `"stop"`).
- **`usage`** (object, optional): Token usage statistics.
  - **`prompt_tokens`** (integer, optional): Number of tokens in the prompt.
  - **`completion_tokens`** (integer, optional): Number of tokens in the completion.
  - **`total_tokens`** (integer, optional): Total tokens used.

Rerank Results JSON String
~~~~~~~~~~~~~~~~~~~~~~~~~~

The `content` field contains a JSON string with rerank results. Multiple formats are supported:

**Format 1: Dictionary with results array (Recommended)**

.. code-block:: json

   {
     "results": [
       {"index": 1, "score": 0.95},
       {"index": 0, "score": 0.80},
       {"index": 2, "score": 0.70}
     ]
   }

**Format 2: Dictionary with data array**

.. code-block:: json

   {
     "data": [
       {"index": 1, "score": 0.95},
       {"index": 0, "score": 0.80}
     ]
   }

**Format 3: Direct list with document text and score**

.. code-block:: json

   [
     ["requests", -2.8233],
     ["urllib", -3.2031],
     ["httpx", -2.7788]
   ]

**Format 4: Direct list with index and score**

.. code-block:: json

   [
     [1, 0.95],
     [0, 0.80],
     [2, 0.70]
   ]

**Result Object Fields:**

- **`index`** (integer, required for dict format): Original index of the document in the candidates array (0-based).
- **`score`** (float, required): Relevance score for the document.
  - Positive scores: Higher is better (e.g., 0.95 > 0.80)
  - Negative scores: Less negative is better (e.g., -2.8 > -3.2)
- **`document`** (string, optional): Original document text (if included).
- **`document_index`** (integer, optional): Alternative field name for index.
- **`relevance_score`** (float, optional): Alternative field name for score.

**Note:** Lexilux automatically handles different field names and formats.

Complete Response Example
~~~~~~~~~~~~~~~~~~~~~~~~~

**Example 1: Dictionary format with results**

.. code-block:: json

   {
     "id": "cmpl-e50d37d944234fceb9c642047aa2adf2",
     "object": "chat.completion",
     "created": 1766981504,
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
       "prompt_tokens": 39,
       "completion_tokens": 49,
       "total_tokens": 88
     }
   }

**Example 2: Direct list format with document text**

.. code-block:: json

   {
     "choices": [
       {
         "message": {
           "content": "[[\"httpx\", -2.7788209915161133], [\"requests\", -2.8233261108398438], [\"urllib\", -3.203111410140991]]"
         }
       }
     ],
     "usage": {
       "total_tokens": 88
     }
   }

Score Format Guidelines
------------------------

Positive Scores
~~~~~~~~~~~~~~~

- **Range:** Typically `0.0` to `1.0` or higher
- **Interpretation:** Higher score = Better relevance
- **Sorting:** Descending order (highest first)
- **Example:** `0.95 > 0.80 > 0.70`

Negative Scores
~~~~~~~~~~~~~~~

- **Range:** Negative numbers (e.g., `-2.0`, `-3.5`)
- **Interpretation:** Less negative = Better relevance
- **Sorting:** Descending order (least negative first, which is mathematically correct)
- **Example:** `-2.8 > -3.2 > -4.0` (because -2.8 > -3.2)

**Important:** Lexilux automatically detects the score format and applies the correct sorting. You can use either format, but be consistent within a single response.

Error Handling
--------------

Error Response Format
~~~~~~~~~~~~~~~~~~~~~

If an error occurs, you can return an error message in the content field:

.. code-block:: json

   {
     "choices": [
       {
         "message": {
           "content": "Error: Invalid query format"
         }
       }
     ]
   }

Or use standard HTTP error codes:

- **400 Bad Request:** Invalid request format
- **401 Unauthorized:** Invalid or missing API key
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Server-side error

Lexilux will raise appropriate exceptions based on HTTP status codes.

Implementation Checklist
------------------------

To implement a chat-based rerank service compatible with Lexilux:

1. **Endpoint Setup**
   - [ ] Implement `POST /chat/completions` endpoint
   - [ ] Support standard chat completion request format
   - [ ] Handle authentication via `Authorization: Bearer {api_key}` header

2. **Request Parsing**
   - [ ] Extract `model` from request body
   - [ ] Parse `messages[0].content` as JSON string
   - [ ] Extract `query` and `candidates` from parsed JSON
   - [ ] Handle optional fields: `top_k`, `prompt`, `batch_size`

3. **Rerank Processing**
   - [ ] Implement reranking algorithm
   - [ ] Calculate relevance scores for each candidate
   - [ ] Sort results by score (descending)
   - [ ] Apply `top_k` limit if specified

4. **Response Formatting**
   - [ ] Format results as JSON string
   - [ ] Use one of the supported formats (dict with results, direct list, etc.)
   - [ ] Include `index` or document text for mapping
   - [ ] Wrap in chat completion response format
   - [ ] Include usage statistics if available

5. **Error Handling**
   - [ ] Validate request format
   - [ ] Return appropriate HTTP status codes
   - [ ] Provide clear error messages

6. **Testing**
   - [ ] Test with Lexilux client
   - [ ] Verify score sorting (positive and negative)
   - [ ] Test with different result formats
   - [ ] Test error cases

Example Implementation (Python/Flask)
--------------------------------------

.. code-block:: python

   from flask import Flask, request, jsonify
   import json

   app = Flask(__name__)

   def rerank_documents(query, candidates, top_k=None):
       """Simple rerank implementation (example)"""
       # Your reranking logic here
       results = []
       for idx, candidate in enumerate(candidates):
           # Calculate relevance score (example)
           score = calculate_relevance(query, candidate)
           results.append({"index": idx, "score": score})
       
       # Sort by score (descending)
       results.sort(key=lambda x: x["score"], reverse=True)
       
       # Apply top_k
       if top_k:
           results = results[:top_k]
       
       return results

   @app.route("/v1/chat/completions", methods=["POST"])
   def chat_completions():
       # Authenticate
       api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
       if not validate_api_key(api_key):
           return jsonify({"error": "Unauthorized"}), 401
       
       # Parse request
       data = request.json
       model = data.get("model")
       message_content = data["messages"][0]["content"]
       
       # Parse rerank data
       rerank_data = json.loads(message_content)
       query = rerank_data["query"]
       candidates = rerank_data["candidates"]
       top_k = rerank_data.get("top_k")
       
       # Perform reranking
       results = rerank_documents(query, candidates, top_k)
       
       # Format response
       response_content = json.dumps({"results": results}, ensure_ascii=False)
       
       return jsonify({
           "model": model,
           "choices": [{
               "message": {
                   "role": "assistant",
                   "content": response_content
               }
           }],
           "usage": {
               "total_tokens": len(query) + sum(len(c) for c in candidates)
           }
       })

   if __name__ == "__main__":
       app.run(host="0.0.0.0", port=20551)

Testing Your Implementation
----------------------------

Use Lexilux to test your implementation:

.. code-block:: python

   from lexilux import Rerank

   # Initialize with chat mode
   rerank = Rerank(
       base_url="http://localhost:20551/v1",
       api_key="your-api-key",
       model="your-rerank-model",
       mode="chat"  # or omit, chat is default
   )

   # Test reranking
   query = "python http library"
   docs = [
       "urllib is a built-in Python library",
       "requests is a popular third-party library",
       "httpx is a modern async client"
   ]

   result = rerank(query, docs, top_k=2)
   print(result.results)  # [(index, score), ...]

Additional Notes
----------------

- **JSON String Encoding:** Ensure proper JSON escaping when embedding rerank data in message content. Use `json.dumps()` with `ensure_ascii=False` for Unicode support.

- **Performance:** For large candidate lists, consider implementing batch processing using the optional `batch_size` parameter.

- **Caching:** Consider caching rerank results for identical queries and candidate sets to improve performance.

- **Rate Limiting:** Implement rate limiting to prevent abuse of your service.

- **Monitoring:** Log requests and responses for debugging and monitoring purposes.

