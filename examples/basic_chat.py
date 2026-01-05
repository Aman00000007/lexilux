#!/usr/bin/env python
"""
Basic Chat Example

Demonstrates simple chat completion using Lexilux.
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
            "  2. Or specify a config file: python examples/basic_chat.py --config /path/to/config.json"
        )
        config = {
            "base_url": "https://api.example.com/v1",
            "api_key": "your-api-key",
            "model": "gpt-4",
        }

    # Initialize chat client
    chat = Chat(**config)

    # Simple call
    result = chat("Hello, world!")
    print(f"Response: {result.text}")
    print(f"Usage: {result.usage.total_tokens} tokens")
    print(f"Finish reason: {result.finish_reason}")

    # With system message
    result = chat("What is Python?", system="You are a helpful assistant")
    print(f"\nResponse: {result.text}")
    print(f"Usage: {result.usage.total_tokens} tokens")


if __name__ == "__main__":
    main()
