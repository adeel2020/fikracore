"use client";

import React, { useState, useEffect, useRef } from "react";
import { Upload, Activity, FileText, Trash2, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const API_BASE = "http://localhost:8000";

export const DocumentsPanel: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [ingesting, setIngesting] = useState(false);
  const [ingestTaskId, setIngestTaskId] = useState<string | null>(null);
  const [ingestStatus, setIngestStatus] = useState<any>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [ingestedFiles, setIngestedFiles] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchIngestedFiles = async () => {
    try {
      const res = await fetch(`${API_BASE}/rag/ingest/list`);
      if (!res.ok) throw new Error("Failed to load files.");
      const data = await res.json();
      setIngestedFiles(data);
    } catch (err) {
      console.error("Failed to load ingested files list:", err);
    }
  };

  useEffect(() => {
    fetchIngestedFiles();
  }, []);

  useEffect(() => {
    if (!ingestTaskId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/rag/ingest/status/${ingestTaskId}`);
        if (!res.ok) throw new Error("Failed to fetch task status.");
        const data = await res.json();
        setIngestStatus(data);

        if (data.status === "COMPLETED" || data.status === "FAILED") {
          setIngesting(false);
          setIngestTaskId(null);
          fetchIngestedFiles();
          clearInterval(interval);
        }
      } catch (err: any) {
        setIngestError(err.message || "Failed to poll task status.");
        setIngesting(false);
        setIngestTaskId(null);
        clearInterval(interval);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [ingestTaskId]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setIngestError(null);
      setIngestStatus(null);
    }
  };

  const triggerUpload = async () => {
    if (!selectedFile) return;
    setIngesting(true);
    setIngestError(null);
    setIngestStatus({ status: "PENDING", progress: 0.0 });

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch(`${API_BASE}/rag/ingest`, {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to start ingestion task.");
      }
      const data = await res.json();
      setIngestTaskId(data.task_id);
    } catch (err: any) {
      setIngestError(err.message || "Upload failed.");
      setIngesting(false);
    }
  };

  const deleteDocument = async (taskId: string) => {
    if (!window.confirm("Are you sure you want to delete this document and all its indexed vector chunks?")) return;

    try {
      const res = await fetch(`${API_BASE}/rag/ingest/${taskId}`, {
        method: "DELETE"
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to delete document.");
      }
      fetchIngestedFiles();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="border border-white/5 bg-neutral-950 backdrop-blur-md rounded-2xl p-6 w-full flex flex-col gap-6 text-white">
      <div className="border-b border-white/5 pb-4">
        <h3 className="text-lg font-bold text-cyan-400 flex items-center gap-2">
          <FileText className="h-5 w-5 text-cyan-400" />
          Document Ingestion
        </h3>
        <p className="text-xs text-neutral-400 mt-1">
          Upload and manage documents for the enterprise RAG pipeline. Supports PDF, Markdown, Excel, CSV, and Plain Text.
        </p>
      </div>

      <div className="border-2 border-dashed border-white/10 hover:border-cyan-500/50 rounded-2xl p-8 bg-neutral-900/20 text-center flex flex-col items-center justify-center transition-all">
        <Upload className="h-10 w-10 text-cyan-400 mb-3" />
        <h4 className="text-sm font-semibold">Select Document File</h4>
        <p className="text-xs text-neutral-500 mt-1 max-w-sm">
          Supported formats: PDF, Markdown (md), Excel (xlsx), CSV, and Plain Text (txt).
        </p>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf,.md,.xlsx,.csv,.txt"
          className="hidden"
        />
        <div className="flex gap-2 mt-4">
          <Button
            onClick={() => fileInputRef.current?.click()}
            className="bg-neutral-900 hover:bg-neutral-800 border border-white/5 text-xs font-semibold rounded-xl"
          >
            Choose File
          </Button>
          {selectedFile && (
            <Button
              onClick={triggerUpload}
              disabled={ingesting}
              className="bg-cyan-500 hover:bg-cyan-400 text-neutral-950 font-bold text-xs rounded-xl flex gap-1.5"
            >
              {ingesting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Ingest Document
            </Button>
          )}
        </div>
        {selectedFile && (
          <p className="text-xs text-cyan-400 font-semibold mt-3">
            Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
          </p>
        )}
      </div>

      {ingestStatus && (
        <div className="border border-white/5 bg-neutral-900/40 rounded-2xl p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
              <Activity className="h-4 w-4" />
              Ingestion Task Status
            </span>
            <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
              ingestStatus.status === "COMPLETED" ? "bg-emerald-950/40 text-emerald-400 border border-emerald-850" :
              ingestStatus.status === "FAILED" ? "bg-rose-950/40 text-rose-450 border border-rose-850" :
              "bg-cyan-950/40 text-cyan-400 border border-cyan-850 animate-pulse"
            }`}>
              {ingestStatus.status}
            </span>
          </div>

          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-[10px] text-neutral-500 font-semibold">
              <span>Task Progress</span>
              <span>{(ingestStatus.progress * 100).toFixed(0)}%</span>
            </div>
            <div className="w-full bg-neutral-950 rounded-full h-2 overflow-hidden border border-white/5">
              <div
                className="bg-cyan-500 h-full transition-all duration-300"
                style={{ width: `${ingestStatus.progress * 100}%` }}
              />
            </div>
          </div>

          <div className="text-[11px] leading-relaxed bg-neutral-950/60 rounded-xl p-3 border border-white/5 font-mono text-neutral-300">
            {ingestStatus.metadata && ingestStatus.metadata.status_message && (
              <p className="text-cyan-400">&gt; {ingestStatus.metadata.status_message}</p>
            )}
            {ingestStatus.metadata && ingestStatus.metadata.child_nodes_count && (
              <p className="text-neutral-400 mt-1">
                &gt; Processed: {ingestStatus.metadata.parent_nodes_count} Parent nodes, {ingestStatus.metadata.child_nodes_count} Vector leaf chunks.
              </p>
            )}
            {ingestStatus.error && (
              <p className="text-rose-455 mt-1">&gt; Error: {ingestStatus.error}</p>
            )}
          </div>
        </div>
      )}

      {ingestError && (
        <div className="border border-rose-955/40 bg-rose-955/10 rounded-2xl p-4 flex gap-2.5 items-start text-xs text-rose-400">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-450 mt-0.5" />
          <div>
            <h5 className="font-bold">Ingestion Trigger Failed</h5>
            <p className="text-neutral-400 mt-0.5">{ingestError}</p>
          </div>
        </div>
      )}

      <div className="border border-white/5 bg-neutral-900/40 rounded-2xl p-5 flex flex-col gap-4">
        <span className="text-xs font-bold text-cyan-400 flex items-center gap-1.5 border-b border-white/5 pb-1">
          <FileText className="h-4 w-4" />
          Ingested File Registry ({ingestedFiles.length})
        </span>
        {ingestedFiles.length > 0 ? (
          <div className="flex flex-col gap-2.5 max-h-[200px] overflow-y-auto pr-1">
            {ingestedFiles.map((file, idx) => (
              <div key={idx} className="flex justify-between items-center bg-neutral-950/60 p-3 rounded-xl border border-white/5 text-xs">
                <div className="flex flex-col gap-0.5">
                  <span className="font-semibold text-neutral-200">{file.filename}</span>
                  <span className="text-[10px] text-neutral-500">
                    {file.parent_nodes} Parents • {file.child_nodes} Children • {new Date(file.timestamp + "Z").toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                    file.status === "COMPLETED" ? "bg-emerald-955/40 text-emerald-400 border border-emerald-850" : "bg-neutral-900 text-neutral-400"
                  }`}>
                    {file.status}
                  </span>
                  <button
                    onClick={() => deleteDocument(file.task_id)}
                    className="p-1 rounded text-neutral-500 hover:text-rose-400 hover:bg-rose-950/20 transition-all"
                    title="Delete Document & Chunks"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-neutral-500 italic text-center py-4">No documents currently registered in the database index.</p>
        )}
      </div>
    </div>
  );
};
