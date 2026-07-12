/** 知识库管理（支持目录分类） */

import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Upload, message, Popconfirm, Typography, Space, Tree, Input, Modal } from 'antd';
import { UploadOutlined, DeleteOutlined, FileOutlined, FolderOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { api } from '../services/api';

const { Text } = Typography;

interface DocRecord {
  id: string; name: string; content_type: string; file_size: number;
  directory: string; status: string; created_at: string;
}

const KnowledgePage: React.FC = () => {
  const [docs, setDocs] = useState<DocRecord[]>([]);
  const [directories, setDirectories] = useState<string[]>(['/']);
  const [currentDir, setCurrentDir] = useState('/');
  const [loading, setLoading] = useState(false);
  const [dirModal, setDirModal] = useState(false);
  const [newDir, setNewDir] = useState('');

  const loadDocs = async (dir: string) => {
    setLoading(true);
    try {
      const params = dir !== '/' ? `?directory=${encodeURIComponent(dir)}` : '';
      const data: any = await api.get(`/knowledge${params}`);
      setDocs(data.documents || []);
    } catch { setDocs([]); }
    setLoading(false);
  };

  const loadDirs = async () => {
    try {
      const data: any = await api.get('/knowledge/directories');
      setDirectories(data.directories || ['/']);
    } catch { }
  };

  useEffect(() => { loadDirs(); loadDocs('/'); }, []);

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('directory', currentDir);
    try {
      await api.post('/knowledge/upload', formData);
      message.success(`已上传 ${file.name}`);
      loadDocs(currentDir);
      loadDirs();
    } catch { message.error('上传失败'); }
    return false;
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/knowledge/${id}`);
      message.success('已删除');
      loadDocs(currentDir);
    } catch { message.error('删除失败'); }
  };

  const handleAddDir = async () => {
    if (!newDir.trim()) return;
    const dir = newDir.startsWith('/') ? newDir : `/${newDir}`;
    if (!directories.includes(dir)) {
      setDirectories([...directories, dir].sort());
    }
    setCurrentDir(dir);
    setDirModal(false);
    setNewDir('');
    loadDocs(dir);
  };

  const columns = [
    { title: '文件名', dataIndex: 'name', key: 'name', render: (n: string) => <><FileOutlined style={{ marginRight: 6 }} />{n}</> },
    { title: '类型', dataIndex: 'content_type', key: 'type', render: (t: string) => <Tag>{t.split('/').pop() || t}</Tag> },
    { title: '大小', dataIndex: 'file_size', key: 'size', render: (s: number) => s > 1024 ? `${(s/1024).toFixed(1)}KB` : `${s}B` },
    { title: '目录', dataIndex: 'directory', key: 'dir', render: (d: string) => <Tag color="blue">{d}</Tag> },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => {
      const colors: Record<string, string> = { ready: 'green', processing: 'blue', failed: 'red', pending: 'orange' };
      return <Tag color={colors[s] || 'default'}>{s}</Tag>;
    }},
    { title: '操作', key: 'action', render: (_: any, r: DocRecord) => (
      <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}>
        <Button size="small" danger icon={<DeleteOutlined />} />
      </Popconfirm>
    )},
  ];

  const treeData = directories.map(d => ({
    key: d,
    title: d === '/' ? '📁 全部文档' : `📁 ${d.replace(/^\//, '').replace(/\/$/, '')}`,
    icon: <FolderOutlined />,
  }));

  return (
    <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 120px)' }}>
      <Card style={{ width: 240, flexShrink: 0, overflow: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <Text strong>目录</Text>
          <Button size="small" icon={<PlusOutlined />} onClick={() => setDirModal(true)} />
        </div>
        <Tree treeData={treeData} selectedKeys={[currentDir]}
          onSelect={(keys) => keys[0] && setCurrentDir(keys[0] as string) && loadDocs(keys[0] as string)}
          style={{ fontSize: 13 }} />
      </Card>

      <Card style={{ flex: 1, overflow: 'auto' }} title={
        <Space><span>知识库文档</span><Tag>{currentDir}</Tag></Space>
      } extra={
        <Space>
          <Button icon={<ReloadOutlined />} size="small" onClick={() => loadDocs(currentDir)}>刷新</Button>
          <Upload accept=".pdf,.docx,.doc,.txt,.md" showUploadList={false} beforeUpload={handleUpload}>
            <Button type="primary" icon={<UploadOutlined />} size="small">上传到当前目录</Button>
          </Upload>
        </Space>
      }>
        <Table dataSource={docs} columns={columns} rowKey="id" loading={loading}
          pagination={{ pageSize: 20, showSizeChanger: false }} size="small"
          locale={{ emptyText: '暂无文档' }} />
      </Card>

      <Modal title="新建目录" open={dirModal} onOk={handleAddDir} onCancel={() => setDirModal(false)}>
        <Input placeholder="目录名称（如 /法规库）" value={newDir}
          onChange={e => setNewDir(e.target.value)} onPressEnter={handleAddDir} />
      </Modal>
    </div>
  );
};

export default KnowledgePage;
