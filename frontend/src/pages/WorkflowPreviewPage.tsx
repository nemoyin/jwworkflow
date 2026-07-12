import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Descriptions, Tag, Table, Button, Modal, Input, message, Typography, Space, Alert, Spin } from 'antd';
import { PlayCircleOutlined, CodeOutlined, ShareAltOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import { useAuthStore } from '../stores/authStore';

const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;

const WorkflowPreviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const token = useAuthStore((s) => s.token);
  const [wf, setWf] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [result, setResult] = useState<any>(null);
  const [running, setRunning] = useState(false);
  const [embedModal, setEmbedModal] = useState(false);
  const [apiModal, setApiModal] = useState(false);

  useEffect(() => {
    if (!id || !token) return;
    api.setToken(token);
    api.get<any>(`/workflows/${id}/preview`).then(setWf).catch(() => message.error('加载失败')).finally(() => setLoading(false));
  }, [id, token]);

  const handleRun = async () => {
    if (!id) return;
    setRunning(true);
    setResult(null);
    try {
      const res: any = await api.post(`/workflows/${id}/run`, inputs);
      setResult(res);
    } catch (e: any) {
      setResult({ status: 'failed', error: e.message || '执行失败' });
    }
    setRunning(false);
  };

  if (loading) return <div style={{ textAlign: 'center', padding: 60 }}><Spin size="large" /></div>;
  if (!wf) return <div style={{ textAlign: 'center', padding: 60 }}>工作流不存在</div>;

  const embedCode = `<iframe src="${window.location.origin}/preview/${id}" width="100%" height="600" frameborder="0"></iframe>`;
  const apiEndpoint = `POST ${window.location.origin}/api/workflows/${id}/execute`;

  return (
    <div style={{ maxWidth: 800, margin: '24px auto', padding: '0 16px' }}>
      <Card>
        <Title level={3}>{wf.name}</Title>
        <Paragraph type="secondary">{wf.description || '暂无描述'}</Paragraph>
        <Tag color={wf.type === 'chatflow' ? 'purple' : 'blue'}>{wf.type === 'chatflow' ? '对话流' : '工作流'}</Tag>

        <Descriptions column={1} size="small" style={{ marginTop: 16 }}>
          <Descriptions.Item label="输入参数">
            {wf.input_fields?.length > 0 ? (
              <Table dataSource={wf.input_fields} columns={[
                { title: '字段名', dataIndex: 'name', key: 'name' },
                { title: '类型', dataIndex: 'type', key: 'type', render: (t: string) => <Tag>{t}</Tag> },
                { title: '说明', dataIndex: 'label', key: 'label' },
              ]} rowKey="name" pagination={false} size="small" />
            ) : <Text type="secondary">无输入参数</Text>}
          </Descriptions.Item>
        </Descriptions>

        <div style={{ marginTop: 16 }}>
          <Text strong>输入参数：</Text>
          <Space direction="vertical" style={{ width: '100%', marginTop: 8 }}>
            {(wf.input_fields || []).map((f: any) => (
              <div key={f.name}>
                <Text style={{ fontSize: 12 }}>{f.label || f.name}:</Text>
                {f.type === 'number' ? (
                  <Input type="number" style={{ marginTop: 4 }}
                    onChange={(e) => setInputs(s => ({ ...s, [f.name]: e.target.value }))} />
                ) : (
                  <TextArea rows={f.type === 'text' ? 3 : 1} style={{ marginTop: 4 }}
                    placeholder={`输入 ${f.label || f.name}`}
                    onChange={(e) => setInputs(s => ({ ...s, [f.name]: e.target.value }))} />
                )}
              </div>
            ))}
          </Space>
        </div>

        <Space style={{ marginTop: 16 }}>
          <Button type="primary" icon={<PlayCircleOutlined />} loading={running} onClick={handleRun}>
            {running ? '执行中...' : '运行'}
          </Button>
          <Button icon={<CodeOutlined />} onClick={() => setApiModal(true)}>API 调用</Button>
          <Button icon={<ShareAltOutlined />} onClick={() => setEmbedModal(true)}>嵌入代码</Button>
        </Space>

        {result && (
          <div style={{ marginTop: 16 }}>
            <Alert
              type={result.status === 'success' ? 'success' : 'error'}
              message={result.status === 'success' ? '执行成功' : '执行失败'}
              description={result.error || JSON.stringify(result.result || result.output, null, 2)}
              showIcon
            />
          </div>
        )}
      </Card>

      {/* Embed Modal */}
      <Modal title="嵌入代码" open={embedModal} onCancel={() => setEmbedModal(false)} footer={null}>
        <Text strong>iframe 嵌入：</Text>
        <TextArea value={embedCode} rows={4} style={{ marginTop: 8, fontFamily: 'monospace', fontSize: 12 }}
          onFocus={(e) => e.target.select()} />
        <Paragraph type="secondary" style={{ marginTop: 8, fontSize: 12 }}>
          将以上代码复制到任意 HTML 页面即可嵌入此工作流。
        </Paragraph>
      </Modal>

      {/* API Modal */}
      <Modal title="API 调用方式" open={apiModal} onCancel={() => setApiModal(false)} footer={null}>
        <Text strong>接口地址：</Text>
        <Paragraph copyable style={{ fontFamily: 'monospace', fontSize: 12 }}>{apiEndpoint}</Paragraph>
        <Text strong>请求示例：</Text>
        <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, fontSize: 11, marginTop: 8 }}>
{`curl -X POST "${window.location.origin}/api/workflows/${id}/execute" \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify(Object.fromEntries((wf.input_fields || []).map((f: any) => [f.name, ''])), null, 2)}'`}
        </pre>
      </Modal>
    </div>
  );
};

export default WorkflowPreviewPage;
