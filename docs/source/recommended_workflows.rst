Recommended Workflows
=====================

This guide provides recommended workflows for common use cases with Lexilux.
These patterns follow best practices and make your code simpler and more reliable.

Simple Conversation (Recommended)
----------------------------------

The simplest way to use Lexilux for basic conversations:

.. code-block:: python

   from lexilux import Chat

   chat = Chat(
       base_url="https://api.example.com/v1",
       api_key="your-key",
       model="gpt-4",
       auto_history=True,  # Enable automatic history
   )

   # Just chat - history is automatically managed
   result1 = chat("What is Python?")
   result2 = chat("Tell me more")

   # Get complete history anytime
   history = chat.get_history()

   # Clear when starting new topic
   chat.clear_history()

**Key Points**:
- Enable ``auto_history=True`` for zero-maintenance history
- No manual history tracking needed
- History grows automatically with each call

Ensuring Complete Responses (Recommended)
------------------------------------------

When you need guaranteed complete responses (e.g., JSON extraction):

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat.exceptions import ChatIncompleteResponse
   import json

   chat = Chat(..., auto_history=True)

   # Method 1: Use complete() (simplest and recommended)
   try:
       result = chat.complete("Write a long JSON", max_tokens=100)
       json_data = json.loads(result.text)  # Guaranteed complete
   except ChatIncompleteResponse as e:
       print(f"Still incomplete after continues: {e.continue_count}")
       # Handle partial result if acceptable
       json_data = json.loads(e.final_result.text)

   # Method 2: Conditional continue
   result = chat("Extract data as JSON", max_tokens=100)
   full_result = chat.continue_if_needed(result, max_continues=3)
   json_data = json.loads(full_result.text)

**Key Points**:
- Use ``chat.complete()`` for guaranteed complete responses
- Automatically handles truncation
- Raises ``ChatIncompleteResponse`` if still incomplete (if ``ensure_complete=True``)

Streaming with Real-time Display
---------------------------------

Real-time output with automatic history updates:

.. code-block:: python

   from lexilux import Chat
   import requests

   chat = Chat(..., auto_history=True)

   try:
       iterator = chat.stream("Long response")
       for chunk in iterator:
           print(chunk.delta, end="", flush=True)
           if chunk.done:
               print(f"\nFinish: {chunk.finish_reason}")
   except requests.RequestException as e:
       print(f"\nStream interrupted: {e}")
       # Partial content is preserved in history
       # Clean up if needed:
       chat.clear_last_assistant_message()

**Key Points**:
- History updates in real-time during streaming
- Assistant message is added on first iteration
- Partial content is preserved on interruption
- Use ``clear_last_assistant_message()`` to clean up if needed

Handling Errors Gracefully
--------------------------

Comprehensive error handling pattern:

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat.exceptions import ChatIncompleteResponse
   import requests
   import time

   chat = Chat(..., auto_history=True)

   def robust_chat(prompt, max_retries=3):
       """Robust chat with retry logic."""
       for attempt in range(max_retries):
           try:
               # Use complete() for guaranteed complete response
               result = chat.complete(prompt, max_tokens=200, max_continues=3)
               return result
           except ChatIncompleteResponse as e:
               # Response still incomplete after continues
               print(f"Warning: Response incomplete after {e.continue_count} continues")
               return e.final_result  # Use partial result
           except requests.RequestException as e:
               # Network error - retry with exponential backoff
               if attempt < max_retries - 1:
                   wait_time = 2 ** attempt
                   print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                   time.sleep(wait_time)
                   continue
               raise  # Last attempt failed
       return None

   result = robust_chat("Your prompt here")

**Key Points**:
- Use ``chat.complete()`` for automatic continuation
- Handle ``ChatIncompleteResponse`` for partial results
- Implement retry logic for network errors
- Use exponential backoff for retries

Long-form Content Generation
----------------------------

Generating long content with automatic continuation:

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat.exceptions import ChatIncompleteResponse

   chat = Chat(..., auto_history=True)

   def generate_long_content(prompt, target_length=None):
       """Generate long content with automatic continuation."""
       # Start with reasonable max_tokens
       max_tokens = 500
       
       try:
           result = chat.complete(
               prompt,
               max_tokens=max_tokens,
               max_continues=5,  # Allow multiple continues
               ensure_complete=False  # Allow partial if needed
           )
           
           if target_length and len(result.text) < target_length:
               print(f"Warning: Generated {len(result.text)} chars, target was {target_length}")
           
           return result
       except ChatIncompleteResponse as e:
           print(f"Generated {len(e.final_result.text)} chars before max continues")
           return e.final_result

   result = generate_long_content("Write a comprehensive guide to Python")

**Key Points**:
- Use ``chat.complete()`` with appropriate ``max_continues``
- Set ``ensure_complete=False`` if partial results are acceptable
- Monitor token usage across continues

Multi-turn Conversations
------------------------

Managing multi-turn conversations with context:

.. code-block:: python

   from lexilux import Chat

   chat = Chat(..., auto_history=True)

   # Conversation with system message
   result1 = chat("Hello", system="You are a helpful Python tutor")
   result2 = chat("What is a list?")
   result3 = chat("How do I iterate over it?")

   # History automatically maintains context
   history = chat.get_history()
   assert history.system == "You are a helpful Python tutor"

   # Continue conversation naturally
   result4 = chat("Give me an example")

   # Clear when switching topics
   chat.clear_history()
   result5 = chat("New topic", system="You are a math tutor")

**Key Points**:
- System messages are automatically preserved
- Context is maintained across turns
- Use ``clear_history()`` when switching topics

JSON Extraction with Validation
-------------------------------

Extracting and validating JSON from responses:

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat.exceptions import ChatIncompleteResponse
   import json

   chat = Chat(..., auto_history=True)

   def extract_json(prompt, schema=None):
       """Extract JSON from response with validation."""
       try:
           result = chat.complete(
               f"{prompt}\n\nReturn the result as valid JSON.",
               max_tokens=500,
               max_continues=3
           )
           
           # Parse JSON
           try:
               data = json.loads(result.text)
           except json.JSONDecodeError as e:
               # Try to fix common issues
               # Remove markdown code blocks if present
               text = result.text.strip()
               if text.startswith("```"):
                   text = text.split("```")[1]
                   if text.startswith("json"):
                       text = text[4:]
                   text = text.strip()
               
               data = json.loads(text)
           
           # Validate schema if provided
           if schema:
               # Use jsonschema or similar for validation
               pass
           
           return data
       except ChatIncompleteResponse as e:
           raise ValueError(f"Response incomplete, cannot extract JSON: {e.final_result.text}")
       except json.JSONDecodeError as e:
           raise ValueError(f"Invalid JSON in response: {e}")

   data = extract_json("List all users with their emails")

**Key Points**:
- Use ``chat.complete()`` to ensure complete JSON
- Handle JSON parsing errors
- Consider response format (may include markdown code blocks)

Streaming with Progress Tracking
---------------------------------

Track progress during long streaming responses:

.. code-block:: python

   from lexilux import Chat
   import requests

   chat = Chat(..., auto_history=True)

   def stream_with_progress(prompt):
       """Stream with progress tracking."""
       iterator = chat.stream(prompt)
       chunk_count = 0
       total_chars = 0
       
       try:
           for chunk in iterator:
               print(chunk.delta, end="", flush=True)
               chunk_count += 1
               total_chars += len(chunk.delta)
               
               # Progress update every 10 chunks
               if chunk_count % 10 == 0:
                   print(f"\n[Progress: {total_chars} chars, {chunk_count} chunks]", end="\r")
               
               if chunk.done:
                   print(f"\n[Complete: {total_chars} chars, finish_reason: {chunk.finish_reason}]")
                   break
       except requests.RequestException as e:
           print(f"\n[Interrupted: {total_chars} chars received]")
           # Clean up partial response
           chat.clear_last_assistant_message()
           raise

   stream_with_progress("Write a long story")

**Key Points**:
- Track progress during streaming
- Handle interruptions gracefully
- Clean up partial responses if needed

Error Recovery Patterns
-----------------------

Recovering from errors and interruptions:

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat.exceptions import ChatIncompleteResponse
   import requests

   chat = Chat(..., auto_history=True)

   def resilient_chat(prompt, max_retries=3):
       """Chat with automatic error recovery."""
       for attempt in range(max_retries):
           try:
               # Try to get complete response
               result = chat.complete(prompt, max_tokens=200, max_continues=3)
               return result
           except ChatIncompleteResponse as e:
               # Response incomplete - use partial if acceptable
               if len(e.final_result.text) > 100:  # Minimum acceptable length
                   print(f"Using partial result ({len(e.final_result.text)} chars)")
                   return e.final_result
               # Too short, retry with higher max_tokens
               if attempt < max_retries - 1:
                   print(f"Retry {attempt + 1} with higher max_tokens...")
                   continue
               raise
           except requests.RequestException as e:
               # Network error - retry
               if attempt < max_retries - 1:
                   print(f"Network error, retry {attempt + 1}...")
                   time.sleep(2 ** attempt)
                   continue
               raise
       return None

   result = resilient_chat("Your prompt")

**Key Points**:
- Handle both ``ChatIncompleteResponse`` and network errors
- Implement retry logic with different strategies
- Use partial results when acceptable

Common Pitfalls to Avoid
------------------------

1. **Forgetting to enable auto_history**:
   
   .. code-block:: python

      # Wrong
      chat = Chat(...)  # auto_history=False by default
      result = chat.complete("JSON")  # Will fail: history not available

      # Correct
      chat = Chat(..., auto_history=True)
      result = chat.complete("JSON")  # Works

2. **Not handling ChatIncompleteResponse**:
   
   .. code-block:: python

      # Wrong
      result = chat.complete("Long response", max_tokens=30, max_continues=1)
      json.loads(result.text)  # May fail if still incomplete

      # Correct
      try:
          result = chat.complete("Long response", max_tokens=30, max_continues=1)
          json.loads(result.text)
      except ChatIncompleteResponse as e:
          # Handle partial result
          pass

3. **Not cleaning up partial streaming responses**:
   
   .. code-block:: python

      # Wrong
      iterator = chat.stream("Long response")
      try:
          for chunk in iterator:
              print(chunk.delta)
      except Exception:
          pass  # Partial response left in history

      # Correct
      iterator = chat.stream("Long response")
      try:
          for chunk in iterator:
              print(chunk.delta)
      except Exception:
          chat.clear_last_assistant_message()  # Clean up

4. **Using old API when new API is simpler**:
   
   .. code-block:: python

      # Old way (still works but verbose)
      result = chat("JSON", max_tokens=100)
      if result.finish_reason == "length":
          history = chat.get_history()
          continue_result = ChatContinue.continue_request(chat, result, history=history)
          full_result = ChatContinue.merge_results(result, continue_result)
      else:
          full_result = result

      # New way (recommended)
      full_result = chat.complete("JSON", max_tokens=100)

See Also
--------

* :doc:`auto_history` - Automatic history management
* :doc:`chat_continue` - Continue generation guide
* :doc:`error_handling` - Error handling guide
* :doc:`quickstart` - Quick start guide

