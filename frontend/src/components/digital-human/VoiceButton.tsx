/** 语音按钮 — 麦克风控制 */

import React, { useCallback } from 'react';
import { AudioOutlined, AudioMutedOutlined, LoadingOutlined } from '@ant-design/icons';
import { useInterviewStore } from './useInterviewStore';
import type { InterviewPhase } from './useInterviewStore';

interface Props {
  onClick: () => void;
}

const phaseStyle: Record<InterviewPhase, { bg: string; shadow: string; icon: React.ReactNode }> = {
  idle: {
    bg: 'rgba(255,255,255,0.12)',
    shadow: '0 0 0 rgba(64,150,255,0)',
    icon: <AudioOutlined style={{ fontSize: 28, color: 'rgba(255,255,255,0.7)' }} />,
  },
  listening: {
    bg: '#e84749',
    shadow: '0 0 24px rgba(232,71,73,0.5)',
    icon: <AudioOutlined style={{ fontSize: 28, color: '#fff' }} />,
  },
  processing: {
    bg: 'rgba(255,255,255,0.12)',
    shadow: '0 0 16px rgba(64,150,255,0.3)',
    icon: <LoadingOutlined style={{ fontSize: 28, color: 'rgba(255,255,255,0.5)' }} spin />,
  },
  speaking: {
    bg: '#1a6dd4',
    shadow: '0 0 24px rgba(26,109,212,0.5)',
    icon: <AudioMutedOutlined style={{ fontSize: 28, color: '#fff' }} />,
  },
  error: {
    bg: 'rgba(255,255,255,0.12)',
    shadow: '0 0 0 rgba(232,71,73,0)',
    icon: <AudioMutedOutlined style={{ fontSize: 28, color: 'rgba(255,255,255,0.4)' }} />,
  },
};

const VoiceButton: React.FC<Props> = ({ onClick }) => {
  const phase = useInterviewStore((s) => s.phase);
  const style = phaseStyle[phase] || phaseStyle.idle;

  const handleClick = useCallback(() => {
    if (phase === 'processing' || phase === 'speaking') return; // ignore during processing/speaking
    onClick();
  }, [phase, onClick]);

  return (
    <button
      onClick={handleClick}
      disabled={phase === 'processing' || phase === 'speaking'}
      style={{
        width: 72,
        height: 72,
        borderRadius: '50%',
        border: '2px solid rgba(255,255,255,0.15)',
        background: style.bg,
        boxShadow: style.shadow,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: phase === 'processing' || phase === 'speaking' ? 'default' : 'pointer',
        transition: 'all 0.3s ease',
        outline: 'none',
      }}
      aria-label={phase === 'listening' ? '停止录音' : '开始录音'}
    >
      {style.icon}
    </button>
  );
};

export default VoiceButton;
