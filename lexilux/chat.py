"""
Chat API client with streaming support.

Provides a simple, function-like API for chat completions with unified usage tracking.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, Iterator, Literal, Sequence, Union

import requests

from lexilux.usage import Json, ResultBase, Usage

if TYPE_CHECKING:
    pass

# Type aliases
Role = Literal["system", "user", "assistant", "tool"]
MessageLike = Union[str, Dict[str, str]]
MessagesLike = Union[str, Sequence[MessageLike]]


class ChatResult(ResultBase):
    """
    Chat completion result (non-streaming).

    Attributes:
        text: The generated text content.
        finish_reason: Reason why the generation stopped. Possible values:
            - "stop": Model stopped naturally or hit stop sequence
            - "length": Reached max_tokens limit
            - "content_filter": Content was filtered
            - None: Unknown or not provided
        usage: Usage statistics.
        raw: Raw API response.

    Examples:
        >>> result = chat("Hello")
        >>> print(result.text)
        "Hello! How can I help you?"
        >>> print(result.usage.total_tokens)
        42
        >>> print(result.finish_reason)
        "stop"
    """

    def __init__(
        self,
        *,
        text: str,
        usage: Usage,
        finish_reason: str | None = None,
        raw: Json | None = None,
    ):
        """
        Initialize ChatResult.

        Args:
            text: Generated text content.
            usage: Usage statistics.
            finish_reason: Reason why generation stopped.
            raw: Raw API response.
        """
        super().__init__(usage=usage, raw=raw)
        self.text = text
        self.finish_reason = finish_reason

    def __str__(self) -> str:
        """Return the text content when converted to string."""
        return self.text

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ChatResult(text={self.text!r}, finish_reason={self.finish_reason!r}, usage={self.usage!r})"


class ChatStreamChunk(ResultBase):
    """
    Chat streaming chunk.

    Each chunk in a streaming response contains:

    - delta: The incremental text content (may be empty)
    - done: Whether this is the final chunk
    - finish_reason: Reason why generation stopped (only set when done=True).
        Possible values:
        - "stop": Model stopped naturally or hit stop sequence
        - "length": Reached max_tokens limit
        - "content_filter": Content was filtered
        - None: Still generating (intermediate chunks) or unknown
    - usage: Usage statistics (may be empty/None for intermediate chunks,
      complete only in the final chunk when include_usage=True)

    Attributes:
        delta: Incremental text content.
        done: Whether this is the final chunk.
        finish_reason: Reason why generation stopped (None for intermediate chunks).
        usage: Usage statistics (may be incomplete for intermediate chunks).
        raw: Raw chunk data.

    Examples:
        >>> for chunk in chat.stream("Hello"):
        ...     print(chunk.delta, end="")
        ...     if chunk.done:
        ...         print(f"\\nUsage: {chunk.usage.total_tokens}")
        ...         print(f"Finish reason: {chunk.finish_reason}")
    """

    def __init__(
        self,
        *,
        delta: str,
        done: bool,
        usage: Usage,
        finish_reason: str | None = None,
        raw: Json | None = None,
    ):
        """
        Initialize ChatStreamChunk.

        Args:
            delta: Incremental text content.
            done: Whether this is the final chunk.
            usage: Usage statistics.
            finish_reason: Reason why generation stopped.
            raw: Raw chunk data.
        """
        super().__init__(usage=usage, raw=raw)
        self.delta = delta
        self.done = done
        self.finish_reason = finish_reason

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ChatStreamChunk(delta={self.delta!r}, done={self.done}, finish_reason={self.finish_reason!r}, usage={self.usage!r})"


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
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self.headers = headers or {}
        self.proxies = proxies  # None means use environment variables

        # Set default headers
        if self.api_key:
            self.headers.setdefault("Authorization", f"Bearer {self.api_key}")
        self.headers.setdefault("Content-Type", "application/json")

    def _normalize_messages(
        self,
        messages: MessagesLike,
        system: str | None = None,
    ) -> list[dict[str, str]]:
        """
        Normalize messages input to a list of message dictionaries.

        Supports multiple input formats:
        - str: Converted to [{"role": "user", "content": str}]
        - List[Dict]: Used as-is
        - List[str]: Converted to [{"role": "user", "content": str}, ...]

        Args:
            messages: Messages in various formats.
            system: Optional system message to prepend.

        Returns:
            Normalized list of message dictionaries.

        Examples:
            >>> chat._normalize_messages("hi")
            [{"role": "user", "content": "hi"}]

            >>> chat._normalize_messages([{"role": "user", "content": "hi"}])
            [{"role": "user", "content": "hi"}]

            >>> chat._normalize_messages("hi", system="You are helpful")
            [{"role": "system", "content": "You are helpful"}, {"role": "user", "content": "hi"}]
        """
        result: list[dict[str, str]] = []

        # Add system message if provided
        if system:
            result.append({"role": "system", "content": system})

        # Normalize messages
        if isinstance(messages, str):
            # Single string -> single user message
            result.append({"role": "user", "content": messages})
        elif isinstance(messages, (list, tuple)):
            # List of messages
            for msg in messages:
                if isinstance(msg, str):
                    # String in list -> user message
                    result.append({"role": "user", "content": msg})
                elif isinstance(msg, dict):
                    # Dict -> use as-is (should have "role" and "content")
                    if "role" in msg and "content" in msg:
                        result.append({"role": msg["role"], "content": msg["content"]})
                    else:
                        raise ValueError(
                            f"Invalid message dict: {msg}. Must have 'role' and 'content' keys."
                        )
                else:
                    raise ValueError(f"Invalid message type: {type(msg)}. Expected str or dict.")
        else:
            raise ValueError(
                f"Invalid messages type: {type(messages)}. Expected str, list, or tuple."
            )

        return result

    def _parse_usage(self, response_data: Json) -> Usage:
        """
        Parse usage information from API response.

        Args:
            response_data: API response data.

        Returns:
            Usage object.
        """
        usage_data = response_data.get("usage")
        if usage_data is None:
            usage_data = {}
        elif not isinstance(usage_data, dict):
            usage_data = {}

        return Usage(
            input_tokens=usage_data.get("prompt_tokens") or usage_data.get("input_tokens"),
            output_tokens=usage_data.get("completion_tokens") or usage_data.get("output_tokens"),
            total_tokens=usage_data.get("total_tokens"),
            details=usage_data,
        )

    @staticmethod
    def _normalize_finish_reason(finish_reason: Any) -> str | None:
        """
        Normalize finish_reason to a valid string or None.

        Handles cases where compatible services may return invalid values:
        - None -> None
        - Empty string "" -> None
        - Valid string ("stop", "length", "content_filter") -> as-is
        - Other types (int, bool, etc.) -> None (defensive)

        Args:
            finish_reason: Raw finish_reason value from API.

        Returns:
            Normalized finish_reason (str or None).
        """
        if finish_reason is None:
            return None
        if isinstance(finish_reason, str):
            # Empty string should be treated as None
            return finish_reason if finish_reason else None
        # For any other type (int, bool, list, etc.), return None defensively
        return None

    def __call__(
        self,
        messages: MessagesLike,
        *,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stop: str | Sequence[str] | None = None,
        extra: Json | None = None,
        return_raw: bool = False,
    ) -> ChatResult:
        """
        Make a non-streaming chat completion request.

        Args:
            messages: Messages in various formats (str, list of str, list of dict).
            model: Model to use (overrides default).
            system: Optional system message.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences (str or list of str).
            extra: Additional parameters to include in the request.
            return_raw: Whether to include full raw response.

        Returns:
            ChatResult with text and usage.

        Raises:
            requests.RequestException: On network or HTTP errors.
            ValueError: On invalid input or response format.
        """
        # Normalize messages
        normalized_messages = self._normalize_messages(messages, system=system)

        # Prepare request
        model = model or self.model
        if not model:
            raise ValueError("Model must be specified (either in __init__ or __call__)")

        payload: Json = {
            "model": model,
            "messages": normalized_messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if stop is not None:
            if isinstance(stop, str):
                payload["stop"] = [stop]
            else:
                payload["stop"] = list(stop)

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
        finish_reason = self._normalize_finish_reason(choice.get("finish_reason"))

        # Parse usage
        usage = self._parse_usage(response_data)

        # Return result
        return ChatResult(
            text=text,
            usage=usage,
            finish_reason=finish_reason,
            raw=response_data if return_raw else {},
        )

    def stream(
        self,
        messages: MessagesLike,
        *,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stop: str | Sequence[str] | None = None,
        extra: Json | None = None,
        include_usage: bool = True,
        return_raw_events: bool = False,
    ) -> Iterator[ChatStreamChunk]:
        """
        Make a streaming chat completion request.

        Args:
            messages: Messages in various formats.
            model: Model to use (overrides default).
            system: Optional system message.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            stop: Stop sequences.
            extra: Additional parameters.
            include_usage: Whether to request usage in the final chunk (OpenAI-style).
            return_raw_events: Whether to include raw event data in chunks.

        Yields:
            ChatStreamChunk objects with delta text and usage.

        Raises:
            requests.RequestException: On network or HTTP errors.
            ValueError: On invalid input or response format.
        """
        # Normalize messages
        normalized_messages = self._normalize_messages(messages, system=system)

        # Prepare request
        model = model or self.model
        if not model:
            raise ValueError("Model must be specified (either in __init__ or __call__)")

        payload: Json = {
            "model": model,
            "messages": normalized_messages,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if stop is not None:
            if isinstance(stop, str):
                payload["stop"] = [stop]
            else:
                payload["stop"] = list(stop)

        if include_usage:
            # OpenAI-style: request usage in final chunk
            payload["stream_options"] = {"include_usage": True}

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

        # Parse SSE stream
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
            finish_reason = self._normalize_finish_reason(choice.get("finish_reason"))
            # done is True when finish_reason is a non-empty string
            done = finish_reason is not None

            # Accumulate text
            accumulated_text += content

            # Parse usage if present (usually only in final chunk when include_usage=True)
            usage = None
            if "usage" in event_data:
                usage = self._parse_usage(event_data)
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
