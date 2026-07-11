import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestKnowledgeAPI:
    """知识库文档管理 API 测试"""

    @pytest.fixture(scope="class")
    def token(self):
        resp = client.post("/api/auth/register", json={
            "tenant_name": "知识库测试",
            "email": "knowledge_test@test.com",
            "password": "Test123!@#"
        })
        return resp.json()["access_token"]

    @pytest.fixture
    def headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def sample_file(self):
        return io.BytesIO(b"Hello, this is a test document content.")

    def test_upload_document(self, headers, sample_file):
        """验证上传文档"""
        resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("test.txt", sample_file, "text/plain")},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "test.txt"
        assert data["status"] == "pending"
        assert "id" in data
        assert data["file_size"] > 0

    def test_list_documents(self, headers, sample_file):
        """验证获取文档列表"""
        # Upload a document first
        client.post(
            "/api/knowledge/upload",
            files={"file": ("list_test.txt", sample_file, "text/plain")},
            headers=headers,
        )

        resp = client.get("/api/knowledge", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "documents" in data
        assert "total" in data
        assert data["total"] >= 1
        assert any(d["name"] == "list_test.txt" for d in data["documents"])

    def test_delete_document(self, headers, sample_file):
        """验证删除文档"""
        # Upload a document first
        upload_resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("delete_test.txt", sample_file, "text/plain")},
            headers=headers,
        )
        doc_id = upload_resp.json()["id"]

        # Delete the document
        resp = client.delete(f"/api/knowledge/{doc_id}", headers=headers)
        assert resp.status_code == 204

        # Verify it's gone
        list_resp = client.get("/api/knowledge", headers=headers)
        assert not any(d["id"] == doc_id for d in list_resp.json()["documents"])

    def test_delete_nonexistent_document(self, headers):
        """验证删除不存在的文档返回 404"""
        resp = client.delete(
            "/api/knowledge/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_upload_without_auth(self, sample_file):
        """验证未认证无法上传文档"""
        resp = client.post(
            "/api/knowledge/upload",
            files={"file": ("test.txt", sample_file, "text/plain")},
        )
        assert resp.status_code in (401, 403)  # 401 Unauthorized or 403 Forbidden
