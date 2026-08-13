/** 数字人访谈模式 — 全屏 Portal 容器 */

import React, { useEffect, useCallback, useRef, useState } from 'react';
import { Button, Typography, Tag, Input } from 'antd';
import { CloseOutlined, SettingOutlined, SendOutlined } from '@ant-design/icons';
import { useInterviewLoop } from './useInterviewLoop';
import { useInterviewStore } from './useInterviewStore';
import VoiceButton from './VoiceButton';
import Subtitles from './Subtitles';
import DigitalHumanAvatar from './DigitalHumanAvatar';
import InterviewControls from './InterviewControls';
import { detectExpression } from './ExpressionController';

const { Text } = Typography;

interface Props {
  workflowId: string;
  scenario: string;
  subjectInfo: string;
  behaviorMode?: string;
  onClose: () => void;
}

const phaseLabel: Record<string, string> = {
  idle: '待机中',
  listening: '聆听中',
  processing: '思考中',
  speaking: '播报中',
  error: '异常',
};

const phaseColor: Record<string, string> = {
  idle: 'default',
  listening: 'red',
  processing: 'processing',
  speaking: 'blue',
  error: 'error',
};

const DigitalHumanInterview: React.FC<Props> = ({ workflowId, scenario, subjectInfo, behaviorMode, onClose }) => {
  const phase = useInterviewStore((s) => s.phase);
  const error = useInterviewStore((s) => s.error);
  const initialized = useInterviewStore((s) => s.initialized);
  const micPermission = useInterviewStore((s) => s.micPermission);

  const [showSettings, setShowSettings] = useState(false);
  const [textInput, setTextInput] = useState('');

  const avatarControlsRef = useRef<{
    setMorphWeight: (name: string, value: number) => void;
    animateMorph: (name: string, target: number, duration: number) => void;
    handleBoundary: (e: { charIndex: number; charLength: number }) => void;
    setExpression: (expression: string, intensity?: number) => void;
  } | null>(null);

  const {
    toggleMic,
    sendText,
    sttSupported,
    ttsSupported,
    voices,
    selectedVoice,
    setVoice,
    rate,
    setRate,
    volume,
    setVolume,
  } = useInterviewLoop({
    workflowId,
    scenario,
    subjectInfo,
    behaviorMode,
    onTTSBoundary: (e) => {
      avatarControlsRef.current?.handleBoundary(e);
    },
    onAssistantReply: (reply) => {
      const expression = detectExpression(reply);
      avatarControlsRef.current?.setExpression(expression);
    },
  });

  // 键盘快捷键：ESC 关闭，Space 切换麦克风
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      // Space toggles mic — but not when typing in an input
      if (e.key === ' ' || e.code === 'Space') {
        const target = e.target as HTMLElement;
        if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
          return;
        }
        e.preventDefault();
        toggleMic();
      }
    },
    [onClose, toggleMic],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // 文本输入回退（语音识别不支持时）
  const handleSendText = useCallback(() => {
    const text = textInput.trim();
    if (!text) return;
    setTextInput('');
    sendText(text);
  }, [textInput, sendText]);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'radial-gradient(ellipse at center, #1a1a2e 0%, #0a0a14 70%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* ---- 顶部状态栏 ---- */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 20px',
          zIndex: 2,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Tag color={phaseColor[phase] || 'default'}>{phaseLabel[phase] || phase}</Tag>
          {scenario && (
            <Text style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
              场景：{scenario}
            </Text>
          )}
          {!sttSupported && (
            <Text style={{ color: 'rgba(255,200,100,0.7)', fontSize: 12 }}>
              ⚠ 浏览器不支持语音识别
            </Text>
          )}
          {!ttsSupported && (
            <Text style={{ color: 'rgba(255,200,100,0.7)', fontSize: 12 }}>
              ⚠ 浏览器不支持语音合成
            </Text>
          )}
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={() => setShowSettings((v) => !v)}
            style={{ color: 'rgba(255,255,255,0.6)', fontSize: 18 }}
          />
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={onClose}
            style={{ color: 'rgba(255,255,255,0.6)', fontSize: 18 }}
          />
        </div>
      </div>

      {/* ---- 设置面板 ---- */}
      {showSettings && (
        <InterviewControls
          voices={voices}
          selectedVoice={selectedVoice}
          onVoiceChange={setVoice}
          rate={rate}
          onRateChange={setRate}
          volume={volume}
          onVolumeChange={setVolume}
          onEnd={onClose}
        />
      )}

      {/* ---- 3D 数字人头像 ---- */}
      <div style={{ marginBottom: 24 }}>
        <DigitalHumanAvatar
          width={340}
          height={400}
          onReady={(controls) => {
            avatarControlsRef.current = controls;
          }}
        />
      </div>

      {/* ---- 字幕 ---- */}
      <Subtitles />

      {/* ---- 麦克风按钮 / 文本输入回退 ---- */}
      <div style={{ marginTop: 8 }}>
        {sttSupported ? (
          <VoiceButton onClick={toggleMic} />
        ) : (
          <div style={{ display: 'flex', gap: 8, width: 320 }}>
            <Input
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onPressEnter={handleSendText}
              placeholder="浏览器不支持语音识别，请输入文字"
              style={{ flex: 1 }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSendText}
              disabled={!textInput.trim()}
            >
              发送
            </Button>
          </div>
        )}
      </div>

      {/* ---- 提示信息 ---- */}
      <div style={{ position: 'absolute', bottom: 40 }}>
        <Text style={{ color: 'rgba(255,255,255,0.2)', fontSize: 12 }}>
          {phase === 'idle'
            ? '点击麦克风或按空格开始 · 按 ESC 退出'
            : '点击麦克风或按空格结束 · 按 ESC 退出'}
        </Text>
      </div>

      {/* ---- 权限/未初始化提示 ---- */}
      {micPermission === 'denied' && (
        <div
          style={{
            position: 'absolute',
            bottom: 80,
            background: 'rgba(232,71,73,0.15)',
            border: '1px solid rgba(232,71,73,0.3)',
            borderRadius: 8,
            padding: '8px 20px',
          }}
        >
          <Text style={{ color: 'rgba(255,150,150,0.9)', fontSize: 13 }}>
            麦克风权限被拒绝，请在浏览器设置中允许麦克风访问
          </Text>
        </div>
      )}

      {error && (
        <div
          style={{
            position: 'absolute',
            bottom: 80,
            background: 'rgba(232,71,73,0.15)',
            border: '1px solid rgba(232,71,73,0.3)',
            borderRadius: 8,
            padding: '8px 20px',
          }}
        >
          <Text style={{ color: 'rgba(255,150,150,0.9)', fontSize: 13 }}>{error}</Text>
        </div>
      )}

      {!initialized && phase === 'processing' && (
        <div
          style={{
            position: 'absolute',
            bottom: 80,
          }}
        >
          <Text style={{ color: 'rgba(255,255,255,0.4)', fontSize: 13 }}>
            正在初始化访谈...
          </Text>
        </div>
      )}
    </div>
  );
};

export default DigitalHumanInterview;
