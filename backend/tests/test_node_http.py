"""Tests for HttpRequestNodeExecutor — REST API calls."""

from unittest.mock import patch, MagicMock

import httpx
import pytest

from app.engine.context import ExecutionContext
from app.nodes.http_request import HttpRequestNodeExecutor


class TestHttpRequestNode:
    def test_get_request(self):
        """验证 GET 请求"""
        executor = HttpRequestNodeExecutor()
        ctx = ExecutionContext({})

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"message": "ok"}
        mock_response.text = '{"message": "ok"}'

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            config = {
                "method": "GET",
                "url": "https://api.example.com/data",
                "headers": {"Authorization": "Bearer token123"},
            }
            result = executor.execute(ctx, config)

        assert result["status_code"] == 200
        assert result["body"] == {"message": "ok"}

    def test_post_with_json_body(self):
        """验证 POST 请求带 JSON body"""
        executor = HttpRequestNodeExecutor()
        ctx = ExecutionContext({})

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"id": 1}
        mock_response.text = '{"id": 1}'

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            config = {
                "method": "POST",
                "url": "https://api.example.com/items",
                "headers": {"Content-Type": "application/json"},
                "body": {"name": "test", "price": 100},
            }
            result = executor.execute(ctx, config)

        assert result["status_code"] == 201
        assert result["body"] == {"id": 1}

        # Verify request was called with json body
        mock_client.request.assert_called_once()
        _, kwargs = mock_client.request.call_args
        assert kwargs.get("json") == {"name": "test", "price": 100}

    def test_variable_resolution_in_url(self):
        """验证 URL 中的变量被解析"""
        executor = HttpRequestNodeExecutor()
        ctx = ExecutionContext({"base_url": "https://api.example.com"})

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "ok"

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            config = {
                "method": "GET",
                "url": "{{ input.base_url }}/data",
            }
            result = executor.execute(ctx, config)

        assert result["status_code"] == 200

        # Verify resolved URL was used
        mock_client.request.assert_called_once()
        _, kwargs = mock_client.request.call_args
        assert kwargs.get("url") == "https://api.example.com/data"

    def test_variable_resolution_in_headers(self):
        """验证 headers 中的变量被解析"""
        executor = HttpRequestNodeExecutor()
        ctx = ExecutionContext({"token": "abc123"})

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"ok": True}
        mock_response.text = '{"ok": true}'

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            config = {
                "method": "GET",
                "url": "https://api.example.com/secure",
                "headers": {"Authorization": "Bearer {{ input.token }}"},
            }
            result = executor.execute(ctx, config)

        assert result["status_code"] == 200
        mock_client.request.assert_called_once()
        _, kwargs = mock_client.request.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer abc123"

    def test_timeout_returns_error(self):
        """验证超时返回错误"""
        executor = HttpRequestNodeExecutor()
        ctx = ExecutionContext({})

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.side_effect = httpx.TimeoutException(
                "timeout", request=None
            )

            config = {
                "method": "GET",
                "url": "https://api.example.com/slow",
            }
            result = executor.execute(ctx, config)

        assert result["status_code"] == 0
        assert "timed out" in result["error"].lower()

    def test_connection_error_returns_error(self):
        """验证连接错误返回错误信息"""
        executor = HttpRequestNodeExecutor()
        ctx = ExecutionContext({})

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.side_effect = httpx.ConnectError(
                "Connection refused", request=None
            )

            config = {
                "method": "GET",
                "url": "https://api.example.com/nonexistent",
            }
            result = executor.execute(ctx, config)

        assert result["status_code"] == 0
        assert "connection refused" in result["error"].lower()

    def test_put_request(self):
        """验证 PUT 请求"""
        executor = HttpRequestNodeExecutor()
        ctx = ExecutionContext({})

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"updated": True}
        mock_response.text = '{"updated": true}'

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            config = {
                "method": "PUT",
                "url": "https://api.example.com/items/1",
                "body": {"name": "updated"},
            }
            result = executor.execute(ctx, config)

        assert result["status_code"] == 200
        assert result["body"] == {"updated": True}

        mock_client.request.assert_called_once()
        _, kwargs = mock_client.request.call_args
        assert kwargs.get("json") == {"name": "updated"}

    def test_delete_request(self):
        """验证 DELETE 请求"""
        executor = HttpRequestNodeExecutor()
        ctx = ExecutionContext({})

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 204
        mock_response.headers = {}
        mock_response.text = ""

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            config = {
                "method": "DELETE",
                "url": "https://api.example.com/items/1",
            }
            result = executor.execute(ctx, config)

        assert result["status_code"] == 204

    def test_non_json_response_returns_text(self):
        """验证非 JSON 响应返回原始文本"""
        executor = HttpRequestNodeExecutor()
        ctx = ExecutionContext({})

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "plain text response"

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.request.return_value = mock_response

            config = {
                "method": "GET",
                "url": "https://api.example.com/text",
            }
            result = executor.execute(ctx, config)

        assert result["status_code"] == 200
        assert result["body"] == "plain text response"
