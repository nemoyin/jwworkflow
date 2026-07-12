/** jwworkflow E2E 全流程测试 */
import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5173';
let _seq = 0;

// ====================== Helpers ======================

async function freshToken(request: any): Promise<string> {
  _seq++;
  return rawToken(request, `ten_${Date.now()}_${_seq}`, `u_${Date.now()}_${_seq}@test.com`);
}
async function rawToken(request: any, tenant: string, email: string): Promise<string> {
  const resp = await request.post(`${BASE}/api/auth/register`, {
    data: { tenant_name: tenant, email, password: 'Test123!@#' }
  });
  return (await resp.json()).access_token;
}

async function createSimpleWF(request: any, token: string, name: string) {
  const dag = {
    nodes: [
      { id: 'n1', type: 'input', config: { fields: [{ name: 'x', type: 'text' }] } },
      { id: 'n2', type: 'template', config: { template: 'Hi {{ input.x }}' } },
      { id: 'n3', type: 'output', config: { variables: [{ name: 'out', source: 'n2.output' }] } },
    ],
    edges: [
      { id: 'e1', source: 'n1', target: 'n2' },
      { id: 'e2', source: 'n2', target: 'n3' },
    ],
  };
  const resp = await request.post(`${BASE}/api/workflows`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { name, type: 'workflow', dag_definition: dag },
  });
  return resp.json();
}

// ====================== Tests ======================

test.describe('jwworkflow E2E', () => {

  // ---- Auth ----
  test('A1 注册+登录+获取用户信息', async ({ request }) => {
    const token = await freshToken(request);
    expect(token).toBeDefined();
    expect(token.length).toBeGreaterThan(20);

    // Verify token with /me
    const meResp = await request.get(`${BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(meResp.ok()).toBeTruthy();
    const me = await meResp.json();
    expect(me.email).toContain('@test.com');
    expect(me.role).toBe('admin');
  });

  test('A2 登录失败返回401', async ({ request }) => {
    const resp = await request.post(`${BASE}/api/auth/login`, {
      data: { email: 'wrong@test.com', password: 'wrong' }
    });
    expect(resp.status()).toBe(401);
  });

  // ---- Workflow CRUD ----
  test('B1 工作流完整CRUD', async ({ request }) => {
    const token = await freshToken(request);

    // Create
    const wf = await createSimpleWF(request, token, 'CRUD测试');
    expect(wf.id).toBeDefined();
    expect(wf.name).toBe('CRUD测试');

    // Get by ID
    const getResp = await request.get(`${BASE}/api/workflows/${wf.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(getResp.ok()).toBeTruthy();

    // List
    const listResp = await request.get(`${BASE}/api/workflows`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const list = await listResp.json();
    expect(Array.isArray(list)).toBeTruthy();
    expect(list.some((w: any) => w.id === wf.id)).toBeTruthy();

    // Update
    const updResp = await request.put(`${BASE}/api/workflows/${wf.id}`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'CRUD已更新' }
    });
    expect(updResp.ok()).toBeTruthy();
    expect((await updResp.json()).name).toBe('CRUD已更新');

    // Delete
    const delResp = await request.delete(`${BASE}/api/workflows/${wf.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(delResp.status()).toBe(204);

    // Verify deleted
    const getDelResp = await request.get(`${BASE}/api/workflows/${wf.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(getDelResp.status()).toBe(404);
  });

  // ---- Workflow Execution ----
  test('B2 工作流同步执行', async ({ request }) => {
    const token = await freshToken(request);
    const wf = await createSimpleWF(request, token, '执行测试');

    const runResp = await request.post(`${BASE}/api/workflows/${wf.id}/run`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { x: 'World' }
    });
    expect(runResp.ok()).toBeTruthy();
    const run = await runResp.json();
    expect(run.status).toBe('success');
    expect(run.result.out).toBe('Hi World');
    expect(run.duration_ms).toBeDefined();
  });

  test('B3 外部系统调用工作流', async ({ request }) => {
    const token = await freshToken(request);
    const wf = await createSimpleWF(request, token, '外部调用测试');

    const execResp = await request.post(`${BASE}/api/workflows/${wf.id}/execute`, {
      data: { x: 'External' }
    });
    expect(execResp.ok()).toBeTruthy();
    const result = await execResp.json();
    expect(result.status).toBe('success');
    expect(result.output.out).toBe('Hi External');
  });

  // ---- Webhook ----
  test('B4 Webhook触发工作流', async ({ request }) => {
    const token = await freshToken(request);
    const wf = await createSimpleWF(request, token, 'Webhook测试');

    const webhookResp = await request.post(`${BASE}/api/webhooks/trigger/${wf.id}`, {
      data: { x: 'Webhook' }
    });
    expect(webhookResp.ok()).toBeTruthy();
    const result = await webhookResp.json();
    expect(result.status).toBe('success');
  });

  // ---- Model Management ----
  test('C1 供应商+模型管理', async ({ request }) => {
    const token = await freshToken(request);

    // List providers (empty initially)
    const listResp = await request.get(`${BASE}/api/admin/providers`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(listResp.status()).toBe(200);

    // Create provider
    const pResp = await request.post(`${BASE}/api/admin/providers`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'E2EAI', provider_type: 'openai', api_key: 'sk-test', base_url: 'https://api.test.com' }
    });
    expect(pResp.status()).toBe(201);
    const provider = await pResp.json();

    // Create model
    const mResp = await request.post(`${BASE}/api/admin/models`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { provider_id: provider.id, model_name: 'e2e-model', display_name: 'E2E', capabilities: { tool_calls: true, max_tokens: 4096 } }
    });
    expect(mResp.status()).toBe(201);

    // List models
    const modelsResp = await request.get(`${BASE}/api/admin/models`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const models = await modelsResp.json();
    expect(models.some((m: any) => m.model_name === 'e2e-model')).toBeTruthy();

    // Update model
    const mid = models.find((m: any) => m.model_name === 'e2e-model').id;
    const updResp = await request.put(`${BASE}/api/admin/models/${mid}`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { display_name: 'E2E Updated' }
    });
    expect(updResp.ok()).toBeTruthy();

    // Available models (dropdown format)
    const availResp = await request.get(`${BASE}/api/admin/models/available`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const avail = await availResp.json();
    expect(avail.length).toBeGreaterThanOrEqual(1);
    expect(avail[0].label).toBeDefined();
    expect(avail[0].model_name).toBeDefined();

    // Delete model
    await request.delete(`${BASE}/api/admin/models/${mid}`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    // Delete provider
    await request.delete(`${BASE}/api/admin/providers/${provider.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
  });

  // ---- Knowledge Base ----
  test('D1 知识库列表API', async ({ request }) => {
    const token = await freshToken(request);

    // List (may be empty, should return 200)
    const listResp = await request.get(`${BASE}/api/knowledge`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(listResp.status()).toBe(200);
    const body = await listResp.json();
    const docs = body.documents || body;
    expect(Array.isArray(docs)).toBeTruthy();
  });

  // ---- Templates ----
  test('E1 模板列表+从模板创建', async ({ request }) => {
    const token = await freshToken(request);

    // List templates
    const tResp = await request.get(`${BASE}/api/templates`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(tResp.status()).toBe(200);
    const templates = await tResp.json();
    expect(templates.length).toBeGreaterThanOrEqual(4);

    // Instantiate from template
    const first = templates[0];
    const instResp = await request.post(`${BASE}/api/templates/${first.id}/instantiate`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: '从模板创建' }
    });
    expect(instResp.ok()).toBeTruthy();
    const inst = await instResp.json();
    expect(inst.workflow_name).toBe('从模板创建');
    expect(inst.workflow_id).toBeDefined();

    // Skip running the template workflow (depends on template type)
    // Just verify it was created successfully
    const getResp = await request.get(`${BASE}/api/workflows/${inst.workflow_id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(getResp.ok()).toBeTruthy();
  });

  // ---- DSL ----
  test('F1 DSL导出+导入', async ({ request }) => {
    const token = await freshToken(request);
    const wf = await createSimpleWF(request, token, 'DSL测试');

    // Export
    const exportResp = await request.get(`${BASE}/api/dsl/export/${wf.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(exportResp.ok()).toBeTruthy();
    const dsl = await exportResp.json();
    expect(dsl.dsl_version).toBe('1.0');
    expect(dsl.dag_definition.nodes.length).toBe(3);

    // Import
    const importResp = await request.post(`${BASE}/api/dsl/import`, {
      headers: { Authorization: `Bearer ${token}` },
      data: dsl
    });
    expect(importResp.status()).toBe(201);
    const imported = await importResp.json();
    expect(imported.name).toBe('DSL测试');
    expect(imported.status).toBe('imported');
  });

  // ---- Analytics ----
  test('G1 分析统计API', async ({ request }) => {
    const token = await freshToken(request);

    const statsResp = await request.get(`${BASE}/api/analytics/stats`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(statsResp.ok()).toBeTruthy();
    const stats = await statsResp.json();
    expect(stats.total_runs).toBeDefined();
    expect(stats.total_workflows).toBeDefined();

    const recentResp = await request.get(`${BASE}/api/analytics/runs/recent`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(recentResp.ok()).toBeTruthy();
    const recent = await recentResp.json();
    expect(Array.isArray(recent)).toBeTruthy();
  });

  // ---- Tools / MCP ----
  test('H1 工具市场和MCP', async ({ request }) => {
    const token = await freshToken(request);

    // Built-in tools
    const toolsResp = await request.get(`${BASE}/api/tools`);
    expect(toolsResp.ok()).toBeTruthy();
    const tools = (await toolsResp.json()).tools;
    expect(tools.length).toBeGreaterThanOrEqual(4);
    const toolNames = tools.map((t: any) => t.name);
    expect(toolNames).toContain('calculator');

    // Execute calculator
    const calcResp = await request.post(`${BASE}/api/tools/calculator/execute`, {
      data: { expression: '1+2*3' }
    });
    expect(calcResp.ok()).toBeTruthy();
    const calcResult = await calcResp.json();
    expect(calcResult.status).toBe('success');
    expect(calcResult.result.result).toBe(7);

    // MCP tools
    const mcpResp = await request.get(`${BASE}/api/mcp/tools`);
    expect(mcpResp.ok()).toBeTruthy();
  });

  // ---- Chatflow / Conversations ----
  test('I1 Chatflow对话', async ({ request }) => {
    const token = await freshToken(request);
    const wf = await createSimpleWF(request, token, 'Chatflow测试');

    // Create conversation
    const convResp = await request.post(`${BASE}/api/conversations`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { workflow_id: wf.id }
    });
    expect(convResp.status()).toBe(201);
    const conv = await convResp.json();
    expect(conv.id).toBeDefined();

    // List conversations
    const listResp = await request.get(`${BASE}/api/conversations`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(listResp.ok()).toBeTruthy();
  });

  // ---- Run History ----
  test('J1 运行历史', async ({ request }) => {
    const token = await freshToken(request);

    // Create and run
    const wf = await createSimpleWF(request, token, '历史测试');
    await request.post(`${BASE}/api/workflows/${wf.id}/run`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { x: 'test' }
    });

    // List runs
    const runsResp = await request.get(`${BASE}/api/runs`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const runs = await runsResp.json();
    expect(Array.isArray(runs)).toBeTruthy();
    expect(runs.length).toBeGreaterThanOrEqual(1);
    expect(runs[0].workflow_name).toBe('历史测试');
    expect(runs[0].status).toBe('success');

    // Run detail
    const detailResp = await request.get(`${BASE}/api/runs/${runs[0].id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(detailResp.ok()).toBeTruthy();
    const detail = await detailResp.json();
    expect(detail.input).toBeDefined();
    expect(detail.output).toBeDefined();
  });

  // ---- User Management ----
  test('K1 用户管理', async ({ request }) => {
    const token = await freshToken(request);

    // List users
    const listResp = await request.get(`${BASE}/api/admin/users`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(listResp.ok()).toBeTruthy();
    const users = await listResp.json();
    expect(Array.isArray(users)).toBeTruthy();

    // Invite member
    const inviteResp = await request.post(`${BASE}/api/admin/users`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { email: `member_${Date.now()}@test.com`, role: 'member', password: 'Test123!@#' }
    });
    expect(inviteResp.status()).toBe(201);
    const newUser = await inviteResp.json();
    expect(newUser.role).toBe('member');
  });

  // ---- Tenant Isolation ----
  test('L1 租户数据隔离', async ({ request }) => {
    const ts = Date.now();
    const tokenA = await rawToken(request, `tenA_${ts}`, `uA_${ts}@test.com`);
    const tokenB = await rawToken(request, `tenB_${ts}`, `uB_${ts}@test.com`);

    // A creates a workflow
    await request.post(`${BASE}/api/workflows`, {
      headers: { Authorization: `Bearer ${tokenA}` },
      data: { name: 'TenantSecret', type: 'workflow', dag_definition: { nodes: [], edges: [] } }
    });

    // B lists - should NOT see A's workflow
    const respB = await request.get(`${BASE}/api/workflows`, {
      headers: { Authorization: `Bearer ${tokenB}` }
    });
    const names = (await respB.json()).map((w: any) => w.name);
    expect(names).not.toContain('TenantSecret');
  });

  // ---- Unauthorized Access ----
  test('M1 未认证被拒绝', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/workflows`);
    expect([401, 403]).toContain(resp.status());
  });

  test('M2 无效Token被拒绝', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/workflows`, {
      headers: { Authorization: 'Bearer invalid_token_xxx' }
    });
    expect([401, 403]).toContain(resp.status());
  });
});
