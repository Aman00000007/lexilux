#!/usr/bin/env python
"""
Basic Chat Example

Demonstrates simple chat completion using Lexilux.
"""

from lexilux import Chat


def main():
    """Main function"""
    # Initialize chat client
    chat = Chat(
        base_url="https://api.example.com/v1",
        api_key="your-api-key",
        model="gpt-4",
    )

    # Simple call
    result = chat("Hello, world!")
    print(f"Response: {result.text}")
    print(f"Usage: {result.usage.total_tokens} tokens")

    # With system message
    result = chat("What is Python?", system="You are a helpful assistant")
    print(f"\nResponse: {result.text}")
    print(f"Usage: {result.usage.total_tokens} tokens")


if __name__ == "__main__":
    main()
