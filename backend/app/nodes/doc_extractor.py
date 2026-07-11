"""Document Extractor Node — reads uploaded documents and extracts text.

Supports TXT, DOCX, and PDF file types.
"""

import pathlib

from app.nodes.base import BaseNodeExecutor
from app.engine.context import ExecutionContext


class DocExtractorNodeExecutor(BaseNodeExecutor):
    """文档提取节点：读取上传的文档并提取文本

    Config
    ------
    file_path : str
        文档文件路径（支持模板变量）
    file_type : str, optional
        文件类型覆盖。不指定时从扩展名自动检测，支持：
        ``"txt"``, ``"docx"``, ``"pdf"``。
    """

    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".txt", ".docx", ".pdf"})
    _TYPE_MAP: dict[str, str] = {
        ".txt": "txt",
        ".docx": "docx",
        ".pdf": "pdf",
    }

    def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        raw_path = config.get("file_path", "")
        if not raw_path:
            return {"error": "No file_path specified", "success": False}

        # Resolve template syntax
        if "{{" in str(raw_path):
            file_path = str(ctx.resolve_variable(raw_path))
        else:
            file_path = raw_path

        path = pathlib.Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}", "success": False}

        # Determine file type
        file_type = config.get("file_type", "")
        if not file_type:
            ext = path.suffix.lower()
            file_type = self._TYPE_MAP.get(ext, "")
            if not file_type:
                return {
                    "error": f"Unsupported file type: {ext}",
                    "success": False,
                }

        try:
            if file_type == "txt":
                text = self._extract_txt(path)
            elif file_type == "docx":
                text = self._extract_docx(path)
            elif file_type == "pdf":
                text = self._extract_pdf(path)
            else:
                return {
                    "error": f"Unsupported file type: {file_type}",
                    "success": False,
                }
        except Exception as exc:
            return {"error": f"Extraction failed: {exc}", "success": False}

        return {
            "text": text,
            "file_name": path.name,
            "file_size": path.stat().st_size,
            "success": True,
        }

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_txt(path: pathlib.Path) -> str:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()

    @staticmethod
    def _extract_docx(path: pathlib.Path) -> str:
        from docx import Document  # type: ignore[import-untyped]

        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    @staticmethod
    def _extract_pdf(path: pathlib.Path) -> str:
        from pypdf import PdfReader  # type: ignore[import-untyped]

        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
