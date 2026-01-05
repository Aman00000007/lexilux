Token Analysis for Chat History
==================================

Lexilux provides comprehensive token analysis capabilities for conversation history,
allowing you to understand token usage patterns, optimize context window management,
and make informed decisions about history truncation.

Overview
--------

Token analysis helps you:

* **Understand token distribution**: See how tokens are distributed across system, user, and assistant messages
* **Optimize context windows**: Identify which rounds consume the most tokens
* **Plan truncation strategies**: Make informed decisions about which rounds to keep
* **Monitor usage patterns**: Track token growth over conversation rounds
* **Debug token issues**: Identify messages that consume excessive tokens

Key Concepts
------------

1. **TokenAnalysis**: A comprehensive data structure containing all token statistics
2. **Per-message analysis**: Token count for each individual message with content previews
3. **Per-round analysis**: Token breakdown for each conversation round (user + assistant)
4. **Role-based statistics**: Token counts grouped by role (system, user, assistant)
5. **Statistical metrics**: Averages, min, max for tokens per message and per round

Basic Usage
-----------

Simple Token Counting
~~~~~~~~~~~~~~~~~~~~~~

The simplest way to count tokens:

.. code-block:: python

   from lexilux import ChatHistory, Tokenizer

   tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct")
   history = ChatHistory.from_messages("Hello")

   # Simple total count
   total = history.count_tokens(tokenizer)
   print(f"Total tokens: {total}")

Comprehensive Analysis
~~~~~~~~~~~~~~~~~~~~~~

For detailed analysis, use ``analyze_tokens()``:

.. code-block:: python

   from lexilux import ChatHistory, Tokenizer, TokenAnalysis

   tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct")
   history = ChatHistory(system="You are a helpful assistant")
   history.add_user("What is Python?")
   history.add_assistant("Python is a programming language...")

   # Get comprehensive analysis
   analysis = history.analyze_tokens(tokenizer)

   # Access summary statistics
   print(f"Total tokens: {analysis.total_tokens}")
   print(f"System tokens: {analysis.system_tokens}")
   print(f"User tokens: {analysis.user_tokens}")
   print(f"Assistant tokens: {analysis.assistant_tokens}")

   # Access per-message breakdown
   for role, preview, tokens in analysis.per_message:
       print(f"{role}: {preview}... ({tokens} tokens)")

   # Access per-round breakdown
   for idx, total, user, assistant in analysis.per_round:
       print(f"Round {idx}: total={total}, user={user}, assistant={assistant}")

TokenAnalysis Object
--------------------

The ``TokenAnalysis`` object provides comprehensive token statistics:

Attributes
~~~~~~~~~~

**Summary Statistics:**

* ``total_tokens``: Total tokens across all messages
* ``system_tokens``: Tokens in system message (if present)
* ``user_tokens``: Total tokens in all user messages
* ``assistant_tokens``: Total tokens in all assistant messages

**Message Counts:**

* ``total_messages``: Total number of messages
* ``system_messages``: Number of system messages (0 or 1)
* ``user_messages``: Number of user messages
* ``assistant_messages``: Number of assistant messages

**Detailed Breakdowns:**

* ``per_message``: List of ``(role, content_preview, tokens)`` tuples
* ``per_round``: List of ``(round_index, total_tokens, user_tokens, assistant_tokens)`` tuples

**Statistical Metrics:**

* ``average_tokens_per_message``: Average tokens per message
* ``average_tokens_per_round``: Average tokens per round
* ``max_message_tokens``: Maximum tokens in a single message
* ``min_message_tokens``: Minimum tokens in a single message

**Distribution:**

* ``token_distribution``: Dictionary mapping role to total tokens
  - Keys: ``"system"``, ``"user"``, ``"assistant"``

Examples
--------

Per-Message Analysis
~~~~~~~~~~~~~~~~~~~~

Analyze token usage for each individual message:

.. code-block:: python

   analysis = history.analyze_tokens(tokenizer)

   print("Per-message token breakdown:")
   for role, preview, tokens in analysis.per_message:
       print(f"  {role:10s}: {tokens:4d} tokens - {preview}")

   # Output:
   # Per-message token breakdown:
   #   system    :   15 tokens - You are a helpful assistant
   #   user      :    8 tokens - What is Python?
   #   assistant :   45 tokens - Python is a programming language...

Per-Round Analysis
~~~~~~~~~~~~~~~~~~

Analyze token usage for each conversation round:

.. code-block:: python

   analysis = history.analyze_tokens(tokenizer)

   print("Per-round token breakdown:")
   for idx, total, user, assistant in analysis.per_round:
       print(f"Round {idx}:")
       print(f"  Total: {total} tokens")
       print(f"  User: {user} tokens")
       print(f"  Assistant: {assistant} tokens")

Role-Based Analysis
~~~~~~~~~~~~~~~~~~~

Get token counts grouped by role:

.. code-block:: python

   # Using analyze_tokens (comprehensive)
   analysis = history.analyze_tokens(tokenizer)
   print(f"Distribution: {analysis.token_distribution}")
   # Output: {'system': 15, 'user': 50, 'assistant': 200}

   # Or using dedicated method (simpler)
   role_tokens = history.count_tokens_by_role(tokenizer)
   print(f"User tokens: {role_tokens['user']}")
   print(f"Assistant tokens: {role_tokens['assistant']}")

Statistical Analysis
~~~~~~~~~~~~~~~~~~~~

Get statistical insights:

.. code-block:: python

   analysis = history.analyze_tokens(tokenizer)

   print(f"Average tokens per message: {analysis.average_tokens_per_message}")
   print(f"Average tokens per round: {analysis.average_tokens_per_round}")
   print(f"Max message tokens: {analysis.max_message_tokens}")
   print(f"Min message tokens: {analysis.min_message_tokens}")

   # Identify outliers
   if analysis.max_message_tokens > analysis.average_tokens_per_message * 3:
       print("Warning: Some messages have unusually high token counts")

Export Analysis
~~~~~~~~~~~~~~~

Export analysis results for further processing:

.. code-block:: python

   analysis = history.analyze_tokens(tokenizer)

   # Convert to dictionary
   analysis_dict = analysis.to_dict()

   # Save to JSON
   import json
   with open("token_analysis.json", "w") as f:
       json.dump(analysis_dict, f, indent=2)

   # Or use the statistics function
   from lexilux.chat import get_statistics
   stats = get_statistics(history, tokenizer=tokenizer)
   print(json.dumps(stats, indent=2))

Advanced Usage
--------------

Context Window Management
~~~~~~~~~~~~~~~~~~~~~~~~~

Use token analysis to manage context windows:

.. code-block:: python

   analysis = history.analyze_tokens(tokenizer)
   max_context = 4000

   if analysis.total_tokens > max_context:
       # Identify which rounds to keep
       kept_rounds = []
       current_tokens = analysis.system_tokens

       # Keep rounds from the end
       for idx in range(len(analysis.per_round) - 1, -1, -1):
           _, round_total, _, _ = analysis.per_round[idx]
           if current_tokens + round_total <= max_context:
               kept_rounds.insert(0, idx)
               current_tokens += round_total
           else:
               break

       print(f"Can keep rounds: {kept_rounds}")
       print(f"Total tokens: {current_tokens}")

Token Growth Monitoring
~~~~~~~~~~~~~~~~~~~~~~~

Monitor token growth across rounds:

.. code-block:: python

   analysis = history.analyze_tokens(tokenizer)

   cumulative = analysis.system_tokens
   print(f"System: {cumulative} tokens")

   for idx, total, user, assistant in analysis.per_round:
       cumulative += total
       print(f"After round {idx}: {cumulative} tokens "
             f"(+{total}: user={user}, assistant={assistant})")

Identifying Token-Heavy Messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Find messages that consume the most tokens:

.. code-block:: python

   analysis = history.analyze_tokens(tokenizer)

   # Sort messages by token count
   sorted_messages = sorted(
       analysis.per_message,
       key=lambda x: x[2],  # Sort by tokens
       reverse=True
   )

   print("Top 5 token-consuming messages:")
   for role, preview, tokens in sorted_messages[:5]:
       print(f"  {tokens} tokens - {role}: {preview}")

Round Efficiency Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyze token efficiency per round:

.. code-block:: python

   analysis = history.analyze_tokens(tokenizer)

   print("Round efficiency (user tokens / assistant tokens):")
   for idx, total, user, assistant in analysis.per_round:
       if assistant > 0:
           efficiency = user / assistant
           print(f"Round {idx}: {efficiency:.2f} "
                 f"(user={user}, assistant={assistant})")

Integration with Truncation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use analysis to inform truncation decisions:

.. code-block:: python

   analysis = history.analyze_tokens(tokenizer)
   max_tokens = 4000

   if analysis.total_tokens > max_tokens:
       # Analyze which rounds to keep
       print("Token analysis before truncation:")
       print(f"  Total: {analysis.total_tokens}")
       print(f"  Rounds: {len(analysis.per_round)}")

       # Truncate
       truncated = history.truncate_by_rounds(
           tokenizer, max_tokens, keep_system=True
       )

       # Verify
       truncated_analysis = truncated.analyze_tokens(tokenizer)
       print("After truncation:")
       print(f"  Total: {truncated_analysis.total_tokens}")
       print(f"  Rounds: {len(truncated_analysis.per_round)}")

Best Practices
--------------

1. **Cache Analysis Results**: Token analysis can be slow for long histories.
   Consider caching results if you need to access them multiple times:

   .. code-block:: python

      # Cache analysis
      analysis = history.analyze_tokens(tokenizer)
      # Use analysis object multiple times instead of re-analyzing

2. **Monitor Token Growth**: Track token growth as conversation progresses:

   .. code-block:: python

      # After each round
      analysis = history.analyze_tokens(tokenizer)
      if analysis.total_tokens > threshold:
          # Take action (truncate, warn, etc.)

3. **Use Per-Round Analysis for Truncation**: When truncating, use per-round
   analysis to make informed decisions:

   .. code-block:: python

      analysis = history.analyze_tokens(tokenizer)
      # Review per_round to decide which rounds to keep

4. **Combine with Statistics**: Use ``get_statistics()`` with tokenizer for
   comprehensive analysis:

   .. code-block:: python

      from lexilux.chat import get_statistics
      stats = get_statistics(history, tokenizer=tokenizer)
      # Includes both character and token statistics

Common Use Cases
----------------

1. **Pre-request Validation**: Check if history fits within context window:

   .. code-block:: python

      analysis = history.analyze_tokens(tokenizer)
      if analysis.total_tokens > max_context:
          # Truncate or warn
          history = history.truncate_by_rounds(tokenizer, max_context)

2. **Cost Estimation**: Estimate API costs based on token usage:

   .. code-block:: python

      analysis = history.analyze_tokens(tokenizer)
      input_cost = analysis.user_tokens * input_price_per_token
      output_cost = analysis.assistant_tokens * output_price_per_token
      total_cost = input_cost + output_cost

3. **Performance Monitoring**: Track token usage patterns over time:

   .. code-block:: python

      # Log token usage
      analysis = history.analyze_tokens(tokenizer)
      logger.info(f"Tokens: total={analysis.total_tokens}, "
                  f"rounds={len(analysis.per_round)}, "
                  f"avg_per_round={analysis.average_tokens_per_round}")

4. **Debugging**: Identify problematic messages:

   .. code-block:: python

      analysis = history.analyze_tokens(tokenizer)
      if analysis.max_message_tokens > 1000:
          # Find the heavy message
          for role, preview, tokens in analysis.per_message:
              if tokens > 1000:
                  print(f"Large message: {role} - {tokens} tokens")

API Reference
-------------

.. autoclass:: lexilux.chat.history.TokenAnalysis
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: lexilux.chat.history.ChatHistory
   :members: count_tokens, count_tokens_per_round, count_tokens_by_role, analyze_tokens
   :noindex:

See Also
--------

* :doc:`chat_history` - Complete guide on history management
* :doc:`api_reference/chat` - API reference for ChatHistory

