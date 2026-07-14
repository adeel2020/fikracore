// CDN URL import declaration
declare module "https://cdn.jsdelivr.net/gh/met4citizen/TalkingHead@1.7/modules/talkinghead.mjs" {
  export { TalkingHead } from "@met4citizen/talkinghead";
}

declare module "@met4citizen/talkinghead" {
  export class TalkingHead {
    constructor(
      node: HTMLElement,
      options?: {
        ttsEndpoint?: string | null;
        ttsApikey?: string | null;
        jwtGet?: (() => string) | null;
        ttsLang?: string;
        ttsVoice?: string;
        ttsRate?: number;
        ttsPitch?: number;
        ttsVolume?: number;
        ttsTrimStart?: number;
        ttsTrimEnd?: number;
        mixerGainSpeech?: number | null;
        mixerGainBackground?: number | null;
        lipsyncModules?: string[];
        lipsyncLang?: string;
        pcmSampleRate?: number;
        audioCtx?: AudioContext | null;
        modelRoot?: string;
        modelPixelRatio?: number;
        modelFPS?: number;
        modelMovementFactor?: number;
        dracoEnabled?: boolean;
        dracoDecoderPath?: string;
        cameraView?: "full" | "mid" | "upper" | "head";
        cameraDistance?: number;
        cameraX?: number;
        cameraY?: number;
        cameraRotateX?: number;
        cameraRotateY?: number;
        cameraRotateEnable?: boolean;
        cameraPanEnable?: boolean;
        cameraZoomEnable?: boolean;
        lightAmbientColor?: number | string;
        lightAmbientIntensity?: number;
        lightDirectColor?: number | string;
        lightDirectIntensity?: number;
        lightDirectPhi?: number;
        lightDirectTheta?: number;
        lightSpotColor?: number | string;
        lightSpotIntensity?: number;
        lightSpotPhi?: number;
        lightSpotTheta?: number;
        lightSpotDispersion?: number;
        avatarMood?: string;
        avatarMute?: boolean;
        avatarIdleEyeContact?: number;
        avatarIdleHeadMove?: number;
        avatarSpeakingEyeContact?: number;
        avatarSpeakingHeadMove?: number;
        avatarIgnoreCamera?: boolean;
        avatarOnly?: boolean;
        avatarOnlyCamera?: any;
        avatarOnlyScene?: any;
        update?: ((delta: number) => void) | null;
        statsNode?: HTMLElement | null;
        statsStyle?: string | null;
      }
    );

    showAvatar(
      avatar: {
        url: string;
        body?: "M" | "F";
        avatarMood?: string;
        lipsyncLang?: string;
        ttsLang?: string;
        ttsVoice?: string;
        ttsRate?: number;
        ttsPitch?: number;
        ttsVolume?: number;
        baseline?: Record<string, number>;
        retarget?: Record<string, any>;
        modelDynamicBones?: any[];
        avatarIdleEyeContact?: number;
        avatarSpeakingEyeContact?: number;
        avatarSpeakingHeadMove?: number;
        avatarIgnoreCamera?: boolean;
      },
      onprogress?: ((url: string, event: ProgressEvent) => void) | null
    ): Promise<void>;

    setView(
      view: "full" | "mid" | "upper" | "head",
      opt?: {
        cameraDistance?: number;
        cameraX?: number;
        cameraY?: number;
        cameraRotateX?: number;
        cameraRotateY?: number;
      }
    ): void;

    setLighting(opt: {
      lightAmbientColor?: number | string;
      lightAmbientIntensity?: number;
      lightDirectColor?: number | string;
      lightDirectIntensity?: number;
      lightDirectPhi?: number;
      lightDirectTheta?: number;
      lightSpotColor?: number | string;
      lightSpotIntensity?: number;
      lightSpotPhi?: number;
      lightSpotTheta?: number;
      lightSpotDispersion?: number;
    }): void;

    speakText(
      text: string,
      opt?: Record<string, any>,
      onsubtitles?: ((node: HTMLElement) => void) | null,
      excludes?: [number, number][]
    ): void;

    speakAudio(
      audio: {
        audio: AudioBuffer | ArrayBuffer[];
        words: string[];
        wtimes: number[];
        wdurations: number[];
        visemes?: string[];
        vtimes?: number[];
        vdurations?: number[];
        markers?: string[];
        mtimes?: number[];
        anim?: Record<string, any>;
      },
      opt?: Record<string, any>,
      onsubtitles?: ((node: HTMLElement) => void) | null
    ): void;

    speakEmoji(e: string): void;
    speakBreak(t: number): void;
    speakMarker(onmarker: () => void): void;

    lookAt(x: number, y: number, t: number): void;
    lookAhead(t: number): void;
    lookAtCamera(t: number): void;
    makeEyeContact(t: number): void;

    setMood(mood: string): void;

    playBackgroundAudio(url: string): void;
    stopBackgroundAudio(): void;

    setMixerGain(
      speech: number | null,
      background?: number | null,
      fadeSecs?: number
    ): void;

    playAnimation(
      url: string,
      onprogress?: ((url: string, event: ProgressEvent) => void) | null,
      dur?: number,
      ndx?: number,
      scale?: number
    ): void;

    stopAnimation(): void;
    stopSpeaking(): void;
  }
}
