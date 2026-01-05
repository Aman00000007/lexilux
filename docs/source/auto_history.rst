Automatic History Management
=============================

Lexilux provides automatic conversation history management through the ``auto_history``
feature, eliminating the need for manual history tracking and maintenance.

Overview
--------

The ``auto_history`` feature automatically records all conversations when enabled,
allowing you to:

* **Zero-maintenance history**: No need to manually track or extract history
* **Automatic accumulation**: History grows automatically with each call
* **Streaming support**: History updates in real-time during streaming
* **Easy access**: Get complete conversation history at any time

Key Benefits
------------

1. **Simplest Usage**: Just enable ``auto_history=True`` and forget about history management
2. **No Manual Tracking**: History is automatically maintained by the Chat client
3. **Streaming Compatible**: Works seamlessly with both streaming and non-streaming calls
4. **Context Preservation**: Complete conversation context is always available

Basic Usage
-----------

Enabling Auto History
~~~~~~~~~~~~~~~~~~~~~

Enable automatic history when creating a Chat client:

.. code-block:: python

   from lexilux import Chat

   # Enable auto_history
   chat = Chat(
       base_url="https://api.example.com/v1",
       api_key="your-key",
       model="gpt-4",
       auto_history=True,  # Enable automatic history
   )

   # Make calls - history is automatically recorded
   result1 = chat("What is Python?")
   result2 = chat("Tell me more about it")

   # Get complete history at any time
   history = chat.get_history()
   print(f"Total messages: {len(history.messages)}")
   print(f"Rounds: {len(history._get_rounds())}")

Non-Streaming Usage
-------------------

With Non-Streaming Calls
~~~~~~~~~~~~~~~~~~~~~~~~

Auto history works seamlessly with regular chat calls:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # First call
   result1 = chat("Hello")
   # History now contains: user("Hello") + assistant(response)

   # Second call
   result2 = chat("How are you?")
   # History now contains: user("Hello") + assistant(response1) + user("How are you?") + assistant(response2)

   # Access history
   history = chat.get_history()
   assert len(history.messages) == 4  # 2 user + 2 assistant

   # Continue conversation naturally
   result3 = chat("Tell me a joke")
   # History automatically grows

Error Handling
~~~~~~~~~~~~~~

When a non-streaming call fails with an exception, the behavior is:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # First call (successful)
   result1 = chat("Hello")
   # History: user("Hello") + assistant(response1)

   # Second call (fails with exception)
   try:
       result2 = chat("How are you?")
   except Exception:
       pass
   
   # History: user("Hello") + assistant(response1) + user("How are you?")
   # Note: NO assistant response for the failed call
   history = chat.get_history()
   assert len([m for m in history.messages if m["role"] == "assistant"]) == 1

With System Messages
~~~~~~~~~~~~~~~~~~~~

System messages are automatically preserved:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # First call with system message
   result1 = chat("Hello", system="You are a helpful assistant")
   history = chat.get_history()
   assert history.system == "You are a helpful assistant"

   # Subsequent calls use the same system message context
   result2 = chat("What is Python?")
   # System message is preserved in history

Streaming Usage
---------------

With Streaming Calls
~~~~~~~~~~~~~~~~~~~~

Auto history works with streaming and updates in real-time. **Important behavior**:

1. **User messages are added immediately** when ``chat.stream()`` is called
2. **Assistant message is added only on first iteration** (lazy initialization)
3. **Assistant message content is updated on each iteration** with accumulated text
4. **If iterator is never iterated**, no assistant message is added to history

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # Streaming call
   iterator = chat.stream("Tell me a story")
   # At this point: history contains user("Tell me a story"), but NO assistant message yet
   
   for chunk in iterator:
       print(chunk.delta, end="")
       # On first iteration: assistant message is added to history (empty initially)
       # On each iteration: assistant message content is updated with accumulated text
       # History is being updated in real-time

   # After streaming completes, history contains the full conversation
   history = chat.get_history()
   assert len(history.messages) == 2  # user + assistant
   assert len(history.messages[1]["content"]) > 0  # Full accumulated text

   # Continue with another streaming call
   iterator2 = chat.stream("Continue the story")
   for chunk in iterator2:
       print(chunk.delta, end="")

   # History now contains both conversations
   history = chat.get_history()
   assert len(history.messages) == 4

Handling Streaming Interruptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If streaming is interrupted, the partial content received before interruption is
preserved in history. You can clean it up using ``clear_last_assistant_message()``:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   iterator = chat.stream("Long response")
   try:
       for chunk in iterator:
           print(chunk.delta, end="")
           # Simulate interruption
           if some_condition:
               raise Exception("Interrupted")
   except Exception:
       # Partial content is preserved in history
       history = chat.get_history()
       # Last assistant message contains partial content
       
       # Clean up if needed
       chat.clear_last_assistant_message()
       # Now history no longer contains the partial response

Accessing Accumulated Text During Streaming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can access the accumulated text during streaming:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   iterator = chat.stream("Write a long story")
   for chunk in iterator:
       print(chunk.delta, end="")
       
       # Access current accumulated text
       current_text = iterator.result.text
       print(f"\n[Current length: {len(current_text)} chars]")

   # After streaming, history contains complete text
   history = chat.get_history()
   full_text = history.messages[1]["content"]
   assert full_text == iterator.result.text

Overriding Auto History
~~~~~~~~~~~~~~~~~~~~~~~

You can override the instance setting per call:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # This call will be recorded (uses instance setting)
   result1 = chat("Hello")

   # This call will NOT be recorded (override to False)
   result2 = chat("Secret message", auto_history=False)

   # This call will be recorded (override to True)
   result3 = chat("Public message", auto_history=True)

   history = chat.get_history()
   # History contains "Hello" and "Public message", but not "Secret message"

Advanced Usage
--------------

Clearing History
~~~~~~~~~~~~~~~~

Clear history when starting a new conversation:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # Have a conversation
   chat("Hello")
   chat("How are you?")
   assert chat.get_history() is not None

   # Start fresh
   chat.clear_history()
   assert chat.get_history() is None

   # New conversation
   chat("New topic")

Clearing Last Assistant Message
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clear the last assistant message (useful for cleaning up incomplete responses):

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # After streaming interruption
   iterator = chat.stream("Long response")
   try:
       for chunk in iterator:
           print(chunk.delta)
   except Exception:
       # Partial response is in history
       pass
   
   # Clean up partial response
   chat.clear_last_assistant_message()
   # History no longer contains the partial assistant message
   
   # This method is idempotent - safe to call multiple times
   chat.clear_last_assistant_message()  # No error, nothing happens

Using History with Other Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The automatically recorded history can be used with other methods:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # Build up history automatically
   chat("What is Python?")
   chat("Tell me more")

   # Use the history with other methods
   history = chat.get_history()

   # Export to Markdown
   from lexilux.chat import ChatHistoryFormatter
   md = ChatHistoryFormatter.to_markdown(history)

   # Analyze tokens
   from lexilux import Tokenizer
   tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct")
   analysis = history.analyze_tokens(tokenizer)
   print(f"Total tokens: {analysis.total_tokens}")

   # Truncate if needed
   if analysis.total_tokens > 4000:
       truncated = history.truncate_by_rounds(tokenizer, max_tokens=4000)
       chat._history = truncated  # Update the auto history

Integration with chat_with_history
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use ``chat_with_history()`` with manually created history:

.. code-block:: python

   chat = Chat(...)  # auto_history can be False or True

   # Create history manually
   from lexilux.chat import ChatHistory
   history = ChatHistory(system="You are helpful")
   history.add_user("Question 1")

   # Use with chat_with_history
   result = chat.chat_with_history(history, temperature=0.7)

   # If auto_history is enabled, this call is also recorded
   if chat.auto_history:
       # The auto history is separate from the manual history
       auto_history = chat.get_history()
       # auto_history may be None or contain other conversations

Integration with stream_with_history
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similarly for streaming:

.. code-block:: python

   chat = Chat(...)

   history = ChatHistory.from_messages("Question")
   iterator = chat.stream_with_history(history, temperature=0.7)

   for chunk in iterator:
       print(chunk.delta, end="")

Common Patterns
---------------

Pattern 1: Simple Conversation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest pattern - just enable auto_history and chat:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   chat("Hello")
   chat("How are you?")
   chat("Tell me a joke")

   # Get complete history
   history = chat.get_history()
   print(f"Conversation has {len(history._get_rounds())} rounds")

Pattern 2: Conversation with Context Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manage context window by checking token count:

.. code-block:: python

   from lexilux import Tokenizer

   chat = Chat(..., auto_history=True)
   tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct")

   # Have a conversation
   chat("Question 1")
   chat("Question 2")
   chat("Question 3")

   # Check if history is getting too long
   history = chat.get_history()
   analysis = history.analyze_tokens(tokenizer)

   if analysis.total_tokens > 4000:
       # Truncate to keep most recent rounds
       truncated = history.truncate_by_rounds(tokenizer, max_tokens=4000, keep_system=True)
       chat._history = truncated  # Update auto history

   # Continue conversation
   chat("Question 4")

Pattern 3: Multi-Turn with System Message
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use system message for consistent behavior:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # First call sets system message
   chat("Hello", system="You are a helpful Python tutor")

   # Subsequent calls maintain system context
   chat("What is a list?")
   chat("How do I iterate over it?")

   history = chat.get_history()
   assert history.system == "You are a helpful Python tutor"

Pattern 4: Streaming with Progress Tracking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Track progress during long streaming responses:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   iterator = chat.stream("Write a detailed explanation of Python")
   
   for chunk in iterator:
       print(chunk.delta, end="", flush=True)
       
       # Show progress
       current = iterator.result.text
       if len(current) % 100 == 0:  # Every 100 chars
           print(f"\n[Progress: {len(current)} chars]", end="\r")

   # After completion, history contains full response
   history = chat.get_history()
   full_response = history.messages[-1]["content"]

Common Pitfalls
---------------

Pitfall 1: Forgetting to Enable auto_history
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: History is not recorded when ``auto_history=False`` (default).

.. code-block:: python

   # Wrong - auto_history defaults to False
   chat = Chat(...)
   chat("Hello")
   history = chat.get_history()  # Returns None!

   # Correct - explicitly enable
   chat = Chat(..., auto_history=True)
   chat("Hello")
   history = chat.get_history()  # Returns ChatHistory

**Solution**: Always set ``auto_history=True`` if you need automatic history.

Pitfall 2: Not Clearing History Between Sessions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: History accumulates across different conversation sessions.

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # Session 1: Python questions
   chat("What is Python?")
   chat("How do I use it?")

   # Session 2: Different topic (but history still contains Python questions)
   chat("What is JavaScript?")  # History now mixes Python and JavaScript

**Solution**: Clear history when starting a new conversation:

.. code-block:: python

   # Session 1
   chat("What is Python?")
   chat("How do I use it?")

   # Start new session
   chat.clear_history()
   chat("What is JavaScript?")  # Clean history

Pitfall 3: Assuming History is Shared Across Chat Instances
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Each Chat instance has its own history.

.. code-block:: python

   chat1 = Chat(..., auto_history=True)
   chat2 = Chat(..., auto_history=True)

   chat1("Hello")
   history2 = chat2.get_history()  # Returns None! Different instance

**Solution**: Use the same Chat instance, or manually share history:

.. code-block:: python

   # Option 1: Use same instance
   chat = Chat(..., auto_history=True)
   chat("Hello")
   history = chat.get_history()

   # Option 2: Manually share
   chat1 = Chat(..., auto_history=True)
   chat1("Hello")
   history = chat1.get_history()
   result2 = chat2.chat_with_history(history)

Pitfall 4: Modifying History Directly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Directly modifying ``chat._history`` can cause inconsistencies.

.. code-block:: python

   chat = Chat(..., auto_history=True)
   chat("Hello")
   
   # Wrong - directly modifying internal history
   chat._history.messages.append({"role": "user", "content": "Manual"})
   # This bypasses auto_history logic and may cause issues

**Solution**: Use proper methods or clear and rebuild:

.. code-block:: python

   # Option 1: Use clear_history and rebuild
   chat.clear_history()
   chat("Hello")
   chat("Manual")  # Proper way

   # Option 2: Get history, modify, then use chat_with_history
   history = chat.get_history()
   history.add_user("Manual")
   chat.chat_with_history(history)

Pitfall 5: Not Handling Streaming Interruptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: If streaming is interrupted, history may contain incomplete text.

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   try:
       iterator = chat.stream("Long response")
       for chunk in iterator:
           print(chunk.delta, end="")
           # If interrupted here, history may have partial text
   except KeyboardInterrupt:
       pass

   history = chat.get_history()
   # History may contain incomplete assistant message

**Solution**: Check completion status or handle errors:

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   iterator = chat.stream("Long response")
   try:
       for chunk in iterator:
           print(chunk.delta, end="")
           if chunk.done:
               break  # Completed successfully
   except Exception as e:
       # Handle error - history may be incomplete
       history = chat.get_history()
       if history and history.messages:
           last_msg = history.messages[-1]
           if last_msg.get("role") == "assistant":
               # May need to remove incomplete message
               history.remove_last_round()

Pitfall 6: Overriding auto_history Incorrectly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: The ``auto_history`` parameter in ``stream()`` may not work as expected.

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   # This should work, but verify behavior
   iterator = chat.stream("Hello", auto_history=False)
   # History should NOT be updated

**Solution**: Test override behavior and document expectations:

.. code-block:: python

   chat = Chat(..., auto_history=True)
   
   # Verify override works
   iterator = chat.stream("Test", auto_history=False)
   list(iterator)  # Consume iterator
   
   history = chat.get_history()
   # Should be None or not contain "Test" depending on implementation

Best Practices
--------------

1. **Always Enable Explicitly**: Don't rely on defaults, always set ``auto_history=True``
   when you need it.

2. **Clear Between Sessions**: Use ``clear_history()`` when starting new conversation topics.

3. **Monitor Token Usage**: Regularly check token count to avoid context window issues:

   .. code-block:: python

      from lexilux import Tokenizer
      tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct")
      
      history = chat.get_history()
      if history:
          analysis = history.analyze_tokens(tokenizer)
          if analysis.total_tokens > threshold:
              # Take action

4. **Use Same Instance**: Keep using the same Chat instance for a conversation session.

5. **Export Regularly**: Save important conversations:

   .. code-block:: python

      history = chat.get_history()
      if history:
          with open(f"conversation_{timestamp}.json", "w") as f:
              f.write(history.to_json())

6. **Handle Errors Gracefully**: Check for None when getting history:

   .. code-block:: python

      history = chat.get_history()
      if history is not None:
          # Use history
      else:
          # Handle case where history is not available

See Also
--------

* :doc:`chat_history` - Complete guide on history management
* :doc:`chat_streaming` - Streaming with history accumulation
* :doc:`token_analysis` - Token analysis for history
* :doc:`api_reference/chat` - API reference for Chat class

