Continue Generation
====================

Lexilux provides functionality to continue generation when responses are cut off
due to token limits, allowing you to seamlessly extend incomplete responses.

Overview
--------

When a chat completion is stopped due to ``max_tokens`` limit (``finish_reason == "length"``),
you may want to continue the generation. The ``ChatContinue`` class provides utilities
for handling continuation requests and merging results.

Key Features
------------

1. **Continue Requests**: Automatically handle continuation when generation is cut off
2. **Result Merging**: Seamlessly merge multiple results into a single complete response
3. **Flexible Options**: Choose whether to add a continue prompt or send history directly
4. **Usage Aggregation**: Automatically combine token usage from multiple requests

When to Use
-----------

Use ``ChatContinue`` when:

* A response has ``finish_reason == "length"`` (cut off due to token limit)
* You want to extend an incomplete response
* You need to merge multiple continuation results
* You're working with long-form content generation

Basic Usage
-----------

Detecting Length Finish Reason
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, check if continuation is needed:

.. code-block:: python

   from lexilux import Chat, ChatResult

   chat = Chat(...)
   result = chat("Write a long story", max_tokens=100)

   if result.finish_reason == "length":
       print("Response was cut off, need to continue")
       # Use ChatContinue to continue

Continue with Prompt
~~~~~~~~~~~~~~~~~~~~

The simplest approach is to add a user continue prompt:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)
   
   # Initial request (gets cut off)
   result1 = chat("Write a long story", max_tokens=100)
   
   if result.finish_reason == "length":
       # Create history from the conversation
       history = ChatHistory.from_chat_result("Write a long story", result1)
       
       # Continue with prompt
       continue_result = ChatContinue.continue_request(
           chat,
           history,
           result1,
           add_continue_prompt=True,
           continue_prompt="continue"
       )
       
       # Merge results
       full_result = ChatContinue.merge_results(result1, continue_result)
       print(full_result.text)  # Complete story

Continue Without Prompt
~~~~~~~~~~~~~~~~~~~~~~~

You can also continue without adding a user prompt:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)
   
   result1 = chat("Write a long story", max_tokens=100)
   
   if result1.finish_reason == "length":
       history = ChatHistory.from_chat_result("Write a long story", result1)
       
       # Continue without adding user prompt
       continue_result = ChatContinue.continue_request(
           chat,
           history,
           result1,
           add_continue_prompt=False  # Send history directly
       )
       
       full_result = ChatContinue.merge_results(result1, continue_result)

Custom Continue Prompt
~~~~~~~~~~~~~~~~~~~~~~~

Customize the continue prompt:

.. code-block:: python

   continue_result = ChatContinue.continue_request(
       chat,
       history,
       result1,
       add_continue_prompt=True,
       continue_prompt="Please continue from where you left off"
   )

Advanced Usage
--------------

Multiple Continuations
~~~~~~~~~~~~~~~~~~~~~~

You can continue multiple times if needed:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)
   
   # Initial request
   result1 = chat("Write a very long story", max_tokens=50)
   history = ChatHistory.from_chat_result("Write a very long story", result1)
   
   results = [result1]
   
   # Continue until complete
   while results[-1].finish_reason == "length":
       continue_result = ChatContinue.continue_request(
           chat, history, results[-1], add_continue_prompt=True
       )
       results.append(continue_result)
       
       # Update history for next iteration
       history.append_result(continue_result)
   
   # Merge all results
   full_result = ChatContinue.merge_results(*results)
   print(f"Complete story: {full_result.text}")
   print(f"Total tokens: {full_result.usage.total_tokens}")

Continue with Parameters
~~~~~~~~~~~~~~~~~~~~~~~~

Pass additional parameters to the continue request:

.. code-block:: python

   continue_result = ChatContinue.continue_request(
       chat,
       history,
       result1,
       add_continue_prompt=True,
       temperature=0.7,  # Additional parameters
       max_tokens=200,   # New max_tokens for continuation
   )

Integration with Auto History
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Works seamlessly with auto_history:

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   result1 = chat("Write a story", max_tokens=100)
   
   if result1.finish_reason == "length":
       # Get auto-recorded history
       history = chat.get_history()
       
       # Continue
       continue_result = ChatContinue.continue_request(
           chat, history, result1, add_continue_prompt=True
       )
       
       # Auto history is updated with continue prompt and response
       updated_history = chat.get_history()
       
       # Merge results
       full_result = ChatContinue.merge_results(result1, continue_result)

Common Patterns
---------------

Pattern 1: Simple Continue
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most common pattern - continue once:

.. code-block:: python

   result = chat("Long content", max_tokens=100)
   
   if result.finish_reason == "length":
       history = ChatHistory.from_chat_result("Long content", result)
       continue_result = ChatContinue.continue_request(
           chat, history, result, add_continue_prompt=True
       )
       full_result = ChatContinue.merge_results(result, continue_result)
   else:
       full_result = result

Pattern 2: Continue Until Complete
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Continue until the response is complete:

.. code-block:: python

   def get_complete_response(chat, prompt, max_tokens_per_chunk=100):
       """Get complete response, continuing if cut off."""
       result = chat(prompt, max_tokens=max_tokens_per_chunk)
       history = ChatHistory.from_chat_result(prompt, result)
       
       results = [result]
       
       while results[-1].finish_reason == "length":
           continue_result = ChatContinue.continue_request(
               chat, history, results[-1], add_continue_prompt=True
           )
           results.append(continue_result)
           history.append_result(continue_result)
       
       return ChatContinue.merge_results(*results)

Pattern 3: Continue with Progress Tracking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Track progress during continuation:

.. code-block:: python

   result1 = chat("Long story", max_tokens=100)
   print(f"Part 1: {len(result1.text)} chars")
   
   if result1.finish_reason == "length":
       history = ChatHistory.from_chat_result("Long story", result1)
       continue_result = ChatContinue.continue_request(
           chat, history, result1, add_continue_prompt=True
       )
       print(f"Part 2: {len(continue_result.text)} chars")
       
       full_result = ChatContinue.merge_results(result1, continue_result)
       print(f"Complete: {len(full_result.text)} chars")

Common Pitfalls
---------------

Pitfall 1: Not Checking finish_reason
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Continuing when it's not needed.

.. code-block:: python

   # Wrong - continuing even when not needed
   result = chat("Short question")
   continue_result = ChatContinue.continue_request(...)  # Unnecessary!

   # Correct - check first
   result = chat("Long content", max_tokens=100)
   if result.finish_reason == "length":
       continue_result = ChatContinue.continue_request(...)

**Solution**: Always check ``finish_reason == "length"`` before continuing.

Pitfall 2: Not Merging Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Using only the continue result, losing the original content.

.. code-block:: python

   # Wrong - only using continue result
   result1 = chat("Story", max_tokens=100)
   if result1.finish_reason == "length":
       continue_result = ChatContinue.continue_request(...)
       print(continue_result.text)  # Missing first part!

   # Correct - merge results
   result1 = chat("Story", max_tokens=100)
   if result1.finish_reason == "length":
       continue_result = ChatContinue.continue_request(...)
       full_result = ChatContinue.merge_results(result1, continue_result)
       print(full_result.text)  # Complete story

**Solution**: Always use ``merge_results()`` to combine results.

Pitfall 3: Incorrect History Construction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: History doesn't match the conversation state.

.. code-block:: python

   # Wrong - history doesn't include the incomplete result
   result1 = chat("Story", max_tokens=100)
   history = ChatHistory.from_messages("Story")  # Missing result1!
   continue_result = ChatContinue.continue_request(chat, history, result1)

   # Correct - include result1 in history
   result1 = chat("Story", max_tokens=100)
   history = ChatHistory.from_chat_result("Story", result1)
   continue_result = ChatContinue.continue_request(chat, history, result1)

**Solution**: Always use ``ChatHistory.from_chat_result()`` to include the incomplete result.

Pitfall 4: Multiple System Messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: If history contains multiple system messages, continuation may behave unexpectedly.

.. code-block:: python

   # History with multiple system messages
   history = ChatHistory(system="System 1")
   history.add_message("system", "System 2")  # Multiple systems
   
   # Continue may not work as expected
   continue_result = ChatContinue.continue_request(chat, history, result1)

**Solution**: Keep only one system message, or be aware of how multiple systems are handled.

Pitfall 5: Not Handling Continue Result Finish Reason
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Continue result may also be cut off.

.. code-block:: python

   # Wrong - assuming continue completes
   result1 = chat("Story", max_tokens=100)
   if result1.finish_reason == "length":
       continue_result = ChatContinue.continue_request(...)
       # continue_result may also have finish_reason == "length"!
       full_result = ChatContinue.merge_results(result1, continue_result)

   # Correct - check continue result too
   result1 = chat("Story", max_tokens=100)
   if result1.finish_reason == "length":
       continue_result = ChatContinue.continue_request(...)
       if continue_result.finish_reason == "length":
           # Need another continue
           pass
       full_result = ChatContinue.merge_results(result1, continue_result)

**Solution**: Check the continue result's finish_reason and continue again if needed.

Pitfall 6: Usage Aggregation Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Not understanding how usage is aggregated.

.. code-block:: python

   result1 = ChatResult(..., usage=Usage(total_tokens=100))
   result2 = ChatResult(..., usage=Usage(total_tokens=50))
   
   merged = ChatContinue.merge_results(result1, result2)
   # merged.usage.total_tokens == 150 (sum of both)

**Solution**: Understand that ``merge_results()`` sums usage statistics.

Best Practices
--------------

1. **Always Check finish_reason**: Only continue when ``finish_reason == "length"``.

2. **Always Merge Results**: Use ``merge_results()`` to combine original and continue results.

3. **Use Proper History**: Always use ``ChatHistory.from_chat_result()`` to ensure history
   includes the incomplete result.

4. **Handle Multiple Continues**: Be prepared to continue multiple times if needed.

5. **Monitor Token Usage**: Track total tokens across all continuations:

   .. code-block:: python

      results = [result1]
      while results[-1].finish_reason == "length":
          continue_result = ChatContinue.continue_request(...)
          results.append(continue_result)
          
          # Check total tokens
          merged = ChatContinue.merge_results(*results)
          if merged.usage.total_tokens > max_total_tokens:
              break  # Stop if too many tokens

6. **Use Appropriate Continue Prompt**: Choose a prompt that fits your use case:

   .. code-block:: python

      # For stories
      continue_prompt = "continue"
      
      # For technical content
      continue_prompt = "Please continue the explanation"
      
      # For code
      continue_prompt = "Continue the code"

7. **Consider add_continue_prompt**: 

   * ``True``: Adds a user message, making continuation explicit
   * ``False``: Sends history directly, continuation is implicit

   Choose based on whether you want the continuation to be part of the conversation.

Examples
--------

Complete Workflow
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)
   
   # Initial request
   prompt = "Write a comprehensive guide to Python"
   result = chat(prompt, max_tokens=200)
   
   # Check if continuation needed
   if result.finish_reason == "length":
       print("Response was cut off, continuing...")
       
       # Create history
       history = ChatHistory.from_chat_result(prompt, result)
       
       # Continue
       continue_result = ChatContinue.continue_request(
           chat,
           history,
           result,
           add_continue_prompt=True,
           continue_prompt="Please continue",
           max_tokens=200,  # New limit for continuation
       )
       
       # Merge
       full_result = ChatContinue.merge_results(result, continue_result)
       
       print(f"Complete guide ({len(full_result.text)} chars)")
       print(f"Total tokens: {full_result.usage.total_tokens}")
   else:
       full_result = result
       print("Response completed in one request")

Continue with Streaming
~~~~~~~~~~~~~~~~~~~~~~~

Continue can also work with streaming, but requires manual handling:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)
   
   # Initial streaming request
   iterator = chat.stream("Long story", max_tokens=100)
   chunks1 = list(iterator)
   result1 = iterator.result.to_chat_result()
   
   if result1.finish_reason == "length":
       history = ChatHistory.from_chat_result("Long story", result1)
       
       # Continue with non-streaming (simpler)
       continue_result = ChatContinue.continue_request(
           chat, history, result1, add_continue_prompt=True
       )
       
       full_result = ChatContinue.merge_results(result1, continue_result)

Error Handling
~~~~~~~~~~~~~~

Handle errors during continuation:

.. code-block:: python

   try:
       result1 = chat("Long content", max_tokens=100)
       if result1.finish_reason == "length":
           history = ChatHistory.from_chat_result("Long content", result1)
           continue_result = ChatContinue.continue_request(
               chat, history, result1, add_continue_prompt=True
           )
           full_result = ChatContinue.merge_results(result1, continue_result)
       else:
           full_result = result1
   except Exception as e:
       print(f"Error during continuation: {e}")
       # Use partial result if available
       if 'result1' in locals():
           full_result = result1

See Also
--------

* :doc:`chat_history` - History management for continuation
* :doc:`auto_history` - Automatic history with continuation
* :doc:`api_reference/chat` - API reference for ChatContinue

