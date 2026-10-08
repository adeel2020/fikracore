"use client";

import React, { useState } from "react";
import {
  X,
  RotateCcw,
  SlidersHorizontal,
  Sparkles,
  Waves,
  Disc3,
  Network,
  Activity,
  Check,
  Type,
} from "lucide-react";
import { useMarkHud, HUD_PRESETS, MARK_FONT_OPTIONS, type MarkFontPreset } from "@/lib/mark-hud-context";

interface MarkControlPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = "style" | "dust" | "waves" | "orb" | "web" | "state";

export function MarkControlPanel({ isOpen, onClose }: MarkControlPanelProps) {
  const { settings, updateSetting, resetDefaults, applyPreset } = useMarkHud();
  const [activeTab, setActiveTab] = useState<TabType>("style");
  const [activePreset, setActivePreset] = useState<string>("balanced");

  if (!isOpen) return null;

  const handleSelectPreset = (key: string) => {
    setActivePreset(key);
    applyPreset(key);
  };

  const handleReset = () => {
    resetDefaults();
    setActivePreset("balanced");
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-6 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl border border-cyan-500/40 bg-[#050B14]/98 text-slate-100 shadow-[0_20px_70px_rgba(0,0,0,0.9),0_0_40px_rgba(0,229,255,0.2)] overflow-hidden">
        {/* Top Glow Bar */}
        <div className="h-1 w-full bg-gradient-to-r from-transparent via-[#00e5ff] to-transparent shadow-[0_0_12px_#00e5ff]" />

        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-cyan-500/20 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/15 border border-cyan-400/40 flex items-center justify-center text-[#00e5ff] shadow-[0_0_15px_rgba(0,229,255,0.3)]">
              <SlidersHorizontal className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-mono text-sm sm:text-base font-bold uppercase tracking-wider text-white">
                  HUD CONTROL PANEL
                </h2>
                <span className="px-1.5 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/40 font-mono text-[9px] font-bold text-[#00e5ff] tracking-wider">
                  ZAKI v2.4
                </span>
              </div>
              <p className="font-mono text-[10px] text-cyan-400/80 mt-0.5">
                Real-time Telemetry & Holographic Parameter Tuning
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white border border-transparent transition-colors cursor-pointer"
            title="Close Panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Presets Bar */}
        <div className="px-5 py-2.5 bg-[#03070e] border-b border-cyan-500/15 flex items-center gap-2 overflow-x-auto jarvis-scrollbar shrink-0">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-400 shrink-0 mr-1">
            Presets:
          </span>
          {Object.entries(HUD_PRESETS).map(([key, preset]) => (
            <button
              key={key}
              onClick={() => handleSelectPreset(key)}
              className={`px-2.5 py-1 rounded-md font-mono text-[10px] font-bold uppercase tracking-wider transition-all cursor-pointer shrink-0 ${
                activePreset === key
                  ? "bg-cyan-500/25 text-[#00e5ff] border border-cyan-400/60 shadow-[0_0_10px_rgba(0,229,255,0.3)]"
                  : "bg-slate-900/60 text-slate-300 hover:bg-white/5 border border-slate-700/60"
              }`}
              title={preset.desc}
            >
              {preset.label}
            </button>
          ))}
        </div>

        {/* Section Tabs */}
        <div className="flex border-b border-cyan-500/20 bg-[#040912] px-5 gap-1 shrink-0 overflow-x-auto jarvis-scrollbar">
          {[
            { id: "style" as const, label: "Typography", icon: Type },
            { id: "dust" as const, label: "Cyan Dust", icon: Sparkles },
            { id: "waves" as const, label: "Plasma Waves", icon: Waves },
            { id: "orb" as const, label: "Orb & Rings", icon: Disc3 },
            { id: "web" as const, label: "Reasoning Web", icon: Network },
            { id: "state" as const, label: "State Simulator", icon: Activity },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 py-2.5 px-3 font-mono text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer shrink-0 ${
                  isActive
                    ? "border-[#00e5ff] text-[#00e5ff] bg-cyan-500/10"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/5"
                }`}
              >
                <Icon className="w-3.5 h-3.5 text-cyan-400" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Main Body (Controls) */}
        <div className="flex-1 overflow-y-auto jarvis-scrollbar p-5 space-y-4">
          {/* TAB 0: TYPOGRAPHY */}
          {activeTab === "style" && (
            <div className="space-y-4">
              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                      Zaki UI Font
                    </h3>
                    <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                      Select a HUD font preset or use a locally installed custom font family.
                    </p>
                  </div>
                  <span className="font-mono text-[10px] font-bold text-[#00e5ff] px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30 shrink-0">
                    {MARK_FONT_OPTIONS[settings.fontPreset]?.label || "System"}
                  </span>
                </div>
                <select
                  value={settings.fontPreset}
                  onChange={(e) => updateSetting("fontPreset", e.target.value as MarkFontPreset)}
                  className="mt-3 h-9 w-full rounded-lg border border-cyan-500/30 bg-slate-950/70 px-3 font-mono text-xs font-bold uppercase tracking-wider text-cyan-100 outline-none focus:border-cyan-300"
                  title="Zaki UI font preset"
                >
                  {Object.entries(MARK_FONT_OPTIONS).map(([key, option]) => (
                    <option key={key} value={key}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {settings.fontPreset === "custom" && (
                <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20">
                  <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                    Custom Font Family
                  </h3>
                  <input
                    type="text"
                    value={settings.customFontFamily}
                    onChange={(e) => updateSetting("customFontFamily", e.target.value)}
                    placeholder={'"Orbitron", "Rajdhani", ui-monospace, monospace'}
                    className="mt-3 h-9 w-full rounded-lg border border-cyan-500/30 bg-slate-950/70 px-3 font-mono text-xs text-cyan-100 placeholder:text-slate-500 outline-none focus:border-cyan-300"
                  />
                </div>
              )}

              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                      Global Font Size
                    </h3>
                    <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                      Applies a consistent typography scale across visible and overlay Zaki UI.
                    </p>
                  </div>
                  <span className="font-mono text-xs font-bold text-[#00e5ff] px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30 shrink-0">
                    {(settings.fontScale * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.85"
                  max="1.25"
                  step="0.05"
                  value={settings.fontScale}
                  onChange={(e) => updateSetting("fontScale", Number(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>

              <div
                className="p-4 rounded-xl bg-[#030914]/80 border border-cyan-500/20 text-center"
                style={{
                  fontFamily:
                    settings.fontPreset === "custom" && settings.customFontFamily.trim()
                      ? settings.customFontFamily
                      : MARK_FONT_OPTIONS[settings.fontPreset]?.family,
                  fontSize: `${settings.fontScale}em`,
                }}
              >
                <div className="text-sm font-bold uppercase tracking-wider text-white">
                  ZAKI TELECOM BRAIN
                </div>
                <div className="mt-1 text-[10px] font-semibold uppercase tracking-wider text-cyan-300">
                  Incident Operations Commander
                </div>
              </div>
            </div>
          )}

          {/* TAB 1: DUST PARTICLES */}
          {activeTab === "dust" && (
            <div className="space-y-4">
              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                    Cyan Dust Spread Radius
                  </h3>
                  <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                    Controls outer boundary radius of stardust cluster (SVG pixels)
                  </p>
                </div>
                <span className="font-mono text-xs font-bold text-[#00e5ff] px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30">
                  {settings.dustRadius}px
                </span>
              </div>
              <input
                type="range"
                min="30"
                max="220"
                step="5"
                value={settings.dustRadius}
                onChange={(e) => updateSetting("dustRadius", Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />

              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                    Twinkle Speed Multiplier
                  </h3>
                  <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                    Controls animation duration and glittering rate
                  </p>
                </div>
                <span className="font-mono text-xs font-bold text-[#00e5ff] px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30">
                  {settings.dustSpeed.toFixed(1)}x
                </span>
              </div>
              <input
                type="range"
                min="0.2"
                max="3.0"
                step="0.1"
                value={settings.dustSpeed}
                onChange={(e) => updateSetting("dustSpeed", Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />

              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                    Particle Density
                  </h3>
                  <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                    Total stardust points rendered inside cluster
                  </p>
                </div>
                <span className="font-mono text-xs font-bold text-[#00e5ff] px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30">
                  {settings.dustCount} dots
                </span>
              </div>
              <input
                type="range"
                min="200"
                max="1200"
                step="20"
                value={settings.dustCount}
                onChange={(e) => updateSetting("dustCount", Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-white">Glow & Shine</span>
                    <span className="font-mono text-[11px] font-bold text-[#00e5ff]">
                      {(settings.dustGlowIntensity * 100).toFixed(0)}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="2.0"
                    step="0.1"
                    value={settings.dustGlowIntensity}
                    onChange={(e) => updateSetting("dustGlowIntensity", Number(e.target.value))}
                    className="w-full accent-cyan-400 cursor-pointer"
                  />
                </div>

                <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-white">Core Aura</span>
                    <span className="font-mono text-[11px] font-bold text-[#00e5ff]">
                      {(settings.dustCoreGlow * 100).toFixed(0)}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max="1.5"
                    step="0.1"
                    value={settings.dustCoreGlow}
                    onChange={(e) => updateSetting("dustCoreGlow", Number(e.target.value))}
                    className="w-full accent-cyan-400 cursor-pointer"
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: PLASMA WAVES */}
          {activeTab === "waves" && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                    Enable Background Plasma Waves
                  </h3>
                  <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                    WebGL GPU organic fluid energy lines in the deep background
                  </p>
                </div>
                <button
                  onClick={() => updateSetting("showWaves", !settings.showWaves)}
                  className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${
                    settings.showWaves ? "bg-cyan-500" : "bg-slate-700"
                  }`}
                >
                  <span
                    className={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform ${
                      settings.showWaves ? "translate-x-5" : ""
                    }`}
                  />
                </button>
              </div>

              {settings.showWaves && (
                <>
                  <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                    <div>
                      <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                        Wave Opacity
                      </h3>
                      <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                        Transparency level in canvas background
                      </p>
                    </div>
                    <span className="font-mono text-xs font-bold text-[#00e5ff] px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30">
                      {(settings.waveOpacity * 100).toFixed(0)}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.05"
                    max="0.80"
                    step="0.02"
                    value={settings.waveOpacity}
                    onChange={(e) => updateSetting("waveOpacity", Number(e.target.value))}
                    className="w-full accent-cyan-400 cursor-pointer"
                  />

                  <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                    <div>
                      <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                        Flow Speed
                      </h3>
                      <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                        Speed of fluid harmonic waves
                      </p>
                    </div>
                    <span className="font-mono text-xs font-bold text-[#00e5ff] px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30">
                      {settings.waveSpeed.toFixed(1)}x
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="3.0"
                    step="0.1"
                    value={settings.waveSpeed}
                    onChange={(e) => updateSetting("waveSpeed", Number(e.target.value))}
                    className="w-full accent-cyan-400 cursor-pointer"
                  />
                </>
              )}
            </div>
          )}

          {/* TAB 3: ORB & RINGS */}
          {activeTab === "orb" && (
            <div className="space-y-4">
              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                    Orb Scale
                  </h3>
                  <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                    Overall size of center 3D sphere and outer orbital rings
                  </p>
                </div>
                <span className="font-mono text-xs font-bold text-[#00e5ff] px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30">
                  {settings.orbScale.toFixed(2)}x
                </span>
              </div>
              <input
                type="range"
                min="0.6"
                max="1.4"
                step="0.05"
                value={settings.orbScale}
                onChange={(e) => updateSetting("orbScale", Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />

              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                    Orbital Rotation Speed
                  </h3>
                  <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                    Speed of clockwise and counter-clockwise spinning rings
                  </p>
                </div>
                <span className="font-mono text-xs font-bold text-[#00e5ff] px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30">
                  {settings.orbRotationSpeed.toFixed(1)}x
                </span>
              </div>
              <input
                type="range"
                min="0.2"
                max="3.0"
                step="0.1"
                value={settings.orbRotationSpeed}
                onChange={(e) => updateSetting("orbRotationSpeed", Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />

              <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                    Sound Wave Ripples
                  </h3>
                  <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                    Concentric acoustic shockwaves during audio events
                  </p>
                </div>
                <button
                  onClick={() => updateSetting("showSoundWaves", !settings.showSoundWaves)}
                  className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${
                    settings.showSoundWaves ? "bg-cyan-500" : "bg-slate-700"
                  }`}
                >
                  <span
                    className={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform ${
                      settings.showSoundWaves ? "translate-x-5" : ""
                    }`}
                  />
                </button>
              </div>

              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-white">Core Glow Intensity</span>
                  <span className="font-mono text-[11px] font-bold text-[#00e5ff]">
                    {(settings.coreGlow * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.2"
                  max="2.0"
                  step="0.1"
                  value={settings.coreGlow}
                  onChange={(e) => updateSetting("coreGlow", Number(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>
            </div>
          )}

          {/* TAB 4: REASONING WEB */}
          {activeTab === "web" && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                    Show Engine Names Outside HUD
                  </h3>
                  <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                    Position CODEX, TELECOM, COLLAB labels outside the central rings
                  </p>
                </div>
                <button
                  onClick={() => updateSetting("showEngineLabels", !settings.showEngineLabels)}
                  className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${
                    settings.showEngineLabels ? "bg-cyan-500" : "bg-slate-700"
                  }`}
                >
                  <span
                    className={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform ${
                      settings.showEngineLabels ? "translate-x-5" : ""
                    }`}
                  />
                </button>
              </div>

              <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex items-center justify-between">
                <div>
                  <h3 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                    Link Line Opacity
                  </h3>
                  <p className="font-mono text-[10px] text-slate-400 mt-0.5">
                    Visibility of synaptic lines linking nodes to the central orb
                  </p>
                </div>
                <span className="font-mono text-xs font-bold text-[#00e5ff] px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-400/30">
                  {(settings.webLineOpacity * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={settings.webLineOpacity}
                onChange={(e) => updateSetting("webLineOpacity", Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>
          )}

          {/* TAB 5: STATE SIMULATOR */}
          {activeTab === "state" && (
            <div className="space-y-4">
              <p className="font-mono text-xs text-slate-300">
                Override Zaki&apos;s current cognitive state to test HUD visuals, colors, and wave reactivity:
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {(
                  [
                    "auto",
                    "idle",
                    "listening",
                    "processing",
                    "speaking",
                    "investigating",
                    "learning",
                    "waiting_for_approval",
                  ] as const
                ).map((st) => (
                  <button
                    key={st}
                    onClick={() => updateSetting("stateOverride", st)}
                    className={`py-2 px-3 rounded-lg font-mono text-[10.5px] font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 transition-all cursor-pointer border ${
                      settings.stateOverride === st
                        ? "bg-cyan-500/25 text-[#00e5ff] border-cyan-400 shadow-[0_0_12px_rgba(0,229,255,0.3)]"
                        : "bg-slate-900/60 text-slate-400 hover:text-white hover:bg-white/5 border-slate-800"
                    }`}
                  >
                    {settings.stateOverride === st && <Check className="w-3 h-3 text-[#00e5ff]" />}
                    <span>{st === "auto" ? "Live Auto" : st.replace("_", " ")}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-cyan-500/20 bg-[#03070e] shrink-0">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white font-mono text-xs font-medium border border-slate-700/60 transition-colors cursor-pointer"
            title="Reset all settings to defaults"
          >
            <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
            <span>Reset Defaults</span>
          </button>

          <button
            onClick={onClose}
            className="px-5 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-[#00e5ff] font-mono text-xs font-bold uppercase tracking-wider border border-cyan-400/50 shadow-[0_0_15px_rgba(0,229,255,0.25)] transition-all cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
