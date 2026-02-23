"""OpenAI API client wrapper with automatic retry and structured outputs.

Provides a production-ready interface to OpenAI's GPT-4o for table cataloging with:
- Automatic API key loading from OPENAI_API_KEY environment variable
- Exponential backoff retry on rate limits (1-60s, max 6 attempts)
- Type-safe structured outputs via Pydantic models
- Support for context-aware analysis with message history

Why GPT-4o-2024-08-06 specifically:
    This is the only model that supports OpenAI's Structured Outputs feature,
    which guarantees 100% schema compliance with Pydantic models. Earlier models
    and other GPT-4 variants don't support this feature.

Why exponential backoff 1-60s:
    OpenAI rate limits are dynamic based on usage tier. Starting at 1s handles
    transient rate limits, capping at 60s prevents infinite waits. Random jitter
    prevents thundering herd when multiple requests retry simultaneously.

Why 6 attempts:
    Provides ~2 minutes of total retry time (1+2+4+8+16+32s average), enough to
    handle typical rate limit windows without excessive delays.
"""

import os
from typing import Any

from openai import OpenAI, RateLimitError
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)


class CatalogClient:
    """OpenAI client wrapper for LLM-powered table cataloging.

    Manages OpenAI API interactions with automatic retry logic and type-safe
    structured outputs. Designed for production use with rate limit handling
    and environment-based configuration.

    Environment Variables:
        OPENAI_API_KEY: Required. OpenAI API key from platform.openai.com.
            Client will raise ValueError if not found.

    Attributes:
        client: Initialized OpenAI client instance. Automatically reads
            OPENAI_API_KEY from environment.

    Example:
        >>> import os
        >>> os.environ["OPENAI_API_KEY"] = "sk-..."
        >>> client = CatalogClient()
        >>> messages = [
        ...     {"role": "system", "content": "Analyze this table..."},
        ...     {"role": "user", "content": "Table: users\\nColumns: id, email"}
        ... ]
        >>> from pydantic import BaseModel
        >>> class Response(BaseModel):
        ...     description: str
        >>> result = client.analyze_table(messages, Response)
        >>> print(result.description)
    """

    def __init__(self) -> None:
        """Initialize OpenAI client with API key from environment.

        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set.
                User must set API key before instantiating client.
        """
        # Verify API key is present before initializing client
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY not found in environment. "
                "Get API key from: https://platform.openai.com/api-keys"
            )

        # OpenAI client automatically reads OPENAI_API_KEY from environment
        # No need to pass api_key parameter explicitly
        self.client = OpenAI()

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(RateLimitError),
    )
    def analyze_table(
        self, messages: list[dict[str, Any]], response_model: type[BaseModel]
    ) -> BaseModel:
        """Analyze table with automatic retry on rate limits.

        Uses OpenAI's Structured Outputs feature to guarantee schema compliance.
        The parse() method returns a typed Pydantic instance, not raw JSON, ensuring
        type safety and validation.

        Retry behavior:
            - Retries only on RateLimitError (429 status code)
            - Waits 1-60 seconds with exponential backoff and random jitter
            - Maximum 6 attempts (~2 minutes total)
            - Non-rate-limit errors (auth, invalid request) fail immediately

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                Typically includes system prompt and user prompt.
                Example: [
                    {"role": "system", "content": "You are a database expert..."},
                    {"role": "user", "content": "Table: users\\nColumns: id, email"}
                ]
            response_model: Pydantic BaseModel subclass defining expected response
                structure. Must use simple types (str, int, list, Literal) compatible
                with OpenAI's strict mode. Avoid validators, computed fields, or
                complex unions.

        Returns:
            Parsed Pydantic instance of response_model type. All fields validated
            and type-checked according to model definition.

        Raises:
            RateLimitError: If rate limit persists after 6 retry attempts
            AuthenticationError: If API key is invalid (no retry)
            BadRequestError: If request is malformed (no retry)
            APIError: For other OpenAI API errors (no retry)

        Example:
            >>> from pydantic import BaseModel
            >>> class TableCatalog(BaseModel):
            ...     description: str
            ...     sensitivity: str
            >>> messages = [
            ...     {"role": "system", "content": "Analyze table..."},
            ...     {"role": "user", "content": "Table: users..."}
            ... ]
            >>> result = client.analyze_table(messages, TableCatalog)
            >>> assert isinstance(result, TableCatalog)
        """
        # Use beta.chat.completions.parse() for structured outputs
        # This guarantees 100% schema compliance (vs ~95% with function calling)
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",  # Required for structured outputs
            messages=messages,  # type: ignore[arg-type]
            response_format=response_model,
        )

        # Return parsed Pydantic object (not raw JSON)
        # Type checker knows this is response_model type
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise ValueError("OpenAI returned None for parsed response")
        return parsed
