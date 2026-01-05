"""
Chat API exceptions.

Provides specific exception types for chat-related errors to enable better
error handling and recovery.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lexilux.chat.models import ChatResult, ChatStreamChunk
else:
    from lexilux.chat.models import ChatResult, ChatStreamChunk


class ChatStreamInterruptedError(Exception):
    """
    Exception raised when a streaming request is interrupted.

    This exception is raised when a streaming request is interrupted before
    receiving a completion signal (done=True chunk). It contains information
    about the partial result that was received before the interruption.

    Attributes:
        partial_result: Partial ChatResult if available.
        received_chunks: List of chunks received before interruption.
        original_error: The original exception that caused the interruption.

    Examples:
        >>> try:
        ...     iterator = chat.stream("Long response")
        ...     for chunk in iterator:
        ...         print(chunk.delta)
        ... except ChatStreamInterruptedError as e:
        ...     print(f"Interrupted. Received: {len(e.get_partial_text())} chars")
        ...     # Can try to recover using ChatContinue or retry
    """

    def __init__(
        self,
        message: str,
        partial_result: ChatResult | None = None,
        received_chunks: list[ChatStreamChunk] | None = None,
        original_error: Exception | None = None,
    ):
        """
        Initialize ChatStreamInterruptedError.

        Args:
            message: Error message.
            partial_result: Partial ChatResult if available.
            received_chunks: List of chunks received before interruption.
            original_error: The original exception that caused the interruption.
        """
        super().__init__(message)
        self.partial_result = partial_result
        self.received_chunks = received_chunks or []
        self.original_error = original_error

    def get_partial_text(self) -> str:
        """
        Get the partial text that was received before interruption.

        Returns:
            Partial text content.
        """
        if self.partial_result:
            return self.partial_result.text
        return "".join(chunk.delta for chunk in self.received_chunks)

    def get_partial_result(self) -> ChatResult:
        """
        Get a ChatResult object representing the partial result.

        Returns:
            ChatResult with partial text and finish_reason="length" (assumed truncated).
        """
        if self.partial_result:
            return self.partial_result

        from lexilux.usage import Usage

        partial_text = self.get_partial_text()
        return ChatResult(
            text=partial_text,
            usage=Usage(),
            finish_reason="length",  # Assume truncated
        )


class ChatIncompleteResponseError(Exception):
    """
    Exception raised when a response is still incomplete after maximum continues.

    This exception is raised when using continue functionality and the response
    is still truncated (finish_reason == "length") after reaching the maximum
    number of continuation attempts.

    Attributes:
        final_result: The final (possibly incomplete) ChatResult.
        continue_count: Number of continuation attempts made.
        max_continues: Maximum number of continues allowed.

    Examples:
        >>> try:
        ...     result = chat.complete("Very long response", max_tokens=50, max_continues=3)
        ... except ChatIncompleteResponseError as e:
        ...     print(f"Still incomplete after {e.continue_count} continues")
        ...     print(f"Received: {len(e.final_result.text)} chars")
    """

    def __init__(
        self,
        message: str,
        final_result: ChatResult,
        continue_count: int,
        max_continues: int,
    ):
        """
        Initialize ChatIncompleteResponseError.

        Args:
            message: Error message.
            final_result: The final (possibly incomplete) ChatResult.
            continue_count: Number of continuation attempts made.
            max_continues: Maximum number of continues allowed.
        """
        super().__init__(message)
        self.final_result = final_result
        self.continue_count = continue_count
        self.max_continues = max_continues

    def get_final_text(self) -> str:
        """
        Get the final (possibly incomplete) text.

        Returns:
            Final text content.
        """
        return self.final_result.text
