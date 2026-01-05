"""
Comprehensive tests for new chat features.

Tests are written based on the public interface specification, not implementation details.
Tests challenge the business logic and verify correct behavior according to the API contract.

New features tested:
1. Auto History behavior specifications
2. ChatContinue.continue_request() enhancements
3. Chat.complete() method
4. Chat.continue_if_needed() method
5. Exception types (ChatIncompleteResponseError, ChatStreamInterruptedError)
6. clear_last_assistant_message() method
"""

from unittest.mock import Mock, patch

import pytest
import requests

from lexilux import Chat, ChatContinue, ChatHistory, ChatResult
from lexilux.chat.exceptions import ChatIncompleteResponseError, ChatStreamInterruptedError
from lexilux.usage import Usage


class TestAutoHistoryNonStreamingExceptionBehavior:
    """
    Test auto_history behavior when non-streaming calls fail with exceptions.

    Specification: When a non-streaming call fails with an exception, the history
    should NOT include the AI response, but the user message should be added
    (if history already exists).
    """

    @patch("lexilux.chat.client.requests.post")
    def test_exception_does_not_add_assistant_response(self, mock_post):
        """Test that exception in non-streaming call does not add assistant response"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # First successful call
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        mock_response1.raise_for_status = Mock()

        # Second call that fails
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "choices": [{"message": {"content": "How are you response"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        # raise_for_status raises exception
        mock_response2.raise_for_status.side_effect = requests.RequestException("Network error")

        mock_post.side_effect = [mock_response1, mock_response2]

        # First call succeeds
        chat("Hello")
        history_before = chat.get_history()
        assistant_count_before = len(
            [m for m in history_before.messages if m["role"] == "assistant"]
        )

        # Second call fails
        with pytest.raises(requests.RequestException):
            chat("How are you?")

        # Check history: should have user message but NO assistant response for failed call
        history_after = chat.get_history()
        assert history_after is not None

        # User message should be added (even if call fails)
        user_messages = [m for m in history_after.messages if m["role"] == "user"]
        assert len(user_messages) == 2  # "Hello" + "How are you?"

        # Assistant responses: should still be 1 (only from first successful call)
        assistant_messages = [m for m in history_after.messages if m["role"] == "assistant"]
        assert len(assistant_messages) == assistant_count_before
        assert len(assistant_messages) == 1  # Only from first call

    @patch("lexilux.chat.client.requests.post")
    def test_exception_on_first_call_no_history(self, mock_post):
        """Test that exception on first call does not create history with assistant message"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.RequestException("Network error")
        mock_post.return_value = mock_response

        # First call fails
        with pytest.raises(requests.RequestException):
            chat("Hello")

        # History should be None or empty (no assistant message)
        history = chat.get_history()
        # According to spec: if first call fails, history might be None or have only user message
        # The key point: NO assistant message should be present
        if history is not None:
            assistant_messages = [m for m in history.messages if m["role"] == "assistant"]
            assert len(assistant_messages) == 0


class TestAutoHistoryStreamingLazyInitialization:
    """
    Test auto_history behavior with streaming calls (lazy initialization).

    Specification:
    1. User messages are added when chat.stream() is called
    2. Assistant message is added ONLY on first iteration (lazy initialization)
    3. Assistant message content is updated on each iteration
    4. If iterator is never iterated, no assistant message is added
    """

    @patch("lexilux.chat.client.requests.post")
    def test_assistant_message_not_added_until_first_iteration(self, mock_post):
        """Test that assistant message is not added until first iteration"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        stream_data = [
            b'data: {"choices": [{"delta": {"content": "Hello"}, "index": 0}]}\n',
            b'data: {"choices": [{"delta": {"content": " world"}, "index": 0}]}\n',
            b'data: {"choices": [{"finish_reason": "stop", "index": 0}]}\n',
            b"data: [DONE]\n",
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter(stream_data)
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Create iterator but don't iterate yet
        iterator = chat.stream("Hello")

        # At this point: user message should be added, but NO assistant message
        history = chat.get_history()
        assert history is not None
        assert len(history.messages) == 1  # Only user message
        assert history.messages[0]["role"] == "user"
        assert history.messages[0]["content"] == "Hello"

        # Now iterate (first iteration)
        iter_obj = iter(iterator)
        next(iter_obj)

        # After first iteration: assistant message should be added
        history = chat.get_history()
        assert len(history.messages) == 2  # user + assistant
        assert history.messages[1]["role"] == "assistant"
        # Content should be empty or contain first chunk
        assert history.messages[1]["content"] == "" or "Hello" in history.messages[1]["content"]

    @patch("lexilux.chat.client.requests.post")
    def test_assistant_message_not_added_if_never_iterated(self, mock_post):
        """Test that assistant message is not added if iterator is never iterated"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        stream_data = [
            b'data: {"choices": [{"delta": {"content": "Hello"}, "index": 0}]}\n',
            b"data: [DONE]\n",
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter(stream_data)
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Create iterator but never iterate
        chat.stream("Hello")

        # History should have user message but NO assistant message
        history = chat.get_history()
        assert history is not None
        assert len(history.messages) == 1  # Only user message
        assert history.messages[0]["role"] == "user"

        # Verify no assistant message
        assistant_messages = [m for m in history.messages if m["role"] == "assistant"]
        assert len(assistant_messages) == 0

    @patch("lexilux.chat.client.requests.post")
    def test_assistant_message_content_updates_on_each_iteration(self, mock_post):
        """Test that assistant message content is updated on each iteration"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        stream_data = [
            b'data: {"choices": [{"delta": {"content": "Hello"}, "index": 0}]}\n',
            b'data: {"choices": [{"delta": {"content": " world"}, "index": 0}]}\n',
            b'data: {"choices": [{"delta": {"content": "!"}, "index": 0}]}\n',
            b'data: {"choices": [{"finish_reason": "stop", "index": 0}]}\n',
            b"data: [DONE]\n",
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter(stream_data)
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        iterator = chat.stream("Hello")

        # First iteration (need to iterate the iterator first)
        iter_obj = iter(iterator)
        next(iter_obj)
        history = chat.get_history()
        assert history.messages[1]["content"] == "Hello"  # Should contain first chunk

        # Second iteration
        next(iter_obj)
        history = chat.get_history()
        assert history.messages[1]["content"] == "Hello world"  # Should contain both chunks

        # Third iteration
        next(iter_obj)
        history = chat.get_history()
        assert history.messages[1]["content"] == "Hello world!"  # Should contain all chunks

    @patch("lexilux.chat.client.requests.post")
    def test_streaming_interruption_preserves_partial_content(self, mock_post):
        """Test that streaming interruption preserves partial content in history"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # Stream that will be interrupted
        stream_data = [
            b'data: {"choices": [{"delta": {"content": "Hello"}, "index": 0}]}\n',
        ]

        mock_response = Mock()
        mock_response.status_code = 200

        # Make iter_lines raise exception after first chunk
        def iter_lines_side_effect():
            yield stream_data[0]
            raise requests.RequestException("Network error")

        mock_response.iter_lines.return_value = iter_lines_side_effect()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        iterator = chat.stream("Hello")

        # First iteration succeeds
        iter_obj = iter(iterator)
        next(iter_obj)
        history = chat.get_history()
        assert "Hello" in history.messages[1]["content"]

        # Second iteration fails
        with pytest.raises(requests.RequestException):
            next(iter_obj)

        # Partial content should be preserved
        history = chat.get_history()
        assert history.messages[1]["role"] == "assistant"
        assert "Hello" in history.messages[1]["content"]

        # Partial content should be preserved
        history = chat.get_history()
        assert history.messages[1]["role"] == "assistant"
        assert "Hello" in history.messages[1]["content"]


class TestClearLastAssistantMessage:
    """Test clear_last_assistant_message() method (idempotent)"""

    def test_clear_last_assistant_message_removes_assistant_message(self):
        """Test that clear_last_assistant_message removes last assistant message"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # Manually set up history
        chat._history = ChatHistory()
        chat._history.add_user("Hello")
        chat._history.add_assistant("Hello! How can I help?")

        assert len(chat.get_history().messages) == 2

        # Clear last assistant message
        chat.clear_last_assistant_message()

        history = chat.get_history()
        assert len(history.messages) == 1
        assert history.messages[0]["role"] == "user"

    def test_clear_last_assistant_message_idempotent(self):
        """Test that clear_last_assistant_message is idempotent"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # Manually set up history
        chat._history = ChatHistory()
        chat._history.add_user("Hello")
        chat._history.add_assistant("Response")

        # Clear once
        chat.clear_last_assistant_message()
        history1 = chat.get_history()
        assert len(history1.messages) == 1

        # Clear again (should be safe)
        chat.clear_last_assistant_message()
        history2 = chat.get_history()
        assert len(history2.messages) == 1  # Still 1, not 0

    def test_clear_last_assistant_message_no_assistant_message(self):
        """Test that clear_last_assistant_message does nothing if last message is not assistant"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # Manually set up history with only user message
        chat._history = ChatHistory()
        chat._history.add_user("Hello")

        # Clear (should do nothing)
        chat.clear_last_assistant_message()

        history = chat.get_history()
        assert len(history.messages) == 1
        assert history.messages[0]["role"] == "user"

    def test_clear_last_assistant_message_empty_history(self):
        """Test that clear_last_assistant_message handles empty history"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # Empty history
        chat._history = ChatHistory()

        # Clear (should do nothing)
        chat.clear_last_assistant_message()

        history = chat.get_history()
        assert len(history.messages) == 0

    def test_clear_last_assistant_message_no_history(self):
        """Test that clear_last_assistant_message handles None history"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # No history
        chat._history = None

        # Clear (should do nothing, no exception)
        chat.clear_last_assistant_message()

        assert chat.get_history() is None


class TestChatContinueEnhancedAPI:
    """
    Test enhanced ChatContinue.continue_request() API.

    New features:
    1. history=None with auto_history=True (automatic retrieval)
    2. max_continues (multiple continues)
    3. auto_merge (automatic merging)
    """

    @patch("lexilux.chat.client.requests.post")
    def test_continue_request_auto_history_retrieval(self, mock_post):
        """Test that continue_request automatically retrieves history when history=None"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # First call (successful)
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "choices": [{"message": {"content": "Part 1"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
        }
        mock_response1.raise_for_status = Mock()

        # Continue call
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "choices": [{"message": {"content": " Part 2"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
        mock_response2.raise_for_status = Mock()

        mock_post.side_effect = [mock_response1, mock_response2]

        # First call
        result1 = chat("Write a story", max_tokens=50)
        assert result1.finish_reason == "length"

        # Continue with history=None (should auto-retrieve)
        full_result = ChatContinue.continue_request(chat, result1, history=None)

        # Should be merged result
        assert isinstance(full_result, ChatResult)
        assert "Part 1" in full_result.text
        assert "Part 2" in full_result.text

    @patch("lexilux.chat.client.requests.post")
    def test_continue_request_auto_history_retrieval_fails_when_no_history(self, mock_post):
        """Test that continue_request raises error when history=None and no history available"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=False,  # Disabled
        )

        result = ChatResult(
            text="Part 1",
            usage=Usage(input_tokens=10, output_tokens=50, total_tokens=60),
            finish_reason="length",
        )

        # Should raise ValueError when history=None and auto_history=False
        with pytest.raises(ValueError, match="History is required"):
            ChatContinue.continue_request(chat, result, history=None)

    @patch("lexilux.chat.client.requests.post")
    def test_continue_request_max_continues(self, mock_post):
        """Test that max_continues allows multiple continuation attempts"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # Initial call
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "choices": [{"message": {"content": "Part 1"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
        }
        mock_response1.raise_for_status = Mock()

        # First continue (still truncated) - this is the actual continue request response
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "choices": [{"message": {"content": " Part 2"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
        mock_response2.raise_for_status = Mock()

        # Second continue (complete) - this is the actual continue request response
        mock_response3 = Mock()
        mock_response3.status_code = 200
        mock_response3.json.return_value = {
            "choices": [{"message": {"content": " Part 3"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
        }
        mock_response3.raise_for_status = Mock()

        # The continue_request adds a continue prompt, so each continue makes a chat() call
        # Sequence: initial call -> continue1 (with prompt) -> continue2 (with prompt)
        mock_post.side_effect = [mock_response1, mock_response2, mock_response3]

        # Initial call
        result1 = chat("Write a long story", max_tokens=30)
        assert result1.finish_reason == "length"

        # Continue with max_continues=2
        full_result = ChatContinue.continue_request(chat, result1, max_continues=2)

        # Should have made 2 continue calls (result1 -> continue1 -> continue2)
        assert mock_post.call_count == 3  # initial + 2 continues

        # Should be merged result
        assert isinstance(full_result, ChatResult)
        assert "Part 1" in full_result.text
        assert "Part 2" in full_result.text
        assert "Part 3" in full_result.text
        assert full_result.finish_reason == "stop"

    @patch("lexilux.chat.client.requests.post")
    def test_continue_request_auto_merge_false_returns_list(self, mock_post):
        """Test that auto_merge=False returns list of results"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # Initial call
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "choices": [{"message": {"content": "Part 1"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
        }
        mock_response1.raise_for_status = Mock()

        # Continue call
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "choices": [{"message": {"content": " Part 2"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
        mock_response2.raise_for_status = Mock()

        mock_post.side_effect = [mock_response1, mock_response2]

        # Initial call
        result1 = chat("Write a story", max_tokens=50)
        assert result1.finish_reason == "length"

        # Continue with auto_merge=False
        all_results = ChatContinue.continue_request(chat, result1, auto_merge=False)

        # Should return list
        assert isinstance(all_results, list)
        assert len(all_results) == 2  # result1 + continue_result
        assert all(isinstance(r, ChatResult) for r in all_results)
        assert all_results[0].text == "Part 1"
        assert all_results[1].text == " Part 2"

    @patch("lexilux.chat.client.requests.post")
    def test_continue_request_requires_length_finish_reason(self, mock_post):
        """Test that continue_request requires finish_reason='length'"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        result = ChatResult(
            text="Complete response",
            usage=Usage(input_tokens=10, output_tokens=50, total_tokens=60),
            finish_reason="stop",  # Not "length"
        )

        # Should raise ValueError
        with pytest.raises(ValueError, match="finish_reason='length'"):
            ChatContinue.continue_request(chat, result)


class TestChatComplete:
    """Test Chat.complete() method"""

    @patch("lexilux.chat.client.requests.post")
    def test_complete_ensures_complete_response(self, mock_post):
        """Test that complete() ensures complete response"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # Initial call (truncated)
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "choices": [{"message": {"content": "Part 1"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
        }
        mock_response1.raise_for_status = Mock()

        # Continue call (complete) - needs continue prompt request
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "choices": [{"message": {"content": " Part 2"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
        mock_response2.raise_for_status = Mock()

        # Response for continue prompt
        mock_response3 = Mock()
        mock_response3.status_code = 200
        mock_response3.json.return_value = {
            "choices": [{"message": {"content": " Part 2"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
        mock_response3.raise_for_status = Mock()

        mock_post.side_effect = [mock_response1, mock_response2, mock_response3]

        result = chat.complete("Write a story", max_tokens=50)

        # Should be complete (merged)
        assert result.finish_reason == "stop"
        assert "Part 1" in result.text
        assert "Part 2" in result.text

    @patch("lexilux.chat.client.requests.post")
    def test_complete_raises_incomplete_response_when_still_truncated(self, mock_post):
        """Test that complete() raises ChatIncompleteResponseError when still truncated"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # All calls return truncated
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Part"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Should raise ChatIncompleteResponseError after max_continues
        with pytest.raises(ChatIncompleteResponseError) as exc_info:
            chat.complete("Write a very long story", max_tokens=10, max_continues=2)

        assert exc_info.value.continue_count == 2
        assert exc_info.value.max_continues == 2
        assert exc_info.value.final_result.finish_reason == "length"

    @patch("lexilux.chat.client.requests.post")
    def test_complete_ensure_complete_false_allows_partial(self, mock_post):
        """Test that ensure_complete=False allows partial result"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # All calls return truncated
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Part"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Should return partial result instead of raising
        result = chat.complete(
            "Write a very long story", max_tokens=10, max_continues=2, ensure_complete=False
        )

        assert result.finish_reason == "length"  # Still truncated

    @patch("lexilux.chat.client.requests.post")
    def test_complete_requires_auto_history(self, mock_post):
        """Test that complete() requires auto_history=True"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=False,  # Disabled
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Part 1"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = chat("Write a story", max_tokens=50)
        assert result.finish_reason == "length"

        # Should raise ValueError when trying to use complete() without auto_history
        with pytest.raises(ValueError, match="auto_history must be enabled"):
            chat.complete("Write a story", max_tokens=50)


class TestChatContinueIfNeeded:
    """Test Chat.continue_if_needed() method"""

    @patch("lexilux.chat.client.requests.post")
    def test_continue_if_needed_continues_when_truncated(self, mock_post):
        """Test that continue_if_needed continues when finish_reason='length'"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        # Initial call (truncated)
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "choices": [{"message": {"content": "Part 1"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
        }
        mock_response1.raise_for_status = Mock()

        # Continue call - needs continue prompt request
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "choices": [{"message": {"content": " Part 2"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
        mock_response2.raise_for_status = Mock()

        # Response for continue prompt
        mock_response3 = Mock()
        mock_response3.status_code = 200
        mock_response3.json.return_value = {
            "choices": [{"message": {"content": " Part 2"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
        mock_response3.raise_for_status = Mock()

        mock_post.side_effect = [mock_response1, mock_response2, mock_response3]

        result = chat("Write a story", max_tokens=50)
        assert result.finish_reason == "length"

        # Should continue
        full_result = chat.continue_if_needed(result)

        assert full_result.finish_reason == "stop"
        assert "Part 1" in full_result.text
        assert "Part 2" in full_result.text

    @patch("lexilux.chat.client.requests.post")
    def test_continue_if_needed_returns_unchanged_when_not_truncated(self, mock_post):
        """Test that continue_if_needed returns result unchanged when not truncated"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=True,
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Complete response"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = chat("Write a story", max_tokens=100)
        assert result.finish_reason == "stop"

        # Should return unchanged
        full_result = chat.continue_if_needed(result)

        assert full_result is result  # Same object
        assert full_result.finish_reason == "stop"
        assert full_result.text == "Complete response"

    @patch("lexilux.chat.client.requests.post")
    def test_continue_if_needed_requires_auto_history(self, mock_post):
        """Test that continue_if_needed requires auto_history=True"""
        chat = Chat(
            base_url="https://api.example.com/v1",
            api_key="test-key",
            model="gpt-4",
            auto_history=False,  # Disabled
        )

        result = ChatResult(
            text="Part 1",
            usage=Usage(input_tokens=10, output_tokens=50, total_tokens=60),
            finish_reason="length",
        )

        # Should raise ValueError
        with pytest.raises(ValueError, match="history not available"):
            chat.continue_if_needed(result)


class TestExceptionTypes:
    """Test exception types"""

    def test_chat_incomplete_response_attributes(self):
        """Test ChatIncompleteResponseError exception attributes"""
        final_result = ChatResult(
            text="Partial text",
            usage=Usage(input_tokens=10, output_tokens=50, total_tokens=60),
            finish_reason="length",
        )

        exc = ChatIncompleteResponseError(
            "Response incomplete",
            final_result=final_result,
            continue_count=3,
            max_continues=5,
        )

        assert exc.final_result == final_result
        assert exc.continue_count == 3
        assert exc.max_continues == 5
        assert exc.get_final_text() == "Partial text"

    def test_chat_stream_interrupted_attributes(self):
        """Test ChatStreamInterruptedError exception attributes"""
        partial_result = ChatResult(
            text="Partial text",
            usage=Usage(input_tokens=10, output_tokens=50, total_tokens=60),
            finish_reason="length",
        )

        exc = ChatStreamInterruptedError(
            "Stream interrupted",
            partial_result=partial_result,
        )

        assert exc.partial_result == partial_result
        assert exc.get_partial_text() == "Partial text"
        assert exc.get_partial_result() == partial_result

    def test_chat_stream_interrupted_from_chunks(self):
        """Test ChatStreamInterrupted with received_chunks"""
        from lexilux.chat.models import ChatStreamChunk

        chunks = [
            ChatStreamChunk(delta="Hello", done=False, usage=Usage(), finish_reason=None),
            ChatStreamChunk(delta=" world", done=False, usage=Usage(), finish_reason=None),
        ]

        exc = ChatStreamInterruptedError(
            "Stream interrupted",
            received_chunks=chunks,
        )

        assert exc.get_partial_text() == "Hello world"
        assert exc.get_partial_result().text == "Hello world"
