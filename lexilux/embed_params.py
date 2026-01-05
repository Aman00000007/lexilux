"""
Embedding API parameter configuration classes.

Provides dataclass-based parameter configuration for OpenAI-compatible embedding APIs,
with support for standard parameters and custom extensions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class EmbedParams:
    """
    Standard parameters for embedding requests.

    This class defines the most commonly used parameters for OpenAI-compatible
    embedding APIs. All parameters are optional and have sensible defaults.

    Attributes:
        dimensions: The number of dimensions the resulting output embeddings
            should have. Only supported in some models (e.g., ``text-embedding-3-*``).
            For example, ``text-embedding-3-large`` can output embeddings with
            dimensions from 256 up to 3072.
            Default: None (use model's default)

        encoding_format: The format to return the embeddings in. Can be either
            "float" (default) or "base64". Some providers may support additional
            formats.
            Default: "float"

        user: A unique identifier representing your end-user, which can help
            providers to monitor and detect abuse. This is useful for tracking
            and rate limiting.
            Default: None

        extra: Additional custom parameters for OpenAI-compatible servers that may
            accept non-standard parameters. These will be merged into the request
            payload. Useful for provider-specific features.
            Default: None (empty dict)

    Examples:
        Basic usage with defaults:
        >>> params = EmbedParams()
        >>> # encoding_format="float", etc.

        Custom dimensions:
        >>> params = EmbedParams(dimensions=512)

        With custom encoding format:
        >>> params = EmbedParams(encoding_format="base64")

        With custom parameters:
        >>> params = EmbedParams(
        ...     dimensions=256,
        ...     extra={"custom_param": "value"}
        ... )
    """

    dimensions: int | None = None
    encoding_format: Literal["float", "base64"] = "float"
    user: str | None = None
    extra: dict[str, Any] | None = None

    def to_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        """
        Convert parameters to dictionary for API request.

        Args:
            exclude_none: Whether to exclude None values from the output.
                Default: True

        Returns:
            Dictionary of parameters ready for API request.

        Examples:
            >>> params = EmbedParams(dimensions=512, encoding_format="float")
            >>> params.to_dict()
            {'dimensions': 512, 'encoding_format': 'float'}
        """
        result: dict[str, Any] = {}

        # Add standard parameters
        if not exclude_none or self.dimensions is not None:
            if self.dimensions is not None:
                result["dimensions"] = self.dimensions
        if not exclude_none or self.encoding_format != "float":
            result["encoding_format"] = self.encoding_format
        if not exclude_none or self.user is not None:
            if self.user is not None:
                result["user"] = self.user

        # Merge extra parameters
        if self.extra:
            result.update(self.extra)

        return result
