#!/usr/bin/env python
"""
Embedding Example

Demonstrates text embedding using Lexilux.
"""

from config_loader import get_embed_config, parse_args

from lexilux import Embed


def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()

    # Load configuration from endpoints.json
    try:
        config = get_embed_config(config_path=args.config)
    except (FileNotFoundError, KeyError) as e:
        print(f"Error loading configuration: {e}")
        print("\nUsing default placeholder values. To use real API:")
        print("  1. Create tests/test_endpoints.json with your API credentials")
        print(
            "  2. Or specify a config file: python examples/embedding_demo.py --config /path/to/config.json"
        )
        config = {
            "base_url": "https://api.example.com/v1",
            "api_key": "your-api-key",
            "model": "text-embedding-ada-002",
        }

    # Initialize embed client
    embed = Embed(**config)

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
