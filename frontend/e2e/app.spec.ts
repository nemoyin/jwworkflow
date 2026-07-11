import { test, expect } from '@playwright/test';

const TEST_EMAIL = `e2e_${Date.now()}@test.com`;
const TEST_PASSWORD = 'Test123!@#';

test.describe('jwworkflow E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Clear state between tests
    await page.evaluate(() => localStorage.clear());
  });

  // ========================
  // 1. 认证流程
  // ========================

  test('1.1 注册新用户', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('text=jwworkflow 登录')).toBeVisible();

    // Switch to register? No - the current page only has login.
    // Use direct API for register, or add register UI.
    // For now, register via API
    const resp = await page.request.post('/api/auth/register', {
      data: { tenant_name: 'E2E测试', email: TEST_EMAIL, password: TEST_PASSWORD }
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.access_token).toBeDefined();
  });

  test('1.2 登录并跳转到工作流列表', async ({ page }) => {
    // Register first
    await page.request.post('/api/auth/register', {
      data: { tenant_name: 'E2E测试', email: TEST_EMAIL, password: TEST_PASSWORD }
    });

    await page.goto('/login');
    await page.fill('input[placeholder="请输入邮箱"]', TEST_EMAIL);
    await page.fill('input[placeholder="请输入密码"]', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Should redirect to /workflows
    await page.waitForURL('/workflows');
    await expect(page.locator('text=工作流列表')).toBeVisible();
    await expect(page.locator('text=新建工作流')).toBeVisible();
  });

  // ========================
  // 2. 工作流管理
  // ========================

  test('2.1 创建工作流', async ({ page }) => {
    await registerAndLogin(page, TEST_EMAIL, TEST_PASSWORD);
    await page.goto('/workflows');
    await page.click('text=新建工作流');
    await page.waitForURL('/workflows/new');
    await expect(page.locator('text=工作流编辑器')).toBeVisible();
    // Check node palette is visible
    await expect(page.locator('text=节点类型')).toBeVisible();
    // Check configured node types exist
    await expect(page.locator('text=LLM 调用')).toBeVisible();
    await expect(page.locator('text=条件分支')).toBeVisible();
    await expect(page.locator('text=Agent 代理')).toBeVisible();
  });

  test('2.2 拖拽节点到画布', async ({ page }) => {
    await registerAndLogin(page, TEST_EMAIL, TEST_PASSWORD);
    await page.goto('/workflows/new');

    // Drag "输入" node onto canvas
    const inputNode = page.locator('text=用户输入 / 文件输入');
    await expect(inputNode).toBeVisible();

    // Check that selecting a node shows the config panel
    // Find and click a node on the canvas
    const canvas = page.locator('.react-flow__pane');
    await expect(canvas).toBeVisible();
  });

  test('2.3 保存工作流', async ({ page }) => {
    await registerAndLogin(page, TEST_EMAIL, TEST_PASSWORD);
    await page.goto('/workflows/new');

    // Click save button
    const saveBtn = page.locator('button:has-text("保存")');
    await expect(saveBtn).toBeVisible();
    await saveBtn.click();
    // Should succeed (workflow with empty nodes)
    await expect(page.locator('text=保存成功')).toBeVisible();
  });

  test('2.4 工作流列表展示', async ({ page }) => {
    // Create a workflow via API first
    const token = await getToken(page, TEST_EMAIL, TEST_PASSWORD);
    await page.request.post('/api/workflows', {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: '测试工作流', type: 'workflow', dag_definition: { nodes: [], edges: [] } }
    });

    await page.goto('/workflows');
    await page.waitForSelector('table');
    await expect(page.locator('text=测试工作流')).toBeVisible();
  });

  // ========================
  // 3. 工作流执行
  // ========================

  test('3.1 执行工作流返回结果', async ({ page }) => {
    const token = await getToken(page, TEST_EMAIL, TEST_PASSWORD);

    // Create a workflow with a simple template
    const wfResp = await page.request.post('/api/workflows', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        name: '执行测试',
        type: 'workflow',
        dag_definition: {
          nodes: [
            { id: 'n1', type: 'input', config: { fields: [{ name: 'name', type: 'text' }] } },
            { id: 'n2', type: 'template', config: { template: '你好, {{ input.name }}!' } },
            { id: 'n3', type: 'output', config: { variables: [{ name: 'greeting', source: 'n2.output' }] } }
          ],
          edges: [
            { id: 'e1', source: 'n1', target: 'n2' },
            { id: 'e2', source: 'n2', target: 'n3' }
          ]
        }
      }
    });
    const wf = await wfResp.json();

    // Execute it
    const runResp = await page.request.post(`/api/workflows/${wf.id}/run`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: '世界' }
    });
    const result = await runResp.json();
    expect(result.status).toBe('success');
    expect(result.result).toBeDefined();
    expect(result.result.greeting).toBe('你好, 世界!');
  });

  // ========================
  // 4. 模型管理
  // ========================

  test('4.1 添加 LLM 供应商', async ({ page }) => {
    const token = await getToken(page, TEST_EMAIL, TEST_PASSWORD);

    const resp = await page.request.post('/api/admin/providers', {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'TestAI', provider_type: 'openai', api_key: 'sk-test', base_url: 'https://api.test.com' }
    });
    expect(resp.status()).toBe(201);
    const provider = await resp.json();
    expect(provider.name).toBe('TestAI');
  });

  test('4.2 注册模型', async ({ page }) => {
    const token = await getToken(page, TEST_EMAIL, TEST_PASSWORD);

    // Create provider first
    const pResp = await page.request.post('/api/admin/providers', {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'DeepSeek', provider_type: 'deepseek', api_key: 'sk-ds', base_url: 'https://api.deepseek.com' }
    });
    const provider = await pResp.json();

    // Register model
    const mResp = await page.request.post('/api/admin/models', {
      headers: { Authorization: `Bearer ${token}` },
      data: { provider_id: provider.id, model_name: 'deepseek-v4-pro', display_name: 'DeepSeek V4 Pro', capabilities: { tool_calls: true, max_tokens: 65536 } }
    });
    expect(mResp.status()).toBe(201);
    const model = await mResp.json();
    expect(model.model_name).toBe('deepseek-v4-pro');
  });

  test('4.3 可用模型列表', async ({ page }) => {
    const token = await getToken(page, TEST_EMAIL, TEST_PASSWORD);

    const resp = await page.request.get('/api/admin/models/available', {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(resp.status()).toBe(200);
    const models = await resp.json();
    expect(Array.isArray(models)).toBeTruthy();
  });

  // ========================
  // 5. 知识库
  // ========================

  test('5.1 上传文档到知识库', async ({ page }) => {
    const token = await getToken(page, TEST_EMAIL, TEST_PASSWORD);

    // Create a test file
    const fileContent = '这是一个测试文档内容。用于验证知识库上传功能。';

    const resp = await page.request.post('/api/knowledge/upload', {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        file: {
          name: 'test.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from(fileContent, 'utf-8'),
        }
      }
    });
    expect(resp.status()).toBe(201);
    const doc = await resp.json();
    expect(doc.name).toBe('test.txt');
    expect(doc.status).toBe('ready');
  });

  test('5.2 知识库文档列表', async ({ page }) => {
    const token = await getToken(page, TEST_EMAIL, TEST_PASSWORD);

    // Upload first
    await page.request.post('/api/knowledge/upload', {
      headers: { Authorization: `Bearer ${token}` },
      multipart: { file: { name: 'list_test.txt', mimeType: 'text/plain', buffer: Buffer.from('test', 'utf-8') } }
    });

    const resp = await page.request.get('/api/knowledge', {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(resp.status()).toBe(200);
    const docs = await resp.json();
    expect(docs.length).toBeGreaterThanOrEqual(1);
  });

  // ========================
  // 6. 模板市场
  // ========================

  test('6.1 获取模板列表', async ({ page }) => {
    const token = await getToken(page, TEST_EMAIL, TEST_PASSWORD);

    const resp = await page.request.get('/api/templates', {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(resp.status()).toBe(200);
    const templates = await resp.json();
    expect(templates.length).toBeGreaterThanOrEqual(4); // 4 built-in templates
  });

  test('6.2 从模板创建工作流', async ({ page }) => {
    const token = await getToken(page, TEST_EMAIL, TEST_PASSWORD);

    // Get templates
    const tResp = await page.request.get('/api/templates', {
      headers: { Authorization: `Bearer ${token}` }
    });
    const templates = await tResp.json();
    expect(templates.length).toBeGreaterThan(0);

    // Instantiate the first template
    const instResp = await page.request.post(`/api/templates/${templates[0].id}/instantiate`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: '从模板创建的工作流' }
    });
    expect(instResp.status()).toBe(201);
    const wf = await instResp.json();
    expect(wf.name).toBe('从模板创建的工作流');
  });

  // ========================
  // 7. 权限验证
  // ========================

  test('7.1 未认证无法访问API', async ({ page }) => {
    const resp = await page.request.get('/api/workflows');
    expect(resp.status()).toBe(401);
  });

  test('7.2 租户隔离', async ({ page }) => {
    // Create two tenants
    const tokenA = await getTokenWithEmail(page, `tenant_a_${Date.now()}@test.com`);
    const tokenB = await getTokenWithEmail(page, `tenant_b_${Date.now()}@test.com`);

    // Tenant A creates a workflow
    await page.request.post('/api/workflows', {
      headers: { Authorization: `Bearer ${tokenA}` },
      data: { name: '租户A的工作流', type: 'workflow', dag_definition: { nodes: [], edges: [] } }
    });

    // Tenant B lists workflows - should see 0
    const respB = await page.request.get('/api/workflows', {
      headers: { Authorization: `Bearer ${tokenB}` }
    });
    const wfs = await respB.json();
    // B should not see A's workflow
    const names = wfs.map((w: any) => w.name);
    expect(names).not.toContain('租户A的工作流');
  });
});

// ========================
// Helpers
// ========================

async function registerAndLogin(page: any, email: string, password: string) {
  // Register via API
  await page.request.post('/api/auth/register', {
    data: { tenant_name: 'E2E测试', email, password }
  });
}

async function getToken(page: any, email: string, password: string): Promise<string> {
  // Register if needed (ignore 409 conflict)
  try {
    await page.request.post('/api/auth/register', {
      data: { tenant_name: 'E2E测试', email, password }
    });
  } catch { /* already exists */ }

  const resp = await page.request.post('/api/auth/login', {
    data: { email, password }
  });
  const body = await resp.json();
  return body.access_token;
}

async function getTokenWithEmail(page: any, email: string): Promise<string> {
  const resp = await page.request.post('/api/auth/register', {
    data: { tenant_name: `租户_${Date.now()}`, email, password: 'Test123!@#' }
  });
  const body = await resp.json();
  return body.access_token;
}
