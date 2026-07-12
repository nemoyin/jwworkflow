/** LLMOps 分析仪表盘 */

import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Typography, Spin, message } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, ThunderboltOutlined, ApiOutlined } from '@ant-design/icons';
import { api } from '../services/api';

const { Title } = Typography;

interface Stats {
  total_runs: number; success_runs: number; failed_runs: number;
  success_rate: number; total_tokens: number; avg_duration_ms: number;
  total_workflows: number;
}

interface RunRecord {
  id: string; workflow_name: string; status: string;
  duration_ms: number; total_tokens: number; model_used: string;
  created_at: string;
}

const AnalyticsDashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<Stats>('/analytics/stats').catch(() => null),
      api.get<RunRecord[]>('/analytics/runs/recent').catch(() => []),
    ]).then(([s, r]) => {
      if (s) setStats(s);
      setRuns(r);
    }).catch(() => message.error('加载失败'))
    .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: 60 }}><Spin size="large" /></div>;

  const statusRender = (s: string) => {
    const map: Record<string, { color: string; icon: any }> = {
      success: { color: 'green', icon: <CheckCircleOutlined /> },
      failed: { color: 'red', icon: <CloseCircleOutlined /> },
      running: { color: 'blue', icon: <ClockCircleOutlined /> },
    };
    const cfg = map[s] || { color: 'default', icon: null };
    return <Tag color={cfg.color}>{cfg.icon} {s}</Tag>;
  };

  return (
    <div>
      <Title level={4}><ThunderboltOutlined /> LLMOps 分析</Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="总运行次数" value={stats?.total_runs || 0} prefix={<ApiOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="成功率" value={stats?.success_rate || 0} suffix="%" prefix={<CheckCircleOutlined />} valueStyle={{ color: (stats?.success_rate || 0) > 80 ? '#3f8600' : '#cf1322' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="平均耗时" value={stats?.avg_duration_ms || 0} suffix="ms" prefix={<ClockCircleOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="工作流数" value={stats?.total_workflows || 0} prefix={<ApiOutlined />} /></Card>
        </Col>
      </Row>

      <Card title="最近运行记录" style={{ marginTop: 16 }}>
        <Table dataSource={runs} rowKey="id" pagination={false} size="small"
          columns={[
            { title: '工作流', dataIndex: 'workflow_name', key: 'name' },
            { title: '状态', dataIndex: 'status', key: 'status', render: statusRender },
            { title: '耗时', dataIndex: 'duration_ms', key: 'duration', render: (v: number) => v ? `${v}ms` : '-' },
            { title: 'Token', dataIndex: 'total_tokens', key: 'tokens', render: (v: number) => v || '-' },
            { title: '模型', dataIndex: 'model_used', key: 'model', render: (v: string) => v ? <Tag>{v}</Tag> : '-' },
            { title: '时间', dataIndex: 'created_at', key: 'time', render: (v: string) => v?.substring(0, 19)?.replace('T', ' ') },
          ]}
        />
      </Card>
    </div>
  );
};

export default AnalyticsDashboard;
