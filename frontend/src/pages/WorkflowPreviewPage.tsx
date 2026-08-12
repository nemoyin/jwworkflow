/** 工作流预览页（聊天界面 + 文件上传 + 流式聚合输出） */

import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Input, Button, Typography, Tag, Space, message, Modal, Upload, Spin } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { SendOutlined, RobotOutlined, UserOutlined, CodeOutlined, ShareAltOutlined, ClearOutlined, UploadOutlined, FileExcelOutlined, DownOutlined, RightOutlined, BugOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import { useAuthStore } from '../stores/authStore';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

interface MessageItem {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

/** 节点类型 → 中文 label */
const NODE_LABEL: Record<string, string> = {
  'excel-parser': '解析文件',
  'intent-classifier': '理解问题意图',
  'query-executor': '执行查询',
  code: '执行代码',
  llm: 'AI 分析',
  output: '整理输出',
};

const NODE_EMOJI: Record<string, string> = {
  'excel-parser': '📂',
  'intent-classifier': '🧠',
  'query-executor': '🔍',
  code: '⌨️',
  llm: '💬',
  output: '📤',
};

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
  const [errorDetail, setErrorDetail] = useState<{ message: string; requestId?: string; body?: any } | null>(null);
  const [errorExpanded, setErrorExpanded] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 流式聚合消息状态
  const [streamContent, setStreamContent] = useState<string>('');          // 当前聚合消息的文本
  const [streamVisible, setStreamVisible] = useState(false);               // 是否显示流式消息
  const [thinkingSec, setThinkingSec] = useState(0);                       // 读秒
  const thinkingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const streamStepRef = useRef<string[]>([]);                              // 步骤文本行

  const needsFileUpload = wf?.input_fields?.some((f: any) => f.name === 'file_path') || false;

  // 自动滚动
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, streamContent]);

  // 加载工作流
  useEffect(() => {
    if (!id || !token) return;
    api.setToken(token);
    api.get<any>(`/workflows/${id}/preview`)
      .then((data) => {
        setWf(data);
        setMessages([{
          role: 'assistant',
          content: data.type === 'chatflow'
            ? '你好！我是 AI 助手，有什么可以帮你的吗？'
            : needsFileUpload
              ? '请先上传 Excel/CSV 文件，然后输入问题发送。'
              : `请输入以下参数后发送：\n${(data.input_fields || []).map((f: any) => `- ${f.label || f.name} (${f.type})`).join('\n')}`,
          timestamp: Date.now(),
        }]);
      })
      .catch(() => message.error('加载失败'))
      .finally(() => setLoading(false));
  }, [id, token]);

  // ----- 读秒计时器 -----
  const startThinkingTimer = () => {
    setThinkingSec(0);
    stopThinkingTimer();
    const start = Date.now();
    thinkingTimerRef.current = setInterval(() => {
      setThinkingSec(Math.floor((Date.now() - start) / 1000));
    }, 200);
  };
  const stopThinkingTimer = () => {
    if (thinkingTimerRef.current) { clearInterval(thinkingTimerRef.current); thinkingTimerRef.current = null; }
  };

  // ----- SSE 流式执行，返回最终文本 -----
  const runWithSSE = async (body: Record<string, any>): Promise<string> => {
    const token = useAuthStore.getState().token;
    const url = `${import.meta.env.VITE_API_URL || ''}/api/workflows/${id}/run-stream`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const text = await response.text().catch(() => '');
      throw new Error(`请求失败 (${response.status}): ${text.slice(0, 200)}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('Response body not readable');

    // 初始化流式消息
    streamStepRef.current = [];
    setStreamVisible(true);
    setStreamContent('');
    startThinkingTimer();

    const decoder = new TextDecoder();
    let buf = '';
    let finalAnswer: string | null = null;
    let lastError: string | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buf += decoder.decode(value, { stream: true });
      const parts = buf.split('\n\n');
      buf = parts.pop() || '';

      for (const part of parts) {
        if (!part.trim()) continue;

        const lines = part.split('\n');
        let evtType = '';
        let dataLines: string[] = [];
        let malformed = false;

        for (const line of lines) {
          const t = line.trim();
          if (t.startsWith('event: ')) evtType = t.slice(7).trim();
          else if (t.startsWith('data: ')) dataLines.push(t.slice(6));
          else if (t === '' || t.startsWith(':')) {}
          else if (dataLines.length > 0) dataLines[dataLines.length - 1] += t;
          else malformed = true;
        }
        if (malformed || dataLines.length === 0) continue;

        let data: any;
        try { data = JSON.parse(dataLines.join('')); } catch { continue; }

        if (evtType === 'node_start') {
          const emoji = NODE_EMOJI[data.node_type] || '🤖';
          const label = NODE_LABEL[data.node_type] || data.node_type;
          streamStepRef.current.push(`⏳ ${emoji} **${label}** — 进行中...`);
          setStreamContent(streamStepRef.current.join('\n'));
        } else if (evtType === 'node_done') {
          const idx = streamStepRef.current.length - 1;
          if (idx >= 0) {
            const emoji = NODE_EMOJI[data.node_type] || '🤖';
            const label = NODE_LABEL[data.node_type] || data.node_type;
            streamStepRef.current[idx] = `✅ ${emoji} **${label}** — 完成`;
            setStreamContent(streamStepRef.current.join('\n'));
          }
        } else if (evtType === 'node_error') {
          const idx = streamStepRef.current.length - 1;
          if (idx >= 0) {
            const emoji = NODE_EMOJI[data.node_type] || '🤖';
            const label = NODE_LABEL[data.node_type] || data.node_type;
            streamStepRef.current[idx] = `❌ ${emoji} **${label}** — 出错`;
            setStreamContent(streamStepRef.current.join('\n'));
          }
          lastError = `[${data.node_type}] ${data.error || '未知错误'}`;
        } else if (evtType === 'workflow_done') {
          const output = data.output || {};
          const found = Object.values(output).find((v: any) => v && typeof v === 'string');
          finalAnswer = typeof found === 'string' ? found : JSON.stringify(output);
        } else if (evtType === 'workflow_error') {
          lastError = data.error || '执行失败';
          throw new Error(lastError || '执行失败');
        }
      }
    }

    if (!finalAnswer) throw new Error(lastError || '服务端异常');

    // 停止计时
    stopThinkingTimer();

    // 流式输出答案
    const finalContent = streamStepRef.current.join('\n') + `\n\n🤔 **思考中** ${Math.max(thinkingSec, 1)}s`;

    await new Promise<void>((resolve) => {
      let idx = 0;
      const streamOne = () => {
        if (idx >= finalAnswer!.length) { resolve(); return; }
        const chunk = Math.min(4, finalAnswer!.length - idx);
        idx += chunk;
        setStreamContent(finalContent + '\n\n' + finalAnswer!.slice(0, idx));
        setTimeout(streamOne, 15 + Math.random() * 25);
      };
      setTimeout(streamOne, 300);
    });

    return finalContent + '\n\n' + finalAnswer!;
  };

  // ----- 上传文件 -----
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

  // ----- 发送 -----
  const handleSend = async () => {
    if ((!input.trim() && !uploadedFile) || !id) return;
    const userMsg = input.trim() || '请分析数据';
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg, timestamp: Date.now() }]);
    setSending(true);
    setErrorDetail(null);
    setStreamVisible(false);
    stopThinkingTimer();

    try {
      const body: Record<string, any> = {};
      const fields = wf?.input_fields || [];
      for (const f of fields) {
        if (f.name === 'file_path' && uploadedFile) body[f.name] = uploadedFile.path;
        else if (f.name === 'question' || f.name === 'input') body[f.name] = userMsg;
        else body[f.name] = userMsg;
      }
      if (fields.length <= 1 && !needsFileUpload) body[fields[0]?.name || 'input'] = userMsg;

      if (wf?.type === 'chatflow') {
        let convId = sessionStorage.getItem(`conv_${id}`) || '';
        if (!convId) {
          const conv = await api.post<any>('/conversations', { workflow_id: id });
          convId = conv.id || '';
          sessionStorage.setItem(`conv_${id}`, convId);
        }
        const resp = await api.post<any>(`/conversations/${convId}/messages`, { content: userMsg });
        const result = resp.response || resp.content || JSON.stringify(resp);
        setMessages((prev) => [...prev, { role: 'assistant', content: typeof result === 'string' ? result : JSON.stringify(result, null, 2), timestamp: Date.now() }]);
      } else {
        const finalText = await runWithSSE(body);
        setMessages((prev) => [...prev, { role: 'assistant', content: finalText, timestamp: Date.now() }]);
      }
    } catch (e: any) {
      const errMsg = e.message || '请求失败';
      setErrorDetail({ message: errMsg });
      setErrorExpanded(false);
      setMessages((prev) => [...prev, { role: 'assistant', content: `❌ **执行出错**\n\n${errMsg}`, timestamp: Date.now() }]);
    } finally {
      setSending(false);
      setStreamVisible(false);
      stopThinkingTimer();
    }
  };

  const handleClear = () => {
    setMessages([]);
    setUploadedFile(null);
    setStreamVisible(false);
    stopThinkingTimer();
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

        {/* 流式聚合消息 */}
        {streamVisible && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', gap: 8 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#1677ff', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <RobotOutlined style={{ color: '#fff', fontSize: 16 }} />
            </div>
            <div style={{ maxWidth: '70%', padding: '10px 14px', borderRadius: 12, background: '#fff', color: '#333', fontSize: 14, lineHeight: 1.6, boxShadow: '0 1px 2px rgba(0,0,0,0.06)', wordBreak: 'break-word' }}>
              {streamContent ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamContent}</ReactMarkdown>
              ) : (
                <span style={{ color: '#999' }}>🤔 思考中 {thinkingSec}s</span>
              )}
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Error Detail */}
      {errorDetail && (
        <div style={{ borderTop: '1px solid #ffd6d6', background: '#fff2f0', padding: '8px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }} onClick={() => setErrorExpanded(!errorExpanded)}>
            <BugOutlined style={{ color: '#ff4d4f' }} />
            <Text style={{ fontSize: 12, color: '#ff4d4f', flex: 1 }}>
              {errorDetail.requestId ? `错误 ID: ${errorDetail.requestId}` : '错误详情'}
            </Text>
            {errorExpanded ? <DownOutlined style={{ fontSize: 10, color: '#999' }} /> : <RightOutlined style={{ fontSize: 10, color: '#999' }} />}
          </div>
          {errorExpanded && (
            <pre style={{ margin: '8px 0 0 0', padding: 8, fontSize: 11, lineHeight: 1.5, background: '#fff', borderRadius: 4, maxHeight: 300, overflow: 'auto', fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all', color: '#666', border: '1px solid #ffd6d6' }}>
              {JSON.stringify(errorDetail.body, null, 2) || errorDetail.message}
            </pre>
          )}
        </div>
      )}

      {/* File Upload + Input */}
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

      <Modal title="嵌入代码" open={embedModal} onCancel={() => setEmbedModal(false)} footer={null}>
        <Paragraph copyable style={{ fontFamily: 'monospace', fontSize: 12 }}>{`<iframe src="${window.location.origin}/preview/${id}" width="100%" height="600" frameborder="0"></iframe>`}</Paragraph>
      </Modal>
      <Modal title="API 调用" open={apiModal} onCancel={() => setApiModal(false)} footer={null}>
        <Text strong>接口：</Text>
        <Paragraph copyable style={{ fontFamily: 'monospace', fontSize: 12 }}>{`POST ${window.location.origin}/api/workflows/${id}/execute`}</Paragraph>
      </Modal>
    </div>
  );
};

export default WorkflowPreviewPage;
