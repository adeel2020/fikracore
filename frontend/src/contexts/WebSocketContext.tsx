"use client";

import React, { createContext, useContext, useRef, useState, useCallback, useEffect } from "react";

interface WordTiming {
  word: string;
  start_time: number;
  end_time: number;
}

interface AudioMessage {
  audio: string;
  word_timings: WordTiming[];
  sample_rate: number;
  method: string;
  transcript: string;
  response: string;
}

interface AudioChunk {
  audio: string;
  word_timings: WordTiming[];
  sample_rate: number;
  chunk_index: number;
  is_last: boolean;
}

interface WebSocketContextType {
  isConnected: boolean;
  wsUrl: string;
  setWsUrl: (url: string) => void;
  connect: () => Promise<void>;
  disconnect: () => void;
  sendAudio: (audioData: ArrayBuffer, imageData?: string) => void;
  onAudioReceived: (cb: (msg: AudioMessage) => void) => void;
  onAudioChunk: (cb: (chunk: AudioChunk) => void) => void;
  onInterrupt: (cb: () => void) => void;
  onWaitingStart: (cb: () => void) => void;
  onWaitingEnd: (cb: () => void) => void;
}

export const WebSocketContext = createContext<WebSocketContextType | null>(null);

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const REALTIME_URL = `${API_BASE.replace(/^http/, "ws")}/v1/realtime`;

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunk = 8192;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

function estimateWordTimings(
  text: string,
  totalDurationMs: number,
): WordTiming[] {
  const words = text.trim().split(/\s+/);
  if (words.length === 0) return [];
  const perWord = totalDurationMs / words.length;
  let t = 0;
  return words.map((w) => {
    const start = t;
    t += perWord;
    return { word: w, start_time: start, end_time: t };
  });
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [wsUrl, setWsUrl] = useState(REALTIME_URL);
  const audioCbRef = useRef<((msg: AudioMessage) => void) | null>(null);
  const audioChunkCbRef = useRef<((chunk: AudioChunk) => void) | null>(null);
  const interruptCbRef = useRef<(() => void) | null>(null);
  const waitingStartCbRef = useRef<(() => void) | null>(null);
  const waitingEndCbRef = useRef<(() => void) | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sessionReadyRef = useRef(false);

  const audioBufferRef = useRef<string[]>([]);
  const userTranscriptRef = useRef("");
  const assistantTranscriptRef = useRef("");
  const wordTimingsRef = useRef<WordTiming[]>([]);
  const chunkIndexRef = useRef(0);
  const waitingEndFiredRef = useRef(false);

  // Reset on response.created
  const cleanup = useCallback(() => {
    const ws = wsRef.current;
    if (ws) {
      ws.onclose = null;
      ws.onerror = null;
      ws.onmessage = null;
      ws.close();
      wsRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    sessionReadyRef.current = false;
    audioBufferRef.current = [];
    userTranscriptRef.current = "";
    assistantTranscriptRef.current = "";
    chunkIndexRef.current = 0;
    setIsConnected(false);
  }, []);

  const connect = useCallback(() => {
    return new Promise<void>((resolve, reject) => {
      const existing = wsRef.current;
      if (existing && existing.readyState === WebSocket.OPEN) {
        setIsConnected(true);
        resolve();
        return;
      }
      cleanup();

      console.log("[WS_REALTIME] Connecting to", REALTIME_URL);
      const ws = new WebSocket(REALTIME_URL);

      ws.onopen = () => {
        console.log("[WS_REALTIME] Connected");
        setIsConnected(true);
        if (reconnectTimerRef.current) {
          clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = null;
        }
        resolve();
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const type = msg.type as string;

          if (type === "session.created") {
            console.log("[WS_REALTIME] Session created, sending session.update");
            ws.send(JSON.stringify({
              type: "session.update",
              session: {
                instructions: `You are a NOC Storyteller. You narrate network operations center ticket data in a conversational, friendly voice. Use the tools available to you to look up issues, trends, and cluster context. Keep responses concise and suitable for spoken output.`,
                voice: "af_heart",
                turn_detection: null,
                input_audio_format: "pcm16",
                output_audio_format: "pcm16",
                input_audio_transcription: { model: "whisper-1" },
              },
            }));
            sessionReadyRef.current = true;
            return;
          }

          if (!sessionReadyRef.current) return;

          if (type === "session.updated") {
            console.log("[WS_REALTIME] Session updated");
            return;
          }

          if (type === "error") {
            console.warn("[WS_REALTIME] Error:", msg.error);
            return;
          }

          if (type === "input_audio_buffer.speech_started") {
            audioBufferRef.current = [];
            userTranscriptRef.current = "";
            assistantTranscriptRef.current = "";
            chunkIndexRef.current = 0;
            interruptCbRef.current?.();
            return;
          }

          if (type === "input_audio_buffer.speech_stopped") {
            return;
          }

          if (type === "conversation.item.created") {
            return;
          }

          if (type === "conversation.item.input_audio_transcription.delta") {
            return;
          }

          if (type === "conversation.item.input_audio_transcription.completed") {
            userTranscriptRef.current = msg.transcript || "";
            return;
          }

          if (type === "response.created") {
            audioBufferRef.current = [];
            assistantTranscriptRef.current = "";
            wordTimingsRef.current = [];
            chunkIndexRef.current = 0;
            waitingEndFiredRef.current = false;
            return;
          }

          if (type === "response.output_audio.delta") {
            if (!waitingEndFiredRef.current) {
              waitingEndFiredRef.current = true;
              waitingEndCbRef.current?.();
            }
            audioBufferRef.current.push(msg.delta);
            const chunk: AudioChunk = {
              audio: msg.delta,
              word_timings: [],
              sample_rate: msg.sample_rate ?? 24000,
              chunk_index: chunkIndexRef.current++,
              is_last: false,
            };
            audioChunkCbRef.current?.(chunk);
            return;
          }

          if (type === "response.output_audio.done") {
            return;
          }

          if (type === "response.output_audio_transcript.done" || type === "response.audio_transcript.done") {
            assistantTranscriptRef.current = msg.transcript || "";
            if (msg.word_timings) {
              wordTimingsRef.current = msg.word_timings;
            }
            return;
          }

          if (type === "response.done") {
            const allAudio = audioBufferRef.current.join("");
            const assistantText = assistantTranscriptRef.current;
            const userText = userTranscriptRef.current;
            if (allAudio && assistantText) {
              const sampleRate = 24000;
              const timings = wordTimingsRef.current.length > 0
                ? wordTimingsRef.current
                : estimateWordTimings(assistantText, (allAudio.length * 3 / 4) / (sampleRate * 2) * 1000);
              audioCbRef.current?.({
                audio: allAudio,
                word_timings: timings,
                sample_rate: sampleRate,
                method: "kokoro",
                transcript: userText,
                response: assistantText,
              });
            }
            audioBufferRef.current = [];
            userTranscriptRef.current = "";
            assistantTranscriptRef.current = "";
            wordTimingsRef.current = [];
            chunkIndexRef.current = 0;
            return;
          }

          if (type === "rate_limits.updated") return;

          console.log("[WS_REALTIME] Unhandled event:", type);
        } catch (e) {
          console.log("[WS_REALTIME] Parse error:", e);
        }
      };

      ws.onclose = () => {
        console.log("[WS_REALTIME] Closed, reconnecting in 3s");
        setIsConnected(false);
        sessionReadyRef.current = false;
        reconnectTimerRef.current = setTimeout(() => connect().catch(() => {}), 3000);
      };

      ws.onerror = () => {
        console.log("[WS_REALTIME] Error");
        ws.close();
        reject(new Error("WebSocket connection failed"));
      };

      wsRef.current = ws;
    });
  }, [cleanup]);

  const disconnect = useCallback(() => {
    cleanup();
  }, [cleanup]);

  const sendAudio = useCallback((audioData: ArrayBuffer, _imageData?: string) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN || !sessionReadyRef.current) {
      return;
    }
    const b64 = arrayBufferToBase64(audioData);
    ws.send(JSON.stringify({
      type: "input_audio_buffer.append",
      audio: b64,
    }));
    // Commit immediately — the frontend VAD already segmented the utterance
    ws.send(JSON.stringify({
      type: "input_audio_buffer.commit",
    }));
    // Start waiting indicator — server is processing
    waitingStartCbRef.current?.();
  }, []);

  const onAudioReceived = useCallback((cb: (msg: AudioMessage) => void) => {
    audioCbRef.current = cb;
  }, []);

  const onAudioChunk = useCallback((cb: (chunk: AudioChunk) => void) => {
    audioChunkCbRef.current = cb;
  }, []);

  const onInterrupt = useCallback((cb: () => void) => {
    interruptCbRef.current = cb;
  }, []);

  const onWaitingStart = useCallback((cb: () => void) => {
    waitingStartCbRef.current = cb;
  }, []);

  const onWaitingEnd = useCallback((cb: () => void) => {
    waitingEndCbRef.current = cb;
  }, []);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  return (
    <WebSocketContext.Provider value={{ isConnected, wsUrl, setWsUrl, connect, disconnect, sendAudio, onAudioReceived, onAudioChunk, onInterrupt, onWaitingStart, onWaitingEnd }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error("useWebSocket must be used within WebSocketProvider");
  return ctx;
}
