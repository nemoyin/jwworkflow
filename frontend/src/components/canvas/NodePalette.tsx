import React, { DragEvent } from 'react';
import { Card, Typography } from 'antd';

const { Text } = Typography;

interface NodeTypeItem {
  type: string;
  label: string;
  color: string;
  description: string;
}

const nodeTypes: NodeTypeItem[] = [
  // Input / Output
  { type: 'input', label: '输入', color: '#52c41a', description: '用户输入 / 文件输入' },

  // AI / Blue
  { type: 'llm', label: 'LLM 调用', color: '#1677ff', description: '大语言模型推理' },
  { type: 'knowledge-retrieval', label: '知识检索', color: '#1677ff', description: '从知识库检索相关内容' },
  { type: 'agent', label: 'Agent 代理', color: '#1677ff', description: 'AI Agent 多工具协同' },

  // Processing / Orange
  { type: 'template', label: '模板渲染', color: '#fa8c16', description: '文本模板变量替换' },
  { type: 'code', label: '代码执行', color: '#fa8c16', description: 'Python / JS 脚本' },
  { type: 'http-request', label: 'HTTP 请求', color: '#fa8c16', description: 'HTTP API 调用' },
  { type: 'doc-extractor', label: '文档提取', color: '#fa8c16', description: 'PDF/DOCX/TXT 内容提取' },
  { type: 'variable-aggregator', label: '变量聚合', color: '#fa8c16', description: '合并多分支输出' },

  // Logic / Purple
  { type: 'ifelse', label: '条件分支', color: '#722ed1', description: '条件判断路由' },
  { type: 'iteration', label: '循环迭代', color: '#722ed1', description: '遍历数组循环执行' },
  { type: 'human-input', label: '人工输入', color: '#722ed1', description: '等待人工审核输入' },

  // Output
  { type: 'output', label: '输出', color: '#52c41a', description: '结果输出 / 导出' },
];

const NodePalette: React.FC = () => {
  const onDragStart = (event: DragEvent<HTMLDivElement>, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      style={{
        width: 220,
        padding: 16,
        borderRight: '1px solid #f0f0f0',
        background: '#fff',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}
    >
      <Text strong style={{ marginBottom: 4, display: 'block' }}>
        节点类型
      </Text>
      {nodeTypes.map((nt) => (
        <Card
          key={nt.type}
          size="small"
          draggable
          onDragStart={(e) => onDragStart(e, nt.type)}
          style={{
            cursor: 'grab',
            borderLeft: `3px solid ${nt.color}`,
          }}
          styles={{ body: { padding: '8px 12px' } }}
        >
          <div style={{ fontWeight: 500, fontSize: 13 }}>{nt.label}</div>
          <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>{nt.description}</div>
        </Card>
      ))}
    </div>
  );
};

export default NodePalette;
