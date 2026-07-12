/** Prompt IDE：专用提示词编辑器，支持变量插入和实时预览 */

import React, { useState } from 'react';
import { Tabs, Input, Button, Space, Tag, Typography, message, Tooltip } from 'antd';
import { ReloadOutlined, CopyOutlined } from '@ant-design/icons';

const { Text } = Typography;
const { TextArea } = Input;

interface PromptEditorProps {
  value: string;
  onChange: (value: string) => void;
  variables?: string[];
  label?: string;
}

const PromptEditor: React.FC<PromptEditorProps> = ({
  value,
  onChange,
  variables = [],
  label = '提示词',
}) => {
  const [preview, setPreview] = useState('');

  const insertVariable = (varName: string) => {
    onChange(value + `{{ ${varName} }}`);
  };

  const handlePreview = () => {
    // Replace variables with sample values
    let rendered = value;
    for (const v of variables) {
      rendered = rendered.replace(
        new RegExp(`\\{\\{\\s*${v}\\s*\\}\\}`, 'g'),
        `[${v}]`
      );
    }
    setPreview(rendered);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(value).then(
      () => message.success('已复制'),
      () => message.error('复制失败')
    );
  };

  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <Text strong style={{ fontSize: 12 }}>{label}</Text>
        <Space size={4}>
          <Tooltip title="插入变量">
            {variables.map((v) => (
              <Tag key={v} color="blue" style={{ cursor: 'pointer', fontSize: 10 }}
                onClick={() => insertVariable(v)}>
                {'{{'} {v} {'}}'}
              </Tag>
            ))}
          </Tooltip>
          <Tooltip title="预览">
            <Button size="small" icon={<ReloadOutlined />} onClick={handlePreview} />
          </Tooltip>
          <Tooltip title="复制">
            <Button size="small" icon={<CopyOutlined />} onClick={handleCopy} />
          </Tooltip>
        </Space>
      </div>
      <Tabs size="small" defaultActiveKey="edit" items={[
        {
          key: 'edit',
          label: '编辑',
          children: (
            <TextArea
              size="small"
              rows={5}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              placeholder="输入提示词，使用 {{变量名}} 引用变量..."
              style={{ fontFamily: 'monospace', fontSize: 12 }}
            />
          ),
        },
        {
          key: 'preview',
          label: '预览',
          children: (
            <div style={{
              background: '#f5f5f5', padding: 12, borderRadius: 4,
              minHeight: 100, fontSize: 12, fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
            }}>
              {preview || '点击预览按钮查看渲染效果'}
            </div>
          ),
        },
      ]} />
    </div>
  );
};

export default PromptEditor;
