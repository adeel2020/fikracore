"use client";

import React from "react";
import { Eye, FileSpreadsheet, Rows3, Upload } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { cn, glassSurfaceStatic } from "@/lib/utils";
import { useDataLoader } from "./useDataLoader";

const iconStroke = { strokeWidth: 1.5 } as const;

export function DataLoaderView() {
  const { selectedId, setSelectedId, selected, files, handleFileUpload, handleRemoveFile } = useDataLoader();
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = React.useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-6">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          glassSurfaceStatic,
          "flex min-h-[280px] flex-col items-center justify-center rounded-3xl border-2 border-dashed p-10 transition-all duration-300 cursor-pointer shadow-[inset_0_0_60px_rgba(0,229,255,0.05)]",
          isDragging
            ? "border-cyan-400 bg-cyan-500/10 shadow-[inset_0_0_60px_rgba(0,229,255,0.15)]"
            : "border-cyan-500/30 hover:border-cyan-500/50 hover:bg-white/[0.07]"
        )}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileChange}
          accept=".xlsx,.xls,.csv,.json"
        />
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-500/20 bg-cyan-500/10">
          <Upload className="h-8 w-8 text-cyan-400" {...iconStroke} />
        </div>
        <h2 className="text-lg font-semibold text-white">Drop datasets here</h2>
        <p className="mt-2 max-w-md text-center text-sm text-neutral-400">
          Drag CSV, Parquet, JSON, or Excel files into the smart loader canvas
        </p>
        <p className="mt-4 text-xs text-neutral-500">or click to browse local storage</p>
      </div>

      <div>
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-neutral-400">
          Loaded files
        </p>
        <div className="flex flex-wrap gap-3">
          {files.map((file) => {
            const active = selectedId === file.id;
            return (
              <button
                key={file.id}
                type="button"
                onClick={() => setSelectedId(file.id)}
                className={cn(
                  glassSurfaceStatic,
                  "flex items-center justify-between gap-3 rounded-full px-4 py-2 text-left transition-all duration-300 group/pill",
                  active
                    ? "border-cyan-500/40 bg-cyan-500/10 ring-1 ring-cyan-500/30"
                    : "hover:bg-white/10 hover:border-white/20"
                )}
              >
                <div className="flex items-center gap-3">
                  <FileSpreadsheet
                    className={cn("h-4 w-4", active ? "text-cyan-400" : "text-neutral-500")}
                    {...iconStroke}
                  />
                  <div>
                    <p className="text-sm font-medium text-white">{file.name}</p>
                    <p className="text-xs text-neutral-500">{file.size}</p>
                  </div>
                </div>
                {/* Delete button (displays on hover or if active) */}
                <span
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveFile(file.id);
                  }}
                  className="p-0.5 rounded-full text-neutral-500 hover:text-white hover:bg-white/15 transition-all cursor-pointer font-bold text-xs shrink-0"
                  title="Remove file and clear uploaded data"
                >
                  ×
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {selected && (
        <GlassCard className="overflow-hidden p-0" hover={false}>
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10">
                <Eye className="h-4 w-4 text-cyan-400" {...iconStroke} />
              </div>
              <div>
                <h2 className="text-sm font-medium text-white">Dataset Preview</h2>
                <p className="text-xs text-neutral-400">{selected.name}</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="default">{selected.format}</Badge>
              <span className="flex items-center gap-1.5 text-xs text-neutral-400">
                <Rows3 className="h-3.5 w-3.5" {...iconStroke} />
                {selected.rows.toLocaleString()} rows · {selected.columns.length} columns
              </span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wider text-neutral-500">
                  {selected.columns.map((col) => (
                    <th key={col} className="px-6 py-3 font-medium whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {selected.preview.map((row, rowIndex) => (
                  <tr
                    key={rowIndex}
                    className="border-t border-white/5 transition-colors hover:bg-gradient-to-r hover:from-cyan-500/5 hover:to-transparent"
                  >
                    {selected.columns.map((col) => (
                      <td
                        key={col}
                        className="px-6 py-3 whitespace-nowrap text-neutral-300"
                      >
                        {String(row[col] ?? "—")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="border-t border-white/10 px-6 py-3">
            <p className="text-xs text-neutral-500">
              Showing first {selected.preview.length} of {selected.rows.toLocaleString()} rows
            </p>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
