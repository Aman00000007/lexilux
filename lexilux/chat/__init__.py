"""
Chat API module.

Provides Chat client, result models, and parameter configuration for chat completions.
"""

from lexilux.chat.client import Chat
from lexilux.chat.continue_ import ChatContinue
from lexilux.chat.exceptions import ChatIncompleteResponseError, ChatStreamInterruptedError
from lexilux.chat.formatters import ChatHistoryFormatter
from lexilux.chat.history import (
    ChatHistory,
    TokenAnalysis,
    filter_by_role,
    get_statistics,
    merge_histories,
    search_content,
)
from lexilux.chat.models import ChatResult, ChatStreamChunk, MessagesLike, Role
from lexilux.chat.params import ChatParams
from lexilux.chat.streaming import StreamingIterator, StreamingResult

__all__ = [
    "Chat",
    "ChatResult",
    "ChatStreamChunk",
    "ChatParams",
    "ChatHistory",
    "ChatHistoryFormatter",
    "ChatContinue",
    "StreamingResult",
    "StreamingIterator",
    "TokenAnalysis",
    "Role",
    "MessageLike",
    "MessagesLike",
    # Exceptions
    "ChatStreamInterruptedError",
    "ChatIncompleteResponseError",
    # Utility functions
    "merge_histories",
    "filter_by_role",
    "search_content",
    "get_statistics",
]
