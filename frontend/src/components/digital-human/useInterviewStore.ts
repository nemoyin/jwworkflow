/** 访谈状态管理 — Zustand Store */

import { create } from 'zustand';

export type InterviewPhase =
  | 'idle'
  | 'listening'
  | 'processing'
  | 'speaking'
  | 'error';

export interface InterviewMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface InterviewState {
  /** 当前阶段 */
  phase: InterviewPhase;
  /** 对话 ID（创建 conversation 后获得） */
  conversationId: string | null;
  /** 对话历史 */
  messages: InterviewMessage[];
  /** 当前字幕文本（用户临时的/最终识别的，或 AI 播报的） */
  subtitle: string;
  /** 用户语音识别中的临时文本 */
  interimText: string;
  /** 错误信息 */
  error: string | null;
  /** 是否已初始化（创建了 conversation） */
  initialized: boolean;
  /** 麦克风权限状态 */
  micPermission: 'prompt' | 'granted' | 'denied' | 'unsupported';

  // Actions
  setPhase: (phase: InterviewPhase) => void;
  setConversationId: (id: string) => void;
  addMessage: (msg: InterviewMessage) => void;
  setSubtitle: (text: string) => void;
  setInterimText: (text: string) => void;
  setError: (err: string | null) => void;
  setInitialized: (v: boolean) => void;
  setMicPermission: (v: 'prompt' | 'granted' | 'denied' | 'unsupported') => void;
  reset: () => void;
}

const initialState = {
  phase: 'idle' as InterviewPhase,
  conversationId: null,
  messages: [],
  subtitle: '',
  interimText: '',
  error: null,
  initialized: false,
  micPermission: 'prompt' as const,
};

export const useInterviewStore = create<InterviewState>((set) => ({
  ...initialState,

  setPhase: (phase) => set({ phase }),
  setConversationId: (id) => set({ conversationId: id }),
  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),
  setSubtitle: (subtitle) => set({ subtitle }),
  setInterimText: (interimText) => set({ interimText }),
  setError: (error) => set({ error, phase: error ? 'error' : 'idle' }),
  setInitialized: (v) => set({ initialized: v }),
  setMicPermission: (v) => set({ micPermission: v }),
  reset: () => set(initialState),
}));
