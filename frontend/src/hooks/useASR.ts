import { useState, useCallback, useRef, useEffect } from 'react';
import { ASRHelper, ASRResult } from '@/lib/asr';

export interface UseASROptions {
  onResult?: (text: string) => void;
  onInterim?: (text: string) => void;
  onError?: (error: string) => void;
}

export function useASR(options: UseASROptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [isSupported, setIsSupported] = useState(true);
  const asrRef = useRef<ASRHelper | null>(null);

  // 初始化 ASR
  useEffect(() => {
    if (!ASRHelper.isSupported()) {
      setIsSupported(false);
      return;
    }

    const asr = new ASRHelper({
      onResult: (result: ASRResult) => {
        if (result.interimText) {
          setInterimText(result.interimText);
          options.onInterim?.(result.interimText);
        }
        if (result.isFinal) {
          setInterimText('');
          options.onResult?.(result.finalText);
        }
      },
      onStart: () => {
        setIsListening(true);
      },
      onEnd: () => {
        setIsListening(false);
        setInterimText('');
      },
      onError: (error: string) => {
        setIsListening(false);
        setInterimText('');
        options.onError?.(error);
      }
    });

    asrRef.current = asr;

    return () => {
      asr.abort();
    };
  }, []);

  // 开始录音
  const start = useCallback(() => {
    if (!asrRef.current || !isSupported) return;
    setInterimText('');
    asrRef.current.start();
  }, [isSupported]);

  // 停止录音
  const stop = useCallback(() => {
    if (!asrRef.current) return;
    asrRef.current.stop();
  }, []);

  // 切换录音状态
  const toggle = useCallback(() => {
    if (isListening) {
      stop();
    } else {
      start();
    }
  }, [isListening, start, stop]);

  return {
    isListening,
    isSupported,
    interimText,
    start,
    stop,
    toggle
  };
}

export default useASR;
