Tokenizer Module
================

The Tokenizer module provides local tokenization functionality using the HuggingFace ``transformers`` library.

.. note::
   This module requires optional dependencies. Install with:
   ``pip install lexilux[tokenizer]`` or ``pip install lexilux[token]``

   If you try to use ``Tokenizer`` without installing these dependencies, you'll get a clear error message with installation instructions.

Features
--------

* **Multiple modes**: Online, auto-offline, and force-offline modes
* **Automatic model downloading**: Downloads models automatically (in online/auto-offline modes)
* **Local caching**: Uses HuggingFace cache for offline access
* **Flexible input**: Supports single text or batch tokenization
* **Usage tracking**: Provides token count statistics

.. automodule:: lexilux.tokenizer
   :members:
   :undoc-members:
   :show-inheritance:

See Also
--------

* :doc:`../installation` - Installation instructions including optional dependencies
* :doc:`../examples/tokenizer` - Tokenizer usage examples

