"""Tests for OpenAI client wrapper with retry logic.

Tests cover:
- Client initialization with and without API key
- Structured output parsing with mock responses
- Retry behavior on rate limits
- Retry exhaustion after max attempts

All tests use mocks - no real OpenAI API calls, zero cost.
"""

from unittest.mock import Mock, patch

import pytest
from openai import RateLimitError
from pydantic import BaseModel
from tenacity import RetryError

from data_cataloger.cataloging.client import CatalogClient


class MockResponse(BaseModel):
    """Simple Pydantic model for testing structured outputs."""

    text: str
    count: int


def test_client_initialization_success() -> None:
    """Test successful client initialization with API key present."""
    with patch("os.getenv") as mock_getenv:
        # Mock OPENAI_API_KEY environment variable
        mock_getenv.return_value = "sk-test-key-12345"

        # Should initialize without error
        client = CatalogClient()

        # Verify client was created
        assert client.client is not None


def test_client_initialization_missing_api_key() -> None:
    """Test client initialization fails when API key missing."""
    with patch("os.getenv") as mock_getenv:
        # Mock missing API key
        mock_getenv.return_value = None

        # Should raise ValueError with helpful message
        with pytest.raises(ValueError, match="OPENAI_API_KEY not found"):
            CatalogClient()


def test_analyze_table_success() -> None:
    """Test successful table analysis with structured output."""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.return_value = "sk-test-key-12345"

        # Create client with mocked OpenAI
        with patch("data_cataloger.cataloging.client.OpenAI") as mock_openai_cls:
            # Create mock response object
            mock_parsed = MockResponse(text="Test table description", count=3)
            mock_message = Mock()
            mock_message.parsed = mock_parsed

            mock_choice = Mock()
            mock_choice.message = mock_message

            mock_response = Mock()
            mock_response.choices = [mock_choice]

            # Mock the parse method
            mock_client = Mock()
            mock_client.beta.chat.completions.parse.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            # Initialize client and call analyze_table
            client = CatalogClient()
            messages = [
                {"role": "system", "content": "You are a database expert"},
                {"role": "user", "content": "Table: users\nColumns: id, email"},
            ]

            result = client.analyze_table(messages, MockResponse)

            # Verify result is correct type with expected data
            assert isinstance(result, MockResponse)
            assert result.text == "Test table description"
            assert result.count == 3

            # Verify parse was called with correct parameters
            mock_client.beta.chat.completions.parse.assert_called_once()
            call_args = mock_client.beta.chat.completions.parse.call_args
            assert call_args.kwargs["model"] == "gpt-4o-2024-08-06"
            assert call_args.kwargs["response_format"] == MockResponse


def test_analyze_table_retry_on_rate_limit() -> None:
    """Test retry behavior when rate limit error occurs."""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.return_value = "sk-test-key-12345"

        with patch("data_cataloger.cataloging.client.OpenAI") as mock_openai_cls:
            # Create successful response for third attempt
            mock_parsed = MockResponse(text="Success after retry", count=1)
            mock_message = Mock()
            mock_message.parsed = mock_parsed

            mock_choice = Mock()
            mock_choice.message = mock_message

            mock_response = Mock()
            mock_response.choices = [mock_choice]

            # Mock the parse method to fail twice, succeed on third
            mock_client = Mock()
            mock_client.beta.chat.completions.parse.side_effect = [
                RateLimitError(
                    message="Rate limit exceeded",
                    response=Mock(status_code=429),
                    body=None,
                ),
                RateLimitError(
                    message="Rate limit exceeded",
                    response=Mock(status_code=429),
                    body=None,
                ),
                mock_response,
            ]
            mock_openai_cls.return_value = mock_client

            # Initialize client and call analyze_table
            client = CatalogClient()
            messages = [{"role": "user", "content": "Test"}]

            result = client.analyze_table(messages, MockResponse)

            # Should eventually succeed after retries
            assert isinstance(result, MockResponse)
            assert result.text == "Success after retry"

            # Verify parse was called 3 times (2 failures + 1 success)
            assert mock_client.beta.chat.completions.parse.call_count == 3


def test_analyze_table_retry_exhaustion() -> None:
    """Test that retry exhaustion raises RetryError after max attempts."""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.return_value = "sk-test-key-12345"

        with patch("data_cataloger.cataloging.client.OpenAI") as mock_openai_cls:
            # Mock the parse method to always raise RateLimitError
            mock_client = Mock()
            mock_client.beta.chat.completions.parse.side_effect = RateLimitError(
                message="Rate limit exceeded",
                response=Mock(status_code=429),
                body=None,
            )
            mock_openai_cls.return_value = mock_client

            # Initialize client and call analyze_table
            client = CatalogClient()
            messages = [{"role": "user", "content": "Test"}]

            # Should raise RetryError after 6 attempts (tenacity wraps the exception)
            with pytest.raises(RetryError):
                client.analyze_table(messages, MockResponse)

            # Verify parse was called exactly 6 times
            assert mock_client.beta.chat.completions.parse.call_count == 6


def test_analyze_table_none_response() -> None:
    """Test that None response from OpenAI raises ValueError."""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.return_value = "sk-test-key-12345"

        with patch("data_cataloger.cataloging.client.OpenAI") as mock_openai_cls:
            # Create response with None parsed value
            mock_message = Mock()
            mock_message.parsed = None

            mock_choice = Mock()
            mock_choice.message = mock_message

            mock_response = Mock()
            mock_response.choices = [mock_choice]

            mock_client = Mock()
            mock_client.beta.chat.completions.parse.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            # Initialize client and call analyze_table
            client = CatalogClient()
            messages = [{"role": "user", "content": "Test"}]

            # Should raise ValueError for None response
            with pytest.raises(ValueError, match="OpenAI returned None"):
                client.analyze_table(messages, MockResponse)
