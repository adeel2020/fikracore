"use client";

import React, { createContext, useContext, useState, useEffect, useMemo } from "react";
import type { MarkVisualState } from "@/lib/mark-capability-graph";

export interface MarkHudSettings {
  // Typography
  fontPreset: MarkFontPreset;
  customFontFamily: string;
  fontScale: number; // 0.85 to 1.25, default: 1.0

  // Dust Particles
  dustRadius: number; // 30 to 220px, default: 115
  dustSpeed: number; // 0.2 to 3.0, default: 1.0
  dustCount: number; // 200 to 1200, default: 780
  dustGlowIntensity: number; // 0.2 to 2.0, default: 1.0
  dustCoreGlow: number; // 0.0 to 1.5, default: 1.0

  // Plasma Waves (Background Shader)
  showWaves: boolean; // default: true
  waveOpacity: number; // 0.05 to 0.80, default: 0.30
  waveSpeed: number; // 0.2 to 3.0, default: 1.0

  // Core Orb & Rings
  orbScale: number; // 0.6 to 1.4, default: 1.0
  orbRotationSpeed: number; // 0.2 to 3.0, default: 1.0
  showSoundWaves: boolean; // default: true
  coreGlow: number; // 0.2 to 2.0, default: 1.0

  // Reasoning Web & Labels
  showEngineLabels: boolean; // default: true
  webLineOpacity: number; // 0.1 to 1.0, default: 0.45

  // State Simulator
  stateOverride: "auto" | MarkVisualState;
}

export type MarkFontPreset =
  | "system"
  | "mono"
  | "aptos"
  | "calibri"
  | "cambria"
  | "times"
  | "arial"
  | "segoe"
  | "georgia"
  | "verdana"
  | "tahoma"
  | "consolas"
  | "orbitron"
  | "rajdhani"
  | "inter"
  | "custom";

export const MARK_FONT_OPTIONS: Record<MarkFontPreset, { label: string; family: string }> = {
  system: {
    label: "System",
    family: 'var(--font-geist-sans), Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  mono: {
    label: "Mono HUD",
    family: 'var(--font-geist-mono), "SFMono-Regular", Consolas, "Liberation Mono", ui-monospace, monospace',
  },
  aptos: {
    label: "Aptos",
    family: 'Aptos, "Aptos Display", Calibri, "Segoe UI", Arial, sans-serif',
  },
  calibri: {
    label: "Calibri",
    family: 'Calibri, "Segoe UI", Arial, sans-serif',
  },
  cambria: {
    label: "Cambria",
    family: 'Cambria, Georgia, "Times New Roman", serif',
  },
  times: {
    label: "Times New Roman",
    family: '"Times New Roman", Times, Georgia, serif',
  },
  arial: {
    label: "Arial",
    family: 'Arial, Helvetica, "Segoe UI", sans-serif',
  },
  segoe: {
    label: "Segoe UI",
    family: '"Segoe UI", Aptos, Calibri, Arial, sans-serif',
  },
  georgia: {
    label: "Georgia",
    family: 'Georgia, Cambria, "Times New Roman", serif',
  },
  verdana: {
    label: "Verdana",
    family: 'Verdana, Geneva, Arial, sans-serif',
  },
  tahoma: {
    label: "Tahoma",
    family: 'Tahoma, Verdana, "Segoe UI", sans-serif',
  },
  consolas: {
    label: "Consolas",
    family: 'Consolas, "Cascadia Mono", "Courier New", ui-monospace, monospace',
  },
  orbitron: {
    label: "Orbitron",
    family: '"Orbitron", "Rajdhani", var(--font-geist-mono), ui-monospace, monospace',
  },
  rajdhani: {
    label: "Rajdhani",
    family: '"Rajdhani", "Inter", var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif',
  },
  inter: {
    label: "Inter",
    family: '"Inter", var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif',
  },
  custom: {
    label: "Custom",
    family: "",
  },
};

export function resolveMarkFontFamily(settings: Pick<MarkHudSettings, "fontPreset" | "customFontFamily">): string {
  if (settings.fontPreset === "custom" && settings.customFontFamily.trim()) {
    return settings.customFontFamily.trim();
  }
  return MARK_FONT_OPTIONS[settings.fontPreset]?.family || MARK_FONT_OPTIONS.system.family;
}

export const DEFAULT_HUD_SETTINGS: MarkHudSettings = {
  fontPreset: "mono",
  customFontFamily: "",
  fontScale: 1.0,

  dustRadius: 115,
  dustSpeed: 1.0,
  dustCount: 780,
  dustGlowIntensity: 1.0,
  dustCoreGlow: 1.0,

  showWaves: true,
  waveOpacity: 0.30,
  waveSpeed: 1.0,

  orbScale: 1.0,
  orbRotationSpeed: 1.0,
  showSoundWaves: true,
  coreGlow: 1.0,

  showEngineLabels: true,
  webLineOpacity: 0.45,

  stateOverride: "auto",
};

export const HUD_PRESETS: Record<string, { label: string; desc: string; settings: Partial<MarkHudSettings> }> = {
  balanced: {
    label: "Balanced Cyber",
    desc: "Default balanced parameters for optimal sci-fi presence",
    settings: { ...DEFAULT_HUD_SETTINGS },
  },
  deepFocus: {
    label: "Deep Focus",
    desc: "Subtle waves, tighter dust nucleus, zero clutter",
    settings: {
      dustRadius: 75,
      dustSpeed: 0.7,
      waveOpacity: 0.16,
      waveSpeed: 0.6,
      coreGlow: 0.8,
    },
  },
  supernova: {
    label: "Supernova Flare",
    desc: "High bloom, expansive stardust, intense wave flux",
    settings: {
      dustRadius: 160,
      dustSpeed: 1.5,
      dustGlowIntensity: 1.6,
      dustCoreGlow: 1.4,
      waveOpacity: 0.55,
      waveSpeed: 1.8,
      coreGlow: 1.6,
    },
  },
  eco: {
    label: "Eco Performance",
    desc: "Minimalist load for low GPU usage and battery saving",
    settings: {
      dustRadius: 90,
      dustSpeed: 0.8,
      dustCount: 350,
      showWaves: false,
      showSoundWaves: false,
    },
  },
};

interface MarkHudContextValue {
  settings: MarkHudSettings;
  updateSetting: <K extends keyof MarkHudSettings>(key: K, value: MarkHudSettings[K]) => void;
  resetDefaults: () => void;
  applyPreset: (presetKey: string) => void;
}

const MarkHudContext = createContext<MarkHudContextValue | null>(null);

const STORAGE_KEY = "mark_hud_settings_v1";

export function MarkHudProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<MarkHudSettings>(DEFAULT_HUD_SETTINGS);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        setSettings((prev) => ({ ...prev, ...JSON.parse(saved) }));
      }
    } catch {
      // Ignore storage errors
    }
  }, []);

  const updateSetting = <K extends keyof MarkHudSettings>(key: K, value: MarkHudSettings[K]) => {
    setSettings((prev) => {
      const next = { ...prev, [key]: value };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const resetDefaults = () => {
    setSettings(DEFAULT_HUD_SETTINGS);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {}
  };

  const applyPreset = (presetKey: string) => {
    const preset = HUD_PRESETS[presetKey];
    if (!preset) return;
    setSettings((prev) => {
      const next = { ...prev, ...preset.settings };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const value = useMemo(
    () => ({ settings, updateSetting, resetDefaults, applyPreset }),
    [settings]
  );

  return <MarkHudContext.Provider value={value}>{children}</MarkHudContext.Provider>;
}

export function useMarkHud() {
  const ctx = useContext(MarkHudContext);
  if (!ctx) {
    return {
      settings: DEFAULT_HUD_SETTINGS,
      updateSetting: () => {},
      resetDefaults: () => {},
      applyPreset: () => {},
    };
  }
  return ctx;
}
