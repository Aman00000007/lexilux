#!/usr/bin/env python
"""
Embedding Example

Demonstrates text embedding using Lexilux.
"""

from lexilux import Embed


def main():
    """Main function"""
    # Initialize embed client
    embed = Embed(
        base_url="https://api.example.com/v1",
        api_key="your-api-key",
        model="text-embedding-ada-002",
    )

    # Single text
    result = embed("Hello, world!")
    print(f"Single embedding: {len(result.vectors)} dimensions")
    print(f"First 5 values: {result.vectors[:5]}")
    print(f"Usage: {result.usage.total_tokens} tokens")

    # Batch
    texts = ["Python is great", "JavaScript is also great", "Both are useful"]
    result = embed(texts)
    print(f"\nBatch embeddings: {len(result.vectors)} texts")
    print(f"Each embedding: {len(result.vectors[0])} dimensions")
    print(f"Usage: {result.usage.total_tokens} tokens")


if __name__ == "__main__":
    main()
