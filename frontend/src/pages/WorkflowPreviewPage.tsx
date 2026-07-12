import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Input, Button, Typography, Spin, Tag, Space, message, Modal } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, CodeOutlined, ShareAltOutlined, ClearOutlined } from '@ant-design/icons';
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
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id || !token) return;
    api.setToken(token);
    api.get<any>(`/workflows/${id}/preview`)
      .then((data) => {
        setWf(data);
        if (data.type === 'chatflow') {
          setMessages([{ role: 'assistant', content: '你好！我是 AI 助手，有什么可以帮你的吗？', timestamp: Date.now() }]);
        } else {
          const fields = data.input_fields || [];
          setMessages([{ role: 'assistant', content: `请输入以下参数后发送：\n${fields.map((f: any) => `- ${f.label || f.name} (${f.type})`).join('\n')}`, timestamp: Date.now() }]);
        }
      })
      .catch(() => message.error('加载失败'))
      .finally(() => setLoading(false));
  }, [id, token]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !id) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg, timestamp: Date.now() }]);
    setSending(true);

    try {
      let result: any;
      if (wf?.type === 'chatflow') {
        // Chatflow: create conversation and send message
        let convId = sessionStorage.getItem(`conv_${id}`) || '';
        if (!convId) {
          const conv = await api.post<any>('/conversations', { workflow_id: id });
          convId = conv.id || '';
          sessionStorage.setItem(`conv_${id}`, convId);
        }
        const resp = await api.post<any>(`/conversations/${convId}/messages`, { content: userMsg });
        result = resp.response || resp.content || JSON.stringify(resp);
      } else {
        // Workflow: run once
        const fields = wf?.input_fields || [];
        const body: Record<string, any> = {};
        // 如果只有一个字段，把用户输入直接赋给它
        if (fields.length === 1) {
          body[fields[0].name] = userMsg;
        } else {
          // 多个字段时尝试解析 JSON
          try { Object.assign(body, JSON.parse(userMsg)); } catch { body['input'] = userMsg; }
        }
        const resp = await api.post<any>(`/workflows/${id}/run`, body);
        if (resp.status === 'success') {
          const output = resp.result || resp.output || {};
          // 提取第一个非空值作为回答
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
    sessionStorage.removeItem(`conv_${id}`);
    setMessages([{ role: 'assistant', content: '对话已重置', timestamp: Date.now() }]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><Spin size="large" tip="加载中..." /></div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', maxWidth: 800, margin: '0 auto', borderLeft: '1px solid #f0f0f0', borderRight: '1px solid #f0f0f0' }}>
      {/* Header */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff' }}>
        <Space>
          <RobotOutlined style={{ fontSize: 20, color: '#1677ff' }} />
          <div>
            <Text strong style={{ fontSize: 15 }}>{wf?.name || '工作流预览'}</Text>
            <div><Tag color={wf?.type === 'chatflow' ? 'purple' : 'blue'} style={{ fontSize: 10 }}>{wf?.type === 'chatflow' ? '对话流' : '工作流'}</Tag></div>
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
            <div style={{ maxWidth: '70%', padding: '10px 14px', borderRadius: 12, background: msg.role === 'user' ? '#1677ff' : '#fff', color: msg.role === 'user' ? '#fff' : '#333', fontSize: 14, lineHeight: 1.6, boxShadow: '0 1px 2px rgba(0,0,0,0.06)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {msg.content}
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
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#1677ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <RobotOutlined style={{ color: '#fff', fontSize: 16 }} />
            </div>
            <div style={{ padding: '10px 14px', borderRadius: 12, background: '#fff' }}>
              <Spin size="small" />
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid #f0f0f0', background: '#fff', display: 'flex', gap: 8 }}>
        <TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息，按 Enter 发送..."
          rows={2}
          style={{ flex: 1, borderRadius: 8 }}
          disabled={sending}
        />
        <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={sending} style={{ height: 'auto', borderRadius: 8 }}>发送</Button>
      </div>

      {/* Embed Modal */}
      <Modal title="嵌入代码" open={embedModal} onCancel={() => setEmbedModal(false)} footer={null}>
        <Text strong>iframe 嵌入：</Text>
        <TextArea value={`<iframe src="${window.location.origin}/preview/${id}" width="100%" height="600" frameborder="0"></iframe>`}
          rows={4} style={{ marginTop: 8, fontFamily: 'monospace', fontSize: 12 }} onFocus={(e) => e.target.select()} />
        <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>将以上代码复制到任意 HTML 页面即可嵌入此工作流。</Text>
      </Modal>

      {/* API Modal */}
      <Modal title="API 调用" open={apiModal} onCancel={() => setApiModal(false)} footer={null}>
        <Text strong>接口：</Text>
        <Paragraph copyable style={{ fontFamily: 'monospace', fontSize: 12 }}>{`POST ${window.location.origin}/api/workflows/${id}/execute`}</Paragraph>
        <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, fontSize: 11, marginTop: 8 }}>
{`curl -X POST "${window.location.origin}/api/workflows/${id}/execute" \\
  -H "Content-Type: application/json" \\
  -d '{"input": "your question"}'`}
        </pre>
      </Modal>
    </div>
  );
};

export default WorkflowPreviewPage;
