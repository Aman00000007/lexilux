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

2. **For streaming, track completion status**:

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

3. **Check finish_reason only after successful response**:

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

