Error Handling and Network Interruptions
==========================================

This guide explains how to handle errors and distinguish between network problems
and normal API completions.

Understanding finish_reason
---------------------------

The ``finish_reason`` field indicates why a chat completion stopped. It is only
available when the API successfully returns a response:

- **"stop"**: Model stopped naturally or hit a stop sequence
- **"length"**: Reached max_tokens limit
- **"content_filter"**: Content was filtered
- **None**: Unknown or not provided (some APIs may not provide this)

**Important**: ``finish_reason`` is **NOT** set when network errors occur.

Distinguishing Network Errors from Normal Completion
----------------------------------------------------

### Non-Streaming Requests

For non-streaming requests (``chat()`` method):

**Network Error**:
- An exception is raised (``requests.RequestException``, ``ConnectionError``, ``TimeoutError``, etc.)
- No ``ChatResult`` is returned
- No ``finish_reason`` is available

**Normal Completion**:
- ``ChatResult`` is returned successfully
- ``finish_reason`` is set to a valid value ("stop", "length", "content_filter", or None)

Example:

.. code-block:: python

   from lexilux import Chat
   import requests

   chat = Chat(base_url="https://api.example.com/v1", api_key="key", model="gpt-4")

   try:
       result = chat("Hello, world!")
       # Success: finish_reason indicates why generation stopped
       print(f"Completed: {result.finish_reason}")
       print(f"Text: {result.text}")
   except requests.RequestException as e:
       # Network error: no finish_reason available
       print(f"Network error: {e}")
       print("Connection was interrupted - not a normal completion")

### Streaming Requests

For streaming requests (``chat.stream()`` method):

**Network Error**:
- An exception is raised during iteration
- The iterator stops yielding chunks
- If interrupted before receiving a ``done=True`` chunk, no ``finish_reason`` is available

**Normal Completion**:
- A chunk with ``done=True`` is received
- ``finish_reason`` is set in that chunk (or may be None for [DONE] messages)

**Incomplete Stream**:
- Exception raised after receiving some chunks
- Check if any chunk has ``done=True`` to determine if completion occurred before interruption

Example:

.. code-block:: python

   from lexilux import Chat
   import requests

   chat = Chat(base_url="https://api.example.com/v1", api_key="key", model="gpt-4")

   try:
       chunks = []
       for chunk in chat.stream("Write a long story"):
           print(chunk.delta, end="", flush=True)
           chunks.append(chunk)
       
       # Check if we received a completion
       done_chunks = [c for c in chunks if c.done]
       if done_chunks:
           final_chunk = done_chunks[-1]
           print(f"\nCompleted: {final_chunk.finish_reason}")
       else:
           print("\nStream ended without completion signal")
           
   except requests.RequestException as e:
       # Network error during streaming
       print(f"\nNetwork error: {e}")
       
       # Check if we got any completion before the error
       done_chunks = [c for c in chunks if c.done]
       if done_chunks:
           print("Completion occurred before network error")
           print(f"Finish reason: {done_chunks[-1].finish_reason}")
       else:
           print("No completion received - stream was interrupted")

Common Network Exceptions
-------------------------

The following exceptions indicate network/connection problems:

- ``requests.ConnectionError``: Failed to establish connection
- ``requests.TimeoutError``: Request timed out
- ``requests.HTTPError``: HTTP error response (4xx, 5xx)
- ``requests.RequestException``: Base class for all request exceptions

When any of these exceptions are raised, ``finish_reason`` is not available because
the API response was not successfully received.

Handling Incomplete Responses
------------------------------

When using ``chat.complete()`` or continuation functionality, you may encounter
``ChatIncompleteResponse`` if the response is still truncated after maximum continues.

.. code-block:: python

   from lexilux import Chat, ChatHistory
   from lexilux.chat.exceptions import ChatIncompleteResponseError

   chat = Chat(...)
   history = ChatHistory()

   try:
       result = chat.complete("Very long response", history=history, max_tokens=30, max_continues=2)
   except ChatIncompleteResponse as e:
       print(f"Still incomplete after {e.continue_count} continues")
       print(f"Received: {len(e.final_result.text)} chars")
       # Use partial result if acceptable
       result = e.final_result

   # Or allow partial results
   result = chat.complete(
       "Very long response",
       history=history,
       max_tokens=30,
       max_continues=2,
       ensure_complete=False  # Returns partial result instead of raising
   )
   if result.finish_reason == "length":
       print("Warning: Response was truncated")

Handling Streaming Interruptions
---------------------------------

When streaming is interrupted, partial content is preserved in history:

.. code-block:: python

   from lexilux import Chat, ChatHistory

   chat = Chat(...)
   history = ChatHistory()

   iterator = chat.stream("Long response", history=history)
   try:
       for chunk in iterator:
           print(chunk.delta, end="")
   except requests.RequestException as e:
       print(f"\nStream interrupted: {e}")
       
       # Partial content is preserved in history
       if history.messages:
           last_msg = history.messages[-1]
           if last_msg.get("role") == "assistant":
               print(f"Partial content: {len(last_msg['content'])} chars")
       
       # Clean up if needed
       chat.clear_last_assistant_message()

Lexilux-Specific Exceptions
----------------------------

ChatIncompleteResponse
~~~~~~~~~~~~~~~~~~~~~~

Raised when a response is still incomplete after maximum continuation attempts.

.. code-block:: python

   from lexilux.chat.exceptions import ChatIncompleteResponse

   try:
       result = chat.complete("Very long response", max_tokens=30, max_continues=2)
   except ChatIncompleteResponse as e:
       print(f"Final result: {e.final_result.text}")
       print(f"Continue count: {e.continue_count}")
       print(f"Max continues: {e.max_continues}")

ChatStreamInterrupted
~~~~~~~~~~~~~~~~~~~~~

Raised when a streaming request is interrupted before completion (if implemented).

.. code-block:: python

   from lexilux.chat.exceptions import ChatStreamInterrupted

   try:
       iterator = chat.stream("Long response")
       for chunk in iterator:
           print(chunk.delta, end="")
   except ChatStreamInterrupted as e:
       print(f"Interrupted. Received: {len(e.get_partial_text())} chars")
       partial_result = e.get_partial_result()
       # Can try to recover using ChatContinue or retry

Best Practices
--------------

1. **Always use try-except blocks** when making API calls:

   .. code-block:: python

      try:
          result = chat("Hello")
          if result.finish_reason:
              print(f"Normal completion: {result.finish_reason}")
      except requests.RequestException as e:
          print(f"Network error: {e}")

2. **Use chat.complete() for guaranteed complete responses**:

   .. code-block:: python

      from lexilux import Chat, ChatHistory
      from lexilux.chat.exceptions import ChatIncompleteResponseError

      chat = Chat(...)
      history = ChatHistory()

      try:
          result = chat.complete("Extract JSON", history=history, max_tokens=100)
          json_data = json.loads(result.text)  # Guaranteed complete
      except ChatIncompleteResponseError as e:
          print(f"Still incomplete: {e.final_result.text}")
          # Handle partial result

3. **For streaming, track completion status and clean up on error**:

   .. code-block:: python

      completed = False
      try:
          for chunk in chat.stream("Hello"):
              print(chunk.delta, end="")
              if chunk.done:
                  completed = True
                  print(f"\nFinished: {chunk.finish_reason}")
      except requests.RequestException as e:
          if completed:
              print(f"\nCompleted before error: {e}")
          else:
              print(f"\nInterrupted: {e}")
              # Clean up partial response if needed
              # You manage history explicitly
              if history.messages and history.messages[-1].get("role") == "assistant":
                  history.remove_last()

4. **Handle history behavior on errors**:

   .. code-block:: python

      from lexilux import Chat, ChatHistory

      chat = Chat(...)
      history = ChatHistory()

      # Non-streaming: Exception means no assistant response in history
      try:
          result = chat("Hello", history=history)
      except Exception:
          # History contains user message but NO assistant response
          # (user message is added before request, assistant only on success)
          # Only user messages, no assistant responses for failed calls

      # Streaming: Partial content is preserved, clean up if needed
      iterator = chat.stream("Long response")
      try:
          for chunk in iterator:
              print(chunk.delta)
      except Exception:
          # Partial content is in history
          chat.clear_last_assistant_message()  # Clean up

5. **Check finish_reason only after successful response**:

   .. code-block:: python

      # Correct: finish_reason is only available on success
      result = chat("Hello")
      if result.finish_reason == "length":
          print("Hit token limit")
      
      # Incorrect: finish_reason won't exist if exception is raised
      # try:
      #     result = chat("Hello")
      # except Exception:
      #     print(result.finish_reason)  # ERROR: result may not exist

6. **Use retry logic for network errors**:

   .. code-block:: python

      import time
      from requests import RequestException

      max_retries = 3
      for attempt in range(max_retries):
          try:
              result = chat("Hello")
              break  # Success
          except RequestException as e:
              if attempt < max_retries - 1:
                  wait_time = 2 ** attempt  # Exponential backoff
                  time.sleep(wait_time)
                  continue
              raise  # Last attempt failed

