/** 工具市场：浏览和测试预置工具 + MCP 工作流工具 */

import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Typography, Tag, Button, Modal, Input, Spin, Tabs, List, Space } from 'antd';
import { SearchOutlined, CalculatorOutlined, ClockCircleOutlined, CloudOutlined, ApiOutlined, PlayCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { api } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const toolIcons: Record<string, any> = {
  web_search: <SearchOutlined />,
  calculator: <CalculatorOutlined />,
  current_time: <ClockCircleOutlined />,
  weather: <CloudOutlined />,
};

const ToolsPage: React.FC = () => {
  const [tools, setTools] = useState<any[]>([]);
  const [mcpTools, setMcpTools] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [testModal, setTestModal] = useState<any>(null);
  const [testInput, setTestInput] = useState('{}');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get<{ tools: any[] }>('/tools').then(r => r.tools).catch(() => []),
      api.get<{ tools: any[] }>('/mcp/tools').then(r => r.tools).catch(() => []),
    ]).then(([t, m]) => {
      setTools(t);
      setMcpTools(m);
    }).finally(() => setLoading(false));
  }, []);

  const handleTest = async () => {
    if (!testModal) return;
    setTesting(true);
    setTestResult(null);
    try {
      let input = {};
      try { input = JSON.parse(testInput); } catch { input = { input: testInput }; }
      const res = await api.post(`/tools/${testModal.name}/execute`, input);
      setTestResult(res);
    } catch (e: any) {
      setTestResult({ status: 'error', error: e.message });
    }
    setTesting(false);
  };

  if (loading) return <div style={{ textAlign: 'center', padding: 60 }}><Spin size="large" /></div>;

  return (
    <div>
      <Title level={4}><ApiOutlined /> 工具市场</Title>

      <Tabs defaultActiveKey="builtin" items={[
        {
          key: 'builtin',
          label: `预置工具 (${tools.length})`,
          children: (
            <Row gutter={[16, 16]}>
              {tools.map(tool => (
                <Col xs={24} sm={12} md={8} key={tool.name}>
                  <Card hoverable
                    onClick={() => { setTestModal(tool); setTestInput(JSON.stringify(tool.parameters?.properties ?
                      Object.fromEntries(Object.keys(tool.parameters.properties).map(k => [k, ''])) : {}, null, 2)); setTestResult(null); }}
                    style={{ borderRadius: 8 }}
                  >
                    <Space>
                      <span style={{ fontSize: 24, color: '#1677ff' }}>{toolIcons[tool.name] || <ApiOutlined />}</span>
                      <div>
                        <Text strong>{tool.name}</Text>
                        <Paragraph type="secondary" style={{ margin: 0, fontSize: 12 }}>{tool.description}</Paragraph>
                      </div>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          ),
        },
        {
          key: 'mcp',
          label: `MCP 工作流工具 (${mcpTools.length})`,
          children: (
            <List
              dataSource={mcpTools}
              renderItem={(tool: any) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<ApiOutlined style={{ fontSize: 20, color: '#722ed1' }} />}
                    title={tool._workflow_name || tool.name}
                    description={<Text type="secondary" style={{ fontSize: 12 }}>{tool.description}</Text>}
                  />
                  <Space>
                    <Tag color="purple">MCP</Tag>
                    <Tag>{Object.keys(tool.inputSchema?.properties || {}).length} 参数</Tag>
                  </Space>
                </List.Item>
              )}
              locale={{ emptyText: '暂无已发布的工作流工具。在编辑器中发布工作流后，将出现在此。' }}
            />
          ),
        },
      ]} />

      {/* Test Modal */}
      <Modal title={`测试工具: ${testModal?.name}`} open={!!testModal}
        onCancel={() => setTestModal(null)} footer={null} width={600}>
        <div style={{ marginBottom: 12 }}>
          <Text strong style={{ fontSize: 12 }}>输入参数 (JSON)</Text>
          <TextArea rows={5} value={testInput} onChange={e => setTestInput(e.target.value)}
            style={{ marginTop: 4, fontFamily: 'monospace', fontSize: 12 }} />
        </div>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleTest} loading={testing}>
          {testing ? '执行中...' : '测试'}
        </Button>
        {testResult && (
          <div style={{ marginTop: 12, background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
            <Text strong><CheckCircleOutlined style={{ color: testResult.status === 'success' ? '#52c41a' : '#ff4d4f' }} /> 结果:</Text>
            <pre style={{ marginTop: 4, fontSize: 11, whiteSpace: 'pre-wrap' }}>{JSON.stringify(testResult, null, 2)}</pre>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ToolsPage;
