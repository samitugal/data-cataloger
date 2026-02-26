"""OpenAI Embeddings client for generating vector representations.

Provides embedding generation for table descriptions using OpenAI's
text-embedding-3-small model. Embeddings are 1536-dimensional vectors
suitable for cosine similarity search in Neo4j.

Model choice:
    text-embedding-3-small is chosen for:
    - Good quality/cost balance ($0.02/1M tokens)
    - 1536 dimensions (same as ada-002, compatible with most vector DBs)
    - Fast inference
    - Sufficient quality for table description similarity
"""

import os
from collections.abc import Sequence

from openai import OpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)


class EmbeddingClient:
    """OpenAI client for generating text embeddings.

    Generates vector embeddings from text using OpenAI's embedding models.
    Supports both single text and batch embedding generation with automatic
    retry on rate limits.

    Environment Variables:
        OPENAI_API_KEY: Required. OpenAI API key from platform.openai.com.

    Attributes:
        client: Initialized OpenAI client instance.
        model: Embedding model name (default: text-embedding-3-small).
        dimensions: Vector dimensions (1536 for text-embedding-3-small).

    Example:
        >>> client = EmbeddingClient()
        >>> embedding = client.embed("Customer information table")
        >>> len(embedding)
        1536
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
    ) -> None:
        """Initialize embedding client with OpenAI API key from environment.

        Args:
            model: OpenAI embedding model to use. Defaults to text-embedding-3-small.

        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set.
        """
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY not found in environment. "
                "Get API key from: https://platform.openai.com/api-keys"
            )

        self.client = OpenAI()
        self.model = model
        self.dimensions = 1536

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(RateLimitError),
    )
    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed. Should be non-empty.

        Returns:
            List of floats representing the embedding vector (1536 dimensions).

        Raises:
            RateLimitError: If rate limit persists after 6 retry attempts.
            ValueError: If text is empty.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        response = self.client.embeddings.create(
            input=text,
            model=self.model,
        )

        return response.data[0].embedding

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(RateLimitError),
    )
    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in a single API call.

        More efficient than calling embed() multiple times as it batches
        the request. OpenAI supports up to 2048 texts per batch.

        Args:
            texts: Sequence of texts to embed. Each should be non-empty.

        Returns:
            List of embedding vectors, one per input text.
            Order matches input order.

        Raises:
            RateLimitError: If rate limit persists after 6 retry attempts.
            ValueError: If any text is empty or texts list is empty.
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Text at index {i} cannot be empty")

        response = self.client.embeddings.create(
            input=list(texts),
            model=self.model,
        )

        return [item.embedding for item in response.data]
