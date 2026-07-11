"""Tests for the RAG service (embedding, chunking, retrieval)."""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document
from app.models.embedding import Embedding
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService, _chunk_text, _extract_text


# ===========================================================================
# Unit: EmbeddingService
# ===========================================================================


class TestEmbeddingService:
    """EmbeddingService stub must produce deterministic vectors."""

    def test_generate_returns_1536_dimensions(self):
        svc = EmbeddingService()
        vec = svc.generate("hello world")
        assert len(vec) == 1536
        assert all(isinstance(v, float) for v in vec)
        assert all(0.0 <= v <= 1.0 for v in vec)

    def test_generate_deterministic(self):
        svc = EmbeddingService()
        assert svc.generate("hello") == svc.generate("hello")

    def test_generate_different_for_different_inputs(self):
        svc = EmbeddingService()
        assert svc.generate("hello") != svc.generate("world")


# ===========================================================================
# Unit: Text chunking
# ===========================================================================


class TestChunkText:
    """_chunk_text splits text into overlapping chunks."""

    def test_empty_text(self):
        assert _chunk_text("") == []
        assert _chunk_text("   ") == []

    def test_short_text_stays_single_chunk(self):
        chunks = _chunk_text("Hello world", chunk_size=500)
        assert len(chunks) == 1
        assert "Hello world" in chunks[0]

    def test_long_text_splits(self):
        para = "A" * 200
        text = "\n\n".join([para] * 5)  # 5 paragraphs, each ~200 chars
        chunks = _chunk_text(text, chunk_size=300)
        # 200*5 = 1000 chars, chunks of 300 → expect 3-4 chunks
        assert 2 <= len(chunks) <= 5
        # Total characters across all chunks (overlap inflates this)
        total_as = sum(c.count("A") for c in chunks)
        assert total_as >= 1000, f"Expected at least 1000 'A's, got {total_as}"

    def test_chunks_contain_overlap(self):
        para = "B" * 400
        text = "\n\n".join([para] * 3)
        chunks = _chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) >= 2
        # Overlap text from previous chunk should appear in the next one
        # (the overlap is the last 50 chars of the previous chunk)
        for i in range(1, len(chunks)):
            prev_end = chunks[i - 1][-50:]
            assert prev_end in chunks[i], (
                f"Chunk {i} should contain overlap from chunk {i-1}"
            )


# ===========================================================================
# Unit: Text extraction (requires a real file)
# ===========================================================================


class TestExtractText:
    """_extract_text reads TXT files (PDF/DOCX tested shallowly)."""

    def test_txt_file(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("Hello from file", encoding="utf-8")
        assert _extract_text(str(p)) == "Hello from file"

    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            _extract_text("/nonexistent/file.txt")

    def test_fallback_raw_read(self, tmp_path):
        p = tmp_path / "test.unknown"
        p.write_bytes(b"raw bytes content")
        assert _extract_text(str(p)) == "raw bytes content"


# ===========================================================================
# Integration: RAGService process_document & search with SQLite
# ===========================================================================


class TestRAGService:
    """End-to-end RAG pipeline using a real document record."""

    @pytest.fixture
    async def doc(self, db_session: AsyncSession) -> Document:
        """Create a document with a real .txt file on disk."""
        from app.config import settings

        tenant_id = uuid.uuid4()
        tenant_dir = __import__("pathlib").Path(settings.KNOWLEDGE_DIR) / str(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)

        file_path = tenant_dir / "test_doc.txt"
        file_path.write_text(
            "Python is a programming language.\n\n"
            "It is used for web development, data science, and AI.\n\n"
            "FastAPI is a modern web framework for building APIs with Python.\n\n"
            "Machine learning models can be deployed with FastAPI.",
            encoding="utf-8",
        )

        doc = Document(
            tenant_id=tenant_id,
            name="test_doc.txt",
            file_path=str(file_path),
            content_type="text/plain",
            file_size=file_path.stat().st_size,
            status="pending",
        )
        db_session.add(doc)
        await db_session.flush()
        return doc

    @pytest.fixture
    async def db_session(self) -> AsyncSession:
        """Provide a clean DB session per test."""
        from app.database import async_session

        async with async_session() as session:
            yield session

    async def test_process_document_sets_status_ready(self, doc, db_session):
        rag = RAGService()
        await rag.process_document(doc.id, db_session)

        # Reload document
        result = await db_session.execute(
            select(Document).where(Document.id == doc.id)
        )
        updated = result.scalar_one()
        assert updated.status == "ready"
        assert updated.content is not None

    async def test_process_document_creates_embeddings(self, doc, db_session):
        rag = RAGService()
        await rag.process_document(doc.id, db_session)

        result = await db_session.execute(
            select(Embedding).where(Embedding.document_id == doc.id)
        )
        embeddings = result.scalars().all()
        assert len(embeddings) >= 1
        for emb in embeddings:
            assert emb.chunk_text
            assert emb.embedding is not None
            assert len(emb.embedding) == 1536

    async def test_process_document_embeddings_have_tenant_id(self, doc, db_session):
        rag = RAGService()
        await rag.process_document(doc.id, db_session)

        result = await db_session.execute(
            select(Embedding).where(Embedding.document_id == doc.id)
        )
        emb = result.scalars().first()
        assert emb is not None
        assert emb.tenant_id == doc.tenant_id

    async def test_search_returns_results(self, doc, db_session):
        rag = RAGService()
        await rag.process_document(doc.id, db_session)

        results = await rag.search("Python", doc.tenant_id, db_session, top_k=3)
        assert len(results) > 0
        assert any("Python" in r["chunk_text"] for r in results)

    async def test_search_returns_scored_results(self, doc, db_session):
        rag = RAGService()
        await rag.process_document(doc.id, db_session)

        results = await rag.search("FastAPI", doc.tenant_id, db_session, top_k=5)
        assert len(results) > 0
        # Results should have a score field
        assert "score" in results[0]

    async def test_search_empty_knowledge_base(self, db_session):
        """Searching an empty knowledge base returns empty list."""
        rag = RAGService()
        tenant_id = uuid.uuid4()
        results = await rag.search("anything", tenant_id, db_session, top_k=5)
        assert results == []

    async def test_search_with_empty_query(self, doc, db_session):
        rag = RAGService()
        await rag.process_document(doc.id, db_session)
        results = await rag.search("", doc.tenant_id, db_session)
        assert results == []

    async def test_search_respects_tenant_isolation(self, doc, db_session):
        rag = RAGService()
        await rag.process_document(doc.id, db_session)

        other_tenant = uuid.uuid4()
        results = await rag.search("Python", other_tenant, db_session, top_k=3)
        assert results == []


# ===========================================================================
# Integration: Upload API triggers RAG processing
# ===========================================================================


class TestUploadTriggersRAG:
    """Document upload should result in ready status with embeddings."""

    @pytest.fixture(scope="class")
    def token(self):
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/api/auth/register",
            json={
                "tenant_name": "RAG测试",
                "email": "rag_test@test.com",
                "password": "Test123!@#",
            },
        )
        return resp.json()["access_token"]

    @pytest.fixture
    def headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_upload_document_becomes_ready(self, headers):
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        resp = client.post(
            "/api/knowledge/upload",
            files={
                "file": (
                    "rag_test.txt",
                    b"Python is a programming language. FastAPI is a framework.",
                    "text/plain",
                )
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "ready", f"Expected ready, got {data['status']}"

        # Verify via list endpoint that status is ready
        list_resp = client.get("/api/knowledge", headers=headers)
        docs = list_resp.json()["documents"]
        matching = [d for d in docs if d["id"] == data["id"]]
        assert matching
        assert matching[0]["status"] == "ready"
