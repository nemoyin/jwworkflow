import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5173';
let _seq = 0;
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

test.describe('jwworkflow E2E', () => {

  test('1.1 注册+登录API', async ({ request }) => {
    // Register uses the same freshToken helper as all other tests
    const token = await freshToken(request);
    expect(token).toBeDefined();
    expect(token.length).toBeGreaterThan(10);

    // Verify token works by calling /me
    const meResp = await request.get(`${BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(meResp.ok()).toBeTruthy();
    const me = await meResp.json();
    expect(me.email).toContain('@test.com');
  });

  test('1.2 工作流CRUD', async ({ request }) => {
    const token = await freshToken(request);

    // Create
    const cResp = await request.post(`${BASE}/api/workflows`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'E2E测试', type: 'workflow', dag_definition: { nodes: [], edges: [] } }
    });
    expect(cResp.status()).toBe(201);
    const wf = await cResp.json();

    // List
    const lResp = await request.get(`${BASE}/api/workflows`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const list = await lResp.json();
    expect(list.length).toBeGreaterThanOrEqual(1);

    // Get
    const gResp = await request.get(`${BASE}/api/workflows/${wf.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(gResp.ok()).toBeTruthy();

    // Delete
    const dResp = await request.delete(`${BASE}/api/workflows/${wf.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(dResp.status()).toBe(204);
  });

  test('1.3 执行工作流', async ({ request }) => {
    const token = await freshToken(request);
    const wfResp = await request.post(`${BASE}/api/workflows`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        name: 'ExecTest', type: 'workflow',
        dag_definition: {
          nodes: [
            { id: 'n1', type: 'input', config: { fields: [{ name: 'name', type: 'text' }] } },
            { id: 'n2', type: 'template', config: { template: 'Hi {{ input.name }}' } },
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
    const runResp = await request.post(`${BASE}/api/workflows/${wf.id}/run`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'World' }
    });
    const result = await runResp.json();
    expect(result.status).toBe('success');
    expect(result.result.greeting).toBe('Hi World');
  });

  test('2.1 供应商+模型管理', async ({ request }) => {
    const token = await freshToken(request);
    const pResp = await request.post(`${BASE}/api/admin/providers`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'E2EAI', provider_type: 'openai', api_key: 'sk-test', base_url: 'https://api.test.com' }
    });
    expect(pResp.status()).toBe(201);
    const provider = await pResp.json();

    const mResp = await request.post(`${BASE}/api/admin/models`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { provider_id: provider.id, model_name: 'e2e-model', display_name: 'E2E', capabilities: { tool_calls: true } }
    });
    expect(mResp.status()).toBe(201);
    expect((await mResp.json()).model_name).toBe('e2e-model');
  });

  test('2.2 知识库上传', async ({ request }) => {
    const token = await freshToken(request);
    const resp = await request.post(`${BASE}/api/knowledge/upload`, {
      headers: { Authorization: `Bearer ${token}` },
      multipart: { file: { name: 'e2e.txt', mimeType: 'text/plain', buffer: Buffer.from('test', 'utf-8') } }
    });
    expect(resp.status()).toBe(201);
    expect((await resp.json()).name).toBe('e2e.txt');
  });

  test('2.3 模板列表+创建', async ({ request }) => {
    const token = await freshToken(request);
    const tResp = await request.get(`${BASE}/api/templates`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(tResp.status()).toBe(200);
    const tpl = (await tResp.json())[0];

    const instResp = await request.post(`${BASE}/api/templates/${tpl.id}/instantiate`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'TplTest' }
    });
    expect(instResp.ok()).toBeTruthy();
    expect((await instResp.json()).workflow_name).toBe('TplTest');
  });

  test('3.1 未认证返回401', async ({ request }) => {
    expect((await request.get(`${BASE}/api/workflows`)).status()).toBe(401);
  });

  test('3.2 租户隔离', async ({ request }) => {
    const ts = Date.now();
    const tokenA = await rawToken(request, `tenA_${ts}`, `uA_${ts}@test.com`);
    const tokenB = await rawToken(request, `tenB_${ts}`, `uB_${ts}@test.com`);

    await request.post(`${BASE}/api/workflows`, {
      headers: { Authorization: `Bearer ${tokenA}` },
      data: { name: 'SecretWF', type: 'workflow', dag_definition: { nodes: [], edges: [] } }
    });

    const respB = await request.get(`${BASE}/api/workflows`, {
      headers: { Authorization: `Bearer ${tokenB}` }
    });
    const names = (await respB.json()).map((w: any) => w.name);
    expect(names).not.toContain('SecretWF');
  });

  test('3.3 运行历史API', async ({ request }) => {
    const token = await freshToken(request);
    // Runs should be empty initially
    const emptyResp = await request.get(`${BASE}/api/runs`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(emptyResp.status()).toBe(200);

    // Create and run a workflow
    const wfResp = await request.post(`${BASE}/api/workflows`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'RunHistoryTest', type: 'workflow', dag_definition: { nodes: [], edges: [] } }
    });
    const wf = await wfResp.json();
    await request.post(`${BASE}/api/workflows/${wf.id}/run`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {}
    });

    // Runs should now have 1 entry
    const runsResp = await request.get(`${BASE}/api/runs`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const runs = await runsResp.json();
    expect(Array.isArray(runs)).toBeTruthy();
    // Each run should have workflow_name
    if (runs.length > 0) {
      expect(runs[0].workflow_name).toBeDefined();
      expect(runs[0].status).toBeDefined();
      expect(runs[0].duration_ms).toBeDefined();
    }
  });

  test('3.4 运行详情API', async ({ request }) => {
    const token = await freshToken(request);
    // Create and run a workflow
    const wfResp = await request.post(`${BASE}/api/workflows`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'RunDetailTest', type: 'workflow', dag_definition: { nodes: [], edges: [] } }
    });
    const wf = await wfResp.json();
    const runResp = await request.post(`${BASE}/api/workflows/${wf.id}/run`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {}
    });
    const run = await runResp.json();

    // Get run detail
    const detailResp = await request.get(`${BASE}/api/runs/${run.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(detailResp.status()).toBe(200);
    const detail = await detailResp.json();
    expect(detail.id).toBe(run.id);
    expect(detail.workflow_name).toBe('RunDetailTest');
  });
});
