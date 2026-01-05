"""
Continue functionality for chat completions.

Provides ChatContinue class for handling continuation requests when generation
is stopped due to max_tokens limit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, overload

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
    @overload
    def continue_request(
        chat: Chat,
        last_result: ChatResult,
        *,
        history: ChatHistory | None = None,
        add_continue_prompt: bool = True,
        continue_prompt: str = "continue",
        max_continues: int = 1,
        auto_merge: Literal[True] = True,
        **params: Any,
    ) -> ChatResult: ...

    @staticmethod
    @overload
    def continue_request(
        chat: Chat,
        last_result: ChatResult,
        *,
        history: ChatHistory | None = None,
        add_continue_prompt: bool = True,
        continue_prompt: str = "continue",
        max_continues: int = 1,
        auto_merge: Literal[False],
        **params: Any,
    ) -> list[ChatResult]: ...

    @staticmethod
    def continue_request(
        chat: Chat,
        last_result: ChatResult,
        *,
        history: ChatHistory | None = None,
        add_continue_prompt: bool = True,
        continue_prompt: str = "continue",
        max_continues: int = 1,
        auto_merge: bool = True,
        **params: Any,
    ) -> ChatResult | list[ChatResult]:
        """
        Continue generation request (enhanced version).

        Automatically handles continuation when finish_reason == "length", with support
        for automatic history retrieval, multiple continues, and automatic merging.

        Args:
            chat: Chat client instance.
            last_result: Last result (must have finish_reason == "length").
            history: Conversation history (optional). If None and chat.auto_history=True,
                automatically retrieved from chat.get_history().
            add_continue_prompt: Whether to add a user continue instruction round.
            continue_prompt: User prompt when add_continue_prompt=True.
            max_continues: Maximum number of continuation attempts. If result is still
                truncated after max_continues, returns merged result (if auto_merge=True)
                or list of results (if auto_merge=False).
            auto_merge: If True, automatically merge all results into a single ChatResult.
                If False, returns a list of all results [last_result, continue_result1, ...].
            **params: Additional parameters to pass to chat (temperature, max_tokens, etc.).

        Returns:
            If auto_merge=True: Merged ChatResult with all continuation results combined.
            If auto_merge=False: List of ChatResult instances [last_result, continue_result1, ...].

        Raises:
            ValueError: If last_result.finish_reason != "length" or history is required but not available.

        Examples:
            Basic usage (automatic history retrieval):
            >>> result = chat("Write a long story", max_tokens=50)
            >>> if result.finish_reason == "length":
            ...     full_result = ChatContinue.continue_request(chat, result)
            ...     print(full_result.text)  # Complete merged text

            Multiple continues:
            >>> result = chat("Very long story", max_tokens=30)
            >>> if result.finish_reason == "length":
            ...     full_result = ChatContinue.continue_request(chat, result, max_continues=3)

            Get all intermediate results:
            >>> result = chat("Story", max_tokens=50)
            >>> if result.finish_reason == "length":
            ...     all_results = ChatContinue.continue_request(chat, result, auto_merge=False)
            ...     # all_results = [result, continue_result1, continue_result2, ...]
        """

        if last_result.finish_reason != "length":
            raise ValueError(
                f"continue_request requires finish_reason='length', "
                f"got '{last_result.finish_reason}'"
            )

        # Auto-retrieve history if not provided
        if history is None:
            if chat.auto_history:
                history = chat.get_history()
                if history is None:
                    raise ValueError(
                        "History not available. Either provide history manually "
                        "or ensure auto_history is enabled and chat was called."
                    )
            else:
                raise ValueError(
                    "History is required when auto_history=False. "
                    "Provide history manually or enable auto_history."
                )

        all_results = [last_result]
        current_result = last_result
        continue_count = 0

        while current_result.finish_reason == "length" and continue_count < max_continues:
            continue_count += 1

            # Execute single continue request
            if add_continue_prompt:
                history.add_user(continue_prompt)

            continue_result = chat(history.get_messages(), **params)
            all_results.append(continue_result)
            current_result = continue_result

            # Update history (if not using auto_history, manually update)
            if not chat.auto_history:
                history.append_result(continue_result)

        # Check if still truncated after max_continues
        if current_result.finish_reason == "length":
            if auto_merge:
                # Return merged result even if truncated
                return ChatContinue.merge_results(*all_results)
            else:
                # Return all results, let user decide
                return all_results

        # Merge results if auto_merge
        if auto_merge:
            if len(all_results) == 1:
                return all_results[0]
            return ChatContinue.merge_results(*all_results)
        else:
            return all_results

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
