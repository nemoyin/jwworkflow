import React, { useCallback } from 'react';
import {
  Typography,
  Input,
  InputNumber,
  Select,
  Empty,
} from 'antd';
import { useWorkflowStore } from '../../stores/workflowStore';
import { nodeColorMap, nodeLabelMap } from '../nodes';

const { Text, Title } = Typography;
const { TextArea } = Input;

const NodeConfigPanel: React.FC = () => {
  const selectedNode = useWorkflowStore((s) => s.selectedNode);
  const updateNodeConfig = useWorkflowStore((s) => s.updateNodeConfig);

  const updateConfig = useCallback(
    (key: string, value: any) => {
      if (!selectedNode) return;
      const newConfig = {
        ...(selectedNode.data.config || {}),
        [key]: value,
      };
      updateNodeConfig(selectedNode.id, newConfig);
    },
    [selectedNode, updateNodeConfig]
  );

  if (!selectedNode) {
    return (
      <div
        style={{
          width: 300,
          borderLeft: '1px solid #f0f0f0',
          padding: 24,
          background: '#fafafa',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Empty description="选择一个节点进行配置" />
      </div>
    );
  }

  const nodeType = selectedNode.type || '';
  const config = selectedNode.data.config || {};
  const color = nodeColorMap[nodeType] || '#1677ff';
  const label = nodeLabelMap[nodeType] || nodeType;

  const renderConfigFields = () => {
    switch (nodeType) {
      case 'input':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                变量名
              </Text>
              <Input
                size="small"
                placeholder="例如: user_input"
                value={config.variable_name || ''}
                onChange={(e) => updateConfig('variable_name', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                输入类型
              </Text>
              <Select
                size="small"
                style={{ width: '100%' }}
                value={config.input_type || 'text'}
                onChange={(v) => updateConfig('input_type', v)}
                options={[
                  { value: 'text', label: '文本' },
                  { value: 'file', label: '文件' },
                  { value: 'json', label: 'JSON' },
                ]}
              />
            </div>
          </>
        );

      case 'llm':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                模型
              </Text>
              <Select
                size="small"
                style={{ width: '100%' }}
                value={config.model || 'gpt-4o'}
                onChange={(v) => updateConfig('model', v)}
                options={[
                  { value: 'gpt-4o', label: 'GPT-4o' },
                  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
                  { value: 'claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
                  { value: 'claude-3-haiku', label: 'Claude 3 Haiku' },
                  { value: 'deepseek-chat', label: 'DeepSeek Chat' },
                  { value: 'qwen-max', label: '通义千问 Max' },
                ]}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                系统提示词
              </Text>
              <TextArea
                size="small"
                rows={3}
                placeholder="输入系统提示词..."
                value={config.system_prompt || ''}
                onChange={(e) => updateConfig('system_prompt', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                用户提示词
              </Text>
              <TextArea
                size="small"
                rows={3}
                placeholder="输入用户提示词..."
                value={config.prompt || ''}
                onChange={(e) => updateConfig('prompt', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                温度 (Temperature)
              </Text>
              <InputNumber
                size="small"
                min={0}
                max={2}
                step={0.1}
                style={{ width: '100%' }}
                value={config.temperature ?? 0.7}
                onChange={(v) => updateConfig('temperature', v)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                最大 Token 数
              </Text>
              <InputNumber
                size="small"
                min={1}
                max={128000}
                step={100}
                style={{ width: '100%' }}
                value={config.max_tokens ?? 4096}
                onChange={(v) => updateConfig('max_tokens', v)}
              />
            </div>
          </>
        );

      case 'template':
        return (
          <div style={{ marginBottom: 12 }}>
            <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
              模板内容
            </Text>
            <TextArea
              size="small"
              rows={6}
              placeholder={'输入模板内容，使用 {{variable}} 引用变量'}
              value={config.template || ''}
              onChange={(e) => updateConfig('template', e.target.value)}
            />
            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 4 }}>
              使用 {'{{变量名}}'} 引用上游输出
            </Text>
          </div>
        );

      case 'code':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                编程语言
              </Text>
              <Select
                size="small"
                style={{ width: '100%' }}
                value={config.language || 'python'}
                onChange={(v) => updateConfig('language', v)}
                options={[
                  { value: 'python', label: 'Python' },
                  { value: 'javascript', label: 'JavaScript' },
                ]}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                代码
              </Text>
              <TextArea
                size="small"
                rows={8}
                placeholder="输入要执行的代码..."
                value={config.code || ''}
                onChange={(e) => updateConfig('code', e.target.value)}
                style={{ fontFamily: 'monospace', fontSize: 12 }}
              />
            </div>
          </>
        );

      case 'ifelse':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                条件表达式
              </Text>
              <TextArea
                size="small"
                rows={3}
                placeholder={'例如: {{score}} > 0.5'}
                value={config.condition || ''}
                onChange={(e) => updateConfig('condition', e.target.value)}
                style={{ fontFamily: 'monospace', fontSize: 12 }}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                True 分支标签
              </Text>
              <Input
                size="small"
                placeholder="True"
                value={config.true_label || ''}
                onChange={(e) => updateConfig('true_label', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                False 分支标签
              </Text>
              <Input
                size="small"
                placeholder="False"
                value={config.false_label || ''}
                onChange={(e) => updateConfig('false_label', e.target.value)}
              />
            </div>
          </>
        );

      case 'output':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                输出类型
              </Text>
              <Select
                size="small"
                style={{ width: '100%' }}
                value={config.output_type || 'text'}
                onChange={(v) => updateConfig('output_type', v)}
                options={[
                  { value: 'text', label: '文本' },
                  { value: 'file', label: '文件' },
                  { value: 'json', label: 'JSON' },
                  { value: 'console', label: '控制台输出' },
                ]}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                输出文件名
              </Text>
              <Input
                size="small"
                placeholder="例如: result.json"
                value={config.file_name || ''}
                onChange={(e) => updateConfig('file_name', e.target.value)}
              />
            </div>
          </>
        );

      case 'knowledge-retrieval':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                知识库
              </Text>
              <Input
                size="small"
                placeholder="知识库名称"
                value={config.knowledge_base || ''}
                onChange={(e) => updateConfig('knowledge_base', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                查询文本
              </Text>
              <TextArea
                size="small"
                rows={3}
                placeholder="输入查询内容..."
                value={config.query || ''}
                onChange={(e) => updateConfig('query', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                返回条数 (Top-K)
              </Text>
              <InputNumber
                size="small"
                min={1}
                max={100}
                style={{ width: '100%' }}
                value={config.top_k ?? 5}
                onChange={(v) => updateConfig('top_k', v)}
              />
            </div>
          </>
        );

      case 'http-request':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                请求方法
              </Text>
              <Select
                size="small"
                style={{ width: '100%' }}
                value={config.method || 'GET'}
                onChange={(v) => updateConfig('method', v)}
                options={[
                  { value: 'GET', label: 'GET' },
                  { value: 'POST', label: 'POST' },
                  { value: 'PUT', label: 'PUT' },
                  { value: 'DELETE', label: 'DELETE' },
                ]}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                URL
              </Text>
              <Input
                size="small"
                placeholder="https://api.example.com/endpoint"
                value={config.url || ''}
                onChange={(e) => updateConfig('url', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                请求头 (JSON)
              </Text>
              <TextArea
                size="small"
                rows={3}
                placeholder='{"Authorization": "Bearer xxx"}'
                value={config.headers || ''}
                onChange={(e) => updateConfig('headers', e.target.value)}
                style={{ fontFamily: 'monospace', fontSize: 12 }}
              />
            </div>
          </>
        );

      case 'human-input':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                提示文本
              </Text>
              <TextArea
                size="small"
                rows={4}
                placeholder="向用户展示的提示内容"
                value={config.prompt_text || ''}
                onChange={(e) => updateConfig('prompt_text', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                输入类型
              </Text>
              <Select
                size="small"
                style={{ width: '100%' }}
                value={config.input_type || 'text'}
                onChange={(v) => updateConfig('input_type', v)}
                options={[
                  { value: 'text', label: '文本' },
                  { value: 'choice', label: '选择' },
                  { value: 'confirm', label: '确认' },
                ]}
              />
            </div>
          </>
        );

      case 'iteration':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                集合变量
              </Text>
              <Input
                size="small"
                placeholder="例如: items"
                value={config.collection || ''}
                onChange={(e) => updateConfig('collection', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                迭代变量名
              </Text>
              <Input
                size="small"
                placeholder="例如: item"
                value={config.item_variable || ''}
                onChange={(e) => updateConfig('item_variable', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                最大迭代次数
              </Text>
              <InputNumber
                size="small"
                min={1}
                max={1000}
                style={{ width: '100%' }}
                value={config.max_iterations ?? 100}
                onChange={(v) => updateConfig('max_iterations', v)}
              />
            </div>
          </>
        );

      case 'doc-extractor':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                文件格式
              </Text>
              <Select
                size="small"
                style={{ width: '100%' }}
                value={config.file_type || 'pdf'}
                onChange={(v) => updateConfig('file_type', v)}
                options={[
                  { value: 'pdf', label: 'PDF' },
                  { value: 'docx', label: 'DOCX' },
                  { value: 'xlsx', label: 'XLSX' },
                  { value: 'txt', label: 'TXT' },
                  { value: 'md', label: 'Markdown' },
                ]}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                文件路径
              </Text>
              <Input
                size="small"
                placeholder="例如: /path/to/document.pdf"
                value={config.file_path || ''}
                onChange={(e) => updateConfig('file_path', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                提取字段（逗号分隔）
              </Text>
              <Input
                size="small"
                placeholder="例如: title, content"
                value={config.extract_fields || ''}
                onChange={(e) => updateConfig('extract_fields', e.target.value)}
              />
            </div>
          </>
        );

      case 'variable-aggregator':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                源分支配置 (JSON)
              </Text>
              <TextArea
                size="small"
                rows={6}
                placeholder={JSON.stringify(
                  [
                    { node_id: 'node_xxx', alias: 'branch_a' },
                    { node_id: 'node_yyy', alias: 'branch_b' },
                  ],
                  null,
                  2
                )}
                value={(() => {
                  try {
                    return JSON.stringify(config.sources || [], null, 2);
                  } catch {
                    return '';
                  }
                })()}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    if (Array.isArray(parsed)) {
                      updateConfig('sources', parsed);
                    }
                  } catch {
                    // Allow editing even when JSON is incomplete
                  }
                }}
                style={{ fontFamily: 'monospace', fontSize: 12 }}
              />
              <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 4 }}>
                每个分支需指定 node_id（上游节点 ID）和 alias（聚合后的字段名）
              </Text>
            </div>
          </>
        );

      case 'agent':
        return (
          <>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                模型
              </Text>
              <Select
                size="small"
                style={{ width: '100%' }}
                value={config.model || 'gpt-4o'}
                onChange={(v) => updateConfig('model', v)}
                options={[
                  { value: 'gpt-4o', label: 'GPT-4o' },
                  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
                  { value: 'claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
                  { value: 'claude-3-haiku', label: 'Claude 3 Haiku' },
                  { value: 'deepseek-chat', label: 'DeepSeek Chat' },
                  { value: 'qwen-max', label: '通义千问 Max' },
                ]}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                系统提示词
              </Text>
              <TextArea
                size="small"
                rows={4}
                placeholder="Agent 系统提示词..."
                value={config.system_prompt || ''}
                onChange={(e) => updateConfig('system_prompt', e.target.value)}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                工具配置 (JSON)
              </Text>
              <TextArea
                size="small"
                rows={5}
                placeholder={JSON.stringify(
                  [{ name: 'search', description: '搜索工具', parameters: {} }],
                  null,
                  2
                )}
                value={(() => {
                  try {
                    return JSON.stringify(config.tools || [], null, 2);
                  } catch {
                    return '';
                  }
                })()}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    if (Array.isArray(parsed)) {
                      updateConfig('tools', parsed);
                    }
                  } catch {
                    // Allow editing even when JSON is incomplete
                  }
                }}
                style={{ fontFamily: 'monospace', fontSize: 12 }}
              />
            </div>
          </>
        );

      default:
        return (
          <Text type="secondary" style={{ fontSize: 12 }}>
            节点类型 "{nodeType}" 暂无配置选项
          </Text>
        );
    }
  };

  return (
    <div
      style={{
        width: 300,
        borderLeft: '1px solid #f0f0f0',
        padding: 16,
        background: '#fafafa',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          paddingBottom: 8,
          borderBottom: `2px solid ${color}`,
          marginBottom: 12,
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: color,
          }}
        />
        <Title level={5} style={{ margin: 0, fontSize: 14 }}>
          {label}
        </Title>
      </div>

      {renderConfigFields()}
    </div>
  );
};

export default NodeConfigPanel;
