"""
Continue functionality for chat completions.

Provides ChatContinue class for handling continuation requests when generation
is stopped due to max_tokens limit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lexilux.chat.history import ChatHistory
from lexilux.chat.models import ChatResult
from lexilux.usage import Usage

if TYPE_CHECKING:
    from lexilux.chat.client import Chat


class ChatContinue:
    """
    Continue functionality handler (user is responsible for determining if continue is needed).

    This class provides utilities for continuing generation when finish_reason == "length".
    The user must check finish_reason and decide when to continue.
    """

    @staticmethod
    def continue_request(
        chat: Chat,
        history: ChatHistory,
        last_result: ChatResult,
        *,
        add_continue_prompt: bool = True,
        continue_prompt: str = "continue",
        **params: Any,
    ) -> ChatResult:
        """
        Make a continue request to extend generation.

        Args:
            chat: Chat client instance.
            history: Conversation history (contains incomplete assistant message).
            last_result: Last result (finish_reason == "length").
            add_continue_prompt: Whether to add a user continue instruction round.
                - True: Add a user message (e.g., "continue"), then continue generation.
                - False: Send original history directly, last round is incomplete assistant.
            continue_prompt: User prompt when add_continue_prompt=True.
            **params: Additional parameters to pass to chat (temperature, max_tokens, etc.).

        Returns:
            New result (needs to be merged with last_result using merge_results).

        Note:
            - User must check finish_reason == "length" before calling this.
            - User must merge results using merge_results().

        Examples:
            >>> result = chat("Write a long story", max_tokens=50)
            >>> history = ChatHistory.from_chat_result("Write a long story", result)
            >>> if result.finish_reason == "length":
            ...     continue_result = ChatContinue.continue_request(
            ...         chat, history, result,
            ...         add_continue_prompt=True,
            ...         continue_prompt="continue"
            ...     )
            ...     full_result = ChatContinue.merge_results(result, continue_result)
        """
        if add_continue_prompt:
            # Add user continue message
            history.add_user(continue_prompt)
            # Make request with updated history
            return chat(history.get_messages(), **params)
        else:
            # Send original history directly (last assistant message is incomplete)
            return chat(history.get_messages(), **params)

    @staticmethod
    def merge_results(*results: ChatResult) -> ChatResult:
        """
        Merge multiple ChatResult instances into a single result.

        Args:
            *results: Multiple ChatResult instances to merge in order.

        Returns:
            Merged ChatResult with combined text and usage.

        Examples:
            >>> result1 = chat("Write a story", max_tokens=50)
            >>> result2 = chat.continue_request(...)
            >>> full_result = ChatContinue.merge_results(result1, result2)
        """
        if not results:
            raise ValueError("At least one result is required")

        if len(results) == 1:
            return results[0]

        # Merge text
        merged_text = "".join(r.text for r in results)

        # Merge usage
        total_input_tokens = sum(
            r.usage.input_tokens or 0 for r in results if r.usage.input_tokens is not None
        )
        total_output_tokens = sum(
            r.usage.output_tokens or 0 for r in results if r.usage.output_tokens is not None
        )
        total_tokens = sum(
            r.usage.total_tokens or 0 for r in results if r.usage.total_tokens is not None
        )

        # Use last result's finish_reason (most recent)
        finish_reason = results[-1].finish_reason

        # Merge raw data (combine details)
        merged_raw = {}
        for r in results:
            if r.raw:
                merged_raw.update(r.raw)

        merged_usage = Usage(
            input_tokens=total_input_tokens if total_input_tokens > 0 else None,
            output_tokens=total_output_tokens if total_output_tokens > 0 else None,
            total_tokens=total_tokens if total_tokens > 0 else None,
            details=merged_raw,
        )

        return ChatResult(
            text=merged_text,
            usage=merged_usage,
            finish_reason=finish_reason,
            raw=merged_raw,
        )
