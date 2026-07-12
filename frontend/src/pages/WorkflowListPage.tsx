import { useEffect, useState } from 'react';
import { Button, Table, Typography, Space, Tag, message, Popconfirm, Upload } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, PlayCircleOutlined, UploadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

const { Title } = Typography;

interface WorkflowItem {
  id: string;
  name: string;
  description: string;
  type: string;
  status: string;
  version: number;
  created_at: string;
}

const WorkflowListPage = () => {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [loading, setLoading] = useState(false);

  const loadWorkflows = async () => {
    setLoading(true);
    try {
      const data = await api.get<WorkflowItem[]>('/workflows');
      setWorkflows(data);
    } catch {
      // Not authenticated or no workflows yet
      setWorkflows([]);
    }
    setLoading(false);
  };

  useEffect(() => { loadWorkflows(); }, []);

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/workflows/${id}`);
      message.success('已删除');
      loadWorkflows();
    } catch {
      message.error('删除失败');
    }
  };

  const handleRun = async (id: string) => {
    try {
      const res: any = await api.post(`/workflows/${id}/run`, {});
      message.success('执行成功');
      console.log('Run result:', res);
    } catch {
      message.error('执行失败');
    }
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '类型', dataIndex: 'type', key: 'type',
      render: (t: string) => <Tag>{t === 'chatflow' ? '对话流' : '工作流'}</Tag>,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => (
        <Tag color={s === 'published' ? 'green' : 'default'}>
          {s === 'published' ? '已发布' : '草稿'}
        </Tag>
      ),
    },
    { title: '版本', dataIndex: 'version', key: 'version', width: 60 },
    {
      title: '操作', key: 'action', width: 200,
      render: (_: any, record: WorkflowItem) => (
        <Space>
          <Button size="small" icon={<EditOutlined />}
            onClick={() => navigate(`/workflows/${record.id}`)}>编辑</Button>
          <Button size="small" icon={<PlayCircleOutlined />}
            onClick={() => handleRun(record.id)}>运行</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>工作流列表</Title>
        <Space>
          <Upload accept=".json,.dsl.json" showUploadList={false}
            beforeUpload={(file) => {
              const reader = new FileReader();
              reader.onload = async (e) => {
                try {
                  const dsl = JSON.parse(e.target?.result as string);
                  const res: any = await api.post('/dsl/import', dsl);
                  message.success(`已导入「${res.name}」`);
                  window.location.reload();
                } catch { message.error('导入失败，请检查文件格式'); }
              };
              reader.readAsText(file);
              return false;
            }}>
            <Button icon={<UploadOutlined />}>导入 DSL</Button>
          </Upload>
          <Button type="primary" icon={<PlusOutlined />}
            onClick={() => navigate('/workflows/new')}>
            新建工作流
          </Button>
        </Space>
      </div>
      <Table
        dataSource={workflows}
        columns={columns}
        rowKey="id"
        loading={loading}
        locale={{ emptyText: '暂无工作流，点击"新建工作流"开始创建' }}
      />
    </div>
  );
};

export default WorkflowListPage;
