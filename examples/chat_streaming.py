#!/usr/bin/env python
"""
Chat Streaming Example

Demonstrates streaming chat completion using Lexilux.
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

    # Streaming call
    print("Streaming response:")
    print("-" * 50)
    for chunk in chat.stream("Tell me a short joke", include_usage=True):
        print(chunk.delta, end="", flush=True)
        if chunk.done:
            print(f"\n\nUsage: {chunk.usage.total_tokens} tokens")
    print("-" * 50)


if __name__ == "__main__":
    main()
