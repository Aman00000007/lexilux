Quick Start
===========

This guide will help you get started with Lexilux in minutes.

Chat
----

Basic chat completion:

.. code-block:: python

   from lexilux import Chat

   chat = Chat(
       base_url="https://api.example.com/v1",
       api_key="your-key",
       model="gpt-4"
   )

   result = chat("Hello, world!")
   print(result.text)
   print(result.usage.total_tokens)

Streaming:

.. code-block:: python

   for chunk in chat.stream("Tell me a joke"):
       print(chunk.delta, end="")
       if chunk.done:
           print(f"\nUsage: {chunk.usage.total_tokens}")

Embedding
---------

Single text:

.. code-block:: python

   from lexilux import Embed

   embed = Embed(
       base_url="https://api.example.com/v1",
       api_key="your-key",
       model="text-embedding-ada-002"
   )

   result = embed("Hello, world!")
   vector = result.vectors  # List[float]

Batch:

.. code-block:: python

   result = embed(["text1", "text2"])
   vectors = result.vectors  # List[List[float]]

Rerank
------

.. code-block:: python

   from lexilux import Rerank

   rerank = Rerank(
       base_url="https://api.example.com/v1",
       api_key="your-key",
       model="rerank-model"
   )

   result = rerank("python http", ["urllib", "requests", "httpx"])
   ranked = result.results  # List[Tuple[int, float]]

Tokenizer
---------

.. note::
   The Tokenizer feature requires optional dependencies. Install with:
   ``pip install lexilux[tokenizer]`` or ``pip install lexilux[token]``

.. code-block:: python

   from lexilux import Tokenizer

   # Auto-offline mode (recommended)
   tokenizer = Tokenizer("Qwen/Qwen2.5-7B-Instruct", mode="auto_offline")

   result = tokenizer("Hello, world!")
   print(result.usage.input_tokens)
   print(result.input_ids)

Next Steps
----------

* :doc:`api_reference/index` - Complete API reference
* :doc:`examples/index` - More examples

