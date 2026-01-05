#!/usr/bin/env python
"""
Error Handling Demo

Demonstrates how to distinguish between network errors and normal API completions.
Shows how to handle exceptions and check finish_reason appropriately.
"""

import requests

from lexilux import Chat


def demo_non_streaming_error_handling():
    """Demonstrate error handling for non-streaming requests"""
    print("=" * 70)
    print("Demo: Non-Streaming Error Handling")
    print("=" * 70)

    chat = Chat(
        base_url="https://api.example.com/v1",
        api_key="your-api-key",
        model="gpt-4",
    )

    try:
        result = chat("Hello, world!")
        # Success: finish_reason indicates why generation stopped
        print(f"✓ Success: finish_reason = {result.finish_reason}")
        print(f"  Text: {result.text[:50]}...")
        print(f"  Tokens: {result.usage.total_tokens}")

        # Check finish_reason to understand why it stopped
        if result.finish_reason == "stop":
            print("  → Normal completion (stopped naturally)")
        elif result.finish_reason == "length":
            print("  → Hit max_tokens limit")
        elif result.finish_reason == "content_filter":
            print("  → Content was filtered")
        elif result.finish_reason is None:
            print("  → Unknown reason (API didn't provide finish_reason)")

    except requests.ConnectionError as e:
        print(f"✗ Connection Error: {e}")
        print("  → Network problem: Could not connect to server")
        print("  → No finish_reason available (connection failed)")

    except requests.Timeout as e:
        print(f"✗ Timeout Error: {e}")
        print("  → Network problem: Request timed out")
        print("  → No finish_reason available (request didn't complete)")

    except requests.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        print("  → Server returned error status code")
        print("  → No finish_reason available (request failed)")

    except requests.RequestException as e:
        print(f"✗ Request Exception: {e}")
        print("  → Network/HTTP problem occurred")
        print("  → No finish_reason available (request failed)")

    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        print("  → Unexpected error occurred")
        print("  → No finish_reason available")


def demo_streaming_error_handling():
    """Demonstrate error handling for streaming requests"""
    print("\n" + "=" * 70)
    print("Demo: Streaming Error Handling")
    print("=" * 70)

    chat = Chat(
        base_url="https://api.example.com/v1",
        api_key="your-api-key",
        model="gpt-4",
    )

    chunks = []
    completed = False
    finish_reason = None

    try:
        print("Streaming response:")
        print("-" * 50)
        for chunk in chat.stream("Write a long story about programming"):
            print(chunk.delta, end="", flush=True)
            chunks.append(chunk)

            # Track if we received a completion
            if chunk.done:
                completed = True
                # Find chunk with finish_reason (may be before [DONE])
                done_chunks = [c for c in chunks if c.done]
                final_chunk = next(
                    (c for c in done_chunks if c.finish_reason is not None),
                    done_chunks[-1] if done_chunks else None,
                )
                if final_chunk:
                    finish_reason = final_chunk.finish_reason

        print("\n" + "-" * 50)

        if completed:
            print(f"✓ Stream completed: finish_reason = {finish_reason}")
            if finish_reason == "stop":
                print("  → Normal completion (stopped naturally)")
            elif finish_reason == "length":
                print("  → Hit max_tokens limit")
            elif finish_reason == "content_filter":
                print("  → Content was filtered")
            elif finish_reason is None:
                print("  → Unknown reason (API sent [DONE] without finish_reason)")
        else:
            print("⚠ Stream ended without completion signal")
            print("  → This shouldn't happen in normal operation")

    except requests.ConnectionError as e:
        print(f"\n✗ Connection Error during streaming: {e}")
        print("  → Network problem: Connection lost during stream")
        if completed:
            print(f"  → Completion occurred before error: finish_reason = {finish_reason}")
        else:
            print("  → No completion received - stream was interrupted")
            print("  → No finish_reason available")

    except requests.Timeout as e:
        print(f"\n✗ Timeout Error during streaming: {e}")
        print("  → Network problem: Stream timed out")
        if completed:
            print(f"  → Completion occurred before timeout: finish_reason = {finish_reason}")
        else:
            print("  → No completion received - stream timed out")
            print("  → No finish_reason available")

    except requests.RequestException as e:
        print(f"\n✗ Request Exception during streaming: {e}")
        print("  → Network/HTTP problem occurred during stream")
        if completed:
            print(f"  → Completion occurred before error: finish_reason = {finish_reason}")
        else:
            print("  → No completion received - stream was interrupted")
            print("  → No finish_reason available")

    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        print("  → Unexpected error occurred")
        if completed:
            print(f"  → Completion occurred before error: finish_reason = {finish_reason}")
        else:
            print("  → No completion received")
            print("  → No finish_reason available")


def demo_detecting_completion_vs_interruption():
    """Demonstrate how to detect if completion occurred or stream was interrupted"""
    print("\n" + "=" * 70)
    print("Demo: Detecting Completion vs Interruption")
    print("=" * 70)

    chat = Chat(
        base_url="https://api.example.com/v1",
        api_key="your-api-key",
        model="gpt-4",
    )

    def check_stream_completion(chunks):
        """Helper function to check if stream completed successfully"""
        done_chunks = [c for c in chunks if c.done]
        if not done_chunks:
            return False, None

        # Find chunk with finish_reason
        final_chunk = next(
            (c for c in done_chunks if c.finish_reason is not None),
            done_chunks[-1],
        )
        return True, final_chunk.finish_reason

    chunks = []
    try:
        for chunk in chat.stream("Say hello", max_tokens=10):
            print(chunk.delta, end="", flush=True)
            chunks.append(chunk)

        # Check completion status
        completed, finish_reason = check_stream_completion(chunks)
        if completed:
            print("\n✓ Stream completed successfully")
            print(f"  Finish reason: {finish_reason}")
        else:
            print("\n⚠ Stream ended without completion signal")

    except requests.RequestException as e:
        # Check if we got completion before error
        completed, finish_reason = check_stream_completion(chunks)
        if completed:
            print("\n✓ Completion occurred before network error")
            print(f"  Finish reason: {finish_reason}")
            print(f"  Error: {e}")
        else:
            print("\n✗ Stream interrupted - no completion received")
            print(f"  Error: {e}")
            print("  No finish_reason available")


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("Error Handling Demo")
    print("=" * 70)
    print("\nThis demo shows how to distinguish between:")
    print("  1. Network errors (no finish_reason available)")
    print("  2. Normal completions (finish_reason indicates why it stopped)")
    print("\n" + "=" * 70)

    demo_non_streaming_error_handling()
    demo_streaming_error_handling()
    demo_detecting_completion_vs_interruption()

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("=" * 70)
    print("1. finish_reason is ONLY available when API successfully returns a response")
    print("2. Network errors raise exceptions - no finish_reason is available")
    print("3. For streaming, check if done=True chunk was received before error")
    print("4. Always use try-except blocks to handle network errors gracefully")
    print("=" * 70)


if __name__ == "__main__":
    main()
