"""
Chat API client.

Provides a simple, function-like API for chat completions with support for
both non-streaming and streaming responses.
"""

from __future__ import annotations

import json
from typing import Iterator, Sequence

import requests

from lexilux.chat.history import ChatHistory
from lexilux.chat.models import ChatResult, ChatStreamChunk, MessagesLike
from lexilux.chat.params import ChatParams
from lexilux.chat.streaming import StreamingIterator, StreamingResult
from lexilux.chat.utils import normalize_finish_reason, normalize_messages, parse_usage
from lexilux.usage import Json, Usage


class Chat:
    """
    Chat API client.

    Provides a simple, function-like API for chat completions with support for
    both non-streaming and streaming responses.

    Examples:
        >>> chat = Chat(base_url="https://api.example.com/v1", api_key="key", model="gpt-4")
        >>> result = chat("Hello, world!")
        >>> print(result.text)

        >>> # Streaming
        >>> for chunk in chat.stream("Tell me a joke"):
        ...     print(chunk.delta, end="")

        >>> # With system message
        >>> result = chat("What is Python?", system="You are a helpful assistant")
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        model: str | None = None,
        timeout_s: float = 60.0,
        headers: dict[str, str] | None = None,
        proxies: dict[str, str] | None = None,
        auto_history: bool = False,
    ):
        """
        Initialize Chat client.

        Args:
            base_url: Base URL for the API (e.g., "https://api.openai.com/v1").
            api_key: API key for authentication (optional if provided in headers).
            model: Default model to use (can be overridden in __call__).
            timeout_s: Request timeout in seconds.
            headers: Additional headers to include in requests.
            proxies: Optional proxy configuration dict (e.g., {"http": "http://proxy:port"}).
                    If None, uses environment variables (HTTP_PROXY, HTTPS_PROXY).
                    To disable proxies, pass {}.
            auto_history: Whether to automatically record conversation history.
                    If True, history is automatically maintained and can be accessed via get_history().
                    Default: False
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self.headers = headers or {}
        self.proxies = proxies  # None means use environment variables
        self.auto_history = auto_history
        self._history: ChatHistory | None = None  # Auto-recorded history

        # Set default headers
        if self.api_key:
            self.headers.setdefault("Authorization", f"Bearer {self.api_key}")
        self.headers.setdefault("Content-Type", "application/json")

    def __call__(
        self,
        messages: MessagesLike,
        *,
        model: str | None = None,
        system: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        stop: str | Sequence[str] | None = None,
        presence_penalty: float | None = None,
        frequency_penalty: float | None = None,
        logit_bias: dict[int, float] | None = None,
        user: str | None = None,
        n: int | None = None,
        params: ChatParams | None = None,
        extra: Json | None = None,
        return_raw: bool = False,
    ) -> ChatResult:
        """
        Make a non-streaming chat completion request.

        Supports both direct parameter passing (backward compatible) and ChatParams
        dataclass for structured configuration.

        Args:
            messages: Messages in various formats (str, list of str, list of dict).
            model: Model to use (overrides default).
            system: Optional system message.
            temperature: Sampling temperature (0.0-2.0). Higher values make output
                more random, lower values more focused. Default: 0.7
            top_p: Nucleus sampling parameter (0.0-1.0). Alternative to temperature.
                Default: 1.0
            max_tokens: Maximum tokens to generate. Default: None (no limit)
            stop: Stop sequences (str or list of str). API stops at these sequences.
            presence_penalty: Penalty for new topics (-2.0 to 2.0). Positive values
                encourage new topics. Default: 0.0
            frequency_penalty: Penalty for repetition (-2.0 to 2.0). Positive values
                reduce repetition. Default: 0.0
            logit_bias: Modify token likelihood. Dict mapping token IDs to bias
                values (-100 to 100). Default: None
            user: Unique identifier for end-user (for monitoring/rate limiting).
            n: Number of chat completion choices to generate. Default: 1
            params: ChatParams dataclass instance. If provided, overrides individual
                parameters above. Useful for structured configuration.
            extra: Additional custom parameters for non-standard providers.
                Merged with params if both are provided.
            return_raw: Whether to include full raw response.

        Returns:
            ChatResult with text and usage.

        Raises:
            requests.RequestException: On network or HTTP errors (connection timeout,
                connection reset, DNS resolution failure, etc.). When this exception
                is raised during streaming, the iterator will stop and no more chunks
                will be yielded. If the stream was interrupted before receiving a
                done=True chunk, finish_reason will not be available. This indicates
                a network/connection problem, not a normal completion.
            ValueError: On invalid input or response format.

        Examples:
            Basic usage (backward compatible):
            >>> result = chat("Hello", temperature=0.5, max_tokens=100)

            Using ChatParams:
            >>> from lexilux import ChatParams
            >>> params = ChatParams(temperature=0.5, max_tokens=100)
            >>> result = chat("Hello", params=params)

            Combining params and extra:
            >>> result = chat("Hello", params=params, extra={"custom": "value"})
        """
        # Normalize messages
        normalized_messages = normalize_messages(messages, system=system)

        # Prepare request
        model = model or self.model
        if not model:
            raise ValueError("Model must be specified (either in __init__ or __call__)")

        # Build parameters from ChatParams or individual args
        if params is not None:
            # Use ChatParams as base, override with individual args if provided
            param_dict = params.to_dict(exclude_none=True)
            # Override with explicit parameters if provided
            if temperature is not None:
                param_dict["temperature"] = temperature
            if top_p is not None:
                param_dict["top_p"] = top_p
            if max_tokens is not None:
                param_dict["max_tokens"] = max_tokens
            if stop is not None:
                if isinstance(stop, str):
                    param_dict["stop"] = [stop]
                else:
                    param_dict["stop"] = list(stop)
            if presence_penalty is not None:
                param_dict["presence_penalty"] = presence_penalty
            if frequency_penalty is not None:
                param_dict["frequency_penalty"] = frequency_penalty
            if logit_bias is not None:
                param_dict["logit_bias"] = logit_bias
            if user is not None:
                param_dict["user"] = user
            if n is not None:
                param_dict["n"] = n
        else:
            # Build from individual parameters (backward compatible)
            param_dict: Json = {}
            if temperature is not None:
                param_dict["temperature"] = temperature
            else:
                param_dict["temperature"] = 0.7  # Default
            if top_p is not None:
                param_dict["top_p"] = top_p
            if max_tokens is not None:
                param_dict["max_tokens"] = max_tokens
            if stop is not None:
                if isinstance(stop, str):
                    param_dict["stop"] = [stop]
                else:
                    param_dict["stop"] = list(stop)
            if presence_penalty is not None:
                param_dict["presence_penalty"] = presence_penalty
            if frequency_penalty is not None:
                param_dict["frequency_penalty"] = frequency_penalty
            if logit_bias is not None:
                param_dict["logit_bias"] = logit_bias
            if user is not None:
                param_dict["user"] = user
            if n is not None:
                param_dict["n"] = n

        # Build payload
        payload: Json = {
            "model": model,
            "messages": normalized_messages,
            **param_dict,
        }

        # Merge extra parameters (highest priority)
        if extra:
            payload.update(extra)

        # Make request
        url = f"{self.base_url}/chat/completions"
        response = requests.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout_s,
            proxies=self.proxies,
        )
        response.raise_for_status()

        response_data = response.json()

        # Parse response
        choices = response_data.get("choices", [])
        if not choices:
            raise ValueError("No choices in API response")

        choice = choices[0]
        if not isinstance(choice, dict):
            raise ValueError(f"Invalid choice format: expected dict, got {type(choice)}")

        # Extract text content
        message = choice.get("message", {})
        if not isinstance(message, dict):
            message = {}
        text = message.get("content", "") or ""

        # Normalize finish_reason (defensive against invalid implementations)
        finish_reason = normalize_finish_reason(choice.get("finish_reason"))

        # Parse usage
        usage = parse_usage(response_data)

        # Create result
        result = ChatResult(
            text=text,
            usage=usage,
            finish_reason=finish_reason,
            raw=response_data if return_raw else {},
        )

        # Auto-record history if enabled
        if self.auto_history:
            if self._history is None:
                # Create new history from messages
                self._history = ChatHistory.from_messages(normalized_messages)
            else:
                # Extract new user messages and add to history
                for msg in normalized_messages:
                    if msg.get("role") == "user":
                        self._history.add_user(msg.get("content", ""))
            # Add assistant response
            self._history.append_result(result)

        return result

    def stream(
        self,
        messages: MessagesLike,
        *,
        model: str | None = None,
        system: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        stop: str | Sequence[str] | None = None,
        presence_penalty: float | None = None,
        frequency_penalty: float | None = None,
        logit_bias: dict[int, float] | None = None,
        user: str | None = None,
        params: ChatParams | None = None,
        extra: Json | None = None,
        include_usage: bool = True,
        return_raw_events: bool = False,
        auto_history: bool | None = None,
    ) -> StreamingIterator:
        """
        Make a streaming chat completion request.

        Supports both direct parameter passing (backward compatible) and ChatParams
        dataclass for structured configuration.

        Args:
            messages: Messages in various formats.
            model: Model to use (overrides default).
            system: Optional system message.
            temperature: Sampling temperature (0.0-2.0). Higher values make output
                more random, lower values more focused. Default: 0.7
            top_p: Nucleus sampling parameter (0.0-1.0). Alternative to temperature.
                Default: 1.0
            max_tokens: Maximum tokens to generate. Default: None (no limit)
            stop: Stop sequences (str or list of str). API stops at these sequences.
            presence_penalty: Penalty for new topics (-2.0 to 2.0). Positive values
                encourage new topics. Default: 0.0
            frequency_penalty: Penalty for repetition (-2.0 to 2.0). Positive values
                reduce repetition. Default: 0.0
            logit_bias: Modify token likelihood. Dict mapping token IDs to bias
                values (-100 to 100). Default: None
            user: Unique identifier for end-user (for monitoring/rate limiting).
            params: ChatParams dataclass instance. If provided, overrides individual
                parameters above. Useful for structured configuration.
            extra: Additional custom parameters for non-standard providers.
                Merged with params if both are provided.
            include_usage: Whether to request usage in the final chunk (OpenAI-style).
            return_raw_events: Whether to include raw event data in chunks.
            auto_history: Override instance auto_history setting (optional).
                    If None, uses instance setting.

        Returns:
            StreamingIterator: Iterator that yields ChatStreamChunk objects.
                    Access accumulated result via iterator.result.

        Raises:
            requests.RequestException: On network or HTTP errors (connection timeout,
                connection reset, DNS resolution failure, etc.). When this exception
                is raised during streaming, the iterator will stop and no more chunks
                will be yielded. If the stream was interrupted before receiving a
                done=True chunk, finish_reason will not be available. This indicates
                a network/connection problem, not a normal completion.
            ValueError: On invalid input or response format.

        Examples:
            Basic streaming (backward compatible):
            >>> for chunk in chat.stream("Hello", temperature=0.5):
            ...     print(chunk.delta, end="")

            Using ChatParams:
            >>> from lexilux import ChatParams
            >>> params = ChatParams(temperature=0.5, max_tokens=100)
            >>> for chunk in chat.stream("Hello", params=params):
            ...     print(chunk.delta, end="")

            With auto_history:
            >>> iterator = chat.stream("Hello", auto_history=True)
            >>> for chunk in iterator:
            ...     print(chunk.delta, end="")
            >>> history = chat.get_history()  # Contains complete conversation
        """
        # Normalize messages
        normalized_messages = normalize_messages(messages, system=system)

        # Prepare request
        model = model or self.model
        if not model:
            raise ValueError("Model must be specified (either in __init__ or __call__)")

        # Build parameters from ChatParams or individual args
        if params is not None:
            # Use ChatParams as base, override with individual args if provided
            param_dict = params.to_dict(exclude_none=True)
            # Override with explicit parameters if provided
            if temperature is not None:
                param_dict["temperature"] = temperature
            if top_p is not None:
                param_dict["top_p"] = top_p
            if max_tokens is not None:
                param_dict["max_tokens"] = max_tokens
            if stop is not None:
                if isinstance(stop, str):
                    param_dict["stop"] = [stop]
                else:
                    param_dict["stop"] = list(stop)
            if presence_penalty is not None:
                param_dict["presence_penalty"] = presence_penalty
            if frequency_penalty is not None:
                param_dict["frequency_penalty"] = frequency_penalty
            if logit_bias is not None:
                param_dict["logit_bias"] = logit_bias
            if user is not None:
                param_dict["user"] = user
        else:
            # Build from individual parameters (backward compatible)
            param_dict: Json = {}
            if temperature is not None:
                param_dict["temperature"] = temperature
            else:
                param_dict["temperature"] = 0.7  # Default
            if top_p is not None:
                param_dict["top_p"] = top_p
            if max_tokens is not None:
                param_dict["max_tokens"] = max_tokens
            if stop is not None:
                if isinstance(stop, str):
                    param_dict["stop"] = [stop]
                else:
                    param_dict["stop"] = list(stop)
            if presence_penalty is not None:
                param_dict["presence_penalty"] = presence_penalty
            if frequency_penalty is not None:
                param_dict["frequency_penalty"] = frequency_penalty
            if logit_bias is not None:
                param_dict["logit_bias"] = logit_bias
            if user is not None:
                param_dict["user"] = user

        # Build payload
        payload: Json = {
            "model": model,
            "messages": normalized_messages,
            "stream": True,
            **param_dict,
        }

        if include_usage:
            # OpenAI-style: request usage in final chunk
            payload["stream_options"] = {"include_usage": True}

        # Merge extra parameters (highest priority)
        if extra:
            payload.update(extra)

        # Make streaming request
        url = f"{self.base_url}/chat/completions"
        response = requests.post(
            url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout_s,
            stream=True,
            proxies=self.proxies,
        )
        response.raise_for_status()

        # Create internal chunk generator
        def _chunk_generator() -> Iterator[ChatStreamChunk]:
            """Internal generator for streaming chunks."""
            accumulated_text = ""
            final_usage: Usage | None = None

            for line in response.iter_lines():
                if not line:
                    continue

                line_str = line.decode("utf-8")
                if not line_str.startswith("data: "):
                    continue

                data_str = line_str[6:]  # Remove "data: " prefix
                if data_str == "[DONE]":
                    # Final chunk with usage (if include_usage=True)
                    if final_usage is None:
                        # No usage received, create empty usage
                        final_usage = Usage()
                    yield ChatStreamChunk(
                        delta="",
                        done=True,
                        usage=final_usage,
                        finish_reason=None,  # [DONE] doesn't provide finish_reason
                        raw={"done": True} if return_raw_events else {},
                    )
                    break

                try:
                    event_data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                # Parse event
                choices = event_data.get("choices", [])
                if not choices:
                    continue

                choice = choices[0]
                if not isinstance(choice, dict):
                    # Skip invalid choice format
                    continue

                delta = choice.get("delta") or {}
                if not isinstance(delta, dict):
                    delta = {}
                content = delta.get("content") or ""

                # Normalize finish_reason (defensive against invalid implementations)
                finish_reason = normalize_finish_reason(choice.get("finish_reason"))
                # done is True when finish_reason is a non-empty string
                done = finish_reason is not None

                # Accumulate text
                accumulated_text += content

                # Parse usage if present (usually only in final chunk when include_usage=True)
                usage = None
                if "usage" in event_data:
                    usage = parse_usage(event_data)
                    final_usage = usage
                elif done and final_usage is None:
                    # Final chunk but no usage yet - create empty usage
                    usage = Usage()
                    final_usage = usage
                else:
                    # Intermediate chunk - empty usage
                    usage = Usage()

                yield ChatStreamChunk(
                    delta=content,
                    done=done,
                    usage=usage,
                    finish_reason=finish_reason,
                    raw=event_data if return_raw_events else {},
                )

        # Create StreamingIterator
        chunk_iterator = _chunk_generator()
        streaming_iterator = StreamingIterator(chunk_iterator)

        # If auto_history, wrap iterator to update history
        use_auto_history = auto_history if auto_history is not None else self.auto_history
        if use_auto_history:
            streaming_iterator = self._wrap_streaming_with_history(
                streaming_iterator, normalized_messages
            )

        return streaming_iterator

    def _wrap_streaming_with_history(
        self,
        iterator: StreamingIterator,
        messages: list[dict[str, str]],
    ) -> StreamingIterator:
        """
        Wrap streaming iterator to automatically update history.

        Args:
            iterator: StreamingIterator to wrap.
            messages: Normalized messages for this request.

        Returns:
            Wrapped StreamingIterator that updates history on each chunk.
        """
        # Create or update history
        if self._history is None:
            self._history = ChatHistory.from_messages(messages)
        else:
            # Extract new user messages
            new_user_msgs = [m for m in messages if m.get("role") == "user"]
            for msg in new_user_msgs:
                self._history.add_user(msg.get("content", ""))

        # Add assistant message placeholder (will be updated during streaming)
        self._history.add_assistant("")

        # Wrap iterator to update history
        class HistoryUpdatingIterator(StreamingIterator):
            """Iterator wrapper that updates history on each chunk."""

            def __init__(self, base_iterator: StreamingIterator, history: ChatHistory):
                # Initialize with base iterator's internal iterator
                super().__init__(base_iterator._iterator)
                self._base = base_iterator
                self._history = history
                # Use base iterator's result (which is already accumulating)
                self._result = base_iterator.result

            def __iter__(self) -> Iterator[ChatStreamChunk]:
                """Iterate chunks and update history."""
                for chunk in self._base:
                    # Update history's last assistant message with current accumulated text
                    if (
                        self._history.messages
                        and self._history.messages[-1].get("role") == "assistant"
                    ):
                        self._history.messages[-1]["content"] = self.result.text
                    yield chunk

            @property
            def result(self) -> StreamingResult:
                """Get accumulated result."""
                return self._result

        return HistoryUpdatingIterator(iterator, self._history)

    def get_history(self) -> ChatHistory | None:
        """
        Get automatically recorded history (if auto_history=True).

        Returns:
            ChatHistory instance if auto_history is enabled, None otherwise.

        Examples:
            >>> chat = Chat(..., auto_history=True)
            >>> result = chat("Hello")
            >>> history = chat.get_history()  # Contains complete conversation
        """
        return self._history

    def clear_history(self) -> None:
        """
        Clear automatically recorded history.

        Examples:
            >>> chat.clear_history()  # Reset conversation history
        """
        self._history = None

    def chat_with_history(
        self,
        history: ChatHistory,
        **params,
    ) -> ChatResult:
        """
        Make a chat completion request using history.

        Args:
            history: ChatHistory instance to use.
            **params: Additional parameters to pass to __call__.

        Returns:
            ChatResult from the API call.

        Examples:
            >>> history = ChatHistory.from_messages("Hello")
            >>> result = chat.chat_with_history(history, temperature=0.7)
        """
        return self(history.get_messages(), **params)

    def stream_with_history(
        self,
        history: ChatHistory,
        **params,
    ) -> StreamingIterator:
        """
        Make a streaming chat completion request using history.

        Args:
            history: ChatHistory instance to use.
            **params: Additional parameters to pass to stream().

        Returns:
            StreamingIterator for the streaming response.

        Examples:
            >>> history = ChatHistory.from_messages("Hello")
            >>> iterator = chat.stream_with_history(history, temperature=0.7)
            >>> for chunk in iterator:
            ...     print(chunk.delta, end="")
        """
        return self.stream(history.get_messages(), **params)
