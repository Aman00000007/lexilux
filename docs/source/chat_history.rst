Chat History Management
=======================

Lexilux provides comprehensive conversation history management with **immutable history objects**.
All history management is explicit - you create and manage `ChatHistory` objects yourself.

.. important::
   **History Immutability**: All methods that receive a `history` parameter create a clone internally
   and **never modify the original history object**. You must manually update your history after each API call.

Overview
--------

The ``ChatHistory`` class provides:

* **Immutable History Objects**: Methods clone history internally, never modify original
* **Explicit History Management**: You create and pass history objects explicitly
* **MutableSequence Protocol**: Array-like operations (indexing, slicing, iteration)
* **Serialization** to/from JSON for persistence
* **Token counting and truncation** for context window management
* **Round-based operations** for conversation management
* **Multi-format export** (Markdown, HTML, Text, JSON)
* **Query and modification methods** for flexible history manipulation

Key Features
------------

1. **Immutable by Default**: All API methods clone history internally - original never modified
2. **Explicit Control**: You manage history objects explicitly - no hidden state
3. **Array-like Operations**: Use indexing, slicing, iteration like a list
4. **Flexible Input**: Supports all message formats (string, list of strings, list of dicts)
5. **Serialization**: Save and load conversations as JSON
6. **Token Management**: Count tokens and truncate by rounds to fit context windows
7. **Format Export**: Export to Markdown, HTML, Text, or JSON formats

History Immutability
--------------------

.. important::
   **All API methods create a clone of the history internally and never modify the original.**

   This means:
   
   * ✅ Thread-safe: Multiple threads can use the same history object
   * ✅ No side effects: Original history is never changed
   * ✅ Functional programming: Predictable behavior
   * ⚠️ **You must manually update history after each API call**

Manual History Updates
~~~~~~~~~~~~~~~~~~~~~~

Since history is immutable, you need to manually update it after each API call:

**Non-streaming methods** (`chat()`, `chat.complete()`):

.. code-block:: python

   from lexilux import Chat, ChatHistory

   chat = Chat(...)
   history = ChatHistory()

   # Call API - original history is NOT modified
   result = chat("What is Python?", history=history)
   
   # Manually update history
   history.add_user("What is Python?")
   history.append_result(result)
   
   # Now history contains the turn
   assert len(history.messages) == 2

**Streaming methods** (`chat.stream()`, `chat.complete_stream()`):

.. code-block:: python

   # Call streaming API - original history is NOT modified
   iterator = chat.stream("Tell me more", history=history)
   
   # Consume iterator
   for chunk in iterator:
       print(chunk.delta, end="", flush=True)
   
   # Get result and manually update history
   result = iterator.result.to_chat_result()
   history.add_user("Tell me more")
   history.append_result(result)

**Complete methods** (`chat.complete()`, `chat.complete_stream()`):

.. code-block:: python

   # complete() also doesn't modify original history
   result = chat.complete("Write JSON", history=history, max_tokens=100)
   
   # Manually update history
   history.add_user("Write JSON")
   history.append_result(result)

Complete Examples: All Interfaces
----------------------------------

Example 1: chat() - Non-streaming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lexilux import Chat, ChatHistory

   chat = Chat(...)
   history = ChatHistory()

   # Single-turn conversation
   result = chat("Hello", history=history)
   # Original history unchanged - manually update
   history.add_user("Hello")
   history.append_result(result)
   assert len(history.messages) == 2

   # Multi-turn conversation
   result2 = chat("How are you?", history=history)
   # Manually update again
   history.add_user("How are you?")
   history.append_result(result2)
   assert len(history.messages) == 4

Example 2: chat.stream() - Streaming
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lexilux import Chat, ChatHistory

   chat = Chat(...)
   history = ChatHistory()

   # Streaming call - original history unchanged
   iterator = chat.stream("Write a story", history=history)
   
   # Consume stream
   for chunk in iterator:
       print(chunk.delta, end="", flush=True)
   
   # Get result and manually update history
   result = iterator.result.to_chat_result()
   history.add_user("Write a story")
   history.append_result(result)
   assert len(history.messages) == 2

   # Continue conversation
   iterator2 = chat.stream("Continue the story", history=history)
   for chunk in iterator2:
       print(chunk.delta, end="", flush=True)
   
   result2 = iterator2.result.to_chat_result()
   history.add_user("Continue the story")
   history.append_result(result2)
   assert len(history.messages) == 4

Example 3: chat.complete() - Complete Response
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lexilux import Chat, ChatHistory

   chat = Chat(...)
   history = ChatHistory()

   # Single-turn (no history needed)
   result = chat.complete("Write JSON", max_tokens=100)
   # No history to update

   # Multi-turn (with history)
   result = chat.complete("First question", history=history, max_tokens=100)
   # Manually update history
   history.add_user("First question")
   history.append_result(result)

   result2 = chat.complete("Follow-up", history=history, max_tokens=100)
   history.add_user("Follow-up")
   history.append_result(result2)

Example 4: chat.complete_stream() - Streaming Complete
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lexilux import Chat, ChatHistory

   chat = Chat(...)
   history = ChatHistory()

   # Single-turn (no history needed)
   iterator = chat.complete_stream("Write JSON", max_tokens=100)
   for chunk in iterator:
       print(chunk.delta, end="", flush=True)
   result = iterator.result.to_chat_result()
   # No history to update

   # Multi-turn (with history)
   iterator = chat.complete_stream("First question", history=history, max_tokens=100)
   for chunk in iterator:
       print(chunk.delta, end="", flush=True)
   result = iterator.result.to_chat_result()
   # Manually update history
   history.add_user("First question")
   history.append_result(result)

   iterator2 = chat.complete_stream("Follow-up", history=history, max_tokens=100)
   for chunk in iterator2:
       print(chunk.delta, end="", flush=True)
   result2 = iterator2.result.to_chat_result()
   history.add_user("Follow-up")
   history.append_result(result2)

Example 5: ChatContinue.continue_request() - Manual Continue
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lexilux import Chat, ChatHistory, ChatContinue

   chat = Chat(...)
   history = ChatHistory()

   # Initial request
   result = chat("Write a long story", history=history, max_tokens=50)
   # Manually update history
   history.add_user("Write a long story")
   history.append_result(result)

   # Continue if truncated
   if result.finish_reason == "length":
       # continue_request also doesn't modify original history
       full_result = ChatContinue.continue_request(
           chat, result, history=history, max_continues=3
       )
       # Note: continue_request adds continue prompts internally to working history
       # But original history is unchanged - you may want to update with final result
       # Or manually add continue prompts if needed
       history.append_result(full_result)  # Add merged result

Example 6: ChatContinue.continue_request_stream() - Streaming Continue
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from lexilux import Chat, ChatHistory, ChatContinue

   chat = Chat(...)
   history = ChatHistory()

   # Initial request
   result = chat("Write a long story", history=history, max_tokens=50)
   history.add_user("Write a long story")
   history.append_result(result)

   # Continue with streaming
   if result.finish_reason == "length":
       iterator = ChatContinue.continue_request_stream(
           chat, result, history=history, max_continues=2
       )
       for chunk in iterator:
           print(chunk.delta, end="", flush=True)
       
       # Get merged result
       full_result = iterator.result.to_chat_result()
       # Update history with final merged result
       history.append_result(full_result)

Helper Function: Update History from Result
--------------------------------------------

For convenience, you can create a helper function:

.. code-block:: python

   def update_history_from_result(history: ChatHistory, user_message: str, result):
       """Helper to update history after API call."""
       history.add_user(user_message)
       if isinstance(result, ChatResult):
           history.append_result(result)
       else:
           # StreamingIterator
           history.append_result(result.result.to_chat_result())

   # Usage
   history = ChatHistory()
   result = chat("Hello", history=history)
   update_history_from_result(history, "Hello", result)

   iterator = chat.stream("How are you?", history=history)
   for chunk in iterator:
       print(chunk.delta, end="", flush=True)
   update_history_from_result(history, "How are you?", iterator)

Basic Usage
-----------

Creating and Using History
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You explicitly create and pass history objects, then manually update them:

.. code-block:: python

   from lexilux import Chat, ChatHistory

   chat = Chat(base_url="https://api.example.com/v1", api_key="key", model="gpt-4")
   
   # Create history explicitly
   history = ChatHistory()
   
   # First turn - pass history explicitly
   result1 = chat("What is Python?", history=history)
   # Original history unchanged - manually update
   history.add_user("What is Python?")
   history.append_result(result1)
   
   # Second turn - same history object
   result2 = chat("Tell me more", history=history)
   # Manually update again
   history.add_user("Tell me more")
   history.append_result(result2)
   
   print(f"Total messages: {len(history.messages)}")  # 4 messages

From Messages
~~~~~~~~~~~~~

You can also build history from message lists:

.. code-block:: python

   # From string
   history = ChatHistory.from_messages("Hello", system="You are helpful")

   # From list of strings
   history = ChatHistory.from_messages(["Hello", "How are you?"])

   # From list of dicts
   messages = [
       {"role": "system", "content": "You are helpful"},
       {"role": "user", "content": "Hello"},
   ]
   history = ChatHistory.from_messages(messages)

   # System message is automatically extracted if present
   assert history.system == "You are helpful"

Manual Construction
~~~~~~~~~~~~~~~~~~~

For more control, you can manually construct and manage history:

.. code-block:: python

   history = ChatHistory(system="You are a helpful assistant")

   # Add user message
   history.add_user("What is Python?")

   # Call API with history (original unchanged)
   result = chat("What is Python?", history=history)
   
   # Manually add result
   history.append_result(result)

   # Continue conversation
   history.add_user("Tell me more")
   result2 = chat("Tell me more", history=history)
   history.append_result(result2)

Why Immutability?
-----------------

Benefits of immutable history:

1. **Thread Safety**: Multiple threads can safely use the same history object
2. **No Side Effects**: Original history is never modified unexpectedly
3. **Functional Programming**: Predictable, testable code
4. **Explicit Control**: You decide exactly when and how history is updated

Multi-turn Conversation Pattern
--------------------------------

Complete pattern for multi-turn conversations:

.. code-block:: python

   from lexilux import Chat, ChatHistory

   chat = Chat(...)
   history = ChatHistory()

   # Turn 1: Non-streaming
   result1 = chat("Hello", history=history)
   history.add_user("Hello")
   history.append_result(result1)

   # Turn 2: Streaming
   iterator2 = chat.stream("How are you?", history=history)
   for chunk in iterator2:
       print(chunk.delta, end="", flush=True)
   result2 = iterator2.result.to_chat_result()
   history.add_user("How are you?")
   history.append_result(result2)

   # Turn 3: Complete (guaranteed complete)
   result3 = chat.complete("Write JSON", history=history, max_tokens=100)
   history.add_user("Write JSON")
   history.append_result(result3)

   # Turn 4: Complete streaming
   iterator4 = chat.complete_stream("Continue", history=history, max_tokens=100)
   for chunk in iterator4:
       print(chunk.delta, end="", flush=True)
   result4 = iterator4.result.to_chat_result()
   history.add_user("Continue")
   history.append_result(result4)

   # History now contains all 4 turns
   assert len(history.messages) == 8  # 4 user + 4 assistant

MutableSequence Operations
---------------------------

ChatHistory implements the ``MutableSequence`` protocol, allowing array-like operations:

Indexing
~~~~~~~~

.. code-block:: python

   history = ChatHistory()
   history.add_user("Hello")
   history.add_assistant("Hi!")
   
   # Get message by index
   first_msg = history[0]
   assert first_msg["role"] == "user"
   
   # Set message by index
   history[0] = {"role": "user", "content": "Updated"}

Slicing
~~~~~~~

.. code-block:: python

   history = ChatHistory()
   history.add_user("Hello")
   history.add_assistant("Hi!")
   history.add_user("How are you?")
   history.add_assistant("I'm fine")
   
   # Get first 2 messages (returns new ChatHistory)
   first_turn = history[:2]
   assert isinstance(first_turn, ChatHistory)
   assert len(first_turn) == 2
   
   # Get last 2 messages
   last_turn = history[-2:]
   assert len(last_turn) == 2

Iteration
~~~~~~~~~

.. code-block:: python

   history = ChatHistory()
   history.add_user("Hello")
   history.add_assistant("Hi!")
   
   # Iterate over messages
   for msg in history:
       print(f"{msg['role']}: {msg['content']}")
   
   # Convert to list
   messages = list(history)

Length and Membership
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   history = ChatHistory()
   history.add_user("Hello")
   history.add_assistant("Hi!")
   
   # Length
   assert len(history) == 2
   
   # Membership
   assert history[0] in history

Modification Operations
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   history = ChatHistory()
   history.add_user("Hello")
   history.add_assistant("Hi!")
   
   # Insert message
   history.insert(0, {"role": "system", "content": "You are helpful"})
   
   # Delete message
   del history[0]
   
   # Replace slice
   history[:2] = [
       {"role": "user", "content": "New 1"},
       {"role": "assistant", "content": "New 2"},
   ]

Query Methods
-------------

Get User/Assistant Messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   history = ChatHistory()
   history.add_user("Hello")
   history.add_assistant("Hi!")
   history.add_user("How are you?")
   history.add_assistant("I'm fine")
   
   # Get all user messages
   user_msgs = history.get_user_messages()
   assert user_msgs == ["Hello", "How are you?"]
   
   # Get all assistant messages
   assistant_msgs = history.get_assistant_messages()
   assert assistant_msgs == ["Hi!", "I'm fine"]

Get Last Message
~~~~~~~~~~~~~~~~

.. code-block:: python

   history = ChatHistory()
   history.add_user("Hello")
   history.add_assistant("Hi!")
   
   # Get last message
   last = history.get_last_message()
   assert last["content"] == "Hi!"
   
   # Get last user message
   last_user = history.get_last_user_message()
   assert last_user == "Hello"

Modification Methods
---------------------

Remove Operations
~~~~~~~~~~~~~~~~~

.. code-block:: python

   history = ChatHistory()
   history.add_user("Hello")
   history.add_assistant("Hi!")
   history.add_user("How are you?")
   
   # Remove last message
   removed = history.remove_last()
   assert removed["content"] == "How are you?"
   
   # Remove at specific index
   removed = history.remove_at(1)
   assert removed["content"] == "Hi!"

Replace Operations
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   history = ChatHistory()
   history.add_user("Hello")
   history.add_assistant("Hi!")
   
   # Replace at index
   history.replace_at(0, "user", "Updated")
   assert history[0]["content"] == "Updated"

System Message
~~~~~~~~~~~~~~

.. code-block:: python

   history = ChatHistory()
   
   # Add or update system message
   history.add_system("You are helpful")
   assert history.system == "You are helpful"
   
   # Update system message
   history.add_system("You are very helpful")
   assert history.system == "You are very helpful"

Clone and Merge
---------------

Clone History
~~~~~~~~~~~~~

.. code-block:: python

   history = ChatHistory(system="You are helpful")
   history.add_user("Hello")
   history.add_assistant("Hi!")
   
   # Clone creates deep copy
   cloned = history.clone()
   assert cloned is not history
   assert cloned.messages is not history.messages
   
   # Modifying clone doesn't affect original
   cloned.add_user("New message")
   assert len(cloned) == 3
   assert len(history) == 2

Merge Histories
~~~~~~~~~~~~~~~

.. code-block:: python

   history1 = ChatHistory(system="You are helpful")
   history1.add_user("Hello")
   history1.add_assistant("Hi!")
   
   history2 = ChatHistory()
   history2.add_user("How are you?")
   history2.add_assistant("I'm fine")
   
   # Merge histories
   combined = history1 + history2
   assert isinstance(combined, ChatHistory)
   assert len(combined) == 4
   assert combined.system == "You are helpful"  # From first history

Serialization
-------------

Save and Load Conversations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

ChatHistory supports full serialization to/from JSON:

.. code-block:: python

   # Save to JSON
   json_str = history.to_json(indent=2)
   with open("conversation.json", "w") as f:
       f.write(json_str)

   # Or use to_dict for custom serialization
   data = history.to_dict()
   # data is a regular dict, can be processed as needed

   # Load from JSON
   with open("conversation.json", "r") as f:
       history = ChatHistory.from_json(f.read())

   # Or from dict
   history = ChatHistory.from_dict(data)

.. warning::
   When serializing, make sure to handle the system message correctly.
   The system message is stored separately from messages, so both need to be
   preserved during serialization.

Round Operations
----------------

Get Last N Rounds
~~~~~~~~~~~~~~~~~

Extract the most recent conversation rounds:

.. code-block:: python

   # Get last 2 rounds
   recent = history.get_last_n_rounds(2)
   # recent is a new ChatHistory instance with only the last 2 rounds

   # Use for context window management
   if history.count_tokens(tokenizer) > max_tokens:
       # Keep only recent rounds
       history = history.get_last_n_rounds(3)

Remove Last Round
~~~~~~~~~~~~~~~~~

Remove the most recent conversation round:

.. code-block:: python

   # Remove last round (user + assistant pair)
   history.remove_last_round()

   # Useful for undo operations or error recovery
   if result.finish_reason == "content_filter":
       history.remove_last_round()  # Remove the filtered response

.. note::
   If the last round is incomplete (only user message, no assistant),
   ``remove_last_round()`` will still remove it.

Token Management
----------------

Lexilux provides comprehensive token analysis capabilities for conversation history.
For detailed token analysis, see :doc:`token_analysis`.

Count Tokens
~~~~~~~~~~~~

Count tokens in the entire history:

.. code-block:: python

   from lexilux import Tokenizer

   tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct")
   total_tokens = history.count_tokens(tokenizer)
   print(f"Total tokens: {total_tokens}")

Count Tokens Per Round
~~~~~~~~~~~~~~~~~~~~~~~

Count tokens for each conversation round:

.. code-block:: python

   round_tokens = history.count_tokens_per_round(tokenizer)
   # Returns: [(round_index, tokens), ...]
   for idx, tokens in round_tokens:
       print(f"Round {idx}: {tokens} tokens")

Count Tokens By Role
~~~~~~~~~~~~~~~~~~~~

Count tokens grouped by role (system, user, assistant):

.. code-block:: python

   role_tokens = history.count_tokens_by_role(tokenizer)
   print(f"System tokens: {role_tokens['system']}")
   print(f"User tokens: {role_tokens['user']}")
   print(f"Assistant tokens: {role_tokens['assistant']}")

Comprehensive Token Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get detailed token analysis with per-message and per-round breakdowns:

.. code-block:: python

   from lexilux import TokenAnalysis

   analysis = history.analyze_tokens(tokenizer)
   
   # Summary statistics
   print(f"Total: {analysis.total_tokens}")
   print(f"User: {analysis.user_tokens}, Assistant: {analysis.assistant_tokens}")
   
   # Per-message breakdown
   for role, preview, tokens in analysis.per_message:
       print(f"{role}: {preview}... ({tokens} tokens)")
   
   # Per-round breakdown
   for idx, total, user, assistant in analysis.per_round:
       print(f"Round {idx}: total={total}, user={user}, assistant={assistant}")

For more details, see :doc:`token_analysis`.

Truncate by Rounds
~~~~~~~~~~~~~~~~~~

Truncate history to fit within a token limit, keeping the most recent rounds:

.. code-block:: python

   # Truncate to fit within 4000 tokens, keeping system message
   truncated = history.truncate_by_rounds(
       tokenizer=tokenizer,
       max_tokens=4000,
       keep_system=True
   )

   # truncated is a new ChatHistory instance
   # Original history is not modified

.. important::
   ``truncate_by_rounds()`` returns a **new** ChatHistory instance.
   It does **not** modify the original history. Make sure to assign the result
   if you want to use the truncated version:

   .. code-block:: python

      # Wrong - original history unchanged
      history.truncate_by_rounds(tokenizer, max_tokens=4000)

      # Correct - use truncated version
      history = history.truncate_by_rounds(tokenizer, max_tokens=4000)

Best Practices
--------------

1. **Always Manually Update History**: After each API call, manually update your history:

   .. code-block:: python

      history = ChatHistory()
      result = chat("Hello", history=history)
      # Don't forget to update!
      history.add_user("Hello")
      history.append_result(result)

2. **Use Helper Functions**: Create helper functions to reduce boilerplate:

   .. code-block:: python

      def chat_with_history(chat, history, message, **kwargs):
          """Chat and automatically update history."""
          result = chat(message, history=history, **kwargs)
          history.add_user(message)
          history.append_result(result)
          return result

      # Usage
      result = chat_with_history(chat, history, "Hello")

3. **Same History Object**: For a conversation session, use the same history object
   across all calls:

   .. code-block:: python

      history = ChatHistory()
      result1 = chat("Hello", history=history)
      history.add_user("Hello")
      history.append_result(result1)
      
      result2 = chat("How are you?", history=history)
      history.add_user("How are you?")
      history.append_result(result2)

4. **Multiple Independent Histories**: You can use multiple history objects for different
   conversations:

   .. code-block:: python

      history1 = ChatHistory()
      history2 = ChatHistory()
      
      result1 = chat("Hello", history=history1)
      history1.add_user("Hello")
      history1.append_result(result1)
      
      result2 = chat("Hi", history=history2)
      history2.add_user("Hi")
      history2.append_result(result2)
      # Two independent conversations

5. **Serialize Regularly**: Save important conversations to JSON for persistence:

   .. code-block:: python

      # After each important exchange
      with open(f"conversation_{timestamp}.json", "w") as f:
          f.write(history.to_json())

6. **Manage Context Windows**: Use token counting and truncation before long conversations:

   .. code-block:: python

      # Before making a new request
      if history.count_tokens(tokenizer) > max_context:
          history = history.truncate_by_rounds(tokenizer, max_tokens=max_context)

7. **Handle Incomplete Rounds**: Be aware that incomplete rounds (user message without
   assistant response) are preserved. Use ``remove_last_round()`` if needed.

8. **Use Token Analysis for Insights**: Use ``analyze_tokens()`` to understand token distribution
   and identify optimization opportunities:

   .. code-block:: python

      from lexilux import Tokenizer, TokenAnalysis

      tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct")
      analysis = history.analyze_tokens(tokenizer)

      # Identify token-heavy rounds
      for idx, total, user, assistant in analysis.per_round:
          if total > 500:  # Round uses more than 500 tokens
              print(f"Round {idx} is token-heavy: {total} tokens")

      # Check distribution
      if analysis.assistant_tokens > analysis.user_tokens * 3:
          print("Assistant responses are much longer than user messages")

Common Pitfalls
---------------

1. **Forgetting to Update History**: Since history is immutable, you must manually update:

   .. code-block:: python

      # Wrong - history not updated
      history = ChatHistory()
      result = chat("Hello", history=history)
      # history is still empty!
      
      # Correct - manually update
      history = ChatHistory()
      result = chat("Hello", history=history)
      history.add_user("Hello")
      history.append_result(result)

2. **Assuming History is Updated Automatically**: History is NOT updated automatically:

   .. code-block:: python

      # Wrong assumption
      history = ChatHistory()
      result1 = chat("Hello", history=history)
      result2 = chat("How are you?", history=history)
      # result2 doesn't have context from result1 because history wasn't updated!

      # Correct
      history = ChatHistory()
      result1 = chat("Hello", history=history)
      history.add_user("Hello")
      history.append_result(result1)
      
      result2 = chat("How are you?", history=history)
      history.add_user("How are you?")
      history.append_result(result2)
      # Now result2 has context

3. **Forgetting to Assign Truncated History**:
   ``truncate_by_rounds()`` returns a new instance. Don't forget to assign it:

   .. code-block:: python

      # Wrong
      history.truncate_by_rounds(tokenizer, max_tokens=4000)
      # history is unchanged!

      # Correct
      history = history.truncate_by_rounds(tokenizer, max_tokens=4000)

4. **Multiple System Messages**: If your messages contain multiple system messages,
   only the first one is extracted to ``history.system``. The rest remain in messages:

   .. code-block:: python

      messages = [
          {"role": "system", "content": "System 1"},
          {"role": "system", "content": "System 2"},  # This stays in messages
          {"role": "user", "content": "Hello"},
      ]
      history = ChatHistory.from_messages(messages)
      # history.system == "System 1"
      # history.messages[0] == {"role": "system", "content": "System 2"}

5. **Incomplete Rounds**: When removing or truncating, incomplete rounds (user without
   assistant) are treated as valid rounds. Check for completion if needed:

   .. code-block:: python

      # Check if last round is complete
      rounds = history._get_rounds()
      if rounds and len(rounds[-1]) == 1:  # Only user message
          # Incomplete round
          history.remove_last_round()

6. **Token Counting Performance**: Token counting can be slow for long histories.
   Consider caching results or only counting when necessary.

7. **Using Different History Objects**: Each history object is independent. Make sure
   to use the same history object for a conversation session:

   .. code-block:: python

      # Wrong - different history objects
      history1 = ChatHistory()
      result1 = chat("Hello", history=history1)
      history1.add_user("Hello")
      history1.append_result(result1)
      
      history2 = ChatHistory()
      result2 = chat("How are you?", history=history2)
      history2.add_user("How are you?")
      history2.append_result(result2)
      # history2 doesn't contain "Hello"
      
      # Correct - same history object
      history = ChatHistory()
      result1 = chat("Hello", history=history)
      history.add_user("Hello")
      history.append_result(result1)
      
      result2 = chat("How are you?", history=history)
      history.add_user("How are you?")
      history.append_result(result2)
      # history contains both turns

Utility Functions
-----------------

Lexilux provides utility functions for common history operations:

Merge Histories
~~~~~~~~~~~~~~~

Merge multiple conversation histories:

.. code-block:: python

   from lexilux.chat import merge_histories

   history1 = ChatHistory.from_messages("Hello")
   history1.add_assistant("Hi!")
   
   history2 = ChatHistory.from_messages("How are you?")
   history2.add_assistant("I'm fine!")

   # Merge histories
   merged = merge_histories(history1, history2)
   assert len(merged.messages) == 4  # 2 user + 2 assistant

   # Useful for combining conversations from different sessions

Filter by Role
~~~~~~~~~~~~~~

Filter history to show only messages from a specific role:

.. code-block:: python

   from lexilux.chat import filter_by_role

   history = ChatHistory.from_messages(["Hello", "Hi there", "How are you?"])
   history.add_assistant("I'm doing well!")

   # Get only user messages
   user_only = filter_by_role(history, "user")
   assert len(user_only.messages) == 3
   assert all(msg["role"] == "user" for msg in user_only.messages)

   # Get only assistant messages
   assistant_only = filter_by_role(history, "assistant")
   assert len(assistant_only.messages) == 1

   # Useful for analyzing user questions or assistant responses separately

Search Content
~~~~~~~~~~~~~~

Search for messages containing specific text:

.. code-block:: python

   from lexilux.chat import search_content

   history = ChatHistory.from_messages([
       "What is Python?",
       "How do I use it?",
       "Show me examples"
   ])
   history.add_assistant("Python is a programming language...")

   # Search for messages containing "Python"
   results = search_content(history, "Python")
   assert len(results) >= 1
   assert any("Python" in msg.get("content", "") for msg in results)

   # Useful for finding specific topics in long conversations

Get Statistics
~~~~~~~~~~~~~~

Get comprehensive statistics about the conversation:

.. code-block:: python

   from lexilux.chat import get_statistics
   from lexilux import Tokenizer

   history = ChatHistory(system="You are helpful")
   history.add_user("Hello")
   history.add_assistant("Hi!")

   # Character-based statistics (no tokenizer needed)
   stats = get_statistics(history)
   print(f"Total rounds: {stats['total_rounds']}")
   print(f"Total messages: {stats['total_messages']}")
   print(f"Total characters: {stats['total_characters']}")
   print(f"Average message length: {stats['average_message_length']} chars")

   # With tokenizer - includes comprehensive token statistics
   tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct")
   stats = get_statistics(history, tokenizer=tokenizer)
   print(f"Total tokens: {stats['total_tokens']}")
   print(f"Tokens by role: {stats['tokens_by_role']}")
   print(f"Average tokens per message: {stats['average_tokens_per_message']}")
   print(f"Average tokens per round: {stats['average_tokens_per_round']}")
   print(f"Max message tokens: {stats['max_message_tokens']}")
   print(f"Min message tokens: {stats['min_message_tokens']}")

   # Access full TokenAnalysis object
   analysis = stats['token_analysis']
   print(f"Per-message breakdown: {len(analysis.per_message)} messages")
   print(f"Per-round breakdown: {len(analysis.per_round)} rounds")

.. note::
   When tokenizer is provided, ``get_statistics()`` includes comprehensive token
   analysis. See :doc:`token_analysis` for details on the TokenAnalysis object.

.. important::
   **Common Pitfall**: Forgetting to pass tokenizer when you need token statistics.
   
   .. code-block:: python

      # Wrong - no token statistics
      stats = get_statistics(history)
      assert "total_tokens" not in stats  # Token stats not included!
      
      # Correct - pass tokenizer for token statistics
      stats = get_statistics(history, tokenizer=tokenizer)
      assert "total_tokens" in stats  # Token stats included
