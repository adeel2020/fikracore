"use client";

import React, { useEffect, useRef, useImperativeHandle, forwardRef, useState, useCallback } from "react";
import TeleportEffect from "./TeleportEffect";
import { VoiceActivityDetector } from "@/components/voice/VoiceActivityDetector";
import { useAvatar } from "./AvatarContext";
import { useWebSocket, WebSocketProvider } from "@/contexts/WebSocketContext";

/**
 * TalkingAvatar — Loads @met4citizen/talkinghead via ES module <script> from CDN
 * at runtime. This bypasses all Next.js/Turbopack bundling issues with the library's
 * internal dynamic `import()` calls for lip-sync modules.
 *
 * The library creates its own Three.js scene, renderer, camera, lighting, and
 * animation loop — so we just provide a container div and call its API.
 */

export interface PersonaConfig {
  mood: string;
  allowedGestures: string[];
  gestureIntervalMin: number;
  gestureIntervalMax: number;
  gestureDurationMin: number;
  gestureDurationMax: number;
  gestureLookAtCameraMs: number;
  gestureTransitionMs: number;
  speakingHeadMove: number;
  speakingEyeContact: number;
  idleHeadMove: number;
  idleEyeContact: number;
  initialPose: string;
}

export type Persona = keyof typeof PERSONAS | Partial<PersonaConfig>;

export const PERSONAS: Record<string, PersonaConfig> = {
  friendly: {
    mood: "happy",
    allowedGestures: ["ok", "handup", "side"],
    gestureIntervalMin: 4000,
    gestureIntervalMax: 6000,
    gestureDurationMin: 2,
    gestureDurationMax: 4,
    gestureLookAtCameraMs: 400,
    gestureTransitionMs: 800,
    speakingHeadMove: 0.65,
    speakingEyeContact: 0.95,
    idleHeadMove: 0.5,
    idleEyeContact: 0.8,
    initialPose: "side",
  },
  professional: {
    mood: "neutral",
    allowedGestures: ["handup", "index", "side", "shrug"],
    gestureIntervalMin: 10000,
    gestureIntervalMax: 20000,
    gestureDurationMin: 1.5,
    gestureDurationMax: 3,
    gestureLookAtCameraMs: 200,
    gestureTransitionMs: 1000,
    speakingHeadMove: 0.4,
    speakingEyeContact: 0.85,
    idleHeadMove: 0.3,
    idleEyeContact: 0.7,
    initialPose: "straight",
  },
  energetic: {
    mood: "happy",
    allowedGestures: ["handup", "ok", "thumbup", "side", "index"],
    gestureIntervalMin: 4000,
    gestureIntervalMax: 10000,
    gestureDurationMin: 2.5,
    gestureDurationMax: 5,
    gestureLookAtCameraMs: 500,
    gestureTransitionMs: 600,
    speakingHeadMove: 0.75,
    speakingEyeContact: 0.9,
    idleHeadMove: 0.6,
    idleEyeContact: 0.85,
    initialPose: "wide",
  },
  serious: {
    mood: "neutral",
    allowedGestures: ["index", "side", "shrug"],
    gestureIntervalMin: 15000,
    gestureIntervalMax: 30000,
    gestureDurationMin: 1,
    gestureDurationMax: 2.5,
    gestureLookAtCameraMs: 150,
    gestureTransitionMs: 1200,
    speakingHeadMove: 0.25,
    speakingEyeContact: 0.65,
    idleHeadMove: 0.2,
    idleEyeContact: 0.5,
    initialPose: "straight",
  },
  sad: {
    mood: "sad",
    allowedGestures: ["shrug"],
    gestureIntervalMin: 20000,
    gestureIntervalMax: 40000,
    gestureDurationMin: 1,
    gestureDurationMax: 2,
    gestureLookAtCameraMs: 0,
    gestureTransitionMs: 1500,
    speakingHeadMove: 0.15,
    speakingEyeContact: 0.4,
    idleHeadMove: 0.15,
    idleEyeContact: 0.3,
    initialPose: "side",
  },
};

function resolvePersona(persona: Persona | undefined): PersonaConfig {
  if (!persona || typeof persona === "string") {
    return PERSONAS[persona || "friendly"] || PERSONAS.friendly;
  }
  const base = PERSONAS[persona.mood === "happy" ? "friendly" : "professional"];
  return { ...base, ...persona };
}

export interface SpeakAudioData {
  audio: AudioBuffer;
  words: string[];
  wtimes: number[];
  wdurations: number[];
}

export interface TalkingAvatarHandle {
  speak: (text: string) => void;
  speakFromData: (data: SpeakAudioData) => void;
  stop: () => void;
  setMood: (mood: string) => void;
  setPersona: (persona: Persona) => void;
  materialize: () => void;
  dematerialize: () => void;
}

interface TalkingAvatarProps {
  gender: "male" | "female";
  isPlaying: boolean;
  persona?: Persona;
  scale?: number;
  accentColor?: string;
  isFullscreen?: boolean;
  onReady?: () => void;
  onSpeakingChange?: (speaking: boolean) => void;
  onListeningChange?: (listening: boolean) => void;
}

const TTS_ENDPOINT = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/tts`
  : "http://localhost:8000/api/tts";

let _teleportAudio: HTMLAudioElement | null = null;

function _playTeleportSound() {
  if (typeof Audio === "undefined") return;
  if (!_teleportAudio) {
    _teleportAudio = new Audio("/sounds/mixkit-sci-fi-confirmation-914.wav");
    _teleportAudio.volume = 0.3;
    _teleportAudio.playbackRate = 0.65;
  }
  _teleportAudio.currentTime = 0;
  const p = _teleportAudio.play();
  if (p) {
    p.catch((e) => console.warn("[AVATAR_SOUND] Teleport sound blocked:", e.message));
  }
}

const AVATAR_URLS: Record<string, { url: string; body: string }> = {
  male: {
    url: "/avatars/avaturn.glb",
    body: "F", // Avaturn in the demo uses female skeleton
  },
  female: {
    url: "/avatars/brunette.glb",
    body: "F",
  },
};

// Global singleton — loaded once, reused across all instances
let _cachedTHClass: any = null;
let _loadingPromise: Promise<any> | null = null;

const TALKINGHEAD_URL = "/talkinghead/talkinghead.mjs";

/**
 * Dynamically loads TalkingHead + Three.js via script injection.
 */
function loadTalkingHeadFromCDN(): Promise<any> {
  if (_cachedTHClass) return Promise.resolve(_cachedTHClass);
  if (_loadingPromise) return _loadingPromise;

  _loadingPromise = new Promise((resolve, reject) => {
    // Inject the import map for Three.js so the TalkingHead module can resolve "three"
    if (!document.querySelector('script[data-talkinghead-importmap]')) {
      const importMap = document.createElement('script');
      importMap.type = 'importmap';
      importMap.setAttribute('data-talkinghead-importmap', 'true');
      importMap.textContent = JSON.stringify({
        imports: {
          "three": "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js/+esm",
          "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/",
        }
      });
      document.head.appendChild(importMap);
    }

    // Create a tiny inline ES module that imports TalkingHead from CDN
    const script = document.createElement("script");
    script.type = "module";
    script.textContent = `
      import { TalkingHead } from "/talkinghead/talkinghead.mjs";
      window.__TalkingHead = TalkingHead;
      window.dispatchEvent(new Event("talkinghead-loaded"));
    `;

    const onLoaded = () => {
      window.removeEventListener("talkinghead-loaded", onLoaded);
      const THClass = (window as any).__TalkingHead;
      if (THClass) {
        _cachedTHClass = THClass;
        resolve(THClass);
      } else {
        reject(new Error("TalkingHead class not found on window after CDN load"));
      }
    };

    window.addEventListener("talkinghead-loaded", onLoaded);

    // Fallback timeout — CDN might be unreachable
    const timer = setTimeout(() => {
      window.removeEventListener("talkinghead-loaded", onLoaded);
      _loadingPromise = null;
      reject(new Error("TalkingHead CDN load timed out (15s)"));
    }, 15000);

    script.onerror = () => {
      clearTimeout(timer);
      window.removeEventListener("talkinghead-loaded", onLoaded);
      _loadingPromise = null;
      reject(new Error("Failed to load TalkingHead script from CDN"));
    };

    // Listen for success to clear timeout
    const origOnLoaded = onLoaded;
    window.addEventListener("talkinghead-loaded", () => clearTimeout(timer), { once: true });

    document.head.appendChild(script);
  });

  return _loadingPromise;
}

const TalkingAvatarBody = forwardRef<TalkingAvatarHandle, TalkingAvatarProps>(
  ({ gender, isPlaying, persona: personaProp, scale = 1, accentColor = "#00E5FF", isFullscreen = false, onReady, onSpeakingChange, onListeningChange }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const headRef = useRef<any>(null);
    
    let isMuted = false;
    try {
      const contextValue = useAvatar();
      if (contextValue) {
        isMuted = contextValue.isMuted;
      }
    } catch (e) {}

    const [isLoaded, setIsLoaded] = useState(false);
    const [loadError, setLoadError] = useState<string | null>(null);
    // Parallel state: both run independently, avatar reveals when both are done
    const [showTeleport, setShowTeleport] = useState(true); // starts immediately
    const [teleportMode, setTeleportMode] = useState<"in" | "out">("in");
    const [teleportDone, setTeleportDone] = useState(false);
    const { isConnected, connect, sendAudio, onAudioReceived, onInterrupt, onWaitingStart, onWaitingEnd } = useWebSocket();
    const [waitingForResponse, setWaitingForResponse] = useState(false);
    const [vadMode, setVadMode] = useState<"active" | "suppressed" | "muted">("active");
    const [isAwake, setIsAwake] = useState(true);
    const waitingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const suppressedRef = useRef(false);

    const stopWaitingAudio = useCallback(() => {
      setWaitingForResponse(false);
      if (waitingTimeoutRef.current) {
        clearTimeout(waitingTimeoutRef.current);
        waitingTimeoutRef.current = null;
      }
    }, []);

    const startWaitingAudio = useCallback(() => {
      console.log("[VAD_MODE] startWaitingAudio called, setting vadMode=suppressed");
      stopWaitingAudio();

      setWaitingForResponse(true);
      setVadMode("suppressed");
      suppressedRef.current = false;
      if (headRef.current) {
        try {
          headRef.current.audioCtx?.resume();
          headRef.current.stopSpeaking?.();
          headRef.current.speakText("One moment please while I look that up for you.");
        } catch {}
      }

      waitingTimeoutRef.current = setTimeout(() => {
        stopWaitingAudio();
      }, 15000);
    }, [stopWaitingAudio]);

    // Wire WebSocket audio to avatar
    useEffect(() => {
      onAudioReceived(async (msg) => {
        console.log("[AVATAR_RECV] Audio received: response=", msg.response);

        const t = (msg.transcript || "").toLowerCase().trim();

        console.log("[AVATAR_CMD] isAwake=", isAwake, "transcript=", t);

        if (!isAwake) {
          if (t === "wake up" || t === "wakeup") {
            console.log("[AVATAR_CMD] Wake command -> awake=true, materialize");
            setIsAwake(true);
            setTeleportMode("in");
            setTeleportDone(false);
            setAvatarRevealed(false);
            setRevealProgress(0);
            setShowTeleport(true);
            _playTeleportSound();
          } else {
            console.log("[AVATAR_CMD] Asleep, suppressing response");
          }
          return;
        }

        if (t === "bye" || t === "goodbye" || t === "see you" || t === "talk to you later") {
          console.log("[AVATAR_CMD] Sleep command -> awake=false, dematerialize");
          setIsAwake(false);
          setTeleportMode("out");
          setTeleportDone(false);
          setAvatarRevealed(false);
          setRevealProgress(1);
          setShowTeleport(true);
          _playTeleportSound();
          return;
        }

        const responseText = msg.response || msg.transcript || "";
        if (responseText) {
          const sentenceCount = (responseText.match(/[.!?]+\s*|\n+/g) || []).length || 1;
          const estimatedMs = responseText.length * 100 + sentenceCount * 500;
          console.log("[VAD_MODE] Response received, sentenceCount=", sentenceCount, "estimatedMs=", estimatedMs);
          if (onSpeakingChange) onSpeakingChange(true);
          setVadMode("muted");
          if (headRef.current) {
            try {
              headRef.current.audioCtx?.resume();
              headRef.current.stopSpeaking?.();
              headRef.current.speakText(responseText);
            } catch {}
          }
          const startTime = Date.now();
          const tryUnmute = () => {
            const actualElapsed = Date.now() - startTime;
            const durationElapsed = actualElapsed >= estimatedMs;
            if (durationElapsed && !isPlaying) {
              console.log("[VAD_MODE] Duration elapsed + avatar done, estimatedMs=", estimatedMs, "actualMs=", actualElapsed, "setting vadMode=active");
              setVadMode("active");
            } else {
              setTimeout(tryUnmute, 500);
            }
          };
          tryUnmute();
        }
      });

      onInterrupt(() => {
        console.log("[AVATAR_INTERRUPT] Interrupt received, stopping avatar");
        setVadMode("active");
        if (headRef.current) {
          try {
            headRef.current.stopSpeaking?.();
            headRef.current.isSpeaking = false;
            headRef.current.speechQueue = [];
            headRef.current.audioPlaylist = [];
          } catch {}
        }
        if (onSpeakingChange) onSpeakingChange(false);
      });

      onWaitingStart(() => {
        startWaitingAudio();
      });

      onWaitingEnd(() => {
        stopWaitingAudio();
      });
    }, [onAudioReceived, onInterrupt, onWaitingStart, onWaitingEnd, isAwake, isPlaying, startWaitingAudio, stopWaitingAudio, onSpeakingChange]);

    const [avatarRevealed, setAvatarRevealed] = useState(false);
    const isPlayingRef = useRef(isPlaying);
    const personaRef = useRef<PersonaConfig>(resolvePersona(personaProp));
    const handTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const gestureTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const audioEndTimerRef = useRef<number | null>(null);
    const teleportSoundRef = useRef<HTMLAudioElement | null>(null);

    const applyPersonaToHead = useCallback((config: PersonaConfig) => {
      const h = headRef.current;
      if (!h) return;
      try {
        h.setMood(config.mood);
        const idleOpts = {
          avatarIdleEyeContact: config.idleEyeContact,
          avatarIdleHeadMove: config.idleHeadMove,
        };
        h.setLighting?.(idleOpts);
        h.avatar.avatarIdleEyeContact = config.idleEyeContact;
        h.avatar.avatarIdleHeadMove = config.idleHeadMove;
        h.avatar.avatarSpeakingEyeContact = config.speakingEyeContact;
        h.avatar.avatarSpeakingHeadMove = config.speakingHeadMove;
      } catch {}
    }, []);

    const clearBodyLanguage = useCallback(() => {
      if (handTimerRef.current) {
        clearTimeout(handTimerRef.current);
        handTimerRef.current = null;
      }
      if (gestureTimerRef.current) {
        clearTimeout(gestureTimerRef.current);
        gestureTimerRef.current = null;
      }
      if (audioEndTimerRef.current) {
        cancelAnimationFrame(audioEndTimerRef.current);
        audioEndTimerRef.current = null;
      }
    }, []);

    const scheduleBodyLanguage = useCallback(() => {
      const h = headRef.current;
      if (!h || !h.isAudioPlaying) return;
      try { h.speakWithHands(0, 0.7); } catch {}
      handTimerRef.current = setTimeout(scheduleBodyLanguage, 1200 + Math.random() * 1500);
    }, []);

    const scheduleRandomGesture = useCallback(() => {
      const h = headRef.current;
      const p = personaRef.current;
      if (!h || !h.isAudioPlaying) return;
      const gestures = p.allowedGestures;
      const gesture = gestures[Math.floor(Math.random() * gestures.length)];
      try {
        if (p.gestureLookAtCameraMs > 0) {
          h.lookAtCamera(p.gestureLookAtCameraMs);
        }
        const dur = p.gestureDurationMin + Math.random() * (p.gestureDurationMax - p.gestureDurationMin);
        h.playGesture(gesture, dur, false, p.gestureTransitionMs);
      } catch {}
      const interval = p.gestureIntervalMin + Math.random() * (p.gestureIntervalMax - p.gestureIntervalMin);
      gestureTimerRef.current = setTimeout(scheduleRandomGesture, interval);
    }, []);

    const startBodyLanguage = useCallback(() => {
      clearBodyLanguage();
      scheduleBodyLanguage();
      const p = personaRef.current;
      const delay = p.gestureIntervalMin * 0.3 + Math.random() * (p.gestureIntervalMax * 0.3);
      gestureTimerRef.current = setTimeout(scheduleRandomGesture, delay);
    }, [clearBodyLanguage, scheduleBodyLanguage, scheduleRandomGesture]);

    const stopBodyLanguage = useCallback(() => {
      clearBodyLanguage();
      if (headRef.current) {
        try { headRef.current.stopGesture?.(500); } catch {}
      }
    }, [clearBodyLanguage]);

    const checkSpeechDone = useCallback(() => {
      const h = headRef.current;
      if (!h) { onSpeakingChange?.(false); stopBodyLanguage(); return; }

      // SDK isSpeaking stays true during async TTS fetch gaps (lines queued
      // but audio not yet loaded), so we check it alongside isAudioPlaying,
      // speechQueue, and audioPlaylist to avoid false "done" signals.
      if (!h.isAudioPlaying && !h.isSpeaking && !h.speechQueue?.length && !h.audioPlaylist?.length) {
        console.log("[SPEECH_DONE] All queues empty, signalling done");
        onSpeakingChange?.(false);
        stopBodyLanguage();
        return;
      }

      audioEndTimerRef.current = requestAnimationFrame(checkSpeechDone);
    }, [onSpeakingChange, stopBodyLanguage]);

    useEffect(() => {
      isPlayingRef.current = isPlaying;
    }, [isPlaying]);

    // Apply persona on change
    useEffect(() => {
      personaRef.current = resolvePersona(personaProp);
      if (isLoaded) {
        applyPersonaToHead(personaRef.current);
      }
    }, [personaProp, isLoaded, applyPersonaToHead]);

    useImperativeHandle(ref, () => ({
      resumeAudioContext: () => {
        const h = headRef.current;
        if (h?.audioCtx && h.audioCtx.state === "suspended") {
          h.audioCtx.resume();
        }
      },
      speak: (text: string) => {
        console.log("[AVATAR_SPEAK] speakText called, text=", text);
        if (headRef.current) {
          try {
            headRef.current.audioCtx?.resume();
            headRef.current.stopSpeaking?.();
            headRef.current.speakText(text);
            onSpeakingChange?.(true);
            checkSpeechDone();
            console.log("[AVATAR_SPEAK] speakText queued");
          } catch {
            const p = personaRef.current;
            try { headRef.current.setMood(p.mood); } catch {}
          }
        } else {
          console.log("[AVATAR_SPEAK] headRef not ready");
        }
      },
      speakFromData: (data: SpeakAudioData) => {
        const h = headRef.current;
        if (!h) {
          console.log("[AVATAR_SPEAK_DATA] headRef not ready, cannot speak");
          return;
        }
        console.log("[AVATAR_SPEAK_DATA] Starting: words=", data.words?.slice(0, 5), "audioDuration=", data.audio?.duration?.toFixed(2) + "s");
        try {
          h.audioCtx?.resume();
          if (h.audioSpeechSource) {
            console.log("[AVATAR_SPEAK_DATA] Nullifying old audioSpeechSource.onended");
            h.audioSpeechSource.onended = null;
          }
          console.log("[AVATAR_SPEAK_DATA] Calling stopSpeaking...");
          h.stopSpeaking?.();
          console.log("[AVATAR_SPEAK_DATA] Calling speakAudio...");
          h.speakAudio(data);

          h.isAudioPlaying = true;
          onSpeakingChange?.(true);
          checkSpeechDone();
          console.log("[AVATAR_SPEAK_DATA] speakAudio queued successfully");
        } catch (e) {
          console.log("[AVATAR_SPEAK_DATA] Error:", e);
        }
      },
      stop: () => {
        console.log("[AVATAR_STOP] Stopping avatar speech");
        stopBodyLanguage();
        if (headRef.current) {
          try {
            headRef.current.stopSpeaking?.();
            headRef.current.isSpeaking = false;
            headRef.current.speechQueue = [];
            headRef.current.audioPlaylist = [];
            const p = personaRef.current;
            headRef.current.setMood(p.mood);
            onSpeakingChange?.(false);
          } catch {}
        }
      },
      setMood: (mood: string) => {
        if (headRef.current) {
          try { headRef.current.setMood(mood); } catch {}
        }
      },
      setPersona: (persona: Persona) => {
        personaRef.current = resolvePersona(persona);
        applyPersonaToHead(personaRef.current);
      },
      dematerialize: () => {
        if (!isLoaded) return;
        console.log("[AVATAR_TELEPORT] Dematerializing");
        setTeleportMode("out");
        setTeleportDone(false);
        setAvatarRevealed(false);
        setRevealProgress(1);
        setShowTeleport(true);
        _playTeleportSound();
      },
      materialize: () => {
        if (!isLoaded) return;
        console.log("[AVATAR_TELEPORT] Materializing");
        setTeleportMode("in");
        setTeleportDone(false);
        setAvatarRevealed(false);
        setRevealProgress(0);
        setShowTeleport(true);
        _playTeleportSound();
      },
    }));

    // Set persona after avatar loads
    useEffect(() => {
      if (!isLoaded) return;
      applyPersonaToHead(personaRef.current);
    }, [isLoaded, applyPersonaToHead]);

    // Initialize TalkingHead from CDN
    useEffect(() => {
      if (!containerRef.current) return;

      let disposed = false;

      const init = async () => {
        try {
          const THClass = await loadTalkingHeadFromCDN();
          if (disposed || !containerRef.current) return;

          // Clear any previous content
          containerRef.current.innerHTML = "";

          const p = personaRef.current;

          const head = new THClass(containerRef.current, {
            ttsEndpoint: TTS_ENDPOINT,
            ttsApikey: null,
            ttsVoice: "nova",
            ttsVolume: 6,
            lipsyncModules: ["en"],
            lipsyncLang: "en",
            cameraView: "full",
            cameraDistance: 0,
            cameraX: 0,
            cameraY: 0,
            cameraRotateEnable: false,
            cameraPanEnable: false,
            cameraZoomEnable: false,
            modelFPS: 30,
            modelPixelRatio: Math.min(window.devicePixelRatio, 2),
            modelMovementFactor: 1,
            lightAmbientColor: 0xffffff,
            lightAmbientIntensity: 2.5,
            lightDirectColor: 0xfff5ea,
            lightDirectIntensity: 25,
            lightDirectPhi: 0.2,
            lightDirectTheta: 2.5,
            lightSpotColor: accentColor,
            lightSpotIntensity: 8,
            lightSpotPhi: 0.1,
            lightSpotTheta: 4,
            lightSpotDispersion: 1,
            avatarMood: isPlaying ? p.mood : "neutral",
            avatarIdleEyeContact: p.idleEyeContact,
            avatarIdleHeadMove: p.idleHeadMove,
            avatarSpeakingEyeContact: p.speakingEyeContact,
            avatarSpeakingHeadMove: p.speakingHeadMove,
            avatarIgnoreCamera: false,
          });

          headRef.current = head;

          const avatarConfig = AVATAR_URLS[gender] || AVATAR_URLS.male;

          await head.showAvatar({
            url: avatarConfig.url,
            body: avatarConfig.body,
            avatarMood: isPlaying ? p.mood : "neutral",
            lipsyncLang: "en",
            avatarIdleEyeContact: p.idleEyeContact,
            avatarSpeakingEyeContact: p.speakingEyeContact,
            avatarSpeakingHeadMove: p.speakingHeadMove,
            avatarIgnoreCamera: false,
          });

          if (!disposed) {
            setIsLoaded(true);
            setLoadError(null);
            onReady?.();

            // Resume AudioContext on first user gesture (browser autoplay policy)
            const unlockAudio = () => {
              if (head.audioCtx?.state === "suspended") {
                head.audioCtx.resume();
              }
              document.removeEventListener("pointerdown", unlockAudio);
            };
            document.addEventListener("pointerdown", unlockAudio, { once: true });

            try {
              head.setView("full", { cameraDistance: 0 });
              head.setPoseFromTemplate(p.initialPose, 1000);
              head.lookAtCamera(0.8);
            } catch {}
          }
        } catch (err: any) {
          console.error("TalkingHead initialization failed:", err);
          if (!disposed) {
            setLoadError(err?.message || "Failed to load 3D avatar engine.");
          }
        }
      };

      init();

      return () => {
        disposed = true;
        stopBodyLanguage();
        if (headRef.current && containerRef.current) {
          try {
            containerRef.current.innerHTML = "";
          } catch {}
        }
        headRef.current = null;
        setIsLoaded(false);
      };
    }, [gender]);

    // Update lighting accent color when theme changes
    useEffect(() => {
      if (!headRef.current || !isLoaded) return;
      try {
        headRef.current.setLighting({
          lightSpotColor: accentColor,
          lightSpotIntensity: 8,
        });
      } catch {}
    }, [accentColor, isLoaded]);

    // Apply avatar scale via camera distance (avoids clipping)
    useEffect(() => {
      if (!headRef.current || !isLoaded) return;
      const dist = (1 - scale) * 3;
      try {
        headRef.current.setView("full", { cameraDistance: dist });
      } catch {}
    }, [scale, isLoaded]);

    const [revealProgress, setRevealProgress] = useState(0);

    const handleTeleportComplete = useCallback(() => {
      setTeleportDone(true);
      setRevealProgress(teleportMode === "in" ? 1 : 0);
    }, [teleportMode]);

    const handleTeleportProgress = useCallback((p: number) => {
      setRevealProgress(p);
    }, []);

    // Toggle manual materialize/dematerialize on click
    const handleToggleTeleport = useCallback(() => {
      if (!isLoaded || showTeleport) return; // Don't interrupt if not loaded or currently teleporting

      if (avatarRevealed) {
        // Currently visible -> Dematerialize
        setTeleportMode("out");
        setTeleportDone(false);
        setAvatarRevealed(false);
        setRevealProgress(1); // Start fully revealed
        setShowTeleport(true);
      } else {
        // Currently hidden -> Materialize
        setTeleportMode("in");
        setTeleportDone(false);
        setRevealProgress(0); // Start fully hidden
        setShowTeleport(true);
      }
      _playTeleportSound();
    }, [isLoaded, showTeleport, avatarRevealed]);

    // Reveal/Hide avatar when BOTH loading and teleport are finished
    useEffect(() => {
      if (isLoaded && teleportDone) {
        // Small delay for the dissolve to finish visually
        const t = setTimeout(() => {
          setShowTeleport(false);
          if (teleportMode === "in") {
            setAvatarRevealed(true);
          }
        }, 300);
        return () => clearTimeout(t);
      }
    }, [isLoaded, teleportDone, teleportMode]);

    const feather = 12; // percentage of feathered edge
    let maskStyle: React.CSSProperties = {};
    
    if (!avatarRevealed) {
      if (teleportMode === "in") {
        // Materialize: Head to Feet. RevealProgress 0 -> 1.
        const maskPercent = revealProgress * 115;
        maskStyle = {
          WebkitMaskImage: `linear-gradient(to bottom, black ${Math.max(0, maskPercent - feather)}%, transparent ${maskPercent}%)`,
          maskImage: `linear-gradient(to bottom, black ${Math.max(0, maskPercent - feather)}%, transparent ${maskPercent}%)`,
        };
      } else {
        // Dematerialize: Feet to Head. RevealProgress 1 -> 0.
        // As revealProgress goes to 0, the transparent area at the bottom grows upwards.
        const hidePercent = (1 - revealProgress) * 115;
        maskStyle = {
          WebkitMaskImage: `linear-gradient(to top, transparent ${Math.max(0, hidePercent - feather)}%, black ${hidePercent}%)`,
          maskImage: `linear-gradient(to top, transparent ${Math.max(0, hidePercent - feather)}%, black ${hidePercent}%)`,
        };
      }
    }

    let containerOpacity = 0;
    if (avatarRevealed) {
      containerOpacity = 1;
    } else if (isLoaded) {
      if (showTeleport) {
        containerOpacity = 1; // Mask handles the hiding
      } else {
        containerOpacity = 0; // Fully hidden when dematerialized
      }
    }

    return (
      <div 
        className="relative w-full h-full cursor-pointer"
        onClick={handleToggleTeleport}
        title="Click to materialize/dematerialize"
      >
        {/* Sci-fi teleportation effect — behind and around the avatar */}
        <TeleportEffect
          isActive={showTeleport}
          mode={teleportMode}
          accentColor={accentColor}
          onComplete={handleTeleportComplete}
          onProgress={handleTeleportProgress}
          duration={5500}
          offsetX={0}
        />

        {/* TalkingHead canvas — centered inside the ring */}
        <div
          ref={containerRef}
          className="transition-opacity duration-700"
          style={{
            position: "absolute",
            left: "50%",
            top: isFullscreen ? "15%" : "0%",
            transform: "translateX(-50%)",
            width: "100%",
            height: "100%",
            maxWidth: "520px",
            filter: "drop-shadow(0 15px 25px rgba(0, 0, 0, 0.5))",
            opacity: containerOpacity,
            backfaceVisibility: "hidden",
            ...maskStyle,
          }}
        />

        {/* Fallback spinner — only if teleport finished but avatar is still loading */}
        {teleportDone && !isLoaded && !loadError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <div className="relative">
              <div
                className="w-16 h-16 rounded-full border-2 animate-spin"
                style={{ 
                  borderTopColor: "transparent",
                  borderRightColor: `${accentColor}40`,
                  borderBottomColor: `${accentColor}40`,
                  borderLeftColor: `${accentColor}40`
                }}
              />
              <div
                className="absolute inset-2 rounded-full border-2 animate-spin"
                style={{
                  borderTopColor: `${accentColor}60`,
                  borderRightColor: `${accentColor}60`,
                  borderBottomColor: "transparent",
                  borderLeftColor: `${accentColor}60`,
                  animationDirection: "reverse",
                  animationDuration: "0.8s",
                }}
              />
            </div>
            <span
              className="text-[10px] font-bold uppercase tracking-widest animate-pulse"
              style={{ color: accentColor }}
            >
              Materializing...
            </span>
          </div>
        )}

        {/* Error State */}
        {loadError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-center px-4">
            <span className="text-3xl">⚠️</span>
            <span className="text-[10px] font-bold text-red-400 uppercase tracking-wider max-w-full break-words">
              {loadError}
            </span>
            <button
              onClick={() => {
                setLoadError(null);
                _loadingPromise = null;
                _cachedTHClass = null;
                if (containerRef.current) containerRef.current.innerHTML = "";
              }}
              className="mt-2 px-3 py-1 text-[9px] font-bold uppercase tracking-wider rounded-full bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 transition-colors cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {/* Voice Activity Detector is now a core background sub-module of the Avatar */}
        <VoiceActivityDetector 
          energyThreshold={0.06} 
          vadMode={isMuted ? "muted" : vadMode} 
          onSuppressedSpeech={() => {
            if (!suppressedRef.current) {
              suppressedRef.current = true;
              headRef.current?.speak("I'm already working on your existing request. Will entertain this later");
            }
          }} 
          onListeningChange={onListeningChange} 
        />
      </div>
    );
  }
);

TalkingAvatarBody.displayName = "TalkingAvatarBody";

const TalkingAvatar = forwardRef<TalkingAvatarHandle, TalkingAvatarProps>(({ isFullscreen, ...props }, ref) => {
  return (
    <WebSocketProvider>
      <TalkingAvatarBody isFullscreen={isFullscreen} {...props} ref={ref} />
    </WebSocketProvider>
  );
});

TalkingAvatar.displayName = "TalkingAvatar";

export default TalkingAvatar;
