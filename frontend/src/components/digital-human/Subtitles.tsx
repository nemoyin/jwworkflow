/** 字幕组件 — 显示识别文本、AI 回复和语音识别状态提示 */

import React from 'react';
import { useInterviewStore } from './useInterviewStore';

const Subtitles: React.FC = () => {
  const phase = useInterviewStore((s) => s.phase);
  const subtitle = useInterviewStore((s) => s.subtitle);
  const interimText = useInterviewStore((s) => s.interimText);
  const error = useInterviewStore((s) => s.error);

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '16px 32px' }}>
        <span style={{ color: 'rgba(255,100,100,0.9)', fontSize: 16 }}>{error}</span>
      </div>
    );
  }

  const isListening = phase === 'listening';
  const isProcessing = phase === 'processing';
  const isSpeaking = phase === 'speaking';

  // 语音识别状态提示文案
  let statusText: string;
  let statusColor: string;
  if (isListening) {
    statusText = interimText ? '正在识别…' : '正在聆听，请说话…';
    statusColor = 'rgba(120,200,255,0.95)';
  } else if (isProcessing) {
    statusText = '正在思考中…';
    statusColor = 'rgba(255,255,255,0.5)';
  } else if (isSpeaking) {
    statusText = '正在播报…';
    statusColor = 'rgba(255,255,255,0.5)';
  } else {
    statusText = '点击麦克风开始访谈';
    statusColor = 'rgba(255,255,255,0.4)';
  }

  // 主文本：识别中的临时文本优先（带「识别中」前缀），其次 AI 回复
  const showInterim = isListening && interimText;
  const mainText = showInterim ? `识别中：${interimText}` : subtitle;

  return (
    <div
      style={{
        textAlign: 'center',
        padding: '14px 48px',
        minHeight: 76,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
      }}
    >
      {mainText && (
        <span
          style={{
            color: showInterim ? 'rgba(255,255,255,0.65)' : 'rgba(255,255,255,0.92)',
            fontSize: isSpeaking ? 18 : 16,
            lineHeight: 1.6,
            maxWidth: 640,
            transition: 'color 0.3s',
          }}
        >
          {mainText}
        </span>
      )}
      <span
        style={{
          color: statusColor,
          fontSize: 13,
          letterSpacing: 1,
          transition: 'color 0.3s',
        }}
      >
        {statusText}
      </span>
    </div>
  );
};

export default Subtitles;
