Continue Generation Examples
=============================

This section provides practical examples of using the ChatContinue functionality.

Basic Continue
--------------

Continue a cut-off response:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)

   # Initial request (gets cut off)
   result = chat("Write a comprehensive guide to Python", max_tokens=100)

   if result.finish_reason == "length":
       print("Response was cut off, continuing...")
       
       # Create history
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

Continue Until Complete
-----------------------

Continue multiple times until response is complete:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)

   def get_complete_response(prompt, max_tokens_per_chunk=100):
       """Get complete response, continuing if needed."""
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

Continue with Progress Tracking
-------------------------------

Track progress during continuation:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)

   result1 = chat("Write a detailed technical document", max_tokens=100)
   print(f"Part 1: {len(result1.text)} chars, {result1.usage.total_tokens} tokens")

   if result1.finish_reason == "length":
       history = ChatHistory.from_chat_result(
           "Write a detailed technical document", result1
       )
       
       continue_result = ChatContinue.continue_request(
           chat, history, result1, add_continue_prompt=True
       )
       print(f"Part 2: {len(continue_result.text)} chars, {continue_result.usage.total_tokens} tokens")
       
       full_result = ChatContinue.merge_results(result1, continue_result)
       print(f"Complete: {len(full_result.text)} chars, {full_result.usage.total_tokens} tokens")

Continue with Auto History
---------------------------

Using continue with auto_history:

.. code-block:: python

   from lexilux import Chat, ChatContinue

   chat = Chat(..., auto_history=True)

   # Initial request
   result1 = chat("Long story", max_tokens=100)

   if result1.finish_reason == "length":
       # Get auto-recorded history
       history = chat.get_history()
       
       # Continue
       continue_result = ChatContinue.continue_request(
           chat, history, result1, add_continue_prompt=True
       )
       
       # Auto history is updated with continue prompt and response
       updated_history = chat.get_history()
       print(f"History now has {len(updated_history.messages)} messages")
       
       # Merge results
       full_result = ChatContinue.merge_results(result1, continue_result)

Continue with Custom Parameters
-------------------------------

Pass additional parameters to continuation:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)

   result1 = chat("Write a story", max_tokens=100, temperature=0.7)

   if result1.finish_reason == "length":
       history = ChatHistory.from_chat_result("Write a story", result1)
       
       # Continue with different parameters
       continue_result = ChatContinue.continue_request(
           chat,
           history,
           result1,
           add_continue_prompt=True,
           temperature=0.8,  # Slightly more creative
           max_tokens=200,    # Longer continuation
       )
       
       full_result = ChatContinue.merge_results(result1, continue_result)

Error Handling
--------------

Handle errors during continuation:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory

   chat = Chat(...)

   try:
       result1 = chat("Long content", max_tokens=100)
       
       if result1.finish_reason == "length":
           history = ChatHistory.from_chat_result("Long content", result1)
           
           try:
               continue_result = ChatContinue.continue_request(
                   chat, history, result1, add_continue_prompt=True
               )
               full_result = ChatContinue.merge_results(result1, continue_result)
           except Exception as e:
               print(f"Error during continuation: {e}")
               # Use partial result
               full_result = result1
       else:
           full_result = result1
           
   except Exception as e:
       print(f"Error in initial request: {e}")
       full_result = None

Complete Workflow
-----------------

Complete workflow with continue:

.. code-block:: python

   from lexilux import Chat, ChatContinue, ChatHistory, ChatHistoryFormatter

   chat = Chat(...)

   # Request long content
   prompt = "Write a comprehensive tutorial on Python"
   result = chat(prompt, max_tokens=200)

   # Check if continuation needed
   if result.finish_reason == "length":
       print("Response was cut off, continuing...")
       
       history = ChatHistory.from_chat_result(prompt, result)
       
       # Continue
       continue_result = ChatContinue.continue_request(
           chat,
           history,
           result,
           add_continue_prompt=True,
           continue_prompt="Please continue the tutorial",
           max_tokens=200,
       )
       
       # Merge
       full_result = ChatContinue.merge_results(result, continue_result)
   else:
       full_result = result

   # Save complete tutorial
   complete_history = ChatHistory.from_chat_result(prompt, full_result)
   ChatHistoryFormatter.save(complete_history, "python_tutorial.md")
   
   print(f"Tutorial saved: {len(full_result.text)} characters")
   print(f"Total tokens used: {full_result.usage.total_tokens}")

