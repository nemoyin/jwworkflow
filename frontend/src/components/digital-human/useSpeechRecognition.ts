/** Web Speech API — STT Hook */

import { useRef, useCallback, useState, useEffect, useMemo } from 'react';

interface UseSpeechRecognitionOptions {
  lang?: string;
  continuous?: boolean;
  interimResults?: boolean;
  onResult?: (text: string, isFinal: boolean) => void;
  onInterim?: (text: string) => void;
  onError?: (err: string) => void;
  onSilence?: () => void; // fired after no speech for a while
}

interface UseSpeechRecognitionReturn {
  start: () => void;
  stop: () => void;
  listening: boolean;
  supported: boolean;
}

export function useSpeechRecognition(opts: UseSpeechRecognitionOptions = {}): UseSpeechRecognitionReturn {
  const {
    lang = 'zh-CN',
    continuous = true,
    interimResults = true,
    onResult,
    onInterim,
    onError,
    onSilence,
  } = opts;

  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Latest-callback refs. The recognition instance is created fresh per `start()`
  // (not in an effect keyed on these callbacks), so unstable callback identities
  // can never abort a live recognition session. These refs always hold the newest
  // callbacks so event handlers read current state without recreating anything.
  const onResultRef = useRef(onResult);
  const onInterimRef = useRef(onInterim);
  const onErrorRef = useRef(onError);
  const onSilenceRef = useRef(onSilence);
  onResultRef.current = onResult;
  onInterimRef.current = onInterim;
  onErrorRef.current = onError;
  onSilenceRef.current = onSilence;

  const SpeechRecognitionCtor =
    (typeof window !== 'undefined' &&
      ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)) as
      | (new () => SpeechRecognition)
      | undefined;

  const supported = !!SpeechRecognitionCtor;

  // Reset silence timer on any speech (final OR interim) — only fires on true silence.
  const resetSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
    silenceTimerRef.current = setTimeout(() => {
      onSilenceRef.current?.();
    }, 3000); // 3 seconds of silence triggers onSilence
  }, []);

  // Build a fresh recognition instance. Creating a new one on each `start()`
  // avoids Chrome's "already started" errors when restarting after onend.
  const createRecognition = useCallback(() => {
    if (!SpeechRecognitionCtor) return null;

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = lang;
    recognition.continuous = continuous;
    recognition.interimResults = interimResults;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalText = '';
      let interimText = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalText += result[0].transcript;
        } else {
          interimText += result[0].transcript;
        }
      }

      if (finalText) {
        resetSilenceTimer();
        onResultRef.current?.(finalText.trim(), true);
      }
      if (interimText) {
        resetSilenceTimer(); // keep silence timer alive while speaking
        onInterimRef.current?.(interimText.trim());
      }
    };

    recognition.onerror = (event: any) => {
      const error = event.error;
      if (error === 'no-speech' || error === 'aborted') {
        // Normal — just silence or we stopped it
        return;
      }
      if (error === 'not-allowed') {
        onErrorRef.current?.('麦克风权限被拒绝');
      } else {
        onErrorRef.current?.(`语音识别错误: ${error}`);
      }
      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognition.onstart = () => {
      setListening(true);
      resetSilenceTimer();
    };

    return recognition;
  }, [lang, continuous, interimResults, SpeechRecognitionCtor, resetSilenceTimer]);

  const start = useCallback(() => {
    if (!SpeechRecognitionCtor) return;

    // Abort any stale instance first
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        // ignore
      }
    }

    const recognition = createRecognition();
    if (!recognition) return;
    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch {
      // Already started — ignore
    }
  }, [createRecognition, SpeechRecognitionCtor]);

  const stop = useCallback(() => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop();
    } catch {
      // ignore
    }
    setListening(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    };
  }, []);

  return useMemo(
    () => ({ start, stop, listening, supported }),
    [start, stop, listening, supported],
  );
}
