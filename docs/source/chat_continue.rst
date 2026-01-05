Continue Generation
====================

Lexilux provides functionality to continue generation when responses are cut off
due to token limits, allowing you to seamlessly extend incomplete responses.

Overview
--------

When a chat completion is stopped due to ``max_tokens`` limit (``finish_reason == "length"``),
you may want to continue the generation. Lexilux provides multiple ways to handle this:

1. **Chat.complete()** - Recommended for most cases, ensures complete response
2. **Chat.continue_if_needed()** - Conditionally continue if truncated
3. **ChatContinue.continue_request()** - Advanced control with full flexibility

Key Features
------------

1. **Automatic History Retrieval**: Works seamlessly with ``auto_history=True``
2. **Multiple Continues**: Automatically continue multiple times if needed
3. **Result Merging**: Automatically merge all continuation results
4. **Usage Aggregation**: Automatically combine token usage from multiple requests

When to Use
-----------

Use continuation when:

* A response has ``finish_reason == "length"`` (cut off due to token limit)
* You need complete responses (e.g., JSON extraction)
* You're working with long-form content generation
* You want to ensure response completeness

Recommended Approach: Chat.complete()
-------------------------------------

The simplest and most recommended way to ensure complete responses:

.. code-block:: python

   from lexilux import Chat

   chat = Chat(..., auto_history=True)

   # Automatically handles truncation, returns complete result
   result = chat.complete("Write a long JSON response", max_tokens=100)
   json_data = json.loads(result.text)  # Guaranteed complete

   # With error handling
   try:
       result = chat.complete("Very long response", max_tokens=50, max_continues=3)
   except ChatIncompleteResponse as e:
       print(f"Still incomplete after {e.continue_count} continues")
       print(f"Received: {len(e.final_result.text)} chars")

Key Features of complete():
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Automatically continues if ``finish_reason == "length"``
* Supports multiple continues (``max_continues`` parameter)
* Raises ``ChatIncompleteResponse`` if still truncated (if ``ensure_complete=True``)
* Requires ``auto_history=True`` (for automatic history retrieval)

Conditional Continue: Chat.continue_if_needed()
------------------------------------------------

Continue only if the result is truncated:

.. code-block:: python

   from lexilux import Chat

   chat = Chat(..., auto_history=True)

   result = chat("Long story", max_tokens=50)
   
   # Only continues if result.finish_reason == "length"
   full_result = chat.continue_if_needed(result, max_continues=3)
   
   # If result.finish_reason != "length", returns result unchanged

Advanced Control: ChatContinue.continue_request()
---------------------------------------------------

For advanced use cases requiring full control:

Enhanced API (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~

The enhanced ``continue_request()`` supports automatic history retrieval,
multiple continues, and automatic merging:

.. code-block:: python

   from lexilux import Chat, ChatContinue

   chat = Chat(..., auto_history=True)

   result = chat("Write a long story", max_tokens=50)
   
   if result.finish_reason == "length":
       # Automatic history retrieval, multiple continues, automatic merging
       full_result = ChatContinue.continue_request(
           chat,
           result,  # Note: history parameter is optional when auto_history=True
           max_continues=3
       )
       print(full_result.text)  # Complete merged text

Key Parameters:
~~~~~~~~~~~~~~~

* ``history``: Optional. If ``None`` and ``chat.auto_history=True``, automatically retrieved
* ``max_continues``: Maximum number of continuation attempts (default: 1)
* ``auto_merge``: If ``True``, automatically merge results (default: ``True``)
* ``add_continue_prompt``: Whether to add a user continue message (default: ``True``)
* ``continue_prompt``: User prompt for continuation (default: "continue")

Return Types:
~~~~~~~~~~~~~

* If ``auto_merge=True``: Returns merged ``ChatResult``
* If ``auto_merge=False``: Returns list of ``ChatResult`` instances

Examples:

.. code-block:: python

   # Basic usage (automatic history, single continue, auto merge)
   result = chat("Story", max_tokens=50)
   if result.finish_reason == "length":
       full_result = ChatContinue.continue_request(chat, result)

   # Multiple continues
   result = chat("Very long story", max_tokens=30)
   if result.finish_reason == "length":
       full_result = ChatContinue.continue_request(chat, result, max_continues=3)

   # Get all intermediate results
   result = chat("Story", max_tokens=50)
   if result.finish_reason == "length":
       all_results = ChatContinue.continue_request(chat, result, auto_merge=False)
       # all_results = [result, continue_result1, continue_result2, ...]

Legacy API (Still Supported)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The legacy API is still supported for backward compatibility:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)
   
   result = chat("Write a long story", max_tokens=50)
   
   if result.finish_reason == "length":
       # Manual history creation
       history = ChatHistory.from_chat_result("Write a long story", result)
       
       # Continue
       continue_result = ChatContinue.continue_request(
           chat,
           history,  # Required in legacy API
           result,
           add_continue_prompt=True
       )
       
       # Manual merging
       full_result = ChatContinue.merge_results(result, continue_result)

Result Merging
--------------

The ``merge_results()`` method combines multiple results:

.. code-block:: python

   from lexilux import ChatContinue

   result1 = chat("Story part 1", max_tokens=50)
   result2 = chat("Story part 2", max_tokens=50)
   
   merged = ChatContinue.merge_results(result1, result2)
   # merged.text = result1.text + result2.text
   # merged.usage.total_tokens = result1.usage.total_tokens + result2.usage.total_tokens

Common Patterns
---------------

Pattern 1: Ensure Complete Response (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``chat.complete()`` for scenarios requiring complete responses:

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   # JSON extraction
   result = chat.complete("Extract data as JSON", max_tokens=100)
   json_data = json.loads(result.text)  # Guaranteed complete
   
   # Long-form content
   result = chat.complete("Write a comprehensive guide", max_tokens=200)

Pattern 2: Conditional Continue
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``chat.continue_if_needed()`` when you want to continue only if needed:

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   result = chat("Response", max_tokens=100)
   # Automatically continues if truncated, otherwise returns result unchanged
   full_result = chat.continue_if_needed(result, max_continues=3)

Pattern 3: Advanced Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``ChatContinue.continue_request()`` for full control:

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   result = chat("Story", max_tokens=50)
   if result.finish_reason == "length":
       # Get all intermediate results
       all_results = ChatContinue.continue_request(
           chat, result, auto_merge=False, max_continues=3
       )
       for i, r in enumerate(all_results):
           print(f"Part {i+1}: {len(r.text)} chars")

Error Handling
--------------

Handling Incomplete Responses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using ``chat.complete()`` with ``ensure_complete=True`` (default),
``ChatIncompleteResponse`` is raised if the response is still truncated
after ``max_continues``:

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat.exceptions import ChatIncompleteResponse

   chat = Chat(..., auto_history=True)
   
   try:
       result = chat.complete("Very long response", max_tokens=30, max_continues=2)
   except ChatIncompleteResponse as e:
       print(f"Still incomplete after {e.continue_count} continues")
       print(f"Received: {len(e.final_result.text)} chars")
       # Use partial result if acceptable
       result = e.final_result

   # Or allow partial results
   result = chat.complete(
       "Very long response",
       max_tokens=30,
       max_continues=2,
       ensure_complete=False  # Returns partial result instead of raising
   )
   if result.finish_reason == "length":
       print("Warning: Response was truncated")

Best Practices
--------------

1. **Use chat.complete() for Most Cases**: Simplest and most reliable

2. **Enable auto_history**: Required for automatic history retrieval

3. **Set Appropriate max_continues**: Balance between completeness and API costs

4. **Handle ChatIncompleteResponse**: Be prepared for cases where response
   is still incomplete after max_continues

5. **Monitor Token Usage**: Track total tokens across all continuations

6. **Consider Increasing max_tokens**: If you frequently need multiple continues,
   consider increasing ``max_tokens`` instead

Examples
--------

Complete Workflow with complete()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lexilux import Chat
   import json

   chat = Chat(..., auto_history=True)
   
   # Ensure complete JSON response
   result = chat.complete(
       "Extract user data as JSON",
       max_tokens=100,
       max_continues=3
   )
   
   # Guaranteed complete
   data = json.loads(result.text)

Multiple Continues
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   result = chat("Very long story", max_tokens=30)
   if result.finish_reason == "length":
       # Automatically continues up to 3 times
       full_result = ChatContinue.continue_request(
           chat, result, max_continues=3
       )
       print(f"Complete story: {len(full_result.text)} chars")

Get All Intermediate Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   result = chat("Story", max_tokens=50)
   if result.finish_reason == "length":
       all_results = ChatContinue.continue_request(
           chat, result, auto_merge=False, max_continues=3
       )
       
       for i, r in enumerate(all_results):
           print(f"Part {i+1}: {len(r.text)} chars, tokens: {r.usage.total_tokens}")

See Also
--------

* :doc:`auto_history` - Automatic history management
* :doc:`chat_history` - Manual history management
* :doc:`api_reference/chat` - Full API reference
* :doc:`error_handling` - Error handling guide
