"""
Lexilux - Unified LLM API client library

Provides Chat, Embedding, Rerank, and Tokenizer support with a simple, function-like API.
"""

from lexilux.chat import Chat, ChatParams, ChatResult, ChatStreamChunk
from lexilux.embed import Embed, EmbedResult
from lexilux.embed_params import EmbedParams
from lexilux.rerank import Rerank, RerankResult
from lexilux.tokenizer import Tokenizer, TokenizeResult, TokenizerMode
from lexilux.usage import ResultBase, Usage

__all__ = [
    # Usage
    "Usage",
    "ResultBase",
    # Chat
    "Chat",
    "ChatResult",
    "ChatStreamChunk",
    "ChatParams",
    # Embed
    "Embed",
    "EmbedResult",
    "EmbedParams",
    # Rerank
    "Rerank",
    "RerankResult",
    # Tokenizer
    "Tokenizer",
    "TokenizeResult",
    "TokenizerMode",
]

__version__ = "0.4.0"
