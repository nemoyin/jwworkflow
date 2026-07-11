import { useEffect, useState, useCallback } from 'react';
import {
  Typography,
  Table,
  Tag,
  Button,
  Upload,
  Spin,
  message,
  Popconfirm,
  Empty,
  Space,
} from 'antd';
import {
  DeleteOutlined,
  ReloadOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { api, KnowledgeDocument } from '../services/api';

const { Title } = Typography;
const { Dragger } = Upload;

/** Format file size in human-readable form */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const base = 1024;
  const unitIndex = Math.min(Math.floor(Math.log(bytes) / Math.log(base)), units.length - 1);
  const value = bytes / Math.pow(base, unitIndex);
  return `${value.toFixed(unitIndex > 0 ? 2 : 0)} ${units[unitIndex]}`;
}

/** Format ISO date string to locale string */
function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** Status tag with color and icon */
const StatusTag = ({ status }: { status: string }) => {
  const config: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
    pending: {
      color: 'orange',
      icon: <ClockCircleOutlined />,
      label: '待处理',
    },
    processing: {
      color: 'processing',
      icon: <SyncOutlined spin />,
      label: '处理中',
    },
    ready: {
      color: 'success',
      icon: <CheckCircleOutlined />,
      label: '已就绪',
    },
    failed: {
      color: 'error',
      icon: <CloseCircleOutlined />,
      label: '处理失败',
    },
  };
  const cfg = config[status] || { color: 'default', icon: null, label: status };
  return (
    <Tag icon={cfg.icon} color={cfg.color}>
      {cfg.label}
    </Tag>
  );
};

const KnowledgePage = () => {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.listDocuments();
      setDocuments(res.documents);
    } catch (err) {
      message.error('获取文档列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleDelete = async (id: string) => {
    try {
      await api.deleteDocument(id);
      message.success('文档已删除');
      fetchDocuments();
    } catch {
      message.error('删除失败');
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf,.docx,.txt',
    showUploadList: false,
    customRequest: async ({ file, onSuccess, onError }) => {
      setUploading(true);
      try {
        await api.uploadDocument(file as File);
        onSuccess?.(null);
        message.success('文档上传成功，正在处理');
        fetchDocuments();
      } catch (err: any) {
        onError?.(err);
        message.error(err?.message || '上传失败');
      } finally {
        setUploading(false);
      }
    },
  };

  const columns = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 120,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      render: (status: string) => <StatusTag status={status} />,
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => formatDate(date),
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_: unknown, record: KnowledgeDocument) => (
        <Popconfirm
          title="确定删除此文档？"
          onConfirm={() => handleDelete(record.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <Title level={2} style={{ margin: 0 }}>
          知识库
        </Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={fetchDocuments} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      <div style={{ marginBottom: 24 }}>
        <Dragger {...uploadProps} disabled={uploading}>
          <p className="ant-upload-drag-icon">
            {uploading ? <Spin size="large" /> : <InboxOutlined />}
          </p>
          <p className="ant-upload-text">
            {uploading ? '正在上传...' : '点击或拖拽文件到此区域上传'}
          </p>
          <p className="ant-upload-hint">
            支持 .pdf .docx .txt 格式，单文件上限 20MB
          </p>
        </Dragger>
      </div>

      <Table
        dataSource={documents}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
        locale={{ emptyText: <Empty description="暂无文档，请上传文件" /> }}
      />
    </div>
  );
};

export default KnowledgePage;
