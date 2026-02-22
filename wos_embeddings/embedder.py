"""Embedding generation using sentence-transformers."""

from __future__ import annotations

import logging
from typing import Sequence

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text using sentence-transformers models.

    This class handles model loading and batch embedding generation with proper
    text preprocessing for nomic-embed-text-v1.5 or similar models.

    Attributes:
        model: Loaded SentenceTransformer model
        model_name: Name/identifier of the model
        text_prefix: Prefix to add before each text (e.g., "search_document:")
        embedding_dim: Dimension of output embeddings
    """

    def __init__(
        self,
        model_name: str = "nomic-ai/nomic-embed-text-v1.5",
        text_prefix: str = "search_document:",
        trust_remote_code: bool = True,
    ):
        """Initialize the embedding generator.

        Args:
            model_name: HuggingFace model identifier
            text_prefix: Prefix to add before each text for embedding
            trust_remote_code: Whether to trust remote code for model loading

        Raises:
            ImportError: If sentence-transformers is not installed
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is required for embedding generation. "
                "Install it with: pip install sentence-transformers"
            ) from e

        self.model_name = model_name
        self.text_prefix = text_prefix

        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, trust_remote_code=trust_remote_code)

        # Get embedding dimension from model
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")

    def prepare_text(self, title: str, abstract: str, skip_empty_abstracts: bool = False) -> str | None:
        """Prepare text for embedding by combining title and abstract.

        Args:
            title: Article title
            abstract: Article abstract
            skip_empty_abstracts: If True, return None for empty abstracts

        Returns:
            Combined text with prefix, or None if should be skipped
        """
        # Handle missing/empty values
        title = (title or "").strip()
        abstract = (abstract or "").strip()

        # Skip if both are empty
        if not title and not abstract:
            return None

        # Skip if abstract is empty and flag is set
        if skip_empty_abstracts and not abstract:
            return None

        # Combine title and abstract
        combined = f"{title} {abstract}".strip()

        # Add prefix
        if self.text_prefix:
            combined = f"{self.text_prefix} {combined}"

        return combined

    def embed_batch(
        self,
        texts: Sequence[str],
        batch_size: int = 64,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for model.encode() calls
            show_progress_bar: Whether to show progress bar during encoding

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, self.embedding_dim)

        logger.debug(f"Embedding {len(texts)} texts with batch size {batch_size}")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
        )

        return embeddings.astype(np.float32)

    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            numpy array of shape (embedding_dim,)
        """
        embeddings = self.embed_batch([text], batch_size=1)
        return embeddings[0]
