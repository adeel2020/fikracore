"use client";

import React, { useState } from "react";

import type { ClusterStory } from "../semantic-cloud-view/types/semantic-cloud.types";
import { cn } from "@/lib/utils";
import { Play, Square, Volume2 } from "lucide-react";
import { PercentageNocTickets } from "../../../complaint-dashboard-view/components/CoreOperationalMetrics";

// --- Editable Text Component ---
function EditableText({ value, onChange, isEditing, className, as: Component = "p", multiline = false, style }: { value: string, onChange: (v: string) => void, isEditing: boolean, className?: string, as?: any, multiline?: boolean, style?: React.CSSProperties }) {
  if (isEditing) {
    if (multiline) {
      return (
        <textarea 
          value={value} 
          onChange={(e) => onChange(e.target.value)} 
          className={cn("w-full bg-white/80 border border-blue-200 rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-400 font-serif text-slate-700 resize-y min-h-[100px]", className)}
          style={style}
        />
      );
    }
    return (
      <input 
        value={value} 
        onChange={(e) => onChange(e.target.value)} 
        className={cn("w-full bg-white/80 border border-blue-200 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400", className)}
        style={style}
      />
    );
  }
  return <Component className={className} style={style}>{value}</Component>;
}

// --- The University Template ---
export function UniversityTemplate({ 
  story, 
  isEditing, 
  onStoryChange,
  isPlaying,
  onPlay,
  onStop
}: { 
  story: ClusterStory;
  isEditing: boolean;
  onStoryChange: (updated: ClusterStory) => void;
  isPlaying: boolean;
  onPlay: () => void;
  onStop: () => void;
}) {
  // Local state for the editable fields mapped to the story
  const handleUpdate = <K extends keyof ClusterStory>(field: K, val: ClusterStory[K]) => {
    onStoryChange({ ...story, [field]: val });
  };



  return (
    <div className="relative w-full max-w-4xl mx-auto bg-[#F8FAFC] shadow-2xl rounded-xl overflow-hidden text-slate-800 font-serif mb-12">
      <div className="relative z-10 px-12 pt-16 pb-12">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          {/* Audio Control Bar */}
          <div className="flex items-center gap-2 rounded-full px-3 py-1.5 border bg-white/50 border-slate-200 shadow-sm backdrop-blur-sm">
            {isPlaying ? (
              <button onClick={onStop} className="p-1.5 rounded-full hover:scale-105 transition-transform bg-rose-500 text-white">
                <Square size={14} fill="currentColor" />
              </button>
            ) : (
              <button onClick={onPlay} className="p-1.5 rounded-full hover:scale-105 transition-transform bg-[#4DD0E1] text-white">
                <Play size={14} fill="currentColor" className="ml-0.5" />
              </button>
            )}
            <Volume2 size={14} className="text-slate-400" />
          </div>

          <p className="text-sm italic text-slate-500">SOC Mobile Core Support</p>
        </div>

        <EditableText 
          as="h1"
          value={story.theme} 
          onChange={(v) => handleUpdate("theme", v)} 
          isEditing={isEditing}
          className="text-5xl font-bold text-[#283593] mb-12"
          style={{ fontFamily: "'Nunito', 'Quicksand', sans-serif" }}
        />

        {/* Summary Section */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-[#283593] mb-4" style={{ fontFamily: "'Nunito', 'Quicksand', sans-serif" }}>Summary</h2>
          <div className="flex flex-col md:flex-row gap-8">
            <div className="flex-1 text-slate-700">
              <h3 className="text-lg font-bold mt-4 mb-2 flex items-center gap-2 text-[#283593]">
                <span>🌐</span> Incident Topology & Cross-Domain Isolation
              </h3>
              
              <p className="font-bold mb-1">Executive Summary</p>
              <p className="text-[15px] leading-relaxed mb-6 italic">
                A sudden correlation of multi-variant customer tickets was registered across distinct core service journeys. The SOC Mobile Core Engineering team initiated an urgent cross-domain analysis to trace systemic anomalies and isolate touchpoint friction. By executing an unsupervised semantic clustering pass over the incident payload, the root-layer operational boundary was successfully identified and contained.
              </p>
              
              <hr className="my-6 border-t border-slate-200" />

              <h3 className="text-lg font-bold mt-4 mb-2 flex items-center gap-2 text-[#283593]">
                <span>📊</span> Strategic Diagnostic Vector
              </h3>
              
              <ul className="list-disc pl-5 mb-6 space-y-2 text-[15px]">
                <li><strong>Primary System Friction:</strong> <code className="px-1.5 py-0.5 rounded font-mono text-sm bg-slate-100 text-rose-600">{story.theme}</code></li>
                <li><strong>Total Incident Volume:</strong> <code className="px-1.5 py-0.5 rounded font-mono text-sm bg-slate-100">{story.complaints_count}</code> raw complaints correlated in this domain.</li>
                <li><strong>Impacted Service Journeys:</strong> {story.service_journeys.join(', ')}</li>
                <li><strong>Ingress Queue Footprint:</strong> {story.ticket_queues.join(', ')}</li>
                <li><strong>Target Domain Stakeholders:</strong> {story.reassigned_to.join(', ')}</li>
              </ul>

              <hr className="my-6 border-t border-slate-200" />

              <h3 className="text-lg font-bold mt-4 mb-2 flex items-center gap-2 text-[#283593]">
                <span>🔍</span> Engineering Root-Cause & Routing Synopsis
              </h3>
              <p className="text-[15px] leading-relaxed mb-6 italic">
                The spatial separation of the data cloud confirms that while incoming telemetry was highly fragmented across multiple edge user-plane ingress points, the core failure signatures converge precisely on a single systemic issue. To prevent ticket loops and safeguard SLA boundaries, ownership has been routed directly to the identified domain stakeholders for final architectural mitigation.
              </p>
            </div>
            <div className="w-full md:w-64 h-48 relative shrink-0">
              <PercentageNocTickets />
            </div>
          </div>
        </div>



        <div className="flex justify-end mt-12">
          <p className="text-sm italic text-slate-500">Cognitive Operations & Customer Center</p>
        </div>
      </div>
    </div>
  );
}
