"""RAG pipeline service.

Handles the full document-processing pipeline:
  parse -> chunk -> embed -> store

And hybrid retrieval:
  vector similarity (cosine) + keyword (full-text / LIKE) search.
"""

import io
import os
import logging
from typing import Sequence

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.embedding import Embedding
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------

def _sanitize_text(text: str) -> str:
    """Remove characters that PostgreSQL cannot store in UTF8 TEXT fields."""
    return text.replace("\x00", "").replace("￾", "").replace("￿", "")


def _extract_text(file_path: str, content_type: str | None = None) -> str:
    """Read the file at *file_path* and return its plain-text content.

    Supports TXT, PDF, and DOCX.  Falls back to reading as raw bytes /
    UTF-8 text for unknown types.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        try:
            # Try UTF-8 first, fall back to binary read + decode
            with open(file_path, "rb") as f:
                raw = f.read()
            # Remove null bytes before decoding
            text = raw.replace(b"\x00", b"").decode("utf-8", errors="replace")
            return _sanitize_text(text)
        except Exception as exc:
            logger.warning("TXT extraction failed for %s: %s", file_path, exc)
            return ""

    if ext == ".pdf":
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(file_path)
            pages = [page.extract_text() for page in reader.pages]
            return _sanitize_text("\n".join(pages))
        except Exception as exc:
            logger.warning("PDF extraction failed for %s: %s", file_path, exc)
            return ""

    if ext == ".docx":
        try:
            from docx import Document as DocxDocument

            doc = DocxDocument(file_path)
            return _sanitize_text("\n".join(p.text for p in doc.paragraphs))
        except Exception as exc:
            logger.warning("DOCX extraction failed for %s: %s", file_path, exc)
            return ""

    # Fallback: raw read
    with open(file_path, "rb") as f:
        raw = f.read()
    return raw.decode("utf-8", errors="replace")


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split *text* into overlapping chunks of approximately *chunk_size* characters.

    Splits on paragraph boundaries (``\\n\\n``) when possible and merges
    until each chunk reaches *chunk_size*.
    """
    if not text.strip():
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []

    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current_len + para_len <= chunk_size:
            current.append(para)
            current_len += para_len
        else:
            if current:
                chunks.append("\n\n".join(current))
            # Start a new chunk; include overlap from previous chunk
            overlap_text = ""
            if chunks and overlap > 0:
                prev = chunks[-1]
                overlap_text = prev[-overlap:] if len(prev) > overlap else prev
            current = [overlap_text, para] if overlap_text else [para]
            current_len = len(overlap_text) + para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks or [text]


# ---------------------------------------------------------------------------
# RAG service
# ---------------------------------------------------------------------------

class RAGService:
    """Orchestrates document processing and hybrid retrieval."""

    def __init__(self, embedding_service: EmbeddingService | None = None):
        self._embedder = embedding_service or EmbeddingService()

    # ---- document processing ------------------------------------------------

    async def process_document(self, doc_id, db: AsyncSession) -> None:
        """Full processing pipeline for the document identified by *doc_id*.

        1. Load document record and extract plain text from the file.
        2. Split text into overlapping chunks.
        3. Generate embedding for each chunk.
        4. Persist embeddings and update document status.
        """
        # 1. Load
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if doc is None:
            logger.warning("process_document: document %s not found", doc_id)
            return

        doc.status = "processing"
        await db.flush()

        try:
            raw_text = _extract_text(doc.file_path, doc.content_type)
        except Exception as exc:
            doc.status = "failed"
            doc.error = f"Extraction error: {exc}"
            logger.exception("Failed to extract text from %s", doc.file_path)
            await db.flush()
            return

        # 2. Chunk
        chunks = _chunk_text(raw_text)

        if not chunks:
            doc.status = "ready"
            doc.content = raw_text
            await db.flush()
            return

        # 3. Embed & 4. Store
        for idx, chunk_text in enumerate(chunks):
            vector = self._embedder.generate(chunk_text)
            emb = Embedding(
                document_id=doc.id,
                chunk_index=idx,
                chunk_text=chunk_text,
                embedding=vector,
                tenant_id=doc.tenant_id,
            )
            db.add(emb)

        doc.content = raw_text
        doc.status = "ready"
        await db.flush()

    # ---- hybrid search ------------------------------------------------------

    @staticmethod
    def _rerank(query: str, chunks: list[dict], top_k: int) -> list[dict]:
        """对检索结果进行重排序（关键词命中+位置加权）"""
        if not chunks:
            return []
        query_terms = set(query.lower().split())
        for chunk in chunks:
            text = chunk.get("chunk_text", chunk.get("text", "")) or ""
            base = chunk.get("score", chunk.get("vector_distance", 1))
            if isinstance(base, (int, float)):
                base_score = 1.0 - float(base) if base < 1 else 0.5  # distance to similarity
            else:
                base_score = 0.5
            term_hits = sum(1 for t in query_terms if t in text.lower())
            kw_score = term_hits / max(len(query_terms), 1) * 0.3
            idx = chunk.get("chunk_index", 0)
            pos_boost = max(0, 1.0 - idx * 0.01) * 0.1
            chunk["_rerank_score"] = base_score * 0.6 + kw_score + pos_boost
        sorted_chunks = sorted(chunks, key=lambda c: c.get("_rerank_score", 0), reverse=True)
        return sorted_chunks[:top_k]

    async def search(
        self,
        query: str,
        tenant_id,
        db: AsyncSession,
        top_k: int = 5,
        rerank: bool = True,
    ) -> list[dict]:
        """Hybrid retrieval — vector similarity + keyword fallback + optional rerank."""
        if not query.strip():
            return []

        query_vec = self._embedder.generate(query)
        dialect = db.bind.dialect.name if db.bind else "sqlite"

        if dialect == "postgresql":
            results = await self._hybrid_search_pg(query, query_vec, tenant_id, db, top_k * 2 if rerank else top_k)
        else:
            results = await self._keyword_search_fallback(query, tenant_id, db, top_k * 2 if rerank else top_k)

        if rerank and len(results) > 1:
            results = self._rerank(query, results, top_k)

        return results[:top_k]

    async def _hybrid_search_pg(
        self,
        query: str,
        query_vec: list[float],
        tenant_id,
        db: AsyncSession,
        top_k: int,
    ) -> list[dict]:
        """PostgreSQL hybrid: cosine distance + ts_rank."""

        # Convert query vector to PostgreSQL string literal
        vec_literal = "[" + ",".join(str(v) for v in query_vec) + "]"

        sql = text(
            """
            SELECT
                e.id,
                e.document_id,
                e.chunk_index,
                e.chunk_text,
                e.tenant_id,
                (e.embedding <=> :query_vec::vector) AS vector_distance,
                ts_rank(
                    to_tsvector('simple', e.chunk_text),
                    plainto_tsquery('simple', :query)
                ) AS text_score
            FROM embeddings e
            WHERE e.tenant_id = :tenant_id
              AND e.embedding IS NOT NULL
            ORDER BY
                vector_distance * 0.5 + (1 - COALESCE(text_score, 0)) * 0.5
            LIMIT :top_k
            """
        )

        rows = await db.execute(
            sql,
            {
                "query_vec": vec_literal,
                "query": query,
                "tenant_id": tenant_id,
                "top_k": top_k,
            },
        )
        return [dict(row._mapping) for row in rows]

    async def _keyword_search_fallback(
        self,
        query: str,
        tenant_id,
        db: AsyncSession,
        top_k: int,
    ) -> list[dict]:
        """SQLite fallback: simple keyword (LIKE) + ordering by vector distance computed in Python."""

        # First get all embeddings for the tenant
        result = await db.execute(
            select(Embedding).where(
                Embedding.tenant_id == tenant_id,
                Embedding.embedding.isnot(None),
            )
        )
        all_embs: Sequence[Embedding] = result.scalars().all()  # type: ignore[assignment]

        query_vec = self._embedder.generate(query)
        query_lower = query.lower()

        scored: list[tuple[float, Embedding]] = []
        for emb in all_embs:
            # Keyword score: simple word-match ratio
            text_lower = emb.chunk_text.lower()
            words = query_lower.split()
            keyword_score = sum(1 for w in words if w in text_lower) / max(len(words), 1)

            # Vector cosine distance (computed in Python for SQLite)
            if emb.embedding and len(emb.embedding) == len(query_vec):
                dot = sum(a * b for a, b in zip(emb.embedding, query_vec))
                norm_a = sum(v * v for v in emb.embedding) ** 0.5
                norm_b = sum(v * v for v in query_vec) ** 0.5
                norm_product = max(norm_a * norm_b, 1e-10)
                cosine_sim = dot / norm_product
                vector_distance = 1.0 - cosine_sim
            else:
                vector_distance = 1.0

            # Combined score: lower is better
            combined = vector_distance * 0.5 + (1.0 - keyword_score) * 0.5
            scored.append((combined, emb))

        scored.sort(key=lambda x: x[0])
        top = scored[:top_k]

        return [
            {
                "id": emb.id,
                "document_id": emb.document_id,
                "chunk_index": emb.chunk_index,
                "chunk_text": emb.chunk_text,
                "tenant_id": emb.tenant_id,
                "score": score,
            }
            for score, emb in top
        ]
