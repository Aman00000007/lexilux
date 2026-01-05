Auto History Examples
======================

This section provides practical examples of using the automatic history management feature.

Basic Conversation
------------------

Simple multi-turn conversation with automatic history:

.. code-block:: python

   from lexilux import Chat

   # Enable auto_history
   chat = Chat(
       base_url="https://api.example.com/v1",
       api_key="your-key",
       model="gpt-4",
       auto_history=True,
   )

   # Just chat - history is automatically recorded
   result1 = chat("What is Python?")
   result2 = chat("How do I install it?")
   result3 = chat("Show me a simple example")

   # Get complete conversation history
   history = chat.get_history()
   print(f"Conversation has {len(history.messages)} messages")
   print(f"Total rounds: {len(history._get_rounds())}")

   # Export conversation
   from lexilux.chat import ChatHistoryFormatter
   ChatHistoryFormatter.save(history, "python_tutorial.md")

Conversation with System Message
--------------------------------

Using system message for consistent behavior:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # First call sets system message
   result1 = chat(
       "Hello",
       system="You are a helpful Python tutor. Always provide code examples."
   )

   # System message is preserved in history
   history = chat.get_history()
   assert history.system == "You are a helpful Python tutor. Always provide code examples."

   # Subsequent calls maintain system context
   result2 = chat("What is a list?")
   result3 = chat("How do I iterate over it?")

   # All conversations share the same system message
   history = chat.get_history()
   assert history.system is not None

Streaming with Auto History
----------------------------

Auto history works seamlessly with streaming:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # Streaming call - history updates in real-time
   iterator = chat.stream("Write a detailed explanation of recursion")
   
   for chunk in iterator:
       print(chunk.delta, end="", flush=True)
       # History is being updated automatically

   # After streaming, history contains complete response
   history = chat.get_history()
   full_response = history.messages[-1]["content"]
   print(f"\n\nComplete response: {len(full_response)} characters")

Context Window Management
--------------------------

Managing context windows with auto history:

.. code-block:: python

   from lexilux import Chat, Tokenizer

   chat = Chat(..., auto_history=True)
   tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct")

   # Have a long conversation
   for i in range(10):
       chat(f"Question {i}")

   # Check token usage
   history = chat.get_history()
   analysis = history.analyze_tokens(tokenizer)

   if analysis.total_tokens > 4000:
       print(f"History too long: {analysis.total_tokens} tokens")
       
       # Truncate to keep most recent rounds
       truncated = history.truncate_by_rounds(
           tokenizer, max_tokens=4000, keep_system=True
       )
       
       # Update auto history
       chat._history = truncated
       
       print(f"Truncated to {truncated.analyze_tokens(tokenizer).total_tokens} tokens")

Session Management
------------------

Starting new conversation sessions:

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # Session 1: Python questions
   chat("What is Python?")
   chat("How do I use lists?")
   
   # Save session 1
   history1 = chat.get_history()
   with open("session1_python.json", "w") as f:
       f.write(history1.to_json())

   # Start new session
   chat.clear_history()
   
   # Session 2: JavaScript questions
   chat("What is JavaScript?")
   chat("How do I use arrays?")
   
   # Save session 2
   history2 = chat.get_history()
   with open("session2_javascript.json", "w") as f:
       f.write(history2.to_json())

Integration with Other Features
-------------------------------

Using auto history with other features:

.. code-block:: python

   from lexilux import Chat, Tokenizer
   from lexilux.chat import ChatHistoryFormatter, get_statistics

   chat = Chat(..., auto_history=True)
   tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct")

   # Build conversation
   chat("What is machine learning?")
   chat("Explain neural networks")
   chat("How do I get started?")

   # Get history
   history = chat.get_history()

   # Format and export
   md = ChatHistoryFormatter.to_markdown(history, show_round_numbers=True)
   with open("ml_conversation.md", "w") as f:
       f.write(md)

   # Get comprehensive statistics
   stats = get_statistics(history, tokenizer=tokenizer)
   print(f"Total tokens: {stats['total_tokens']}")
   print(f"Average tokens per round: {stats['average_tokens_per_round']}")
   print(f"Token distribution: {stats['tokens_by_role']}")

   # Analyze token usage
   analysis = history.analyze_tokens(tokenizer)
   print(f"User tokens: {analysis.user_tokens}")
   print(f"Assistant tokens: {analysis.assistant_tokens}")

Common Patterns
---------------

Pattern 1: Simple Q&A Bot
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   chat = Chat(..., auto_history=True)

   while True:
       question = input("You: ")
       if question.lower() == "quit":
           break
       
       result = chat(question)
       print(f"Bot: {result.text}")

   # Save conversation at end
   history = chat.get_history()
   ChatHistoryFormatter.save(history, "conversation.md")

Pattern 2: Research Assistant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # Research topic
   chat("What is quantum computing?", system="You are a research assistant")
   chat("Explain qubits")
   chat("What are the applications?")

   # Get research notes
   history = chat.get_history()
   notes = ChatHistoryFormatter.to_markdown(history)
   print(notes)

Pattern 3: Code Tutor
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   chat = Chat(..., auto_history=True)

   # Learning session
   chat("Teach me Python", system="You are a Python tutor")
   chat("What is a function?")
   chat("Show me an example")
   chat("How do I use parameters?")

   # Review session
   history = chat.get_history()
   print("Session summary:")
   for idx, round_msgs in enumerate(history._get_rounds(), 1):
       user_msg = next(m for m in round_msgs if m["role"] == "user")
       print(f"Q{idx}: {user_msg['content']}")

