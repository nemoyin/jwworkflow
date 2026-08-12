import { useEffect, useState } from 'react';
import { Table, Tag, Typography, message } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined, BugOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

const { Title, Text, Paragraph } = Typography;

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

/** Extended detail fetched on row expand */
interface RunDetail extends RunRecord {
  input: Record<string, any>;
  output: Record<string, any>;
  node_results: any[] | null;
  error: string | null;
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
  const [runDetails, setRunDetails] = useState<Record<string, RunDetail>>({});
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

  const loadRunDetail = async (runId: string) => {
    if (runDetails[runId]) return;
    try {
      const detail = await api.get<RunDetail>(`/runs/${runId}`);
      setRunDetails((prev) => ({ ...prev, [runId]: detail }));
    } catch {
      message.error('加载运行详情失败');
    }
  };

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
      width: 80,
      render: (status: string) => {
        const cfg = statusConfig[status] || { color: 'default', icon: null, text: status };
        return <Tag icon={cfg.icon} color={cfg.color}>{cfg.text}</Tag>;
      },
    },
    {
      title: '耗时',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 80,
      render: (ms: number | null) => formatDuration(ms),
    },
    {
      title: '错误',
      dataIndex: 'error',
      key: 'error',
      width: 200,
      ellipsis: true,
      render: (err: string | null) =>
        err ? (
          <Tag icon={<BugOutlined />} color="error" style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {err.slice(0, 40)}{err.length > 40 ? '...' : ''}
          </Tag>
        ) : (
          <Text type="secondary" style={{ fontSize: 12 }}>—</Text>
        ),
    },
    {
      title: '执行时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (iso: string) => formatDateTime(iso),
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
        expandable={{
          expandedRowRender: (record) => {
            const detail = runDetails[record.id];
            if (!detail) return <Text type="secondary">点击展开加载详情...</Text>;
            return (
              <div style={{ padding: '8px 0', maxWidth: 700 }}>
                {/* Error detail (highest priority) */}
                {detail.error && (
                  <div style={{ marginBottom: 12 }}>
                    <Text strong style={{ color: '#ff4d4f', fontSize: 13 }}>❌ 错误信息</Text>
                    <pre style={{
                      marginTop: 4, padding: 8, fontSize: 11, lineHeight: 1.5,
                      background: '#fff2f0', borderRadius: 4, border: '1px solid #ffd6d6',
                      fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                      maxHeight: 200, overflow: 'auto',
                    }}>{detail.error}</pre>
                  </div>
                )}

                {/* Node results */}
                {detail.node_results && detail.node_results.length > 0 && (
                  <div style={{ marginBottom: 12 }}>
                    <Text strong style={{ fontSize: 13 }}>📋 节点执行步骤</Text>
                    {detail.node_results.map((r: any, i: number) => (
                      <div key={i} style={{
                        fontSize: 12, padding: '4px 8px', marginTop: 4,
                        background: r.type === 'node_error' ? '#fff2f0' : '#f5f5f5',
                        borderRadius: 4, fontFamily: 'monospace',
                      }}>
                        <Text style={{ color: r.type === 'node_error' ? '#ff4d4f' : '#333' }}>
                          {r.type === 'node_start' ? '▶' : r.type === 'node_done' ? '✅' : '❌'}
                          {' '}[{r.node_type}] {r.node_id}
                          {r.type === 'node_error' && `: ${r.data?.error || r.error || ''}`}
                        </Text>
                      </div>
                    ))}
                  </div>
                )}

                {/* Input / Output summary */}
                {detail.input && Object.keys(detail.input).length > 0 && (
                  <Paragraph ellipsis={{ rows: 2, expandable: true }} style={{ fontSize: 11, margin: 0 }}>
                    <Text strong style={{ fontSize: 12 }}>输入: </Text>
                    {JSON.stringify(detail.input)}
                  </Paragraph>
                )}
              </div>
            );
          },
          onExpand: (expanded: boolean, record: RunRecord) => {
            if (expanded) loadRunDetail(record.id);
          },
          rowExpandable: () => true,
        }}
      />
    </div>
  );
};

export default RunHistoryPage;
