/** Web Speech API — TTS Hook */

import { useRef, useCallback, useState, useEffect } from 'react';

export interface TTSBoundaryEvent {
  charIndex: number;
  charLength: number;
}

interface UseSpeechSynthesisOptions {
  lang?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
  onBoundary?: (e: TTSBoundaryEvent) => void;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (err: string) => void;
}

interface UseSpeechSynthesisReturn {
  speak: (text: string) => void;
  cancel: () => void;
  speaking: boolean;
  supported: boolean;
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  setVoice: (voice: SpeechSynthesisVoice) => void;
  setRate: (rate: number) => void;
  setVolume: (volume: number) => void;
  rate: number;
  volume: number;
}

export function useSpeechSynthesis(opts: UseSpeechSynthesisOptions = {}): UseSpeechSynthesisReturn {
  const {
    lang = 'zh-CN',
    onBoundary,
    onStart,
    onEnd,
    onError,
  } = opts;

  const [speaking, setSpeaking] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [rate, setRateState] = useState(opts.rate ?? 1.0);
  const [volume, setVolumeState] = useState(opts.volume ?? 1.0);

  // Mutable refs so speak() always uses the latest values
  const rateRef = useRef(rate);
  const pitchRef = useRef(opts.pitch ?? 1.0);
  const volumeRef = useRef(volume);
  const voiceRef = useRef<SpeechSynthesisVoice | null>(null);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  // Load voices (they load asynchronously in Chrome)
  useEffect(() => {
    if (!supported) return;

    const loadVoices = () => {
      const available = speechSynthesis.getVoices();
      setVoices(available);

      // Prefer a native zh-CN voice
      const preferred = available.find(
        (v) => v.lang.startsWith('zh-CN') && v.localService && v.name.includes('Female')
      ) || available.find(
        (v) => v.lang.startsWith('zh-CN') && v.localService
      ) || available.find(
        (v) => v.lang.startsWith('zh-CN')
      );
      if (preferred && !voiceRef.current) {
        voiceRef.current = preferred;
        setSelectedVoice(preferred);
      }
    };

    loadVoices();
    speechSynthesis.addEventListener('voiceschanged', loadVoices);
    return () => speechSynthesis.removeEventListener('voiceschanged', loadVoices);
  }, [supported]);

  const speak = useCallback(
    (text: string) => {
      if (!supported || !text.trim()) return;

      // Cancel any in-progress speech
      speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      utterance.rate = rateRef.current;
      utterance.pitch = pitchRef.current;
      utterance.volume = volumeRef.current;
      if (voiceRef.current) utterance.voice = voiceRef.current;

      utterance.onstart = () => {
        setSpeaking(true);
        onStart?.();
      };

      utterance.onend = () => {
        setSpeaking(false);
        onEnd?.();
      };

      utterance.onerror = (e) => {
        setSpeaking(false);
        // 'canceled' is normal when we cancel or when new speech starts
        if (e.error !== 'canceled') {
          onError?.(e.error);
        }
      };

      utterance.onboundary = (e) => {
        if (e.charIndex !== undefined) {
          onBoundary?.({ charIndex: e.charIndex, charLength: e.charLength ?? 0 });
        }
      };

      utteranceRef.current = utterance;
      speechSynthesis.speak(utterance);
    },
    [supported, lang, onBoundary, onStart, onEnd, onError],
  );

  const cancel = useCallback(() => {
    if (!supported) return;
    speechSynthesis.cancel();
    setSpeaking(false);
  }, [supported]);

  const setVoice = useCallback((voice: SpeechSynthesisVoice) => {
    voiceRef.current = voice;
    setSelectedVoice(voice);
  }, []);

  const setRate = useCallback((r: number) => {
    rateRef.current = r;
    setRateState(r);
  }, []);

  const setVolume = useCallback((v: number) => {
    volumeRef.current = v;
    setVolumeState(v);
  }, []);

  return {
    speak,
    cancel,
    speaking,
    supported,
    voices,
    selectedVoice,
    setVoice,
    setRate,
    setVolume,
    rate,
    volume,
  };
}
