import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Row,
  Col,
  Card,
  Tag,
  Spin,
  message,
  Modal,
  Input,
  Form,
  Space,
} from 'antd';
import {
  FileTextOutlined,
  TeamOutlined,
  CustomerServiceOutlined,
  SearchOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import { api } from '../services/api';
import { useAuthStore } from '../stores/authStore';

const { Title, Paragraph } = Typography;

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  dag_definition: Record<string, unknown>;
  icon: string;
  sort_order: number;
  is_builtin: boolean;
  created_at: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  compliance: '合规审查',
  collusion: '围串标分析',
  interview: '模拟谈话',
  chat: 'AI 对话',
  general: '通用',
};

const CATEGORY_COLORS: Record<string, string> = {
  compliance: 'blue',
  collusion: 'red',
  interview: 'purple',
  chat: 'green',
  general: 'default',
};

const ICON_MAP: Record<string, React.ReactNode> = {
  FileTextOutlined: <FileTextOutlined style={{ fontSize: 48, color: '#1677ff' }} />,
  TeamOutlined: <TeamOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />,
  CustomerServiceOutlined: <CustomerServiceOutlined style={{ fontSize: 48, color: '#722ed1' }} />,
  SearchOutlined: <SearchOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
};

const TemplateMarketPage = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [instantiating, setInstantiating] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const token = useAuthStore((state) => state.token);

  useEffect(() => {
    if (token) {
      api.setToken(token);
    }
    fetchTemplates();
  }, [token]);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const data = await api.get<Template[]>('/templates');
      setTemplates(data);
    } catch {
      message.error('获取模板列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleInstantiate = (tpl: Template) => {
    setSelectedTemplate(tpl);
    form.resetFields();
    form.setFieldsValue({ name: `${tpl.name}` });
    setModalVisible(true);
  };

  const handleConfirm = async () => {
    if (!selectedTemplate) return;
    try {
      const values = await form.validateFields();
      setInstantiating(selectedTemplate.id);
      setModalVisible(false);

      const result = await api.post<{ workflow_id: string; workflow_name: string }>(
        `/templates/${selectedTemplate.id}/instantiate`,
        {
          name: values.name,
          description: values.description,
        },
      );

      message.success(`已从模板创建「${result.workflow_name}」`);
      // 跳转到工作流编辑器
      navigate(`/workflows/${result.workflow_id}`);
    } catch {
      // 表单校验失败或 API 报错时不做额外处理
    } finally {
      setInstantiating(null);
    }
  };

  const getIcon = (iconName: string): React.ReactNode => {
    return ICON_MAP[iconName] || <AppstoreOutlined style={{ fontSize: 48, color: '#999' }} />;
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" tip="加载模板..." />
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Title level={2} style={{ marginBottom: 8 }}>模板市场</Title>
      <Paragraph type="secondary" style={{ marginBottom: 24 }}>
        从预置模板快速创建工作流，一键部署常见业务场景
      </Paragraph>

      <Spin spinning={!!instantiating} tip="正在创建工作流...">
        <Row gutter={[24, 24]}>
          {templates.map((tpl) => (
            <Col xs={24} sm={12} lg={8} xl={6} key={tpl.id}>
              <Card
                hoverable
                onClick={() => handleInstantiate(tpl)}
                style={{ height: '100%', borderRadius: 8 }}
                bodyStyle={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  textAlign: 'center',
                  padding: 32,
                }}
              >
                <div style={{ marginBottom: 16 }}>
                  {getIcon(tpl.icon)}
                </div>
                <Title level={4} style={{ marginBottom: 8 }}>
                  {tpl.name}
                </Title>
                <Paragraph
                  type="secondary"
                  ellipsis={{ rows: 2 }}
                  style={{ marginBottom: 12, fontSize: 13 }}
                >
                  {tpl.description}
                </Paragraph>
                <Space>
                  <Tag color={CATEGORY_COLORS[tpl.category] || 'default'}>
                    {CATEGORY_LABELS[tpl.category] || tpl.category}
                  </Tag>
                  {tpl.is_builtin && <Tag color="gold">内置</Tag>}
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </Spin>

      <Modal
        title={`从模板创建：${selectedTemplate?.name || ''}`}
        open={modalVisible}
        onOk={handleConfirm}
        onCancel={() => setModalVisible(false)}
        okText="创建工作流"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="工作流名称"
            rules={[{ required: true, message: '请输入工作流名称' }]}
          >
            <Input placeholder="请输入工作流名称" />
          </Form.Item>
          <Form.Item name="description" label="描述（可选）">
            <Input.TextArea placeholder="请输入描述信息" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TemplateMarketPage;
