"""Embeddings module for semantic search functionality.

Provides OpenAI embedding generation for table descriptions,
enabling vector similarity search in Neo4j.
"""

from data_cataloger.embeddings.client import EmbeddingClient

__all__ = ["EmbeddingClient"]
