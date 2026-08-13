/** 访谈设置面板 — 语音选择 / 语速 / 音量 / 结束访谈 */

import React from 'react';
import { Button, Select, Slider, Space, Typography } from 'antd';
import { SettingOutlined, StopOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface Props {
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  onVoiceChange: (voice: SpeechSynthesisVoice) => void;
  rate: number;
  onRateChange: (rate: number) => void;
  volume: number;
  onVolumeChange: (volume: number) => void;
  onEnd: () => void;
}

const InterviewControls: React.FC<Props> = ({
  voices,
  selectedVoice,
  onVoiceChange,
  rate,
  onRateChange,
  volume,
  onVolumeChange,
  onEnd,
}) => {
  const zhVoices = voices.filter((v) => v.lang.startsWith('zh'));

  return (
    <div
      style={{
        position: 'absolute',
        right: 20,
        top: 70,
        width: 260,
        background: 'rgba(20,20,35,0.9)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 12,
        padding: 16,
        backdropFilter: 'blur(10px)',
        zIndex: 3,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <SettingOutlined style={{ color: 'rgba(255,255,255,0.6)' }} />
        <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 14, fontWeight: 500 }}>
          访谈设置
        </Text>
      </div>

      <div style={{ marginBottom: 14 }}>
        <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12, display: 'block', marginBottom: 6 }}>
          数字人声音
        </Text>
        <Select
          size="small"
          style={{ width: '100%' }}
          value={selectedVoice?.name}
          placeholder="选择语音"
          onChange={(name) => {
            const v = voices.find((x) => x.name === name);
            if (v) onVoiceChange(v);
          }}
          options={(zhVoices.length ? zhVoices : voices).map((v) => ({
            value: v.name,
            label: `${v.name} (${v.lang})`,
          }))}
        />
      </div>

      <div style={{ marginBottom: 14 }}>
        <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12, display: 'block', marginBottom: 6 }}>
          语速：{rate.toFixed(1)}x
        </Text>
        <Slider
          min={0.5}
          max={1.5}
          step={0.1}
          value={rate}
          onChange={onRateChange}
          tooltip={{ open: false }}
        />
      </div>

      <div style={{ marginBottom: 18 }}>
        <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12, display: 'block', marginBottom: 6 }}>
          音量：{Math.round(volume * 100)}%
        </Text>
        <Slider
          min={0}
          max={1}
          step={0.1}
          value={volume}
          onChange={onVolumeChange}
          tooltip={{ open: false }}
        />
      </div>

      <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
        <Button
          size="small"
          danger
          icon={<StopOutlined />}
          onClick={onEnd}
        >
          结束访谈
        </Button>
      </Space>
    </div>
  );
};

export default InterviewControls;
