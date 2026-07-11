import React, { useEffect, useState } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, Select, Switch, Space, Tag,
  message, Popconfirm, Tabs, Typography, Spin, Descriptions, Alert,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, EditOutlined, ApiOutlined,
  BugOutlined, CheckCircleOutlined, CloseCircleOutlined,
} from '@ant-design/icons';
import { api } from '../services/api';

interface Provider {
  id: string; name: string; provider_type: string; api_key: string;
  base_url: string; is_active: boolean; sort_order: number; model_count: number;
}

interface Model {
  id: string; provider_id: string; provider_name: string;
  model_name: string; display_name: string; capabilities: Record<string, any>;
  is_active: boolean;
}

interface TestResult {
  success: boolean; message: string; latency_ms: number;
}

const PROVIDER_TYPES = ['openai', 'deepseek', 'ollama', 'azure', 'anthropic', 'google'];

const ModelManagementPage: React.FC = () => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [providerModal, setProviderModal] = useState(false);
  const [modelModal, setModelModal] = useState(false);
  const [editingProvider, setEditingProvider] = useState<Provider | null>(null);
  const [editingModel, setEditingModel] = useState<Model | null>(null);
  const [form] = Form.useForm();
  const [modelForm] = Form.useForm();
  const [testingModel, setTestingModel] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testModalVisible, setTestModalVisible] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [providersData, modelsData] = await Promise.all([
        api.get<Provider[]>('/admin/providers'),
        api.get<Model[]>('/admin/models'),
      ]);
      setProviders(providersData);
      setModels(modelsData);
    } catch {
      message.error('加载数据失败');
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  // --- Provider ---
  const handleSaveProvider = async () => {
    const values = await form.validateFields();
    try {
      if (editingProvider) {
        await api.put(`/admin/providers/${editingProvider.id}`, values);
        message.success('供应商已更新');
      } else {
        await api.post('/admin/providers', values);
        message.success('供应商已创建');
      }
      setProviderModal(false);
      form.resetFields();
      loadData();
    } catch { message.error('操作失败'); }
  };

  const handleDeleteProvider = async (id: string) => {
    await api.delete(`/admin/providers/${id}`);
    message.success('已删除');
    loadData();
  };

  // --- Model ---
  const handleSaveModel = async () => {
    const values = await modelForm.validateFields();
    try {
      if (editingModel) {
        await api.put(`/admin/models/${editingModel.id}`, values);
        message.success('模型已更新');
      } else {
        await api.post('/admin/models', values);
        message.success('模型已注册');
      }
      setModelModal(false);
      setEditingModel(null);
      modelForm.resetFields();
      loadData();
    } catch { message.error('操作失败'); }
  };

  const handleDeleteModel = async (id: string) => {
    await api.delete(`/admin/models/${id}`);
    message.success('已删除');
    loadData();
  };

  const handleTestModel = async (modelId: string) => {
    setTestingModel(modelId);
    setTestResult(null);
    setTestModalVisible(true);
    try {
      const result = await api.post<TestResult>(`/admin/models/${modelId}/test`, {});
      setTestResult(result);
    } catch {
      setTestResult({ success: false, message: '测试请求失败', latency_ms: 0 });
    }
    setTestingModel(null);
  };

  const openModelEdit = (model: Model) => {
    setEditingModel(model);
    modelForm.setFieldsValue({
      provider_id: model.provider_id,
      model_name: model.model_name,
      display_name: model.display_name,
      capabilities: model.capabilities,
    });
    setModelModal(true);
  };

  const openModelCreate = () => {
    setEditingModel(null);
    modelForm.resetFields();
    setModelModal(true);
  };

  // --- Columns ---
  const providerColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: '类型', dataIndex: 'provider_type', key: 'provider_type',
      render: (t: string) => <Tag color="blue">{t}</Tag>,
    },
    { title: '接口地址', dataIndex: 'base_url', key: 'base_url', ellipsis: true },
    { title: '模型数', dataIndex: 'model_count', key: 'model_count', width: 80 },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? '启用' : '禁用'}</Tag>,
    },
    {
      title: '操作', key: 'action', width: 160,
      render: (_: any, record: Provider) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => {
            setEditingProvider(record);
            form.setFieldsValue(record);
            setProviderModal(true);
          }}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDeleteProvider(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const modelColumns = [
    { title: '显示名称', dataIndex: 'display_name', key: 'display_name' },
    { title: '模型名', dataIndex: 'model_name', key: 'model_name' },
    { title: '供应商', dataIndex: 'provider_name', key: 'provider_name' },
    {
      title: '能力', key: 'capabilities',
      render: (_: any, r: Model) => (
        <Space size={4}>
          {r.capabilities?.tool_calls && <Tag color="purple">工具调用</Tag>}
          {r.capabilities?.streaming && <Tag color="cyan">流式</Tag>}
          {r.capabilities?.max_tokens && <Tag>{(r.capabilities.max_tokens / 1024).toFixed(0)}K</Tag>}
        </Space>
      ),
    },
    {
      title: '操作', key: 'action', width: 200,
      render: (_: any, record: Model) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openModelEdit(record)}>编辑</Button>
          <Button size="small" icon={<BugOutlined />} onClick={() => handleTestModel(record.id)}>调试</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDeleteModel(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={4} style={{ marginBottom: 16 }}><ApiOutlined /> 模型管理</Typography.Title>

      <Tabs defaultActiveKey="models" items={[
        {
          key: 'providers',
          label: '供应商管理',
          children: (
            <Card extra={
              <Button type="primary" icon={<PlusOutlined />} onClick={() => {
                setEditingProvider(null); form.resetFields(); setProviderModal(true);
              }}>添加供应商</Button>
            }>
              <Table dataSource={providers} columns={providerColumns} rowKey="id" loading={loading} pagination={false} />
            </Card>
          ),
        },
        {
          key: 'models',
          label: '模型注册表',
          children: (
            <Card extra={
              <Button type="primary" icon={<PlusOutlined />} onClick={openModelCreate}>注册模型</Button>
            }>
              <Table dataSource={models} columns={modelColumns} rowKey="id" loading={loading} pagination={false} />
            </Card>
          ),
        },
      ]} />

      {/* Provider Modal */}
      <Modal title={editingProvider ? '编辑供应商' : '添加供应商'} open={providerModal}
        onOk={handleSaveProvider} onCancel={() => { setProviderModal(false); form.resetFields(); }}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="provider_type" label="类型" rules={[{ required: true }]}>
            <Select options={PROVIDER_TYPES.map(t => ({ label: t, value: t }))} />
          </Form.Item>
          <Form.Item name="api_key" label="API Key">
            <Input.Password placeholder={editingProvider ? '留空则不修改' : 'sk-...'} />
          </Form.Item>
          <Form.Item name="base_url" label="接口地址"><Input /></Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked"><Switch defaultChecked /></Form.Item>
        </Form>
      </Modal>

      {/* Model Modal (Create/Edit) */}
      <Modal title={editingModel ? '编辑模型' : '注册模型'} open={modelModal}
        onOk={handleSaveModel} onCancel={() => { setModelModal(false); setEditingModel(null); modelForm.resetFields(); }}>
        <Form form={modelForm} layout="vertical">
          <Form.Item name="provider_id" label="所属供应商" rules={[{ required: true }]}>
            <Select options={providers.map(p => ({ label: p.name, value: p.id }))} />
          </Form.Item>
          <Form.Item name="model_name" label="模型名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="display_name" label="展示名称"><Input /></Form.Item>
          <Form.Item label="能力标签">
            <Space>
              <Form.Item name={['capabilities', 'tool_calls']} valuePropName="checked" noStyle>
                <Switch checkedChildren="工具调用" unCheckedChildren="无" />
              </Form.Item>
              <Form.Item name={['capabilities', 'streaming']} valuePropName="checked" noStyle>
                <Switch checkedChildren="流式" unCheckedChildren="无" />
              </Form.Item>
            </Space>
          </Form.Item>
          <Form.Item name={['capabilities', 'max_tokens']} label="最大 Token">
            <Input type="number" placeholder="4096" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Test Result Modal */}
      <Modal title="模型调试结果" open={testModalVisible}
        onCancel={() => setTestModalVisible(false)} footer={null}>
        {testingModel ? (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin tip="正在测试模型连接..." />
          </div>
        ) : testResult ? (
          <div>
            <Alert
              type={testResult.success ? 'success' : 'error'}
              message={testResult.success ? '连接成功' : '连接失败'}
              description={testResult.message}
              showIcon
              icon={testResult.success ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              style={{ marginBottom: 12 }}
            />
            <Descriptions column={1} size="small">
              <Descriptions.Item label="状态">{testResult.success ? '✅ 成功' : '❌ 失败'}</Descriptions.Item>
              <Descriptions.Item label="延迟">{testResult.latency_ms}ms</Descriptions.Item>
            </Descriptions>
          </div>
        ) : null}
      </Modal>
    </div>
  );
};

export default ModelManagementPage;
