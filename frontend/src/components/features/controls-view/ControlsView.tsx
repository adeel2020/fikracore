"use client";

import { Slider } from "@/components/ui/slider";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";

const CONTROL_GROUPS = [
  {
    label: "Temperature",
    value: [0.7],
    recommended: "0.7",
    min: 0,
    max: 2,
  },
  {
    label: "Top P",
    value: [0.9],
    recommended: "0.9",
    min: 0,
    max: 1,
  },
  {
    label: "Max Tokens",
    value: [4096],
    recommended: "4096",
    min: 512,
    max: 8192,
  },
];

export function ControlsView() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {CONTROL_GROUPS.map((control) => (
        <GlassCard key={control.label} className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <span className="text-sm font-medium text-white">{control.label}</span>
            <Badge variant="default">Recommended: {control.recommended}</Badge>
          </div>
          <Slider
            defaultValue={control.value}
            min={control.min}
            max={control.max}
            step={control.label === "Max Tokens" ? 256 : 0.1}
          />
          <p className="mt-2 text-right text-xs text-neutral-500">
            Current: {control.value[0]}
          </p>
        </GlassCard>
      ))}

      <GlassCard className="p-5 md:col-span-2 xl:col-span-3">
        <h3 className="text-sm font-medium text-white">Runtime Flags</h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Streaming", on: true },
            { label: "Cache Responses", on: true },
            { label: "Strict JSON", on: false },
            { label: "Anomaly Alerts", on: true },
          ].map((flag) => (
            <div
              key={flag.label}
              className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3"
            >
              <span className="text-sm text-neutral-300">{flag.label}</span>
              <Switch defaultChecked={flag.on} />
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
