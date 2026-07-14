import React from "react";

interface TaskProgressBarProps {
  label: string;
  value: number;
  color: string;
}

export const TaskProgressBar: React.FC<TaskProgressBarProps> = React.memo(({ label, value, color }) => {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-neutral-400">{label}</span>
        <span className="text-white font-semibold" style={{ color }}>{value}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${value}%`,
            background: `linear-gradient(90deg, ${color}, ${color}88)`,
            boxShadow: `0 0 8px ${color}40`,
          }}
        />
      </div>
    </div>
  );
});

TaskProgressBar.displayName = "TaskProgressBar";
