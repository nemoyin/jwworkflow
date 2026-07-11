"""Knowledge Retrieval Node — retrieves relevant document chunks via RAG.

Uses the ``RAGService`` to perform hybrid search (vector + keyword) against
the tenant's knowledge base and returns the top-k matching chunks.
"""

import asyncio
import concurrent.futures
import logging

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext

logger = logging.getLogger(__name__)

_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="knowledge_retrieval"
)


def _run_async(coro):
    """Execute a coroutine from a synchronous context.

    If no event loop is running (typical production path via WorkflowExecutor)
    this uses ``asyncio.run()`` directly.  If a loop is already running (e.g.
    inside a pytest-asyncio test) the coroutine is submitted to a background
    thread where a fresh event loop is created.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop — plain asyncio.run() is fine.
        return asyncio.run(coro)

    # A loop is already running — run the coroutine in a separate thread
    # so it can safely create its own event loop without conflict.
    future = _THREAD_POOL.submit(asyncio.run, coro)
    return future.result()


class KnowledgeRetrievalNodeExecutor(BaseNodeExecutor):
    """知识检索节点：从知识库中检索相关文档片段

    Config
    ------
    knowledge_base_id : str, optional
        知识库 ID（预留字段，当前未使用，默认为当前租户知识库）。
    query : str
        检索查询语句（支持模板变量，如 ``{{ n1.output }}``）。
    top_k : int, default 5
        返回的匹配片段数量。
    """

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        query_template = config.get("query", "")
        if not query_template:
            return {"error": "No query specified", "chunks": [], "count": 0}

        # Resolve template syntax in query
        if "{{" in str(query_template):
            query = str(ctx.resolve_variable(query_template))
        else:
            query = query_template

        top_k = int(config.get("top_k", 5))
        tenant_id = ctx.tenant_id

        if tenant_id is None:
            return {
                "error": "tenant_id not available in context",
                "chunks": [],
                "count": 0,
            }

        try:
            chunks = _run_async(self._search(query, tenant_id, top_k))
            return {"chunks": chunks, "count": len(chunks)}
        except Exception as exc:
            logger.exception("Knowledge retrieval failed for query=%r", query)
            return {
                "error": f"Knowledge retrieval failed: {exc}",
                "chunks": [],
                "count": 0,
            }

    @staticmethod
    async def _search(query: str, tenant_id, top_k: int) -> list[dict]:
        """Create a DB session and run the RAG search."""
        from app.database import async_session
        from app.services.rag_service import RAGService

        async with async_session() as db:
            rag = RAGService()
            return await rag.search(query, tenant_id, db, top_k=top_k)
