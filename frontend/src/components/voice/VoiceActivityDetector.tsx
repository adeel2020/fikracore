"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { Mic, MicOff } from "lucide-react";
import { useWebSocket } from "@/contexts/WebSocketContext";
import { useAvatar } from "@/components/features/narrative-notebook-view/components/presentation-template/AvatarContext";

interface VADProps {
  cameraStream?: MediaStream | null;
  energyThreshold?: number;
  conversationBreakDuration?: number;
  minSpeechDuration?: number;
  maxSpeechDuration?: number;
  onListeningChange?: (listening: boolean) => void;
  vadMode?: "active" | "suppressed" | "muted";
  onSuppressedSpeech?: () => void;
}

export function VoiceActivityDetector({
  cameraStream,
  energyThreshold = 0.06,
  conversationBreakDuration = 1.0,
  minSpeechDuration = 0.8,
  maxSpeechDuration = 15,
  onListeningChange,
  vadMode = "active",
  onSuppressedSpeech,
}: VADProps) {
  const { isConnected, connect, sendAudio } = useWebSocket();
  let setIsMuted: ((muted: boolean) => void) | undefined;
  try {
    const avatarCtx = useAvatar();
    if (avatarCtx) {
      setIsMuted = avatarCtx.setIsMuted;
    }
  } catch (e) {}
  const [isListening, setIsListening] = useState(false);
  const [isSpeechActive, setIsSpeechActive] = useState(false);
  const [energy, setEnergy] = useState(0);

  const audioCtxRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const audioBufferRef = useRef<Float32Array[]>([]);
  const silenceRef = useRef(0);
  const speechRef = useRef(0);
  const inSpeechRef = useRef(false);
  const listeningRef = useRef(false);
  const thresholdRef = useRef(energyThreshold);
  const calibratingRef = useRef(false);
  const noiseFloorRef = useRef<number[]>([]);
  const onListeningChangeRef = useRef(onListeningChange);
  const onSuppressedSpeechRef = useRef(onSuppressedSpeech);
  const vadModeRef = useRef(vadMode);
  onListeningChangeRef.current = onListeningChange;
  onSuppressedSpeechRef.current = onSuppressedSpeech;
  vadModeRef.current = vadMode;

  useEffect(() => {
    console.log("[VAD_MODE_CHANGE] vadMode prop changed to:", vadMode, "| ref =", vadModeRef.current);
  }, [vadMode]);
  const CALIBRATION_FRAMES = 100;
  const SPEECH_CONFIRMATION_FRAMES = 2;
  const consecutiveSpeechRef = useRef(0);
  const consecutiveAboveRef = useRef(0);
  const preSpeechMissRef = useRef(0);
  const PRE_SPEECH_TOLERANCE = 2;

  const sendAudioSegment = useCallback((buffers: Float32Array[]) => {
    const totalLen = buffers.reduce((s, b) => s + b.length, 0);
    console.log("[VAD] Sending segment: frames=", buffers.length, "duration=", (totalLen / 16000).toFixed(2) + "s");
    const combined = new Float32Array(totalLen);
    let offset = 0;
    for (const buf of buffers) {
      combined.set(buf, offset);
      offset += buf.length;
    }
    const int16 = new Int16Array(combined.length);
    for (let i = 0; i < combined.length; i++) {
      int16[i] = Math.max(-32768, Math.min(32767, combined[i] * 32767));
    }
    sendAudio(int16.buffer);
  }, [sendAudio]);

  const resetSpeechState = useCallback(() => {
    speechRef.current = 0;
    silenceRef.current = 0;
    consecutiveAboveRef.current = 0;
    inSpeechRef.current = false;
    audioBufferRef.current = [];
    setIsSpeechActive(false);
  }, []);

  const processFrame = useCallback((energyVal: number, audioData: Float32Array) => {
    setEnergy(energyVal);

    const mode = vadModeRef.current;
    // Muted: completely skip VAD processing
    if (mode === "muted") return;

    // Calibration phase
    if (calibratingRef.current) {
      calibratingRef.current = false;
      return;
    }

    const breakFrames = Math.floor((conversationBreakDuration * 16000) / 1024);
    const maxFrames = Math.floor((maxSpeechDuration * 16000) / 1024);

    const currentThreshold = thresholdRef.current;
    const threshold = inSpeechRef.current ? Math.max(0.01, currentThreshold - 0.01) : currentThreshold;

    if (energyVal > threshold) {
      if (!inSpeechRef.current) {
        consecutiveSpeechRef.current++;
        preSpeechMissRef.current = 0;
        if (consecutiveSpeechRef.current === 1) {
          console.log("[VAD_SPEECH_DETECTED] First frame above threshold, energy=", energyVal.toFixed(4));
          audioBufferRef.current = [new Float32Array(audioData)];
        } else {
          audioBufferRef.current.push(new Float32Array(audioData));
        }
        if (consecutiveSpeechRef.current >= SPEECH_CONFIRMATION_FRAMES) {
          console.log("[VAD_SPEECH] Speech confirmed after", SPEECH_CONFIRMATION_FRAMES, "consecutive frames, energy=", energyVal.toFixed(4), "threshold=", currentThreshold.toFixed(4));
          consecutiveSpeechRef.current = 0;
          consecutiveAboveRef.current = 0;
          inSpeechRef.current = true;
          setIsSpeechActive(true);
          speechRef.current = 0;
        }
      } else {
        consecutiveAboveRef.current++;
        audioBufferRef.current.push(new Float32Array(audioData));
        if (consecutiveAboveRef.current >= SPEECH_CONFIRMATION_FRAMES) {
          speechRef.current++;
          silenceRef.current = 0;
        }
      }
    } else {
      consecutiveAboveRef.current = 0;
      if (consecutiveSpeechRef.current > 0) {
        preSpeechMissRef.current++;
        if (preSpeechMissRef.current >= PRE_SPEECH_TOLERANCE) {
          consecutiveSpeechRef.current = 0;
          audioBufferRef.current = [];
          preSpeechMissRef.current = 0;
        }
      }
      if (inSpeechRef.current) {
        audioBufferRef.current.push(new Float32Array(audioData));
        silenceRef.current++;
        if (silenceRef.current >= breakFrames) {
          console.log("[VAD_SILENCE] Break detected: speechFrames=", speechRef.current, "silenceFrames=", silenceRef.current);
          if (mode === "suppressed") {
            console.log("[VAD_SUPPRESSED] Break detected while suppressed, firing onSuppressedSpeech");
            onSuppressedSpeechRef.current?.();
          } else {
            console.log("[VAD_SEND] Break detected, mode=", mode, "sending audio to backend");
            const keepSilenceFrames = 5;
            const trimFrames = Math.max(0, silenceRef.current - keepSilenceFrames);
            const buf = trimFrames > 0
              ? audioBufferRef.current.slice(0, audioBufferRef.current.length - trimFrames)
              : audioBufferRef.current;
            sendAudioSegment(buf);
          }
          resetSpeechState();
        }
      }
    }

    if (inSpeechRef.current && speechRef.current >= maxFrames) {
      console.log("[VAD_MAXFRAMES] Max speech duration reached: frames=", speechRef.current, "mode=", mode);
      if (mode === "suppressed") {
        console.log("[VAD_SUPPRESSED] Max frames while suppressed, firing onSuppressedSpeech");
        onSuppressedSpeechRef.current?.();
      } else {
        console.log("[VAD_SEND] Max frames reached, mode=", mode, "sending audio to backend");
        sendAudioSegment(audioBufferRef.current);
      }
      resetSpeechState();
    }

  }, [conversationBreakDuration, maxSpeechDuration, sendAudioSegment, resetSpeechState]);

  const startListening = useCallback(async () => {
    console.log("[VAD_START] Starting voice activity detection...");
    try {
      if (!isConnected) {
        console.log("[VAD_START] WebSocket not connected, connecting...");
        await connect();
        console.log("[VAD_START] WebSocket connected");
      }

      console.log("[VAD_START] Requesting microphone access...");
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      streamRef.current = stream;
      console.log("[VAD_START] Microphone access granted");

      const audioCtx = new AudioContext({ sampleRate: 16000 });
      audioCtxRef.current = audioCtx;
      await audioCtx.resume();
      console.log("[VAD_START] AudioContext created, state:", audioCtx.state);

      const workletCode = `
        class VADProc extends AudioWorkletProcessor {
          constructor() { super(); this.buf = new Float32Array(1024); this.idx = 0; }
          process(inputs) {
            const ch = inputs[0]?.[0];
            if (!ch) return true;
            for (let i = 0; i < ch.length; i++) {
              this.buf[this.idx++] = ch[i];
              if (this.idx >= 1024) {
                let sum = 0;
                for (let j = 0; j < 1024; j++) sum += this.buf[j] * this.buf[j];
                this.port.postMessage({ energy: Math.sqrt(sum / 1024), data: new Float32Array(this.buf) });
                this.idx = 0;
              }
            }
            return true;
          }
        }
        registerProcessor('vad-proc', VADProc);
      `;
      const blob = new Blob([workletCode], { type: "application/javascript" });
      const url = URL.createObjectURL(blob);
      await audioCtx.audioWorklet.addModule(url);
      URL.revokeObjectURL(url);
      console.log("[VAD_START] AudioWorklet module loaded");

      thresholdRef.current = 0.05;
      calibratingRef.current = true;

      const source = audioCtx.createMediaStreamSource(stream);
      sourceNodeRef.current = source;
      const node = new AudioWorkletNode(audioCtx, "vad-proc");
      workletRef.current = node;
      node.port.onmessage = (e) => processFrame(e.data.energy, e.data.data);
      source.connect(node);
      setIsListening(true);
      onListeningChangeRef.current?.(true);
      listeningRef.current = true;
      console.log("[VAD_START] VAD now listening (calibrating noise floor)");
    } catch (err) {
      console.error("[VAD_ERROR] start failed:", err);
      // Automatically toggle control panel mic to muted if browser blocks it
      setIsMuted?.(true);
    }
  }, [isConnected, connect, processFrame]);

  const stopListening = useCallback(() => {
    console.log("[VAD_STOP] Stopping voice activity detection");
    listeningRef.current = false;
    workletRef.current?.disconnect();
    workletRef.current = null;
    sourceNodeRef.current = null;
    audioCtxRef.current?.close();
    audioCtxRef.current = null;
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    setIsListening(false);
    onListeningChangeRef.current?.(false);
    setIsSpeechActive(false);
    setEnergy(0);
    audioBufferRef.current = [];
    speechRef.current = 0;
    silenceRef.current = 0;
    inSpeechRef.current = false;
    consecutiveSpeechRef.current = 0;
    consecutiveAboveRef.current = 0;
    console.log("[VAD_STOP] VAD stopped");
  }, []);

  useEffect(() => {
    if (vadMode === "active") {
      startListening();
    } else {
      stopListening();
    }
  }, [vadMode, startListening, stopListening]);

  useEffect(() => {
    return () => stopListening();
  }, []);

  return null;
}
