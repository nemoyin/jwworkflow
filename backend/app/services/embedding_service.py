"""Embedding generation service.

MVP stage: returns a deterministic fixed-dimension vector based on
the MD5 hash of the input text.  This allows end-to-end testing without
an external embedding API.  Replace with a real embedding model or API
call in production.
"""

import hashlib


class EmbeddingService:
    """Generates embedding vectors for text chunks."""

    DIMENSION: int = 1536

    def generate(self, text: str) -> list[float]:
        """Return a deterministic 1536-dimensional vector for *text*.

        The vector is derived from the MD5 hash of the input so that
        identical texts always produce the same vector — useful for
        repeatable tests and basic similarity ranking.

        In production this should call an embedding model (e.g.
        ``text-embedding-3-small``, ``all-MiniLM-L6-v2``, etc.).
        """
        h = hashlib.md5(text.encode()).hexdigest()
        return [float(ord(h[i % 32])) / 255.0 for i in range(self.DIMENSION)]
