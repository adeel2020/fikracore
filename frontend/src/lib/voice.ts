"use client";

import { WS_BASE } from "@/lib/api/config";
import type { MarkPresentation } from "@/lib/mark-presentation";

// Global reference array to prevent Chrome garbage-collection bug
const activeUtterances: SpeechSynthesisUtterance[] = [];

export type VoiceState = "idle" | "listening" | "processing" | "speaking";
export type MarkVoiceTone = "young_male" | "executive" | "calm" | "operator" | "demo";
export type MarkVoiceMode = "backend" | "browser";

export interface MarkVoiceSettings {
  voiceURI: string;
  tone: MarkVoiceTone;
  mode: MarkVoiceMode;
  playbackRate: number;
  autoCorrect: boolean;
}

export interface LiveVoiceCallbacks {
  onStateChange?: (state: VoiceState) => void;
  onTranscript?: (text: string, isFinal: boolean) => void;
  onResponse?: (text: string, spokenText?: string, presentation?: MarkPresentation) => void;
  onMessageSubmit?: (text: string) => Promise<string | void>;
  onError?: (err: unknown) => void;
}

interface BrowserSpeechRecognitionResult {
  readonly isFinal: boolean;
  readonly 0: { readonly transcript: string };
}

interface BrowserSpeechRecognitionEvent {
  readonly resultIndex: number;
  readonly results: {
    readonly length: number;
    readonly [index: number]: BrowserSpeechRecognitionResult;
  };
}

interface BrowserSpeechRecognitionError {
  readonly error?: string;
}

interface BrowserSpeechRecognition {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onresult: ((event: BrowserSpeechRecognitionEvent) => void) | null;
  onerror: ((event: BrowserSpeechRecognitionError) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

type BrowserSpeechRecognitionConstructor = new () => BrowserSpeechRecognition;

type BrowserWindow = Window & {
  AudioContext?: typeof AudioContext;
  webkitAudioContext?: typeof AudioContext;
  SpeechRecognition?: BrowserSpeechRecognitionConstructor;
  webkitSpeechRecognition?: BrowserSpeechRecognitionConstructor;
};

const VOICE_SETTINGS_KEY = "mark_voice_settings";
export const MARK_PLAYBACK_RATES = [0.75, 0.9, 1, 1.25, 1.5, 2] as const;

const TONE_PROFILES: Record<MarkVoiceTone, { label: string; rate: number; pitch: number; volume: number }> = {
  young_male: { label: "Young Male (Soft)", rate: 0.98, pitch: 1.08, volume: 0.94 },
  executive: { label: "Executive", rate: 1.0, pitch: 0.98, volume: 1 },
  calm: { label: "Calm", rate: 0.88, pitch: 0.96, volume: 1 },
  operator: { label: "Operator", rate: 1.02, pitch: 0.94, volume: 1 },
  demo: { label: "Demo", rate: 0.98, pitch: 1.0, volume: 1 },
};

export const MARK_VOICE_TONES = Object.entries(TONE_PROFILES).map(([id, profile]) => ({
  id: id as MarkVoiceTone,
  label: profile.label,
}));

export const DEFAULT_VOICE_SETTINGS: MarkVoiceSettings = {
  voiceURI: "auto",
  tone: "young_male",
  mode: "backend",
  playbackRate: 1,
  autoCorrect: true,
};

const INCOMPLETE_TRAILING_WORDS = new Set([
  // Prepositions
  "to", "for", "with", "about", "from", "in", "on", "at", "by", "of", "into", "through",
  "during", "before", "after", "above", "below", "between", "under", "without", "against",
  // Conjunctions
  "and", "or", "but", "because", "since", "while", "though", "although", "unless", "if",
  "than", "as", "so", "that", "whether",
  // Articles & determiners
  "the", "a", "an", "this", "that", "these", "those", "my", "your", "his", "her", "its", "our", "their", "any", "some", "every",
  // Auxiliary verbs / modal helpers
  "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "can", "could", "shall", "should", "will", "would", "may", "might", "must",
]);

const INCOMPLETE_STARTERS = [
  "can you", "could you", "would you", "will you", "should i", "do you", "did you",
  "are there", "is there", "what is", "what are", "what was", "where is", "where are",
  "how do", "how does", "how can", "why is", "why did", "tell me", "show me",
  "give me", "look at", "check the", "explain the", "summarize the", "find the",
  "help me", "i want", "i need", "please", "can i", "could i",
];

export function isLikelyIncompleteUtterance(text: string): boolean {
  const trimmed = text.trim().toLowerCase();
  const words = trimmed.split(/\s+/).filter(Boolean);
  if (words.length === 0) return true;

  // Single or two-word lead-ins like "can you", "what is", "tell me" are never complete commands
  if (words.length < 3) {
    const allowedShortCommands = new Set(["status", "help", "clear", "stop", "reset", "incidents", "alerts", "overview", "rca"]);
    if (words.length === 1 && allowedShortCommands.has(words[0])) {
      return false;
    }
    return true;
  }

  // Check if starts with common question opener but has fewer than 4 words
  if (words.length < 4) {
    if (INCOMPLETE_STARTERS.some((starter) => trimmed.startsWith(starter))) {
      return true;
    }
  }

  // Check if ending in trailing dangling word
  const lastWord = words[words.length - 1].replace(/[^a-z0-9]/g, "");
  if (INCOMPLETE_TRAILING_WORDS.has(lastWord)) {
    return true;
  }

  return false;
}

/**
 * Phonetic & domain-specific normalizer for browser speech recognition.
 * Corrects common STT mis-transcriptions for telecom acronyms & phrases.
 */
export function normalizeTelecomTranscript(rawText: string): string {
  let t = rawText;

  const replacements: [RegExp, string][] = [
    // Misheard "these functions" / "this function" / "dysfunctions"
    [/\bdysfunctions\b/gi, "network functions"],
    [/\bdysfunction\b/gi, "network function"],
    [/\bdisfunctions\b/gi, "network functions"],
    [/\bdisfunction\b/gi, "network function"],
    [/\bthese functions\b/gi, "network functions"],
    [/\bthis functions\b/gi, "network functions"],
    [/\bthis function\b/gi, "network function"],
    [/\bnetworking\s+inventory\b/gi, "network inventory"],
    [/\bnetworking\s+event\s+(three|tree|free)\b/gi, "network inventory"],
    [/\bnetwork\s+event\s+(three|tree|free)\b/gi, "network inventory"],
    [/\bnetworking\s+in\s+the\s+tree\b/gi, "network inventory"],

    // Network Functions Acronyms
    [/\ba\s+m\s+f\b/gi, "AMF"],
    [/\ba\.m\.f\b/gi, "AMF"],
    [/\bu\s+p\s+f\b/gi, "UPF"],
    [/\byou\s+p\s+f\b/gi, "UPF"],
    [/\bu\.p\.f\b/gi, "UPF"],
    [/\bs\s+m\s+f\b/gi, "SMF"],
    [/\bs\.m\.f\b/gi, "SMF"],
    [/\bg\s+node\s*b\b/gi, "gNodeB"],
    [/\bg\s+note\s*b\b/gi, "gNodeB"],
    [/\be\s+node\s*b\b/gi, "eNodeB"],
    [/\be\s+note\s*b\b/gi, "eNodeB"],
    [/\bm\s+m\s+e\b/gi, "MME"],
    [/\bh\s+s\s+s\b/gi, "HSS"],
    [/\bp\s+c\s+f\b/gi, "PCF"],
    [/\bu\s+d\s+m\b/gi, "UDM"],

    // Operational Metrics & Tools
    [/\br\s+c\s+a\b/gi, "RCA"],
    [/\bm\s+t\s+t\s+r\b/gi, "MTTR"],
    [/\bf\s+c\s+a\s+p\s+s\b/gi, "FCAPS"],
    [/\br\s+s\s+r\b/gi, "RSR"],
    [/\bg\s+brain\b/gi, "gbrain"],
    [/\b5\s+g\s+c\b/gi, "5GC"],
    [/\b5\s+g\s+core\b/gi, "5G Core"],
    [/\bv\s+e\s+p\s+c\b/gi, "vEPC"],
    [/\bs\s+1\s+m\s*m\s*e\b/gi, "S1-MME"],
    [/\bs\s*gi\b/gi, "SGi"],
  ];

  for (const [regex, replacement] of replacements) {
    t = t.replace(regex, replacement);
  }

  return t.replace(/\s+/g, " ").trim();
}

function prepareSpeechText(rawText: string): string {
  if (!rawText || !rawText.trim()) return "";

  let text = rawText
    .replace(/```[\s\S]*?```/g, "Code snippet omitted.")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/- From `[^`]+` \/ [^:]+:/g, "")
    .replace(/https?:\/\/\S+/g, "link")
    // Strip emojis and pictographs so speech engines never pronounce them aloud (e.g. 🎙️ -> "studio mic", ⚠️ -> "warning sign")
    .replace(/[\u{1F300}-\u{1FAD6}\u{200D}\u{FE0E}\u{FE0F}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}]/gu, "")
    // Turn parenthetical notes into natural conversational pauses
    .replace(/\s*\(([^)]+)\)\s*/g, ", $1, ")
    // Turn clause-separating dashes and semicolons into breathing pauses
    .replace(/\s+[-—–]\s+/g, ", ")
    .replace(/;\s*/g, ". ")
    .replace(/:\s+/g, ". ")
    // Natural pause after introductory transition adverbs
    .replace(/\b(Specifically|Consequently|As a result|However|Furthermore|Additionally|In this case|Notice that)\s+/gi, "$1, ")
    // Format percentages into natural speech (18.4% -> 18 point 4 percent)
    .replace(/(\d+)\.(\d+)\s*%/g, "$1 point $2 percent")
    .replace(/(\d+)\s*%/g, "$1 percent")
    // Format error codes and HTTP numbers for spoken cadence (502 -> 5, 0, 2)
    .replace(/\b(HTTP|status|code|error)\s+([1-5])(\d)(\d)\b/gi, "$1 $2, $3, $4")
    // Format durations (14ms -> 14 milliseconds)
    .replace(/(\d+)\s*ms\b/gi, "$1 milliseconds")
    // Strip boilerplates and markdown headers
    .replace(/^Under scenario[^\n.]+\.\s*/gi, "")
    .replace(/^Terminal state is[^\n.]+\.\s*/gi, "")
    .replace(/^#{1,6}\s+/gm, "")
    // Remove formatting symbols, bullets, and quotes
    .replace(/[*_#~>\[\]|•]/g, " ")
    .replace(/["“”«»]/g, "");

  const pronunciation: [RegExp, string][] = [
    [/\bMARK\b/g, "Mark"],
    [/\bAMF\b/g, "A M F"],
    [/\bSMF\b/g, "S M F"],
    [/\bUPF\b/g, "U P F"],
    [/\bUDM\b/g, "U D M"],
    [/\bAUSF\b/g, "A U S F"],
    [/\bPCF\b/g, "P C F"],
    [/\bMME\b/g, "M M E"],
    [/\bHSS\b/g, "H S S"],
    [/\bIMS\b/g, "I M S"],
    [/\bRAN\b/g, "ran"],
    [/\bRCA\b/g, "R C A"],
    [/\bMTTR\b/g, "M T T R"],
    [/\bFCAPS\b/g, "F caps"],
    [/\bgbrain\b/gi, "G brain"],
    [/\bgNodeB\b/g, "G node B"],
    [/\beNodeB\b/g, "E node B"],
    [/\b5GC\b/g, "five G core"],
    [/\b5G Core\b/gi, "five G core"],
    [/\b4G\b/g, "four G"],
    [/\b5G\b/g, "five G"],
    [/\bLTE\b/g, "L T E"],
    [/\bVoLTE\b/g, "voice over L T E"],
    [/\bS1-MME\b/g, "S one M M E"],
    [/\bSGi\b/g, "S G I"],
    [/\bN6\b/g, "N six"],
    [/\bQoS\b/g, "quality of service"],
    [/\bKPI\b/g, "K P I"],
    [/\bKPIs\b/g, "K P I's"],
    [/\bSLA\b/g, "S L A"],
    [/\bSLAs\b/g, "S L A's"],
    [/\bPDU\b/g, "P D U"],
    [/\bUE\b/g, "U E"],
    [/\bNOC\b/g, "knock"],
    // Entity keys & Telecom names to natural spoken form
    [/\bIP:PE:RTR-21\b/gi, "Provider Edge router 21"],
    [/\bPE:RTR-21\b/gi, "Provider Edge router 21"],
    [/\bPE-RTR-21\b/gi, "Provider Edge router 21"],
    [/\bSA5G:UPF:003\b/gi, "User Plane Function 3"],
    [/\bUPF-003\b/gi, "User Plane Function 3"],
    [/\bUPF-03\b/gi, "User Plane Function 3"],
    [/\bIP:VRF:N3-01\b/gi, "N 3 routing instance"],
    [/\bVRF-N3-01\b/gi, "N 3 routing instance"],
    [/\bRAN:eNodeB:101\b/gi, "Radio Network Node 101"],
    [/\beNodeB:101\b/gi, "Radio Network Node 101"],
    [/\bbufferOverflowTrap\b/gi, "buffer overflow alert"],
    [/\bPE_ROUTER_DEGRADED\b/gi, "Provider Edge router degradation"],
    [/\bVRF_DEGRADED\b/gi, "VRF interface degradation"],
    [/\bUPF_DEGRADED\b/gi, "User Plane Function degradation"],
    [/\bRADIO SERVICE LOST\b/gi, "Radio Service Lost"],
    [/\bPE-RTR-0?(\d+)\b/gi, "Provider Edge router $1"],
    [/\bUPF-0?(\d+)\b/gi, "U-P-F $1"],
    [/\bSCN-0?(\d+)\b/gi, "Scenario $1"],
    [/\bRUN-0?(\d+)\b/gi, "Run $1"],
    [/\b(\d+(?:\.\d+)?)\s*Gbps\b/gi, "$1 gigabits per second"],
    [/\b(\d+(?:\.\d+)?)\s*Mbps\b/gi, "$1 megabits per second"],
  ];

  for (const [regex, replacement] of pronunciation) {
    text = text.replace(regex, replacement);
  }

  // Clean up punctuation spacing
  text = text
    .replace(/,\s*,+/g, ",")
    .replace(/,\s*\./g, ".")
    .replace(/\s+/g, " ")
    .trim();

  // Enforce conversational brevity: max 2 sentences (~30 words) for natural speech cadence
  const sentences = text.match(/[^.!?\n]+[.!?\n]+|[^.!?\n]+$/g) || [text];
  if (sentences.length > 2) {
    let brief = sentences.slice(0, 2).map((s) => s.trim()).join(" ");
    const words = brief.split(/\s+/);
    if (words.length > 35) {
      brief = words.slice(0, 32).join(" ") + "...";
    }
    return `${brief}... I've outlined the full operational details on your screen.`;
  }

  return text;
}

export interface SpeechQueueItem {
  id: string;
  text: string;
  cleanText: string;
  chunks: string[];
  options?: {
    onStart?: () => void;
    onEnd?: () => void;
    onError?: (err: unknown) => void;
    priority?: "normal" | "interrupt";
  };
}

class JarvisVoiceAssistant {
  private isSpeaking: boolean = false;
  private isPaused: boolean = false;
  private isListening: boolean = false;
  private isLiveMode: boolean = false;
  private isSubmitting: boolean = false;
  private isMuted: boolean = false;
  private speechQueue: SpeechQueueItem[] = [];
  private currentSpeechItem: SpeechQueueItem | null = null;
  private isProcessingSpeechQueue: boolean = false;
  private activeRunId: string | null = null;
  private lastSpokenText: string = "";
  private audioCtx: AudioContext | null = null;
  private recognition: BrowserSpeechRecognition | null = null;
  private silenceTimer: ReturnType<typeof setTimeout> | null = null;
  private currentTranscript: string = "";
  private callbacks: LiveVoiceCallbacks = {};
  private ws: WebSocket | null = null;
  private wsSessionId: string = "";
  private micStream: MediaStream | null = null;
  private micSource: MediaStreamAudioSourceNode | null = null;
  private micNode: ScriptProcessorNode | null = null;
  private playbackCtx: AudioContext | null = null;
  private playbackQueue: AudioBuffer[] = [];
  private activeSources: AudioBufferSourceNode[] = [];
  private nextPlayTime: number = 0;
  private speakingEndTime: number = 0;
  private isBackendLive: boolean = false;
  private isPlayingBackendAudio: boolean = false;
  private nextOutputSampleRate: number = 24000;
  private lastBackendAnswer: string = "";
  private activeGeneration = 0;
  private lastBargeInAt = 0;
  private browserBargeInGraceUntil = 0;
  private speechEndGraceUntil = 0;
  private activeSpokenText = "";
  private speechChunks: string[] = [];
  private currentChunkIndex = 0;
  private speechKeepAliveTimer: ReturnType<typeof setInterval> | null = null;
  private lastTranscriptAt = 0;
  private voiceSettings: MarkVoiceSettings = DEFAULT_VOICE_SETTINGS;
  private voicesLoadedPromise: Promise<SpeechSynthesisVoice[]> | null = null;
  private cachedSelectedVoice: SpeechSynthesisVoice | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.isMuted = false;
      this.voiceSettings = this.loadVoiceSettings();
      this.setupGlobalUnlock();
      this.ensureVoicesLoaded().then(() => {
        this.getOrSelectVoice();
      });
      if ("speechSynthesis" in window) {
        window.speechSynthesis.addEventListener("voiceschanged", () => {
          this.cachedSelectedVoice = null;
          this.getOrSelectVoice();
        });
      }
    }
  }

  private setupGlobalUnlock() {
    if (typeof window === "undefined") return;

    const unlock = () => {
      this.prime();
      window.removeEventListener("click", unlock);
      window.removeEventListener("keydown", unlock);
      window.removeEventListener("touchstart", unlock);
    };

    window.addEventListener("click", unlock, { once: false, passive: true });
    window.addEventListener("keydown", unlock, { once: false, passive: true });
    window.addEventListener("touchstart", unlock, { once: false, passive: true });
  }

  private getAudioContextCtor(): typeof AudioContext | null {
    if (typeof window === "undefined") return null;
    const w = window as BrowserWindow;
    return w.AudioContext || w.webkitAudioContext || null;
  }

  public prime() {
    if (typeof window === "undefined") return;

    try {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.resume();
      }
    } catch {}

    try {
      const AudioCtx = this.getAudioContextCtor();
      if (AudioCtx) {
        if (!this.audioCtx) {
          this.audioCtx = new AudioCtx();
        }
        if (this.audioCtx.state === "suspended") {
          this.audioCtx.resume();
        }
      }
    } catch {}
  }

  /**
   * Plays an audible high-tech HUD chime to verify speaker output
   */
  public playChime(freq: number = 587.33, duration: number = 0.12) {
    if (typeof window === "undefined") return;
    this.prime();

    try {
      const AudioCtx = this.getAudioContextCtor();
      if (!AudioCtx) return;
      const ctx = this.audioCtx || new AudioCtx();
      this.audioCtx = ctx;

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(freq * 1.5, ctx.currentTime + duration);

      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch (e) {
      console.warn("[MARK Audio] Chime error:", e);
    }
  }

  public setMuted(muted: boolean) {
    this.isMuted = muted;
    if (typeof window !== "undefined") {
      localStorage.setItem("jarvis_voice_muted", muted ? "true" : "false");
    }
    if (muted) {
      this.stop();
    }
  }

  public getIsMuted(): boolean {
    return this.isMuted;
  }

  public getIsSpeaking(): boolean {
    return this.isSpeaking;
  }

  public getIsPaused(): boolean {
    return this.isPaused;
  }

  public pause(): void {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.pause();
      this.isPaused = true;
    }
  }

  public resume(): void {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.resume();
      this.isPaused = false;
    }
  }

  public repeatLastAnswer(): void {
    if (this.lastSpokenText) {
      this.speak(this.lastSpokenText);
    }
  }

  public getLastSpokenText(): string {
    return this.lastSpokenText;
  }

  public getIsListening(): boolean {
    return this.isListening;
  }

  public getIsLiveMode(): boolean {
    return this.isLiveMode;
  }

  public getVoiceSettings(): MarkVoiceSettings {
    return this.voiceSettings;
  }

  public getPlaybackRate(): number {
    return this.voiceSettings.playbackRate || 1.0;
  }

  public setPlaybackRate(rate: number): void {
    const clamped = Math.max(0.75, Math.min(1.5, Number(rate) || 1.0));
    this.setVoiceSettings({ playbackRate: clamped });
  }

  public setVoiceSettings(settings: Partial<MarkVoiceSettings>) {
    this.voiceSettings = {
      ...this.voiceSettings,
      ...settings,
    };
    if (typeof window !== "undefined") {
      localStorage.setItem(VOICE_SETTINGS_KEY, JSON.stringify(this.voiceSettings));
    }
  }

  public getAvailableVoices(): SpeechSynthesisVoice[] {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return [];
    return window.speechSynthesis.getVoices().filter((voice) => voice.lang.toLowerCase().startsWith("en"));
  }

  public async ensureVoicesLoaded(): Promise<SpeechSynthesisVoice[]> {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      return [];
    }
    const current = window.speechSynthesis.getVoices();
    if (current.length > 0) {
      return current;
    }
    if (this.voicesLoadedPromise) {
      return this.voicesLoadedPromise;
    }
    this.voicesLoadedPromise = new Promise<SpeechSynthesisVoice[]>((resolve) => {
      let resolved = false;
      const onVoices = () => {
        if (resolved) return;
        resolved = true;
        window.speechSynthesis.removeEventListener("voiceschanged", onVoices);
        this.voicesLoadedPromise = null;
        resolve(window.speechSynthesis.getVoices());
      };
      window.speechSynthesis.addEventListener("voiceschanged", onVoices);
      setTimeout(() => {
        if (resolved) return;
        resolved = true;
        window.speechSynthesis.removeEventListener("voiceschanged", onVoices);
        this.voicesLoadedPromise = null;
        resolve(window.speechSynthesis.getVoices());
      }, 500);
    });
    return this.voicesLoadedPromise;
  }

  public async getOrSelectVoice(): Promise<SpeechSynthesisVoice | null> {
    if (this.cachedSelectedVoice) {
      return this.cachedSelectedVoice;
    }
    const voices = await this.ensureVoicesLoaded();
    if (voices.length === 0) {
      return null;
    }

    const savedVoice =
      this.voiceSettings.voiceURI === "auto"
        ? null
        : voices.find((v) => v.voiceURI === this.voiceSettings.voiceURI);

    // Strict list of female names to avoid for Zaki (NOC SME male persona)
    const isFemale = (name: string) =>
      /samantha|karen|victoria|moira|tessa|fiona|veena|ava|serena|allison|susan|kathy|vicki|kate|stephanie|olivia|amelia|charlotte|mia|harper|evelyn|abigail|emily|ella|elizabeth|camila|luna|sofia|avery|mila|aria|scarlett|penelope|layla|chloe|victoria|madison|eleanor|grace|nora|riley|zoey|hazel|violet|aurora|savannah|audrey|brooklyn|bella|claire|skylar|lucy|paisley|everly|anna|caroline|nova|genesis|emilia|kennedy|maya|willow|kinsley|naomi|aaliyah|elena|sarah|ariana|gabriella|alice|madelyn|cora|ruby|eva|serenity|autumn|adeline|hailey|gianna|valentina|isla|eliana|quinn|nevaeh|ivy|sadie|piper|lydia|alexa|josephine|emery|julia|delilah|arianna|vivian|kaylee|sophie|brielle|madeline|peyton|rylee|clara|hadley|melanie|mackenzie|reagan|adelyn|aubree|isabelle|ashlyn|annabelle|alivia|alana|mckenna|kylie|jocelyn|reese|eden|bailee|alyssa|norah|leilani|mariana|mary|miriam|ruth/i.test(
        name
      );

    const selectedVoice =
      savedVoice ||
      // 1. Soft tone young male voices (Evan, Nathan, Oliver, Aaron, Tom, Daniel, Arthur, Alex)
      voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          (v.name.includes("Evan") ||
            v.name.includes("Nathan") ||
            v.name.includes("Oliver") ||
            v.name.includes("Aaron") ||
            v.name.includes("Tom") ||
            v.name.includes("Daniel") ||
            v.name.includes("Arthur") ||
            v.name.includes("Alex") ||
            v.name.includes("David") ||
            v.name.includes("Guy") ||
            v.name.includes("Fred") ||
            /young|soft/i.test(v.name) ||
            /male/i.test(v.name)) &&
          !isFemale(v.name)
      ) ||
      // 2. English Natural / Neural / Google male voices
      voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          /natural|neural|google/i.test(v.name) &&
          !isFemale(v.name)
      ) ||
      // 3. English (UK) male fallback
      voices.find(
        (v) =>
          (v.lang.startsWith("en-GB") || v.lang.startsWith("en_GB")) &&
          !isFemale(v.name)
      ) ||
      // 4. Any English voice that is not female
      voices.find((v) => v.lang.startsWith("en") && !isFemale(v.name)) ||
      // 5. Any voice not female
      voices.find((v) => !isFemale(v.name)) ||
      voices[0];

    if (selectedVoice) {
      this.cachedSelectedVoice = selectedVoice;
    }
    return selectedVoice || null;
  }

  private loadVoiceSettings(): MarkVoiceSettings {
    if (typeof window === "undefined") return DEFAULT_VOICE_SETTINGS;
    try {
      const raw = localStorage.getItem(VOICE_SETTINGS_KEY);
      if (!raw) return DEFAULT_VOICE_SETTINGS;
      const parsed = JSON.parse(raw) as Partial<MarkVoiceSettings>;
      return {
        voiceURI: typeof parsed.voiceURI === "string" ? parsed.voiceURI : DEFAULT_VOICE_SETTINGS.voiceURI,
        tone: parsed.tone && parsed.tone in TONE_PROFILES ? parsed.tone : DEFAULT_VOICE_SETTINGS.tone,
        mode: parsed.mode === "browser" || parsed.mode === "backend" ? parsed.mode : DEFAULT_VOICE_SETTINGS.mode,
        playbackRate:
          typeof parsed.playbackRate === "number" && parsed.playbackRate >= 0.75 && parsed.playbackRate <= 1.4
            ? parsed.playbackRate
            : 1.0,
        autoCorrect: typeof parsed.autoCorrect === "boolean" ? parsed.autoCorrect : DEFAULT_VOICE_SETTINGS.autoCorrect,
      };
    } catch {
      return DEFAULT_VOICE_SETTINGS;
    }
  }

  public clearSpeechQueue(): void {
    this.speechQueue = [];
    this.currentSpeechItem = null;
    this.isProcessingSpeechQueue = false;
  }

  public stop() {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
    if (this.speechKeepAliveTimer) {
      clearInterval(this.speechKeepAliveTimer);
      this.speechKeepAliveTimer = null;
    }
    this.clearSpeechQueue();
    this.speechChunks = [];
    this.currentChunkIndex = 0;
    this.activeSpokenText = "";
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    activeUtterances.length = 0;
    this.isSpeaking = false;
    SpeechCompletionBarrier.setSpeaking(false);
    this.stopBackendOutput();
  }

  public startLiveMode(callbacks: LiveVoiceCallbacks, options?: { runId?: string }) {
    this.callbacks = callbacks;
    this.activeRunId = options?.runId || null;
    this.isLiveMode = true;
    this.isSubmitting = false;
    this.currentTranscript = "";
    this.prime();
    this.playChime(659.25, 0.15); // E5 chime
    if (this.voiceSettings.mode === "browser") {
      this.startListening();
      return;
    }
    this.startBackendLiveMode().catch((err) => {
      console.info("[MARK Voice] Backend live voice unavailable, gracefully switching to browser voice engine:", err?.message || err);
      this.stopBackendLiveMode();
      this.voiceSettings.mode = "browser";
      if (this.isLiveMode) {
        this.startListening();
      }
    });
  }

  public stopLiveMode() {
    this.isLiveMode = false;
    this.isSubmitting = false;
    this.currentTranscript = "";
    this.stopBackendLiveMode();
    this.stopListening();
    this.stop();
    this.playChime(440.0, 0.12);
    this.callbacks.onStateChange?.("idle");
  }

  private async startBackendLiveMode() {
    if (typeof window === "undefined") return;

    this.stopListening();
    this.stopBackendLiveMode();
    this.prime();

    const sessionSuffix =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID().slice(0, 8)
        : `${Date.now()}`;
    this.wsSessionId = `mark-live-${sessionSuffix}`;
    this.activeGeneration = 0;
    this.lastBargeInAt = 0;
    const query = this.activeRunId ? `?run_id=${encodeURIComponent(this.activeRunId)}` : "";
    const ws = new WebSocket(`${WS_BASE}/ws/jarvis-voice/${this.wsSessionId}${query}`);
    this.ws = ws;
    ws.binaryType = "arraybuffer";
    ws.onmessage = (event) => this.handleBackendMessage(event);
    ws.onclose = () => {
      this.isBackendLive = false;
      this.stopBackendMic();
      this.stopBackendOutput();
      if (this.isLiveMode && this.voiceSettings.mode !== "browser") {
        this.callbacks.onStateChange?.("idle");
      }
    };

    await new Promise<void>((resolve, reject) => {
      const timer = window.setTimeout(() => {
        reject(new Error("backend voice socket connection timed out"));
      }, 3000);

      ws.onopen = () => {
        window.clearTimeout(timer);
        this.isBackendLive = true;
        resolve();
      };

      ws.onerror = () => {
        window.clearTimeout(timer);
        reject(new Error("backend voice socket connection unavailable"));
      };
    });

    ws.onerror = (event) => {
      if (this.voiceSettings.mode !== "browser") {
        this.callbacks.onError?.(event);
      }
    };

    this.sendBackendJson({ type: "start" });
    await this.startBackendMic();
  }

  private stopBackendLiveMode() {
    this.isBackendLive = false;
    this.stopBackendMic();
    this.stopBackendOutput();
    if (this.ws) {
      try {
        if (this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ type: "stop" }));
        }
        this.ws.close();
      } catch {}
      this.ws = null;
    }
  }

  private async startBackendMic() {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("microphone capture is not supported in this browser");
    }

    this.micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    const AudioCtx = this.getAudioContextCtor();
    if (!AudioCtx) {
      throw new Error("Web Audio is not supported in this browser");
    }
    this.audioCtx = this.audioCtx || new AudioCtx();
    if (this.audioCtx.state === "suspended") {
      await this.audioCtx.resume();
    }

    this.micSource = this.audioCtx.createMediaStreamSource(this.micStream);
    this.micNode = this.audioCtx.createScriptProcessor(4096, 1, 1);
    this.micNode.onaudioprocess = (event) => {
      if (!this.isBackendLive || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
      const input = event.inputBuffer.getChannelData(0);
      const pcm = this.downsampleToPcm16(input, event.inputBuffer.sampleRate, 16000);
      if (this.isSpeaking || this.isPlayingBackendAudio) {
        const level = this.audioLevel(input);
        const now = Date.now();
        if (level > 0.018 && now - this.lastBargeInAt > 700) {
          this.lastBargeInAt = now;
          this.stopBackendOutput();
          this.sendBackendJson({ type: "interrupt", reason: "client_barge_in" });
          this.callbacks.onStateChange?.("listening");
        } else {
          return;
        }
      }
      if (pcm.byteLength > 0) {
        this.ws.send(pcm.buffer);
      }
    };

    // Mute gain node keeps processor active without outputting mic to speakers
    const muteNode = this.audioCtx.createGain();
    muteNode.gain.value = 0;
    this.micSource.connect(this.micNode);
    this.micNode.connect(muteNode);
    muteNode.connect(this.audioCtx.destination);
    this.isListening = true;
    this.callbacks.onStateChange?.("listening");
  }

  private stopBackendMic() {
    if (this.micNode) {
      try {
        this.micNode.disconnect();
      } catch {}
      this.micNode = null;
    }
    if (this.micSource) {
      try {
        this.micSource.disconnect();
      } catch {}
      this.micSource = null;
    }
    if (this.micStream) {
      this.micStream.getTracks().forEach((track) => track.stop());
      this.micStream = null;
    }
    this.isListening = false;
  }

  private handleBackendMessage(event: MessageEvent) {
    if (event.data instanceof ArrayBuffer) {
      this.enqueueBackendAudio(event.data, this.nextOutputSampleRate);
      return;
    }

    let message: Record<string, unknown>;
    try {
      message = JSON.parse(String(event.data));
    } catch {
      return;
    }

    if (message.type === "ready") {
      const output = message.output as { sample_rate?: number } | undefined;
      this.nextOutputSampleRate = output?.sample_rate || 24000;
      return;
    }
    const generation = message.generation_id;
    if (typeof generation === "number") {
      if (generation < this.activeGeneration) return;
      if (generation > this.activeGeneration) {
        this.stopBackendOutput();
        this.lastBackendAnswer = "";
        this.activeGeneration = generation;
      }
    }
    if (message.type === "interrupted") {
      this.stopBackendOutput();
      this.lastBackendAnswer = "";
      this.callbacks.onStateChange?.("listening");
      return;
    }
    if (message.type === "state") {
      const state = message.state;
      // Server synthesis can finish while scheduled audio is still playing.
      if ((state === "idle" || state === "listening") && this.activeSources.length) return;
      if (state === "idle" || state === "listening" || state === "processing" || state === "speaking") {
        this.callbacks.onStateChange?.(state);
      }
      return;
    }
    if (message.type === "transcript_partial" || message.type === "transcript") {
      const text = normalizeTelecomTranscript(String(message.text || ""));
      if (text) {
        this.currentTranscript = text;
        this.callbacks.onTranscript?.(text, message.type === "transcript");
      }
      return;
    }
    if (message.type === "response") {
      const answer = String(message.answer || "");
      const spokenAnswer = String(message.spoken_answer || answer);
      this.lastBackendAnswer = spokenAnswer;
      this.callbacks.onResponse?.(answer, spokenAnswer, {
        narrative: message.narrative as MarkPresentation["narrative"],
        visual_explanation: message.visual_explanation as MarkPresentation["visual_explanation"],
      });
      return;
    }
    if (message.type === "audio") {
      this.nextOutputSampleRate = typeof message.sample_rate === "number" ? message.sample_rate : 24000;
      return;
    }
    if (message.type === "error") {
      this.stopBackendOutput();
      this.callbacks.onStateChange?.("idle");
      if (message.code === "stt_error" && this.isLiveMode) {
        this.stopBackendLiveMode();
        this.startListening();
        return;
      }
      if (message.code === "tts_error" && this.lastBackendAnswer) {
        const fallbackAnswer = this.lastBackendAnswer;
        this.lastBackendAnswer = "";
        this.speak(fallbackAnswer, {
          onStart: () => this.callbacks.onStateChange?.("speaking"),
          onEnd: () => {
            if (this.isLiveMode) {
              this.callbacks.onStateChange?.("listening");
            } else {
              this.callbacks.onStateChange?.("idle");
            }
          },
        });
        return;
      }
      this.callbacks.onError?.(message);
    }
  }

  private sendBackendJson(payload: Record<string, unknown>) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  private downsampleToPcm16(input: Float32Array, inputSampleRate: number, outputSampleRate: number): Int16Array {
    if (inputSampleRate === outputSampleRate) {
      const out = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        const s = Math.max(-1, Math.min(1, input[i]));
        out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      return out;
    }

    const ratio = inputSampleRate / outputSampleRate;
    const newLength = Math.max(0, Math.floor(input.length / ratio));
    const out = new Int16Array(newLength);

    for (let i = 0; i < newLength; i++) {
      const start = Math.floor(i * ratio);
      const end = Math.min(Math.floor((i + 1) * ratio), input.length);
      let sum = 0;
      let count = 0;
      for (let j = start; j < end; j++) {
        sum += input[j];
        count += 1;
      }
      const sample = count > 0 ? sum / count : input[start] || 0;
      const s = Math.max(-1, Math.min(1, sample));
      out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return out;
  }

  private audioLevel(input: Float32Array): number {
    if (!input.length) return 0;
    let sum = 0;
    for (let i = 0; i < input.length; i += 1) {
      sum += input[i] * input[i];
    }
    return Math.sqrt(sum / input.length);
  }

  private enqueueBackendAudio(data: ArrayBuffer, sampleRate: number) {
    if (this.isMuted || typeof window === "undefined") return;
    const AudioCtx = this.getAudioContextCtor();
    if (!AudioCtx) return;
    this.playbackCtx = this.playbackCtx || this.audioCtx || new AudioCtx();
    if (this.playbackCtx.state === "suspended") {
      this.playbackCtx.resume().catch(() => {});
    }
    const pcm = new Int16Array(data);
    if (pcm.length === 0) return;

    const buffer = this.playbackCtx.createBuffer(1, pcm.length, sampleRate || 24000);
    const channel = buffer.getChannelData(0);
    for (let i = 0; i < pcm.length; i++) {
      channel[i] = pcm[i] / 32768;
    }

    const source = this.playbackCtx.createBufferSource();
    source.buffer = buffer;
    source.playbackRate.value = this.voiceSettings.playbackRate;
    source.connect(this.playbackCtx.destination);
    this.activeSources.push(source);

    const currentTime = this.playbackCtx.currentTime;
    const startTime = Math.max(currentTime, this.nextPlayTime);
    source.start(startTime);
    this.nextPlayTime = startTime + buffer.duration;
    this.isPlayingBackendAudio = true;
    this.isSpeaking = true;
    this.callbacks.onStateChange?.("speaking");

    source.onended = () => {
      const idx = this.activeSources.indexOf(source);
      if (idx !== -1) {
        this.activeSources.splice(idx, 1);
      }
      if (
        this.activeSources.length === 0 &&
        this.playbackCtx &&
        this.playbackCtx.currentTime >= this.nextPlayTime - 0.05
      ) {
        this.speakingEndTime = Date.now();
        this.isPlayingBackendAudio = false;
        this.isSpeaking = false;
        this.callbacks.onStateChange?.("listening");
      }
    };
  }

  private stopBackendOutput() {
    for (const source of this.activeSources) {
      try {
        source.onended = null;
        source.stop();
        source.disconnect();
      } catch {}
    }
    this.activeSources = [];
    this.nextPlayTime = 0;
    this.playbackQueue = [];
    this.speakingEndTime = Date.now();
    this.isPlayingBackendAudio = false;
    this.isSpeaking = false;
  }

  public startListening() {
    if (typeof window === "undefined") return;

    const w = window as BrowserWindow;
    const SpeechRecognition = w.SpeechRecognition || w.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("[MARK Voice] Web SpeechRecognition is not supported in this browser.");
      return;
    }

    this.currentTranscript = "";
    this.lastTranscriptAt = 0;
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }

    if (this.recognition) {
      const prevRec = this.recognition;
      this.recognition = null;
      prevRec.onresult = null;
      prevRec.onend = null;
      prevRec.onerror = null;
      try {
        prevRec.abort();
      } catch {}
    }

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onstart = () => {
      if (this.recognition !== rec) return;
      this.isListening = true;
      this.callbacks.onStateChange?.("listening");
    };

    rec.onresult = (event: BrowserSpeechRecognitionEvent) => {
      // Ignore results if already submitting, not listening, or replaced by another instance
      if (this.isSubmitting || !this.isListening || this.recognition !== rec) {
        return;
      }

      const now = Date.now();
      // Grace period right after Mark finishes speaking: discard acoustic room reverberation/speaker tail
      if (now < this.speechEndGraceUntil) {
        return;
      }

      let fullFinal = "";
      let fullInterim = "";

      for (let i = 0; i < event.results.length; ++i) {
        const item = event.results[i];
        if (!item || !item[0]) continue;
        const transcript = item[0].transcript;
        if (item.isFinal) {
          fullFinal += transcript + " ";
        } else {
          fullInterim += transcript;
        }
      }

      const rawText = `${fullFinal} ${fullInterim}`.replace(/\s+/g, " ").trim();
      const normalizedText = this.voiceSettings.autoCorrect
        ? normalizeTelecomTranscript(rawText)
        : rawText;
      if (!normalizedText) return;

      // Handle user interruption / barge-in while Mark is speaking
      if (this.isSpeaking) {
        const lowerNorm = normalizedText.toLowerCase();
        // Discard speaker acoustic feedback: if recognized speech matches Mark's current response
        if (
          this.activeSpokenText &&
          (this.activeSpokenText.includes(lowerNorm) ||
            lowerNorm.split(/\s+/).every((w) => this.activeSpokenText.includes(w)))
        ) {
          // Acoustic feedback from laptop speaker into microphone; ignore so Mark isn't interrupted by himself
          return;
        }

        // Genuine user interruption!
        console.log("[MARK Voice] User barge-in detected, interrupting speech:", normalizedText);
        this.stop();
        this.browserBargeInGraceUntil = now + 2500;
        this.callbacks.onStateChange?.("listening");
      }

      this.currentTranscript = normalizedText;
      this.lastTranscriptAt = now;
      const hasFinal = Boolean(fullFinal.trim());
      this.callbacks.onTranscript?.(normalizedText, hasFinal);

      if (this.silenceTimer) {
        clearTimeout(this.silenceTimer);
        this.silenceTimer = null;
      }

      if (this.isLiveMode && !this.isSubmitting) {
        const wordCount = normalizedText.split(/\s+/).filter(Boolean).length;
        const isIncomplete = isLikelyIncompleteUtterance(normalizedText);

        // Generous, natural pauses:
        // Ensure short speech pauses or inter-word breaks NEVER cut off the sentence!
        let delay: number;
        if (isIncomplete) {
          // Incomplete clause or question opener (e.g. "Can you", "What is", dangling preposition):
          // Allow 3.5s - 4.5s so thinking pauses never cut off the utterance.
          delay = wordCount < 3 ? 4500 : 3500;
        } else {
          // Complete sentence: allow generous 2600ms of absolute silence before finalizing.
          delay = hasFinal ? 2600 : 3000;
        }

        if (now < this.browserBargeInGraceUntil) {
          delay = Math.max(delay, 2800);
        }

        const transcriptAtSchedule = this.lastTranscriptAt;
        this.silenceTimer = setTimeout(() => {
          this.handleSilenceTrigger(transcriptAtSchedule);
        }, delay);
      }
    };

    rec.onerror = (e: BrowserSpeechRecognitionError) => {
      if (this.recognition !== rec) return;
      if (e.error !== "no-speech" && e.error !== "aborted") {
        console.warn("[MARK Voice] Speech recognition error:", e.error);
        this.callbacks.onError?.(e);
      }
    };

    rec.onend = () => {
      // Discard end events from superseded recognition sessions
      if (this.recognition !== rec) return;

      this.isListening = false;
      if (this.isLiveMode && !this.isSpeaking && !this.isSubmitting) {
        try {
          rec.start();
        } catch {}
      } else if (!this.isSpeaking && !this.isSubmitting) {
        this.callbacks.onStateChange?.("idle");
      }
    };

    this.recognition = rec;

    try {
      rec.start();
    } catch (e) {
      console.warn("[MARK Voice] Could not start recognition:", e);
    }
  }

  public stopListening() {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
    if (this.recognition) {
      const rec = this.recognition;
      this.recognition = null;
      rec.onresult = null;
      rec.onend = null;
      rec.onerror = null;
      try {
        rec.stop();
      } catch {}
    }
    this.isListening = false;
  }

  private async handleSilenceTrigger(transcriptAtSchedule?: number) {
    if (this.isSubmitting) return;
    if (transcriptAtSchedule && transcriptAtSchedule !== this.lastTranscriptAt) return;

    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }

    const textToSubmit = this.currentTranscript.trim();
    if (!textToSubmit) return;

    // Safety guard: Never submit incomplete fragments (e.g. "Can you", "What is", "Tell me")
    // If the user pauses after just 1-2 words, do not submit! Wait for user to finish speaking.
    if (isLikelyIncompleteUtterance(textToSubmit) && textToSubmit.split(/\s+/).length < 3) {
      console.log("[MARK Voice] Incomplete phrase detected, holding submission:", textToSubmit);
      return;
    }

    this.isSubmitting = true;
    this.currentTranscript = "";
    this.stopListening();
    this.callbacks.onStateChange?.("processing");
    this.playChime(880.0, 0.08); // High acknowledge tone

    try {
      const reply = await this.callbacks.onMessageSubmit?.(textToSubmit);
      if (typeof reply === "string" && reply) {
        this.speak(reply, {
          onStart: () => {
            this.isSubmitting = false;
            this.callbacks.onStateChange?.("speaking");
            if (this.isLiveMode && !this.isBackendLive) {
              this.startListening();
            }
          },
          onEnd: () => {
            this.isSubmitting = false;
            this.currentTranscript = "";
            this.lastTranscriptAt = 0;
            if (this.silenceTimer) {
              clearTimeout(this.silenceTimer);
              this.silenceTimer = null;
            }
            if (this.isLiveMode) {
              this.startListening();
            } else {
              this.callbacks.onStateChange?.("idle");
            }
          },
          onError: () => {
            this.isSubmitting = false;
            this.currentTranscript = "";
            this.lastTranscriptAt = 0;
            if (this.silenceTimer) {
              clearTimeout(this.silenceTimer);
              this.silenceTimer = null;
            }
            if (this.isLiveMode) {
              this.startListening();
            } else {
              this.callbacks.onStateChange?.("idle");
            }
          },
        });
      } else {
        this.isSubmitting = false;
        this.currentTranscript = "";
        this.lastTranscriptAt = 0;
        if (this.isLiveMode) {
          this.startListening();
        } else {
          this.callbacks.onStateChange?.("idle");
        }
      }
    } catch {
      this.isSubmitting = false;
      this.currentTranscript = "";
      this.lastTranscriptAt = 0;
      if (this.isLiveMode) {
        this.startListening();
      } else {
        this.callbacks.onStateChange?.("idle");
      }
    }
  }

  /**
   * Speak text aloud using a non-dropping FIFO speech queue and sequential sentence chunking.
   * Guarantees zero voice drops when simulation stages or messages advance in rapid succession.
   */
  public speak(
    text: string,
    options?: {
      onStart?: () => void;
      onEnd?: () => void;
      onError?: (err: unknown) => void;
      priority?: "normal" | "interrupt";
    }
  ): void {
    if (this.isMuted || !text || !text.trim() || typeof window === "undefined" || !("speechSynthesis" in window)) {
      options?.onEnd?.();
      return;
    }

    const cleanText = prepareSpeechText(text);
    if (!cleanText.trim()) {
      options?.onEnd?.();
      return;
    }

    // Explicit user interruption (e.g. barge-in or manual Stop): clear queue & cancel active speech
    if (options?.priority === "interrupt") {
      this.clearSpeechQueue();
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      activeUtterances.length = 0;
      this.isSpeaking = false;
    }

    // Deduplication check: if identical text is currently playing or queued, avoid stuttering duplicates
    if (
      (this.currentSpeechItem && this.currentSpeechItem.cleanText === cleanText) ||
      this.speechQueue.some((item) => item.cleanText === cleanText)
    ) {
      console.log(`[MARK Voice] Deduplicated identical speech request (${cleanText.slice(0, 45)}...)`);
      return;
    }

    // Chunk strictly by sentence boundary for distinct human cadence
    const rawMatches = cleanText.match(/[^.!?\n]+[.!?\n]+|[^.!?\n]+$/g) || [cleanText];
    const chunks: string[] = [];
    for (const raw of rawMatches) {
      const s = raw.trim();
      if (s) chunks.push(s);
    }
    if (!chunks.length) chunks.push(cleanText);

    const queueItem: SpeechQueueItem = {
      id: `speech-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      text,
      cleanText,
      chunks,
      options,
    };

    // If already speaking or processing queue: queue sequentially without cutting off active speech!
    if (this.isSpeaking || this.isProcessingSpeechQueue) {
      console.log(`[MARK Voice Queueing: ${chunks.length} sentence(s) behind active narration, queue size: ${this.speechQueue.length + 1}]`);
      this.speechQueue.push(queueItem);
      SpeechCompletionBarrier.setSpeaking(true);
      return;
    }

    // Start processing queue
    this.speechQueue.push(queueItem);
    this.processSpeechQueue();
  }

  private processSpeechQueue(): void {
    if (this.speechQueue.length === 0) {
      this.currentSpeechItem = null;
      this.isProcessingSpeechQueue = false;
      this.isSpeaking = false;
      SpeechCompletionBarrier.setSpeaking(false);
      this.activeSpokenText = "";
      this.speechEndGraceUntil = Date.now() + 450;
      if (this.speechKeepAliveTimer) {
        clearInterval(this.speechKeepAliveTimer);
        this.speechKeepAliveTimer = null;
      }
      activeUtterances.length = 0;
      return;
    }

    const item = this.speechQueue.shift()!;
    this.currentSpeechItem = item;
    this.isProcessingSpeechQueue = true;
    this.isSpeaking = true;
    SpeechCompletionBarrier.setSpeaking(true);

    this.prime();
    item.options?.onStart?.();

    this.activeSpokenText = item.cleanText.toLowerCase();
    this.lastSpokenText = item.text;
    this.isPaused = false;
    this.speechChunks = item.chunks;
    this.currentChunkIndex = 0;

    console.log(`[MARK Voice Speaking item: ${item.chunks.length} sentences with natural pauses, ${item.cleanText.length} chars]`);

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.resume();
    }

    // Keep-alive timer prevents Chrome from freezing during long responses
    if (this.speechKeepAliveTimer) {
      clearInterval(this.speechKeepAliveTimer);
    }
    this.speechKeepAliveTimer = setInterval(() => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        if (window.speechSynthesis.speaking && !this.isPaused) {
          window.speechSynthesis.pause();
          window.speechSynthesis.resume();
        } else if (!window.speechSynthesis.speaking && !this.isSpeaking) {
          if (this.speechKeepAliveTimer) {
            clearInterval(this.speechKeepAliveTimer);
            this.speechKeepAliveTimer = null;
          }
        }
      }
    }, 8000);

    const playNextChunk = async () => {
      if (!this.isSpeaking || this.isPaused) return;

      if (this.currentChunkIndex >= this.speechChunks.length) {
        // Complete current speech item finished
        item.options?.onEnd?.();
        // Schedule next queued speech item with natural inter-message breathing pause
        setTimeout(() => {
          this.processSpeechQueue();
        }, 320);
        return;
      }

      const chunk = this.speechChunks[this.currentChunkIndex];
      try {
        const utterance = new SpeechSynthesisUtterance(chunk);
        const tone = TONE_PROFILES[this.voiceSettings.tone] ?? TONE_PROFILES.executive;
        // Subtle prosodic modulation: questions slightly higher pitch, critical statements slightly slower
        const isQuestion = chunk.endsWith("?");
        const isCritical = /\b(critical|root cause|breach|outage|failure|down)\b/i.test(chunk);
        const pitchMod = isQuestion ? 1.04 : isCritical ? 0.96 : 1.0;
        const rateMod = isCritical ? 0.94 : 1.0;

        utterance.rate = Math.max(0.5, Math.min(2, tone.rate * this.voiceSettings.playbackRate * rateMod));
        utterance.pitch = Math.max(0.5, Math.min(2, tone.pitch * pitchMod));
        utterance.volume = tone.volume;
        utterance.lang = "en-US";

        const selectedVoice = await this.getOrSelectVoice();
        if (selectedVoice) {
          utterance.voice = selectedVoice;
        }

        activeUtterances.push(utterance);

        let chunkCompleted = false;
        let chunkTimeout: ReturnType<typeof setTimeout> | null = null;

        const completeChunk = () => {
          if (chunkCompleted) return;
          chunkCompleted = true;
          if (chunkTimeout) {
            clearTimeout(chunkTimeout);
            chunkTimeout = null;
          }
          const idx = activeUtterances.indexOf(utterance);
          if (idx !== -1) activeUtterances.splice(idx, 1);
          this.currentChunkIndex++;
          // Human-like inter-sentence pause: 180ms for clauses, 400ms for paragraphs, 250ms for normal sentences
          const isParagraphEnd = chunk.includes("\n") || this.currentChunkIndex % 3 === 0;
          const isClauseBreak = chunk.endsWith(",");
          const pauseMs = isClauseBreak ? 180 : isParagraphEnd ? 400 : isQuestion ? 320 : 250;
          setTimeout(playNextChunk, pauseMs);
        };

        const wordCount = chunk.split(/\s+/).filter(Boolean).length;
        const maxSpeechMs = Math.max(2500, Math.ceil((wordCount / 2.0) * 1000) + 1200);
        chunkTimeout = setTimeout(() => {
          console.warn(`[MARK Voice] Chunk timeout fallback fired after ${maxSpeechMs}ms for: "${chunk.slice(0, 30)}..."`);
          completeChunk();
        }, maxSpeechMs);

        utterance.onend = () => {
          completeChunk();
        };

        utterance.onerror = (e) => {
          if (e.error === "interrupted" || e.error === "canceled") {
            if (!this.isProcessingSpeechQueue) {
              if (chunkTimeout) clearTimeout(chunkTimeout);
              return;
            }
          }
          console.warn("[MARK Voice] Speech chunk error:", e);
          completeChunk();
        };

        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.error("[MARK Voice] Speak chunk failed:", err);
        this.currentChunkIndex++;
        playNextChunk();
      }
    };

    setTimeout(playNextChunk, 40);
  }

  public testVoice() {
    this.setMuted(false);
    this.playChime(587.33, 0.15);
    this.speak("MARK online. Real-time incident operations voice active.");
  }
}

/**
 * Stage-Synchronized Speech Completion Barrier (Zero Voice Drop)
 * Holds simulation stage progression until Zaki finishes narrating the active stage.
 */
export class SpeechCompletionBarrier {
  private static listeners: Array<() => void> = [];
  private static _isSpeaking: boolean = false;

  public static get isSpeaking(): boolean {
    return this._isSpeaking;
  }

  public static setSpeaking(speaking: boolean): void {
    this._isSpeaking = speaking;
    if (!speaking) {
      const callbacks = [...this.listeners];
      this.listeners = [];
      callbacks.forEach((cb) => {
        try {
          cb();
        } catch (e) {
          console.error("[SpeechCompletionBarrier] Callback error:", e);
        }
      });
    }
  }

  public static async awaitSpeechCompletion(): Promise<void> {
    if (!this._isSpeaking) {
      return Promise.resolve();
    }
    return new Promise<void>((resolve) => {
      this.listeners.push(resolve);
    });
  }

  public static onSpeechCompleted(callback: () => void): void {
    if (!this._isSpeaking) {
      callback();
    } else {
      this.listeners.push(callback);
    }
  }
}

export const speechCompletionBarrier = SpeechCompletionBarrier;
export const awaitSpeechCompletion = (timeoutMs: number = 6000): Promise<void> => {
  return Promise.race([
    SpeechCompletionBarrier.awaitSpeechCompletion(),
    new Promise<void>((resolve) => setTimeout(resolve, timeoutMs)),
  ]);
};

export const jarvisVoice = new JarvisVoiceAssistant();

