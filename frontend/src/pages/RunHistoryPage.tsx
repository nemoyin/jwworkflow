import { useEffect, useState } from 'react';
import { Table, Tag, Typography, message } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

const { Title } = Typography;

interface RunRecord {
  id: string;
  workflow_id: string;
  workflow_name: string;
  status: string;
  triggered_by: string | null;
  duration_ms: number | null;
  error: string | null;
  created_at: string;
}

const statusConfig: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
  success: { color: 'success', icon: <CheckCircleOutlined />, text: '成功' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
  running: { color: 'processing', icon: <LoadingOutlined />, text: '运行中' },
};

const formatDuration = (ms: number | null): string => {
  if (ms === null || ms === undefined) return '-';
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
  const minutes = Math.floor(ms / 60000);
  const seconds = ((ms % 60000) / 1000).toFixed(1);
  return `${minutes}m ${seconds}s`;
};

const formatDateTime = (iso: string): string => {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};

const RunHistoryPage = () => {
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await api.get<RunRecord[]>('/runs');
      setRuns(data);
    } catch {
      message.error('加载运行历史失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const columns = [
    {
      title: '工作流名称',
      dataIndex: 'workflow_name',
      key: 'workflow_name',
      render: (name: string, record: RunRecord) => (
        <a onClick={() => navigate(`/workflows/${record.workflow_id}`)}>
          {name || '(未命名)'}
        </a>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const cfg = statusConfig[status] || { color: 'default', icon: null, text: status };
        return <Tag icon={cfg.icon} color={cfg.color}>{cfg.text}</Tag>;
      },
    },
    {
      title: '耗时',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 100,
      render: (ms: number | null) => formatDuration(ms),
    },
    {
      title: '执行时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (iso: string) => formatDateTime(iso),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: RunRecord) => (
        <a onClick={() => navigate(`/workflows/${record.workflow_id}`)}>查看工作流</a>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>运行历史</Title>
      <Table
        dataSource={runs}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, showSizeChanger: false }}
        locale={{ emptyText: '暂无运行记录' }}
      />
    </div>
  );
};

export default RunHistoryPage;
