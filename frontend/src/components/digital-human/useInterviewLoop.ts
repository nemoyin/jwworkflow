/** 访谈循环控制器 — 状态机编排 STT → API → TTS 全自动循环 */

import { useCallback, useEffect, useRef } from 'react';
import { useSpeechSynthesis, TTSBoundaryEvent } from './useSpeechSynthesis';
import { useSpeechRecognition } from './useSpeechRecognition';
import { useInterviewStore } from './useInterviewStore';
import { stripSpeechAnnotations } from './ExpressionController';
import { api } from '../../services/api';

interface UseInterviewLoopOptions {
  workflowId: string;
  /** 模板输入字段（school_info / student_info / interview_mode 等，任意字段名均可） */
  inputs?: Record<string, string>;
  /** Callback for TTS word boundaries — wired to 3D avatar lip-sync */
  onTTSBoundary?: (e: TTSBoundaryEvent) => void;
  /** Callback when AI reply text is ready — wired to expression detection */
  onAssistantReply?: (text: string) => void;
}

export function useInterviewLoop({ workflowId, inputs, onTTSBoundary, onAssistantReply }: UseInterviewLoopOptions) {
  const store = useInterviewStore;
  const initialized = useInterviewStore((s) => s.initialized);

  // Track if we should restart listening after speaking
  const shouldRestartRef = useRef(false);
  // Track current AI response text for boundary events
  const aiTextRef = useRef('');
  // Track if loop is active (not cancelled)
  const activeRef = useRef(false);

  // ---- TTS ----
  const tts = useSpeechSynthesis({
    lang: 'zh-CN',
    rate: 1.0,
    onBoundary: (e) => {
      onTTSBoundary?.(e);
    },
    onStart: () => {
      store.getState().setPhase('speaking');
    },
    onEnd: () => {
      store.getState().setPhase('idle');
      // If user was mid-interview, restart listening
      if (shouldRestartRef.current && activeRef.current) {
        setTimeout(() => {
          if (activeRef.current && store.getState().phase === 'idle') {
            startListening();
          }
        }, 500);
      }
    },
    onError: (err) => {
      console.warn('[TTS] Error:', err);
      store.getState().setPhase('idle');
    },
  });

  // ---- API: Create conversation ----
  const initConversation = useCallback(async () => {
    try {
      store.getState().setPhase('processing');
      const res: any = await api.post('/conversations', {
        workflow_id: workflowId,
        title: `访谈-${new Date().toLocaleString('zh-CN')}`,
      });
      store.getState().setConversationId(res.id);
      store.getState().setInitialized(true);
      store.getState().setPhase('idle');
      return res.id;
    } catch (err: any) {
      store.getState().setError(err.message || '创建对话失败');
      throw err;
    }
  }, [workflowId]);

  // ---- API: Send message and get reply ----
  const sendMessage = useCallback(
    async (text: string) => {
      const cid = store.getState().conversationId;
      if (!cid) {
        store.getState().setError('对话未初始化');
        return;
      }

      // Record user message locally
      store.getState().addMessage({ role: 'user', content: text, timestamp: Date.now() });
      store.getState().setSubtitle(text);
      store.getState().setPhase('processing');

      try {
        const res: any = await api.post(`/conversations/${cid}/messages`, {
          content: text,
          inputs: inputs ? { ...inputs } : {},
        });

        // Extract AI reply text
        const replyContent = res.message?.content || res.output?.message || '';
        const fallback =
          typeof res.output === 'string'
            ? res.output
            : res.output
              ? Object.values(res.output).find((v) => typeof v === 'string' && v.trim()) || ''
              : '';

        const reply = (typeof replyContent === 'string' && replyContent.trim()) || fallback || '处理完成';

        // Record assistant message
        store.getState().addMessage({ role: 'assistant', content: reply, timestamp: Date.now() });
        store.getState().setSubtitle(reply);
        aiTextRef.current = reply;

        // Notify for expression detection
        onAssistantReply?.(reply);

        // Speak the reply — strip emotion/action annotations so TTS doesn't read them aloud
        tts.speak(stripSpeechAnnotations(reply));
      } catch (err: any) {
        store.getState().setError(err.message || '发送消息失败');
      }
    },
    [inputs, tts, onAssistantReply],
  );

  // ---- STT ----
  const onFinalResult = useCallback(
    (text: string, _isFinal: boolean) => {
      if (!activeRef.current) return;
      // Guard double-send: only act while still listening (not already processing).
      if (store.getState().phase !== 'listening') return;
      store.getState().setInterimText('');
      // Send to API
      sendMessage(text);
    },
    [sendMessage],
  );

  const onInterim = useCallback((text: string) => {
    if (!activeRef.current) return;
    store.getState().setInterimText(text);
  }, []);

  const onSilence = useCallback(() => {
    // Fallback: when the recognizer never delivers a final result, finalize
    // whatever interim text we captured so the user's words still get sent.
    const state = store.getState();
    if (state.phase !== 'listening') return;
    const interim = state.interimText;
    if (interim.trim() && activeRef.current) {
      state.setInterimText('');
      sendMessage(interim.trim());
    }
  }, [sendMessage]);

  const onSTTError = useCallback((err: string) => {
    console.warn('[STT] Error:', err);
    if (err.includes('权限')) {
      store.getState().setMicPermission('denied');
    }
  }, []);

  const stt = useSpeechRecognition({
    lang: 'zh-CN',
    continuous: false, // one-shot: stops after a final result, so TTS won't be re-heard
    interimResults: true,
    onResult: (text, isFinal) => {
      if (isFinal) onFinalResult(text, isFinal);
    },
    onInterim,
    onSilence,
    onError: onSTTError,
  });

  // ---- Start/Stop listening ----
  const startListening = useCallback(() => {
    if (!stt.supported) return;
    store.getState().setPhase('listening');
    stt.start();
  }, [stt]);

  const stopListening = useCallback(() => {
    stt.stop();
    store.getState().setPhase('idle');
  }, [stt]);

  // ---- Toggle microphone ----
  const toggleMic = useCallback(() => {
    const currentPhase = store.getState().phase;

    if (currentPhase === 'listening') {
      // Stop listening
      shouldRestartRef.current = false;
      stopListening();

      // If we have interim text, send it as final
      const interim = store.getState().interimText;
      if (interim.trim()) {
        store.getState().setInterimText('');
        sendMessage(interim.trim());
      }
    } else if (currentPhase === 'idle') {
      // Start listening
      shouldRestartRef.current = true;
      // Request mic permission if needed
      if (store.getState().micPermission !== 'granted') {
        navigator.mediaDevices
          ?.getUserMedia({ audio: true })
          .then(() => {
            store.getState().setMicPermission('granted');
            startListening();
          })
          .catch(() => {
            store.getState().setMicPermission('denied');
            store.getState().setError('需要麦克风权限才能使用语音输入');
          });
      } else {
        startListening();
      }
    } else if (currentPhase === 'speaking') {
      // Cancel TTS
      tts.cancel();
      shouldRestartRef.current = true;
      store.getState().setPhase('idle');
      setTimeout(() => startListening(), 300);
    } else if (currentPhase === 'error') {
      store.getState().setError(null);
      shouldRestartRef.current = true;
      startListening();
    }
    // processing — do nothing
  }, [startListening, stopListening, tts, sendMessage]);

  // ---- Initialize on first mount ----
  useEffect(() => {
    if (!initialized && workflowId) {
      initConversation();
    }
  }, [initialized, workflowId, initConversation]);

  // ---- Activation ----
  useEffect(() => {
    activeRef.current = true;
    return () => {
      activeRef.current = false;
      tts.cancel();
      stt.stop();
    };
  }, []);

  return {
    toggleMic,
    sendText: sendMessage,
    supported: stt.supported && tts.supported,
    sttSupported: stt.supported,
    ttsSupported: tts.supported,
    // TTS controls — exposed for settings panel
    voices: tts.voices,
    selectedVoice: tts.selectedVoice,
    setVoice: tts.setVoice,
    rate: tts.rate,
    setRate: tts.setRate,
    volume: tts.volume,
    setVolume: tts.setVolume,
  };
}
