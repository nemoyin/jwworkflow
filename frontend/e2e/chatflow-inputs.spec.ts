/**
 * E2E：chatflow 预览页渲染输入节点的字段，并在每次消息中携带 `inputs`
 *
 * 背景：纪检模拟谈话等 chatflow 工作流的 agent 节点在 system_prompt 中引用
 * `{{ input.scenario }}` / `{{ input.subject_info }}`，但前端 chatflow 分支此前
 * 只发送 `{ content }`，字段从未传入，导致模板渲染为空。
 *
 * 本测试覆盖：
 *   1. 预览页把 input 字段渲染成表单（场景参数区）
 *   2. 发送消息时 POST /api/conversations/:id/messages 的 body 携带 `inputs`
 *   3. 字段值经后端 input 节点进入模板并渲染进回复（全链路）
 */
import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5173';

let _seq = 0;

/** 注册全新租户+用户，返回邮箱与 token */
async function freshUser(request: any) {
  _seq++;
  const ts = `${Date.now()}_${_seq}`;
  const tenant = `ct_${ts}`;
  const email = `u_${ts}@test.com`;
  const resp = await request.post(`${BASE}/api/auth/register`, {
    data: { tenant_name: tenant, email, password: 'Test123!@#' },
  });
  expect(resp.ok()).toBeTruthy();
  const token = (await resp.json()).access_token;
  expect(token).toBeDefined();
  return { email, token };
}

/** 创建一个带 scenario/subject_info 输入字段的 chatflow（镜像纪检模拟谈话输入节点） */
async function createChatflow(request: any, token: string, name: string) {
  const dag = {
    nodes: [
      {
        id: 'n1',
        type: 'input',
        config: {
          fields: [
            { name: 'scenario', type: 'text', label: '谈话场景设定' },
            { name: 'subject_info', type: 'text', label: '被谈话人信息' },
          ],
        },
      },
      {
        id: 'n2',
        type: 'template',
        config: { template: '场景={{ input.scenario }}|人员={{ input.subject_info }}' },
      },
      {
        id: 'n3',
        type: 'output',
        config: { variables: [{ name: 'out', source: 'n2.output' }] },
      },
    ],
    edges: [
      { id: 'e1', source: 'n1', target: 'n2' },
      { id: 'e2', source: 'n2', target: 'n3' },
    ],
  };
  const resp = await request.post(`${BASE}/api/workflows`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { name, type: 'chatflow', dag_definition: dag },
  });
  expect(resp.ok()).toBeTruthy();
  return resp.json();
}

/** 真实登录并客户端导航到预览页（保留内存中的 token，避免整页刷新丢登录态） */
async function loginAndOpenPreview(page: any, email: string, workflowId: string) {
  await page.goto('/login');
  await page.getByPlaceholder('请输入邮箱').fill(email);
  await page.getByPlaceholder('请输入密码').fill('Test123!@#');
  // antd 会在两字中文按钮文本中插入空格，需用正则匹配
  await page.getByRole('button', { name: /登\s*录/ }).click();
  await page.waitForURL('**/workflows');

  await page.evaluate((url) => {
    window.history.pushState(null, '', url);
    window.dispatchEvent(new PopStateEvent('popstate'));
  }, `/preview/${workflowId}`);
}

test.describe('chatflow 输入字段', () => {
  test('预览页渲染 input 字段，并在发送消息时以 inputs 携带字段值', async ({ browser, request }) => {
    const { email, token } = await freshUser(request);
    const wf = await createChatflow(request, token, 'Chatflow输入字段测试');

    const context = await browser.newContext();
    const page = await context.newPage();
    await loginAndOpenPreview(page, email, wf.id);

    // 1. 输入字段渲染为表单（场景参数区 + 两个字段）
    await expect(page.getByText('场景参数')).toBeVisible();
    await expect(page.getByText('谈话场景设定')).toBeVisible();
    await expect(page.getByText('被谈话人信息')).toBeVisible();

    // 2. 填写字段并发送消息
    const scenario = '某部门负责人涉嫌违规收受礼品礼金';
    const subject = '张某某，某部门主任，中共党员，正科级';
    await page.getByTestId('chatflow-field-scenario').fill(scenario);
    await page.getByTestId('chatflow-field-subject_info').fill(subject);

    const msgReqPromise = page.waitForRequest(
      (req) => req.method() === 'POST' && /\/api\/conversations\/[^/]+\/messages$/.test(req.url()),
    );
    await page.getByPlaceholder(/输入消息/).fill('开始谈话');
    await page.getByPlaceholder(/输入消息/).press('Enter');

    // 3. 断言 POST body 携带 content 与 inputs
    const msgReq = await msgReqPromise;
    const body = msgReq.postDataJSON();
    expect(body.content).toBe('开始谈话');
    expect(body.inputs).toBeDefined();
    expect(body.inputs.scenario).toBe(scenario);
    expect(body.inputs.subject_info).toBe(subject);

    await context.close();
  });

  test('字段值经后端 input 节点进入模板并渲染进回复', async ({ browser, request }) => {
    const { email, token } = await freshUser(request);
    const wf = await createChatflow(request, token, 'Chatflow模板渲染测试');

    const context = await browser.newContext();
    const page = await context.newPage();
    await loginAndOpenPreview(page, email, wf.id);

    const subject = '李某某，某科室科长，中共党员';
    await page.getByTestId('chatflow-field-scenario').fill('涉嫌违规审批项目');
    await page.getByTestId('chatflow-field-subject_info').fill(subject);

    await page.getByPlaceholder(/输入消息/).fill('请开始');
    await page.getByPlaceholder(/输入消息/).press('Enter');

    // 模板节点输出 场景=...|人员=<subject>，应作为干净文本出现在回复气泡中
    await expect(page.getByText(new RegExp(`人员=${subject}`))).toBeVisible();
    // 回归：不得显示整个响应 JSON（JSON.stringify(resp)）或输出 dict 的 repr
    await expect(page.getByText(/^\{"message"/)).toHaveCount(0);
    await expect(page.getByText(/\{'out':/)).toHaveCount(0);

    await context.close();
  });

  test('纪检模拟谈话模板：预览渲染字段并在消息中携带 inputs（拦截 LLM 调用）', async ({ browser, request }) => {
    const { email, token } = await freshUser(request);

    // 从真实内置模板实例化 chatflow（input 节点含 scenario/subject_info，agent 节点引用 {{ input.* }}）
    const instResp = await request.post(`${BASE}/api/templates/builtin_纪检模拟谈话/instantiate`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: '纪检模拟谈话验收测试' },
    });
    expect(instResp.ok()).toBeTruthy();
    const { workflow_id } = await instResp.json();
    expect(workflow_id).toBeDefined();

    const context = await browser.newContext();
    const page = await context.newPage();

    // 收集未捕获的 JS 异常
    const pageErrors: string[] = [];
    page.on('pageerror', (err) => pageErrors.push(err.message));

    await loginAndOpenPreview(page, email, workflow_id);

    // 1. 真实模板的 input 字段渲染为表单
    await expect(page.getByText('场景参数')).toBeVisible();
    await expect(page.getByText('谈话场景设定')).toBeVisible();
    await expect(page.getByText('被谈话人信息')).toBeVisible();

    // 2. 填写字段，拦截消息请求并断言 body 携带 inputs（避免真实 LLM 调用）
    const scenario = '某单位负责人涉嫌违规收受礼品礼金';
    const subject = '王某，某单位负责人，中共党员';
    await page.getByTestId('chatflow-field-scenario').fill(scenario);
    await page.getByTestId('chatflow-field-subject_info').fill(subject);

    let capturedBody: any = null;
    await page.route('**/api/conversations/*/messages', async (route) => {
      capturedBody = route.request().postDataJSON();
      await route.fulfill({
        json: { message: { content: '模拟谈话回复', role: 'assistant' }, output: {}, duration_ms: 1 },
      });
    });

    await page.getByPlaceholder(/输入消息/).fill('开始谈话');
    await page.getByPlaceholder(/输入消息/).press('Enter');

    await expect.poll(() => capturedBody).toBeTruthy();
    expect(capturedBody.content).toBe('开始谈话');
    expect(capturedBody.inputs).toBeDefined();
    expect(capturedBody.inputs.scenario).toBe(scenario);
    expect(capturedBody.inputs.subject_info).toBe(subject);

    // 3. 模拟回复出现在对话区（干净文本，而非整个响应 JSON）
    await expect(page.getByText('模拟谈话回复')).toBeVisible();
    await expect(page.getByText(/^\{"message"/)).toHaveCount(0);
    await page.screenshot({ path: 'test-results/acceptance-chatflow-fields.png', fullPage: false });

    // 4. 无未捕获 JS 异常
    expect(pageErrors).toEqual([]);

    await context.close();
  });
});
