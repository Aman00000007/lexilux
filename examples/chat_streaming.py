#!/usr/bin/env python
"""
Chat Streaming Example

Demonstrates streaming chat completion using Lexilux.
"""

from config_loader import get_chat_config, parse_args

from lexilux import Chat


def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()

    # Load configuration from endpoints.json
    try:
        config = get_chat_config(config_path=args.config)
    except (FileNotFoundError, KeyError) as e:
        print(f"Error loading configuration: {e}")
        print("\nUsing default placeholder values. To use real API:")
        print("  1. Create tests/test_endpoints.json with your API credentials")
        print(
            "  2. Or specify a config file: python examples/chat_streaming.py --config /path/to/config.json"
        )
        config = {
            "base_url": "https://api.example.com/v1",
            "api_key": "your-api-key",
            "model": "gpt-4",
        }

    # Initialize chat client
    chat = Chat(**config)

    # Streaming call
    print("Streaming response:")
    print("-" * 50)
    for chunk in chat.stream("Tell me a short joke", include_usage=True):
        print(chunk.delta, end="", flush=True)
        if chunk.done:
            print(f"\n\nUsage: {chunk.usage.total_tokens} tokens")
            print(f"Finish reason: {chunk.finish_reason}")
    print("-" * 50)


if __name__ == "__main__":
    main()
