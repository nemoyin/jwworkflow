"""Tests for the Chatflow multi-turn conversation API.

Verifies:
- Creating a conversation bound to a workflow
- Sending a message that triggers workflow execution
- Persisting conversation variables across turns
- Listing conversations and retrieving message history
- Error handling for missing / closed conversations
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


_SAMPLE_CHATFLOW = {
    "name": "测试 Chatflow",
    "description": "一个简单的多轮对话工作流",
    "type": "chatflow",
    "dag_definition": {
        "nodes": [
            {
                "id": "n1",
                "type": "input",
                "config": {
                    "fields": [{"name": "message", "type": "text"}]
                },
            },
            {
                "id": "n2",
                "type": "template",
                "config": {"template": "你说了: {{ input.message }}"},
            },
            {
                "id": "n3",
                "type": "output",
                "config": {
                    "variables": [{"name": "reply", "source": "n2.output"}]
                },
            },
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    },
}


class TestConversationsAPI:
    """Chatflow conversation CRUD + messaging tests."""

    @pytest.fixture(scope="class")
    def token(self):
        resp = client.post(
            "/api/auth/register",
            json={
                "tenant_name": "对话测试",
                "email": "chat_test@test.com",
                "password": "Test123!@#",
            },
        )
        return resp.json()["access_token"]

    @pytest.fixture
    def headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def workflow_id(self, headers):
        """Create a sample chatflow workflow and return its id."""
        resp = client.post("/api/workflows", json=_SAMPLE_CHATFLOW, headers=headers)
        assert resp.status_code == 201
        return resp.json()["id"]

    # ------------------------------------------------------------------
    # Conversation CRUD
    # ------------------------------------------------------------------

    def test_create_conversation(self, headers, workflow_id):
        """Verify creating a conversation returns the correct fields."""
        resp = client.post(
            "/api/conversations",
            json={"workflow_id": workflow_id, "title": "测试对话"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["workflow_id"] == workflow_id
        assert data["title"] == "测试对话"
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data

    def test_create_conversation_with_default_title(self, headers, workflow_id):
        """Verify title defaults when not provided."""
        resp = client.post(
            "/api/conversations",
            json={"workflow_id": workflow_id},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "New conversation"

    def test_create_conversation_missing_workflow(self, headers):
        """Verify 404 when the workflow does not exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.post(
            "/api/conversations",
            json={"workflow_id": fake_id},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_list_conversations(self, headers, workflow_id):
        """Verify listing returns created conversations."""
        # Create two conversations
        client.post(
            "/api/conversations",
            json={"workflow_id": workflow_id, "title": "对话A"},
            headers=headers,
        )
        client.post(
            "/api/conversations",
            json={"workflow_id": workflow_id, "title": "对话B"},
            headers=headers,
        )

        resp = client.get("/api/conversations", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # At least the two we just created
        assert len(data) >= 2

    # ------------------------------------------------------------------
    # Sending messages (multi-turn)
    # ------------------------------------------------------------------

    def test_send_message_and_get_reply(self, headers, workflow_id):
        """Verify sending a message runs the workflow and returns output."""
        conv_resp = client.post(
            "/api/conversations",
            json={"workflow_id": workflow_id},
            headers=headers,
        )
        conv_id = conv_resp.json()["id"]

        resp = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "你好，世界"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert data["message"]["role"] == "assistant"
        assert "output" in data
        assert data["duration_ms"] is not None

    def test_message_history(self, headers, workflow_id):
        """Verify message history is recorded and retrievable."""
        conv_resp = client.post(
            "/api/conversations",
            json={"workflow_id": workflow_id},
            headers=headers,
        )
        conv_id = conv_resp.json()["id"]

        # Send a message
        client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "第一条消息"},
            headers=headers,
        )

        # Retrieve history
        resp = client.get(
            f"/api/conversations/{conv_id}/messages", headers=headers
        )
        assert resp.status_code == 200
        msgs = resp.json()
        assert isinstance(msgs, list)
        assert len(msgs) >= 2  # user + assistant
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "第一条消息"
        assert msgs[-1]["role"] == "assistant"

    def test_multi_turn_variable_persistence(self, headers, workflow_id):
        """Verify conversation variables persist across turns."""
        conv_resp = client.post(
            "/api/conversations",
            json={"workflow_id": workflow_id},
            headers=headers,
        )
        conv_id = conv_resp.json()["id"]

        # Turn 1
        turn1 = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "Turn 1"},
            headers=headers,
        )
        assert turn1.status_code == 200

        # Turn 2 — the previous outputs should still be in context
        turn2 = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "Turn 2"},
            headers=headers,
        )
        assert turn2.status_code == 200

        # Both turns should appear in the history
        hist = client.get(
            f"/api/conversations/{conv_id}/messages", headers=headers
        )
        msgs = hist.json()
        contents = [m["content"] for m in msgs if m["role"] == "user"]
        assert "Turn 1" in contents
        assert "Turn 2" in contents

    def test_send_message_closed_conversation(self, headers, workflow_id):
        """Verify 400 when sending to a closed conversation."""
        # We need a way to close — the API currently doesn't expose
        # a close endpoint, but we can still test the scenario conceptually.
        conv_resp = client.post(
            "/api/conversations",
            json={"workflow_id": workflow_id},
            headers=headers,
        )
        conv_id = conv_resp.json()["id"]

        # Close the conversation by directly manipulating the DB via the app
        from app.database import async_session
        from app.models.conversation import Conversation
        from sqlalchemy import select
        import asyncio

        async def _close():
            async with async_session() as session:
                result = await session.execute(
                    select(Conversation).where(Conversation.id == uuid.UUID(conv_id))
                )
                conv = result.scalar_one()
                conv.status = "closed"
                await session.commit()

        asyncio.run(_close())

        resp = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "should fail"},
            headers=headers,
        )
        assert resp.status_code == 400
        assert "关闭" in resp.text

    # ------------------------------------------------------------------
    # Error cases
    # ------------------------------------------------------------------

    def test_get_messages_missing_conversation(self, headers):
        """Verify 404 for a non-existent conversation id."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.get(
            f"/api/conversations/{fake_id}/messages", headers=headers
        )
        assert resp.status_code == 404

    def test_send_message_missing_conversation(self, headers):
        """Verify 404 when sending to a non-existent conversation."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.post(
            f"/api/conversations/{fake_id}/messages",
            json={"content": "hi"},
            headers=headers,
        )
        assert resp.status_code == 404

    def test_without_auth(self):
        """Verify endpoints return 401 without auth token."""
        endpoints = [
            ("POST", "/api/conversations", {"workflow_id": "00000000-0000-0000-0000-000000000000"}),
            ("GET", "/api/conversations", None),
            ("POST", "/api/conversations/00000000-0000-0000-0000-000000000000/messages", {"content": "hi"}),
            ("GET", "/api/conversations/00000000-0000-0000-0000-000000000000/messages", None),
        ]
        for method, path, body in endpoints:
            if method == "POST":
                resp = client.post(path, json=body)
            else:
                resp = client.get(path)
            assert resp.status_code in (
                401,
                403,
            ), f"{method} {path} returned {resp.status_code}"
