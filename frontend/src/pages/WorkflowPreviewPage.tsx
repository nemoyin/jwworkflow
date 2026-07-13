/** 工作流预览页（聊天界面 + 文件上传） */

import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Input, Button, Typography, Spin, Tag, Space, message, Modal, Upload } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { SendOutlined, RobotOutlined, UserOutlined, CodeOutlined, ShareAltOutlined, ClearOutlined, UploadOutlined, FileExcelOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import { useAuthStore } from '../stores/authStore';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

interface MessageItem {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

const WorkflowPreviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const token = useAuthStore((s) => s.token);
  const [wf, setWf] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [embedModal, setEmbedModal] = useState(false);
  const [apiModal, setApiModal] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<{ name: string; path: string } | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Check if workflow has file-related nodes
  const needsFileUpload = wf?.input_fields?.some((f: any) => f.name === 'file_path') || false;

  useEffect(() => {
    if (!id || !token) return;
    api.setToken(token);
    api.get<any>(`/workflows/${id}/preview`)
      .then((data) => {
        setWf(data);
        const msg = data.type === 'chatflow'
          ? '你好！我是 AI 助手，有什么可以帮你的吗？'
          : needsFileUpload
            ? '请先上传 Excel/CSV 文件，然后输入问题发送。'
            : `请输入以下参数后发送：\n${(data.input_fields || []).map((f: any) => `- ${f.label || f.name} (${f.type})`).join('\n')}`;
        setMessages([{ role: 'assistant', content: msg, timestamp: Date.now() }]);
      })
      .catch(() => message.error('加载失败'))
      .finally(() => setLoading(false));
  }, [id, token]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleUpload = async (file: File) => {
    if (!id) return false;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const result = await api.uploadFormData(`/workflows/${id}/upload`, formData);
      setUploadedFile({ name: result.file_name, path: result.file_path });
      message.success(`已上传 ${result.file_name}`);
      setMessages(prev => [...prev, { role: 'assistant', content: `已收到文件：**${result.file_name}**（${(result.size / 1024).toFixed(1)}KB）\n请提出您的问题。`, timestamp: Date.now() }]);
    } catch (e: any) {
      message.error(`上传失败: ${e.message}`);
    }
    return false;
  };

  const handleSend = async () => {
    if ((!input.trim() && !uploadedFile) || !id) return;
    const userMsg = input.trim() || '请分析数据';
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg, timestamp: Date.now() }]);
    setSending(true);

    try {
      const body: Record<string, any> = {};
      const fields = wf?.input_fields || [];

      // Build input body based on field names
      for (const f of fields) {
        if (f.name === 'file_path' && uploadedFile) {
          body[f.name] = uploadedFile.path;
        } else if (f.name === 'question' || f.name === 'input') {
          body[f.name] = userMsg;
        } else {
          // Try to parse as JSON if multiple fields
          body[f.name] = userMsg;
        }
      }

      // If only question field (no file_path), use simple flow
      if (fields.length <= 1 && !needsFileUpload) {
        body[fields[0]?.name || 'input'] = userMsg;
      }

      let result: any;
      if (wf?.type === 'chatflow') {
        let convId = sessionStorage.getItem(`conv_${id}`) || '';
        if (!convId) {
          const conv = await api.post<any>('/conversations', { workflow_id: id });
          convId = conv.id || '';
          sessionStorage.setItem(`conv_${id}`, convId);
        }
        const resp = await api.post<any>(`/conversations/${convId}/messages`, { content: userMsg });
        result = resp.response || resp.content || JSON.stringify(resp);
      } else {
        const resp = await api.post<any>(`/workflows/${id}/run`, body);
        if (resp.status === 'success') {
          const output = resp.result || resp.output || {};
          const answer = Object.values(output).find((v: any) => v && typeof v === 'string') || JSON.stringify(output);
          result = answer;
        } else {
          result = `执行失败: ${resp.error || '未知错误'}`;
        }
      }
      setMessages((prev) => [...prev, { role: 'assistant', content: typeof result === 'string' ? result : JSON.stringify(result, null, 2), timestamp: Date.now() }]);
    } catch (e: any) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `错误: ${e.message || '请求失败'}`, timestamp: Date.now() }]);
    }
    setSending(false);
  };

  const handleClear = () => {
    setMessages([]);
    setUploadedFile(null);
    sessionStorage.removeItem(`conv_${id}`);
    setMessages([{ role: 'assistant', content: '对话已重置', timestamp: Date.now() }]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><Spin size="large" /></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', maxWidth: 800, margin: '0 auto', borderLeft: '1px solid #f0f0f0', borderRight: '1px solid #f0f0f0' }}>
      {/* Header */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff' }}>
        <Space>
          <RobotOutlined style={{ fontSize: 20, color: '#1677ff' }} />
          <div>
            <Text strong style={{ fontSize: 15 }}>{wf?.name || '工作流预览'}</Text>
            <Tag color={wf?.type === 'chatflow' ? 'purple' : 'blue'} style={{ fontSize: 10, marginLeft: 8 }}>{wf?.type === 'chatflow' ? '对话流' : '工作流'}</Tag>
          </div>
        </Space>
        <Space>
          <Button size="small" icon={<ClearOutlined />} onClick={handleClear}>清空</Button>
          <Button size="small" icon={<CodeOutlined />} onClick={() => setApiModal(true)}>API</Button>
          <Button size="small" icon={<ShareAltOutlined />} onClick={() => setEmbedModal(true)}>嵌入</Button>
        </Space>
      </div>

      {/* Chat Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: 16, background: '#f5f5f5', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', gap: 8 }}>
            {msg.role === 'assistant' && (
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#1677ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <RobotOutlined style={{ color: '#fff', fontSize: 16 }} />
              </div>
            )}
            <div style={{ maxWidth: '70%', padding: '10px 14px', borderRadius: 12, background: msg.role === 'user' ? '#1677ff' : '#fff', color: msg.role === 'user' ? '#fff' : '#333', fontSize: 14, lineHeight: 1.6, boxShadow: '0 1px 2px rgba(0,0,0,0.06)', wordBreak: 'break-word' }}>
              {msg.role === 'assistant' ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              ) : (
                <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
              )}
            </div>
            {msg.role === 'user' && (
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#52c41a', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <UserOutlined style={{ color: '#fff', fontSize: 16 }} />
              </div>
            )}
          </div>
        ))}
        {sending && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', gap: 8 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#1677ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><RobotOutlined style={{ color: '#fff', fontSize: 16 }} /></div>
            <div style={{ padding: '10px 14px', borderRadius: 12, background: '#fff' }}><Spin size="small" /></div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* File Upload Banner + Input Area */}
      <div style={{ borderTop: '1px solid #f0f0f0', background: '#fff' }}>
        {needsFileUpload && (
          <div style={{ padding: '8px 16px', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 8, background: '#fafafa' }}>
            {uploadedFile ? (
              <><FileExcelOutlined style={{ color: '#52c41a', fontSize: 16 }} /><Text style={{ fontSize: 12, flex: 1 }}>{uploadedFile.name}</Text><Button size="small" onClick={() => setUploadedFile(null)}>更换</Button></>
            ) : (
              <Upload accept=".xlsx,.xls,.csv" showUploadList={false} beforeUpload={handleUpload} style={{ width: '100%' }}>
                <Button icon={<UploadOutlined />} block>上传 Excel/CSV 文件</Button>
              </Upload>
            )}
          </div>
        )}
        <div style={{ padding: '12px 16px', display: 'flex', gap: 8 }}>
          <TextArea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
            placeholder={needsFileUpload && !uploadedFile ? '请先上传文件...' : '输入消息，按 Enter 发送...'}
            rows={2} style={{ flex: 1, borderRadius: 8 }} disabled={sending || (needsFileUpload && !uploadedFile)} />
          <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={sending}
            style={{ height: 'auto', borderRadius: 8 }} disabled={needsFileUpload && !uploadedFile}>发送</Button>
        </div>
      </div>

      {/* Embed Modal */}
      <Modal title="嵌入代码" open={embedModal} onCancel={() => setEmbedModal(false)} footer={null}>
        <Paragraph copyable style={{ fontFamily: 'monospace', fontSize: 12 }}>{`<iframe src="${window.location.origin}/preview/${id}" width="100%" height="600" frameborder="0"></iframe>`}</Paragraph>
      </Modal>

      {/* API Modal */}
      <Modal title="API 调用" open={apiModal} onCancel={() => setApiModal(false)} footer={null}>
        <Text strong>接口：</Text>
        <Paragraph copyable style={{ fontFamily: 'monospace', fontSize: 12 }}>{`POST ${window.location.origin}/api/workflows/${id}/execute`}</Paragraph>
      </Modal>
    </div>
  );
};

export default WorkflowPreviewPage;
