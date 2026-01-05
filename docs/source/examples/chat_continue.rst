Continue Generation Examples
=============================

This section provides practical examples of using the continue generation functionality,
including the recommended new APIs and legacy patterns.

Recommended: Using chat.complete()
-----------------------------------

The simplest and most recommended approach:

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat.exceptions import ChatIncompleteResponse
   import json

   chat = Chat(..., auto_history=True)

   # Ensure complete JSON response
   try:
       result = chat.complete("Extract user data as JSON", max_tokens=100)
       json_data = json.loads(result.text)  # Guaranteed complete
   except ChatIncompleteResponse as e:
       print(f"Still incomplete after {e.continue_count} continues")
       # Use partial result if acceptable
       json_data = json.loads(e.final_result.text)

Conditional Continue
--------------------

Continue only if needed:

.. code-block:: python

   from lexilux import Chat

   chat = Chat(..., auto_history=True)

   result = chat("Long story", max_tokens=50)
   # Automatically continues if truncated, otherwise returns result unchanged
   full_result = chat.continue_if_needed(result, max_continues=3)

Enhanced ChatContinue API
--------------------------

Using the enhanced continue_request() with automatic history:

.. code-block:: python

   from lexilux import Chat, ChatContinue

   chat = Chat(..., auto_history=True)

   result = chat("Write a long story", max_tokens=50)
   
   if result.finish_reason == "length":
       # Automatic history retrieval, multiple continues, auto merge
       full_result = ChatContinue.continue_request(
           chat, result, max_continues=3
       )
       print(f"Complete story: {len(full_result.text)} chars")

Get All Intermediate Results
-----------------------------

Get all parts separately:

.. code-block:: python

   from lexilux import Chat, ChatContinue

   chat = Chat(..., auto_history=True)

   result = chat("Story", max_tokens=50)
   if result.finish_reason == "length":
       all_results = ChatContinue.continue_request(
           chat, result, auto_merge=False, max_continues=3
       )
       
       for i, r in enumerate(all_results):
           print(f"Part {i+1}: {len(r.text)} chars, tokens: {r.usage.total_tokens}")

Legacy: Manual History Management
----------------------------------

The old way (still supported for backward compatibility):

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)

   # Initial request (gets cut off)
   result = chat("Write a comprehensive guide to Python", max_tokens=100)

   if result.finish_reason == "length":
       print("Response was cut off, continuing...")
       
       # Create history manually
       history = ChatHistory.from_chat_result(
           "Write a comprehensive guide to Python", result
       )
       
       # Continue
       continue_result = ChatContinue.continue_request(
           chat, history, result, add_continue_prompt=True
       )
       
       # Merge results
       full_result = ChatContinue.merge_results(result, continue_result)
       print(f"Complete guide: {len(full_result.text)} characters")

Continue Until Complete (Legacy Pattern)
-----------------------------------------

Continue multiple times until response is complete (old pattern):

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)

   def get_complete_response(prompt, max_tokens_per_chunk=100):
       """Get complete response, continuing if needed (legacy pattern)."""
       result = chat(prompt, max_tokens=max_tokens_per_chunk)
       history = ChatHistory.from_chat_result(prompt, result)
       
       results = [result]
       
       # Continue until complete
       while results[-1].finish_reason == "length":
           print(f"Continuing... (part {len(results) + 1})")
           continue_result = ChatContinue.continue_request(
               chat, history, results[-1], add_continue_prompt=True
           )
           results.append(continue_result)
           history.append_result(continue_result)
       
       # Merge all parts
       return ChatContinue.merge_results(*results)

   # Use it
   full_result = get_complete_response("Write a very long story", max_tokens_per_chunk=50)
   print(f"Complete story: {len(full_result.text)} characters")
   print(f"Total tokens: {full_result.usage.total_tokens}")

**Note**: The new recommended way is to use ``chat.complete()``:

.. code-block:: python

   chat = Chat(..., auto_history=True)
   result = chat.complete("Write a very long story", max_tokens=50, max_continues=5)

Continue with Progress Tracking
--------------------------------

Track progress during continuation:

.. code-block:: python

   from lexilux import Chat, ChatContinue

   chat = Chat(..., auto_history=True)

   result1 = chat("Write a detailed technical document", max_tokens=100)
   print(f"Part 1: {len(result1.text)} chars, {result1.usage.total_tokens} tokens")

   if result1.finish_reason == "length":
       # Use enhanced API
       all_results = ChatContinue.continue_request(
           chat, result1, auto_merge=False, max_continues=3
       )
       
       for i, r in enumerate(all_results[1:], start=2):  # Skip first (already printed)
           print(f"Part {i}: {len(r.text)} chars, {r.usage.total_tokens} tokens")
       
       # Merge
       full_result = ChatContinue.merge_results(*all_results)
       print(f"Complete: {len(full_result.text)} chars, {full_result.usage.total_tokens} tokens")

Continue with Custom Parameters
-------------------------------

Pass additional parameters to continuation:

.. code-block:: python

   from lexilux import Chat, ChatContinue

   chat = Chat(..., auto_history=True)

   result1 = chat("Write a story", max_tokens=100, temperature=0.7)

   if result1.finish_reason == "length":
       # Continue with different parameters
       continue_result = ChatContinue.continue_request(
           chat,
           result1,
           temperature=0.8,  # Slightly more creative
           max_tokens=200,    # Longer continuation
           max_continues=2,
       )
       
       full_result = ChatContinue.merge_results(result1, continue_result)

Error Handling
--------------

Handle errors during continuation:

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat.exceptions import ChatIncompleteResponse
   import requests

   chat = Chat(..., auto_history=True)

   try:
       # Use complete() for automatic error handling
       result = chat.complete("Long content", max_tokens=100, max_continues=3)
   except ChatIncompleteResponse as e:
       print(f"Response incomplete after {e.continue_count} continues")
       print(f"Received: {len(e.final_result.text)} chars")
       # Use partial result if acceptable
       result = e.final_result
   except requests.RequestException as e:
       print(f"Network error: {e}")
       result = None

Complete Workflow
-----------------

Complete workflow with continue (recommended pattern):

.. code-block:: python

   from lexilux import Chat, ChatHistoryFormatter
   from lexilux.chat.exceptions import ChatIncompleteResponse

   chat = Chat(..., auto_history=True)

   # Request long content
   prompt = "Write a comprehensive tutorial on Python"
   
   try:
       result = chat.complete(prompt, max_tokens=200, max_continues=3)
   except ChatIncompleteResponse as e:
       print(f"Warning: Tutorial incomplete after {e.continue_count} continues")
       result = e.final_result

   # Save complete tutorial
   history = chat.get_history()
   ChatHistoryFormatter.save(history, "python_tutorial.md")
   
   print(f"Tutorial saved: {len(result.text)} characters")
   print(f"Total tokens used: {result.usage.total_tokens}")

JSON Extraction Pattern
------------------------

Extract JSON with guaranteed completeness:

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat.exceptions import ChatIncompleteResponse
   import json

   chat = Chat(..., auto_history=True)

   def extract_json(prompt):
       """Extract JSON from response, ensuring completeness."""
       try:
           result = chat.complete(
               f"{prompt}\n\nReturn the result as valid JSON.",
               max_tokens=500,
               max_continues=3
           )
           
           # Parse JSON (may need to strip markdown code blocks)
           text = result.text.strip()
           if text.startswith("```"):
               text = text.split("```")[1]
               if text.startswith("json"):
                   text = text[4:]
               text = text.strip()
           
           return json.loads(text)
       except ChatIncompleteResponse as e:
           raise ValueError(f"Cannot extract JSON from incomplete response")
       except json.JSONDecodeError as e:
           raise ValueError(f"Invalid JSON in response: {e}")

   data = extract_json("List all users with their emails and roles")

Long-form Content Generation
----------------------------

Generate long content with automatic continuation:

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat.exceptions import ChatIncompleteResponse

   chat = Chat(..., auto_history=True)

   def generate_long_content(prompt, target_length=None):
       """Generate long content with automatic continuation."""
       try:
           result = chat.complete(
               prompt,
               max_tokens=500,
               max_continues=5,
               ensure_complete=False  # Allow partial if needed
           )
           
           if target_length and len(result.text) < target_length:
               print(f"Warning: Generated {len(result.text)} chars, target was {target_length}")
           
           return result
       except ChatIncompleteResponse as e:
           print(f"Generated {len(e.final_result.text)} chars before max continues")
           return e.final_result

   result = generate_long_content("Write a comprehensive guide to Python")
