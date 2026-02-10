/**
 * Web Speech API (ASR) Helper Class
 * 封装浏览器原生的语音识别功能，易于集成和迁移。
 */

// 扩展 Window 接口以支持 Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

// 类型定义
export interface ASRResult {
  finalText: string;
  interimText: string;
  isFinal: boolean;
}

export interface ASROptions {
  lang?: string;
  interimResults?: boolean;
  maxAlternatives?: number;
  onResult: (result: ASRResult) => void;
  onError?: (error: string) => void;
  onEnd?: () => void;
  onStart?: () => void;
}

export class ASRHelper {
  private lang: string;
  private interimResults: boolean;
  private maxAlternatives: number;
  private onResult: (result: ASRResult) => void;
  private onError: (error: string) => void;
  private onEnd: () => void;
  private onStart: () => void;
  private recognition: any;
  private isListening: boolean = false;

  constructor(options: ASROptions) {
    this.lang = options.lang || 'zh-CN';
    this.interimResults = options.interimResults !== undefined ? options.interimResults : true;
    this.maxAlternatives = options.maxAlternatives || 1;
    this.onResult = options.onResult || (() => {});
    this.onError = options.onError || (() => {});
    this.onEnd = options.onEnd || (() => {});
    this.onStart = options.onStart || (() => {});

    this.recognition = this._setupRecognition();
  }

  /**
   * 初始化语音识别引擎
   */
  private _setupRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.error('当前浏览器不支持 Web Speech API');
      return null;
    }

    const recognizer = new SpeechRecognition();
    recognizer.lang = this.lang;
    recognizer.interimResults = this.interimResults;
    recognizer.maxAlternatives = this.maxAlternatives;

    recognizer.addEventListener('start', () => {
      this.isListening = true;
      this.onStart();
    });

    recognizer.addEventListener('result', (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      this.onResult({
        finalText: finalTranscript,
        interimText: interimTranscript,
        isFinal: finalTranscript.length > 0
      });
    });

    recognizer.addEventListener('error', (event: any) => {
      console.error('ASR Error:', event.error, 'Event:', event);
      this.onError(event.error);
    });

    recognizer.addEventListener('end', () => {
      this.isListening = false;
      this.onEnd();
    });

    return recognizer;
  }

  /**
   * 检查是否支持
   */
  static isSupported(): boolean {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  /**
   * 开始监听
   */
  start() {
    if (!this.recognition) {
      this.onError('not-supported');
      return;
    }
    if (this.isListening) return;

    try {
      this.recognition.start();
    } catch (err) {
      this.onError(err as string);
    }
  }

  /**
   * 停止监听
   */
  stop() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }
  }

  /**
   * 强制取消
   */
  abort() {
    if (this.recognition && this.isListening) {
      this.recognition.abort();
    }
  }
}

export default ASRHelper;
