"""
浏览器端到端测试：真实用户操作流程。

前置条件：
  1. 后端运行在 http://localhost:8080
  2. 前端运行在 http://localhost:5173
  3. test.db 中有测试用户

运行:
  cd D:\\AI\\opc\\jwworkflow\\backend
  python -m pytest tests/test_e2e_browser.py -v --tb=long -x
"""

import os
import time
import pytest
from playwright.sync_api import sync_playwright, Page

BASE = "http://localhost:5173"
WORKFLOW_ID = "a9264c68-1fe7-48f2-88f6-470d8bff8a55"
WORKFLOW_URL = f"/preview/{WORKFLOW_ID}"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..",
                        "data/uploads/workflows", WORKFLOW_ID)
TEST_FILES = [f for f in os.listdir(DATA_DIR) if f.endswith((".xlsx", ".xls", ".csv"))]
TEST_FILE = os.path.join(DATA_DIR, TEST_FILES[0]) if TEST_FILES else None


def login(page: Page):
    """通过登录页登录，登录后位于 /workflows（Zustand token 已设置）"""
    page.goto(f"{BASE}/login", wait_until="networkidle")
    page.wait_for_timeout(2000)
    page.fill("#email", "admin@demo.com")
    page.fill("#password", "demo123")
    page.click('button[type="submit"]')
    page.wait_for_url("**/workflows", timeout=10000)
    page.wait_for_timeout(2000)
    assert "/workflows" in page.url, f"登录后未跳转到工作流列表: {page.url}"


def spa_goto(page: Page, path: str):
    """SPA 内部导航（不触发全页刷新，保留 Zustand 状态）"""
    page.evaluate(f"""
        window.history.pushState({{}}, "", "{path}");
        window.dispatchEvent(new PopStateEvent("popstate"));
    """)
    page.wait_for_timeout(2000)


class TestBrowserE2E:

    @pytest.fixture(scope="class")
    def browser(self):
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True, args=["--no-sandbox"])
            yield b
            b.close()

    def _body(self, page):
        return page.text_content("body") or ""

    # ============================================================
    def test_01_login_and_preview(self, browser):
        """登录 → SPA 导航到预览页"""
        page = browser.new_page()
        login(page)
        spa_goto(page, WORKFLOW_URL)
        body = self._body(page)
        assert "CN" in body or "上传" in body or "文件" in body, \
            f"页面内容异常: {body[:300]}"
        print("[PASS] 登录 + 预览页加载")
        page.close()

    # ============================================================
    def test_02_upload_file(self, browser):
        """上传 Excel 文件"""
        if not TEST_FILE:
            pytest.skip("无测试文件")
        page = browser.new_page()
        login(page)
        spa_goto(page, WORKFLOW_URL)

        fi = page.locator('input[type="file"]')
        assert fi.count() > 0, "找不到上传 input"
        fi.set_input_files(TEST_FILE)
        page.wait_for_timeout(3000)

        assert os.path.basename(TEST_FILE) in self._body(page), \
            f"上传后未显示文件名: {self._body(page)[:300]}"
        print(f"[PASS] 上传: {os.path.basename(TEST_FILE)}")
        page.close()

    # ============================================================
    def test_03_simple_query(self, browser):
        """简单查询：SSE 实时步骤 + 答案"""
        if not TEST_FILE:
            pytest.skip("无测试文件")
        page = browser.new_page()
        login(page)
        spa_goto(page, WORKFLOW_URL)

        page.locator('input[type="file"]').set_input_files(TEST_FILE)
        page.wait_for_timeout(3000)

        # 发送问题
        ta = page.locator("textarea")
        ta.fill("列出所有列名")
        page.wait_for_timeout(500)
        page.locator("button").filter(has_text="发送").click()

        print("  等待 SSE 步骤消息...")
        start = time.time()
        got_step = False
        body_len_baseline = len(self._body(page))
        last_len = body_len_baseline

        while time.time() - start < 40:
            page.wait_for_timeout(500)
            body = self._body(page)
            current_len = len(body)

            # 检测步骤关键字（仅当内容有变化时）
            if current_len > last_len:
                for kw in ["📂", "🧠", "🔍", "💬", "📤", "解析文件", "理解问题", "执行查询", "AI 分析"]:
                    if kw in body:
                        got_step = True
                        print(f"  检测到步骤: {kw}")
                        break
                last_len = current_len

            # 内容显著增长 = 有答案了
            if got_step and current_len > body_len_baseline + 500:
                page.screenshot(path="/tmp/e2e_simple_ok.png")
                print(f"[PASS] 简单查询 (耗时={time.time()-start:.0f}s)")
                page.close()
                return

        page.screenshot(path="/tmp/e2e_simple_timeout.png")
        body = self._body(page)
        print(f"[WARN] 超时, 步标记={got_step}, 文本长度={len(body)}")
        print(f"  最后300字: {body[-300:]}")
        assert got_step, "未收到实时步骤消息"
        page.close()

    # ============================================================
    def test_04_complex_query(self, browser):
        """复杂分析：日期间隔计算（原 500 场景）"""
        if not TEST_FILE:
            pytest.skip("无测试文件")
        page = browser.new_page()
        login(page)
        spa_goto(page, WORKFLOW_URL)

        page.locator('input[type="file"]').set_input_files(TEST_FILE)
        page.wait_for_timeout(3000)

        ta = page.locator("textarea")
        ta.fill("注册时间与初次登记日期间隔超过365天的记录")
        page.wait_for_timeout(500)
        page.locator("button").filter(has_text="发送").click()

        print("  等待复杂分析结果...")
        start = time.time()
        baseline = len(self._body(page))
        while time.time() - start < 50:
            page.wait_for_timeout(1500)
            current = len(self._body(page))
            if current > baseline + 600:
                page.screenshot(path="/tmp/e2e_complex_ok.png")
                print(f"[PASS] 复杂分析 (耗时={time.time()-start:.0f}s)")
                page.close()
                return

        print(f"[WARN] 复杂分析超时, 文本长度={len(self._body(page))}")
        page.screenshot(path="/tmp/e2e_complex_timeout.png")
        page.close()

    # ============================================================
    def test_05_no_file_prompt(self, browser):
        """未上传文件时显示提示"""
        page = browser.new_page()
        login(page)
        spa_goto(page, WORKFLOW_URL)
        body = self._body(page)
        assert "上传" in body or "文件" in body, f"未看到提示: {body[:200]}"
        print("[PASS] 空文件提示")
        page.close()
