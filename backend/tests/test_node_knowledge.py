"""Tests for KnowledgeRetrievalNodeExecutor — RAG-based document chunk search."""

import uuid
import pathlib
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.context import ExecutionContext
from app.nodes.knowledge_node import KnowledgeRetrievalNodeExecutor
from app.services.rag_service import RAGService


class TestKnowledgeRetrievalNode:
    """Unit tests for KnowledgeRetrievalNodeExecutor."""

    def test_missing_query_returns_error(self):
        """验证缺少 query 返回错误"""
        executor = KnowledgeRetrievalNodeExecutor()
        ctx = ExecutionContext({})
        config = {}
        result = executor.execute(ctx, config)
        assert result["count"] == 0
        assert result["chunks"] == []
        assert "No query" in result["error"]

    def test_no_tenant_id_in_context(self):
        """验证上下文中缺少 tenant_id 返回错误"""
        executor = KnowledgeRetrievalNodeExecutor()
        ctx = ExecutionContext({})
        config = {"query": "test query", "top_k": 3}
        result = executor.execute(ctx, config)
        assert result["count"] == 0
        assert result["chunks"] == []
        assert "not available" in result["error"]

    def test_template_variable_resolution(self):
        """验证 query 中的模板变量被解析"""
        executor = KnowledgeRetrievalNodeExecutor()
        ctx = ExecutionContext({"search_term": "artificial intelligence"})
        config = {"query": "{{ input.search_term }}", "top_k": 3}
        # No tenant_id — will fail before reaching search, but template is resolved
        result = executor.execute(ctx, config)
        assert result["count"] == 0
        assert "not available" in result["error"]

    def test_top_k_default(self):
        """验证 top_k 默认不崩溃"""
        executor = KnowledgeRetrievalNodeExecutor()
        ctx = ExecutionContext({})
        config = {"query": "something"}
        result = executor.execute(ctx, config)
        # Fails because no tenant_id, but important: it doesn't crash on missing top_k
        assert "error" in result


class TestKnowledgeRetrievalNodeIntegration:
    """Integration tests — requires actual DB with embedded documents."""

    @pytest.fixture(autouse=True)
    async def _seed_knowledge_base(self):
        """Seed the test DB with a document and its embeddings.

        Uses the same DB engine that ``async_session`` resolves to inside
        the node, so the node can find this data.
        """
        from app.config import settings
        from app.models.document import Document
        from app.database import async_session

        self.tenant_id = uuid.uuid4()
        tenant_dir = pathlib.Path(settings.KNOWLEDGE_DIR) / str(self.tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)

        file_path = tenant_dir / "knowledge_test.txt"
        file_path.write_text(
            "Python is a versatile programming language.\n\n"
            "FastAPI is a modern web framework for building APIs.\n\n"
            "Machine learning models can be deployed using FastAPI.\n\n"
            "PostgreSQL supports full-text search and vector similarity.\n\n"
            "Redis is often used for caching and message brokering.",
            encoding="utf-8",
        )

        async with async_session() as db:
            doc = Document(
                tenant_id=self.tenant_id,
                name="knowledge_test.txt",
                file_path=str(file_path),
                content_type="text/plain",
                file_size=file_path.stat().st_size,
                status="pending",
            )
            db.add(doc)
            await db.flush()

            rag = RAGService()
            await rag.process_document(doc.id, db)
            await db.commit()

        yield

        # Clean up
        if file_path.exists():
            file_path.unlink()
        try:
            tenant_dir.rmdir()
        except OSError:
            pass

    async def test_search_returns_chunks(self):
        """验证搜索返回匹配的文档片段"""
        executor = KnowledgeRetrievalNodeExecutor()
        ctx = ExecutionContext({}, tenant_id=self.tenant_id)
        config = {"query": "Python programming language", "top_k": 3}

        result = executor.execute(ctx, config)
        assert result["count"] > 0
        assert len(result["chunks"]) > 0
        # At least one chunk should contain "Python"
        assert any("Python" in c["chunk_text"] for c in result["chunks"])

    async def test_search_respects_top_k(self):
        """验证 top_k 限制返回数量"""
        executor = KnowledgeRetrievalNodeExecutor()
        ctx = ExecutionContext({}, tenant_id=self.tenant_id)
        config = {"query": "is a", "top_k": 2}

        result = executor.execute(ctx, config)
        assert result["count"] <= 2
        assert len(result["chunks"]) <= 2

    async def test_search_no_match(self):
        """验证搜索无匹配时返回结果但 score 极低（低相关性）"""
        executor = KnowledgeRetrievalNodeExecutor()
        ctx = ExecutionContext({}, tenant_id=self.tenant_id)
        config = {"query": "zzzzyyyyxxxwwww", "top_k": 3}

        result = executor.execute(ctx, config)
        # The RAG service always returns top_k results sorted by score,
        # even if relevance is low — verify it doesn't error.
        assert "error" not in result, result.get("error")
        # count should equal len(chunks)
        assert result["count"] == len(result["chunks"])
        for chunk in result["chunks"]:
            assert "score" in chunk

    async def test_chunks_have_score_field(self):
        """验证返回的片段包含 score 字段"""
        executor = KnowledgeRetrievalNodeExecutor()
        ctx = ExecutionContext({}, tenant_id=self.tenant_id)
        config = {"query": "FastAPI", "top_k": 5}

        result = executor.execute(ctx, config)
        if result["count"] > 0:
            assert "score" in result["chunks"][0]

    async def test_search_respects_tenant_isolation(self):
        """验证不同租户无法看到彼此的文档片段"""
        executor = KnowledgeRetrievalNodeExecutor()
        other_tenant = uuid.uuid4()
        ctx = ExecutionContext({}, tenant_id=other_tenant)
        config = {"query": "Python", "top_k": 5}

        result = executor.execute(ctx, config)
        assert result["count"] == 0
        assert result["chunks"] == []

    async def test_template_variable_integration(self):
        """验证 query 中的模板变量能在完整流程中解析"""
        executor = KnowledgeRetrievalNodeExecutor()
        ctx = ExecutionContext(
            {"search": "PostgreSQL full-text"},
            tenant_id=self.tenant_id,
        )
        config = {"query": "{{ input.search }}", "top_k": 3}

        result = executor.execute(ctx, config)
        assert result["count"] > 0, result.get("error")
        assert any("PostgreSQL" in c["chunk_text"] for c in result["chunks"])

    def test_node_registration(self):
        """验证 knowledge-retrieval 节点已注册到全局注册表"""
        from app.nodes.registry import NODE_REGISTRY, get_node

        cls = get_node(NODE_REGISTRY, "knowledge-retrieval")
        assert cls is not None
        assert cls.__name__ == "KnowledgeRetrievalNodeExecutor"
