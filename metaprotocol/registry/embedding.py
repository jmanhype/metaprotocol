from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class EmbeddingEngine:
    """Generates and manages vector embeddings for semantic skill discovery."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer as ST
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is required for semantic search. "
                    "Install with: pip install metaprotocol[vectors]"
                ) from e
            self._model = ST(self.model_name)
        return self._model

    def encode(self, texts: str | list[str]) -> np.ndarray:
        """Generate embeddings for one or more texts."""
        if isinstance(texts, str):
            texts = [texts]
        return self.model.encode(texts, convert_to_numpy=True)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        return float(np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))

    def encode_skill(self, name: str, description: str | None = None) -> list[float]:
        """Generate an embedding for a skill name + optional description."""
        text = name
        if description:
            text = f"{name}: {description}"
        embedding = self.encode(text)
        return embedding.tolist()

    def find_best_match(
        self,
        query: str,
        skill_embeddings: dict[str, list[float]],
        skill_texts: dict[str, str],
        top_k: int = 10,
    ) -> list[tuple[str, float]]:
        """Find the most semantically similar skills to a query."""
        query_embedding = self.encode(query)
        similarities: list[tuple[str, float]] = []

        for skill_id, embedding in skill_embeddings.items():
            similarity = self.similarity(query_embedding, np.array(embedding))
            similarities.append((skill_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
