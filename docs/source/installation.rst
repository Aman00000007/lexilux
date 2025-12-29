Installation
=============

Quick Install
-------------

Install Lexilux with pip:

.. code-block:: bash

   pip install lexilux

With Tokenizer Support
----------------------

To use the Tokenizer feature, install with the optional ``tokenizer`` extra:

.. code-block:: bash

   pip install lexilux[tokenizer]

This will install the required ``transformers`` and ``tokenizers`` libraries.

Development Install
-------------------

For development with all dependencies:

.. code-block:: bash

   pip install -e ".[dev]"

Or using Makefile:

.. code-block:: bash

   make dev-install

Requirements
------------

* Python 3.7+
* requests>=2.28.0

Optional Dependencies
---------------------

* transformers>=4.30.0 (for Tokenizer)
* tokenizers>=0.13.0 (for Tokenizer)

