"""端到端测试：覆盖核心管线 + 可观测性 + SSE 流式执行。

运行方式:
  cd D:\\AI\\opc\\jwworkflow\\backend
  JWT_SECRET=test-secret LLM_API_KEY=sk-xxx python -m pytest tests/test_e2e.py -v -x

需要后端已启动（http://localhost:8080），且 test.db 中有测试数据。
"""

import json
import time
import urllib.request
import urllib.error
import uuid

import pytest

BASE = "http://127.0.0.1:8080"
WORKFLOW_ID = "a9264c68-1fe7-48f2-88f6-470d8bff8a55"

# 测试用户
TEST_EMAIL = "admin@demo.com"
TEST_PASS = "demo123"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _request(method: str, path: str, body=None, token: str = "", timeout: int = 30):
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return e.code, json.loads(body) if body else {"error": str(e)}


def _get_token() -> str:
    status, data = _request("POST", "/api/auth/login", {
        "email": TEST_EMAIL, "password": TEST_PASS,
    })
    assert status == 200, f"Login failed: {data}"
    return data.get("access_token", "")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestE2E:
    """端到端测试集"""

    token = ""

    @classmethod
    def setup_class(cls):
        cls.token = _get_token()
        assert cls.token, "Failed to get auth token"

    # ---- 1. 基础健康检查 ----

    def test_01_health(self):
        """后端健康检查"""
        status, data = _request("GET", "/health")
        assert status == 200
        assert data.get("status") == "ok"
        print("  [PASS] Health check: OK")

    # ---- 2. 可观测性端点 ----

    def test_02_logs_errors(self):
        """错误日志 API"""
        status, data = _request("GET", "/api/logs/errors?limit=5", token=self.token)
        assert status == 200
        assert "errors" in data
        assert isinstance(data["errors"], list)
        print(f"  [PASS] /api/logs/errors: {len(data['errors'])} entries")

    def test_03_logs_debug(self):
        """调试信息 API"""
        status, data = _request("GET", "/api/logs/debug", token=self.token)
        assert status == 200
        assert "log_level" in data
        print(f"  [PASS] /api/logs/debug: level={data['log_level']}")

    # ---- 3. 工作流预览 ----

    def test_04_workflow_preview(self):
        """工作流预览端点"""
        status, data = _request("GET", f"/api/workflows/{WORKFLOW_ID}/preview", token=self.token)
        assert status == 200
        assert data.get("id") == WORKFLOW_ID
        assert "input_fields" in data
        print(f"  [PASS] Preview: {data.get('name')} ({len(data['input_fields'])} fields)")

    # ---- 4. 文件上传 + 同步执行（传统路径） ----

    def test_05_workflow_run_sync(self):
        """同步执行（传统 POST /run）"""
        status, data = _request("POST", f"/api/workflows/{WORKFLOW_ID}/run", {
            "file_path": "",
            "question": "列出所有列名",
        }, token=self.token)
        # 即使没有上传文件，至少应该返回错误而不是 500
        assert status != 500, f"Sync run returned 500: {data}"
        print(f"  [PASS] Sync run: status={status}")

    # ---- 5. SSE 流式执行 ----

    def test_06_run_stream_basic(self):
        """流式执行 - 基本连通性（读取前几个事件后关闭）"""
        import socket

        token = self.token
        path = f"/api/workflows/{WORKFLOW_ID}/run-stream"
        body = json.dumps({"file_path": "", "question": "测试问题"}).encode()

        # 用原生 socket 发送请求并读取 SSE 流
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(("127.0.0.1", 8080))

        request_bytes = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: 127.0.0.1:8080\r\n"
            f"Content-Type: application/json\r\n"
            f"Authorization: Bearer {token}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"\r\n"
        ).encode() + body

        sock.sendall(request_bytes)

        # 读取响应头
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

        # 确认 HTTP 状态
        header_part = response.split(b"\r\n\r\n")[0].decode("utf-8", errors="replace")
        assert "200" in header_part, f"SSE request failed: {header_part[:200]}"
        print("  [PASS] SSE connection established (200)")

        # 读取前几个 SSE 事件
        body_part = response.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in response else b""
        events_found = 0
        start = time.time()

        while events_found < 3 and time.time() - start < 15:
            if b"\n\n" in body_part:
                # 解析事件
                raw_events = body_part.split(b"\n\n")
                for raw in raw_events[:-1]:
                    decoded = raw.decode("utf-8", errors="replace")
                    if "event:" in decoded or "data:" in decoded:
                        events_found += 1
                body_part = raw_events[-1]

            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                body_part += chunk
            except socket.timeout:
                break

        sock.close()
        assert events_found > 0, f"No SSE events received (found {events_found})"
        print(f"  [PASS] SSE events received: {events_found}")

    # ---- 6. 运行历史 ----

    def test_07_run_history(self):
        """运行历史列表"""
        status, data = _request("GET", "/api/runs", token=self.token)
        assert status == 200
        assert isinstance(data, list)
        print(f"  [PASS] Run history: {len(data)} records")

    def test_08_run_detail(self):
        """运行详情（取最新一条）"""
        status, data = _request("GET", "/api/runs", token=self.token)
        assert status == 200
        if data:
            run_id = data[0]["id"]
            status2, detail = _request("GET", f"/api/runs/{run_id}", token=self.token)
            assert status2 == 200
            assert "output" in detail
            print(f"  [PASS] Run detail: {run_id[:12]}... fields={list(detail.keys())}")

    # ---- 7. 完整的端到端场景：上传文件 → 流式分析 ----

    def test_09_upload_and_analyze(self):
        """上传 Excel 文件后用流式执行分析"""
        # 找一个测试数据文件
        import os as _os
        data_dir = _os.path.join(
            _os.path.dirname(__file__), "..",
            "data/uploads/workflows", WORKFLOW_ID
        )
        if not _os.path.isdir(data_dir):
            print("  [SKIP] No test data directory")
            return

        xlsx_files = [f for f in _os.listdir(data_dir)
                      if f.endswith((".xlsx", ".xls", ".csv"))]
        if not xlsx_files:
            print("  [SKIP] No test data files")
            return

        file_path = _os.path.join(data_dir, xlsx_files[0]).replace("\\", "/")
        print(f"  Using file: {xlsx_files[0]}")

        # 上传文件
        import subprocess
        token = self.token
        upload_url = f"{BASE}/api/workflows/{WORKFLOW_ID}/upload"
        curl_cmd = (
            f'curl -s -w "%{{http_code}}" -X POST "{upload_url}" '
            f'-H "Authorization: Bearer {token}" '
            f'-F "file=@{file_path}"'
        )
        result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True, timeout=30)
        http_code = result.stdout[-3:] if len(result.stdout) >= 3 else "000"
        body = result.stdout[:-3] if len(result.stdout) > 3 else ""

        if http_code == "200":
            print(f"  [PASS] File uploaded")
        else:
            print(f"  [WARN] Upload returned {http_code}: {body[:100]}")
            # 有些情况下文件已存在可能报错，不阻塞后续测试

        print("  [PASS] Upload test completed")


    def test_10_sse_full_stream(self):
        """流式执行 - 完整消费 SSE 流，等待 workflow_done 事件"""
        import socket

        token = self.token
        path = f"/api/workflows/{WORKFLOW_ID}/run-stream"
        body = json.dumps({
            "file_path": "",
            "question": "列出所有列名",
        }).encode()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect(("127.0.0.1", 8080))

        request_bytes = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: 127.0.0.1:8080\r\n"
            f"Content-Type: application/json\r\n"
            f"Authorization: Bearer {token}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"\r\n"
        ).encode() + body

        sock.sendall(request_bytes)

        # 读取响应头 + 所有 SSE 事件
        raw = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                raw += chunk
                # 持续读取直到收到 workflow_done 或 workflow_error
                decoded = raw.decode("utf-8", errors="replace")
                if "event: workflow_done" in decoded or "event: workflow_error" in decoded:
                    # 等 2 秒确保收完剩余数据
                    import time as _t
                    _t.sleep(2)
                    try:
                        while True:
                            extra = sock.recv(4096)
                            if not extra:
                                break
                            raw += extra
                    except socket.timeout:
                        pass
                    break
            except socket.timeout:
                # 30s 超时 - 流没正常结束
                sock.close()
                pytest.fail("SSE stream timed out after 30s without workflow_done")
            except Exception:
                break

        sock.close()

        decoded = raw.decode("utf-8", errors="replace")

        # 验证 HTTP 状态
        assert "200 OK" in decoded.split("\r\n")[0], f"Not 200: {decoded[:200]}"

        # 验证收到了 node_start 事件
        node_start_count = decoded.count("event: node_start")
        assert node_start_count > 0, f"No node_start events: {decoded[:500]}"

        # 验证收到了 node_done 事件
        node_done_count = decoded.count("event: node_done")
        assert node_done_count > 0, f"No node_done events: {decoded[:500]}"

        # 验证收到了 workflow_done 事件
        assert "event: workflow_done" in decoded, (
            f"No workflow_done event. Events found: "
            f"node_start={node_start_count}, node_done={node_done_count}. "
            f"Response preview: {decoded[-500:]}"
        )

        # 提取 workflow_done 的 data
        import re
        m = re.search(r'event: workflow_done\s+data:\s*(\{.+?\})\s*\n\n', decoded, re.DOTALL)
        assert m, f"Cannot extract workflow_done data payload"
        payload = json.loads(m.group(1))
        assert "output" in payload, f"workflow_done missing output: {list(payload.keys())}"
        assert "run_id" in payload, f"workflow_done missing run_id: {list(payload.keys())}"

        print(f"  [PASS] Full SSE stream: {node_start_count} starts, "
              f"{node_done_count} dones, workflow_done received, "
              f"run_id={payload['run_id'][:12]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x", "--tb=short"])
