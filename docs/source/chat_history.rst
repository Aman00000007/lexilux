Chat History Management
========================

Lexilux provides comprehensive conversation history management with automatic extraction,
serialization, token counting, truncation, and multi-format export capabilities.

Overview
--------

The ``ChatHistory`` class eliminates the need for manual history maintenance by providing:

* **Automatic extraction** from any Chat call or message list
* **Automatic history management** via ``auto_history`` feature (see :doc:`auto_history`)
* **Serialization** to/from JSON for persistence
* **Token counting and truncation** for context window management
* **Round-based operations** for conversation management
* **Multi-format export** (Markdown, HTML, Text, JSON)

Key Features
------------

1. **Zero Maintenance**: Extract history from any Chat call automatically, or use ``auto_history=True`` for automatic recording
2. **Flexible Input**: Supports all message formats (string, list of strings, list of dicts)
3. **Serialization**: Save and load conversations as JSON
4. **Token Management**: Count tokens and truncate by rounds to fit context windows
5. **Format Export**: Export to Markdown, HTML, Text, or JSON formats
6. **Automatic History**: Use ``Chat(..., auto_history=True)`` for zero-maintenance conversation tracking

Basic Usage
-----------

Automatic History (Simplest - Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way is to use ``auto_history=True`` when creating the Chat client.
This automatically records all conversations with zero maintenance:

.. code-block:: python

   from lexilux import Chat

   # Enable auto_history - simplest approach
   chat = Chat(..., auto_history=True)

   # Just chat - history is automatically recorded
   result1 = chat("What is Python?")
   result2 = chat("Tell me more")

   # Get complete history at any time
   history = chat.get_history()
   print(f"Total messages: {len(history.messages)}")

   # Clear when starting new topic
   chat.clear_history()

For detailed guide on auto_history, see :doc:`auto_history`.

Automatic Extraction (Alternative)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternatively, you can extract history from Chat calls manually:

.. code-block:: python

   from lexilux import Chat
   from lexilux.chat import ChatHistory

   chat = Chat(base_url="https://api.example.com/v1", api_key="key", model="gpt-4")

   # Extract history from a Chat call - no manual maintenance!
   result = chat("What is Python?")
   history = ChatHistory.from_chat_result("What is Python?", result)

   # Continue the conversation
   result2 = chat(history.get_messages() + [{"role": "user", "content": "Tell me more"}])
   history = ChatHistory.from_chat_result(
       history.get_messages() + [{"role": "user", "content": "Tell me more"}],
       result2
   )

   # Now history contains the complete conversation

.. note::
   This approach requires no manual history maintenance. Simply extract history
   from each Chat call, and the conversation is automatically tracked.

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

   # Call API
   result = chat(history.get_messages())

   # Add assistant response
   history.append_result(result)

   # Continue conversation
   history.add_user("Tell me more")
   result2 = chat(history.get_messages())
   history.append_result(result2)

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
~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

1. **Use Auto History When Possible**: For simplest usage, use ``Chat(..., auto_history=True)``.
   This eliminates all manual history management. See :doc:`auto_history` for details.

2. **Use Automatic Extraction**: If not using auto_history, prefer ``ChatHistory.from_chat_result()`` over
   manual construction. It's simpler and less error-prone.

3. **Serialize Regularly**: Save important conversations to JSON for persistence:

   .. code-block:: python

      # After each important exchange
      with open(f"conversation_{timestamp}.json", "w") as f:
          f.write(history.to_json())

4. **Manage Context Windows**: Use token counting and truncation before long conversations:

   .. code-block:: python

      # Before making a new request
      if history.count_tokens(tokenizer) > max_context:
          history = history.truncate_by_rounds(tokenizer, max_tokens=max_context)

5. **Handle Incomplete Rounds**: Be aware that incomplete rounds (user message without
   assistant response) are preserved. Use ``remove_last_round()`` if needed.

6. **Use Token Analysis for Insights**: Use ``analyze_tokens()`` to understand token distribution
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

1. **Forgetting to Assign Truncated History**:
   ``truncate_by_rounds()`` returns a new instance. Don't forget to assign it:

   .. code-block:: python

      # Wrong
      history.truncate_by_rounds(tokenizer, max_tokens=4000)
      # history is unchanged!

      # Correct
      history = history.truncate_by_rounds(tokenizer, max_tokens=4000)

2. **Multiple System Messages**: If your messages contain multiple system messages,
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

3. **Incomplete Rounds**: When removing or truncating, incomplete rounds (user without
   assistant) are treated as valid rounds. Check for completion if needed:

   .. code-block:: python

      # Check if last round is complete
      rounds = history._get_rounds()
      if rounds and len(rounds[-1]) == 1:  # Only user message
          # Incomplete round
          history.remove_last_round()

4. **Token Counting Performance**: Token counting can be slow for long histories.
   Consider caching results or only counting when necessary.

5. **Using Auto History Incorrectly**: Remember that ``auto_history=True`` must be set
   when creating the Chat client. It defaults to ``False``:

   .. code-block:: python

      # Wrong - auto_history defaults to False
      chat = Chat(...)
      chat("Hello")
      history = chat.get_history()  # Returns None!

      # Correct - explicitly enable
      chat = Chat(..., auto_history=True)
      chat("Hello")
      history = chat.get_history()  # Returns ChatHistory

6. **Not Clearing History Between Sessions**: When using auto_history, remember to
   clear history when starting new conversation topics:

   .. code-block:: python

      chat = Chat(..., auto_history=True)
      
      # Session 1
      chat("What is Python?")
      
      # Session 2 - should clear first
      chat.clear_history()
      chat("What is JavaScript?")

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

