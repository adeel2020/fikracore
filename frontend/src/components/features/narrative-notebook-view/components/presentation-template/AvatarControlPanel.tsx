"use client";

import React from "react";
import { useAvatar } from "./AvatarContext";
import { 
  Play, 
  Square, 
  Mic, 
  MicOff, 
  User, 
  MessageSquare, 
  Video 
} from "lucide-react";

interface AvatarControlPanelProps {
  currentNarrative?: string;
  className?: string;
}

export const AvatarControlPanel: React.FC<AvatarControlPanelProps> = ({ currentNarrative = "", className = "" }) => {
  const {
    isPlaying,
    isMuted,
    persona,
    gender,
    cameraView,
    isChatBotOpen,
    speak,
    stop,
    setPersona,
    setGender,
    setCameraView,
    toggleMute,
    toggleChatBot,
  } = useAvatar();

  return (
    <div className={`bg-white/10 border border-white/20 backdrop-blur-md rounded-full px-4 py-1.5 flex items-center gap-3 shadow-lg select-none pointer-events-auto ${className}`}>
      {/* Play/Stop Narration */}
      <button
        onClick={() => {
          if (isPlaying) {
            stop();
          } else {
            speak(currentNarrative || "Hello, I am your operations assistant. How can I help you today?");
          }
        }}
        title={isPlaying ? "Stop Narration" : "Play Narration"}
        className="p-1.5 rounded-full hover:bg-white/10 text-white transition-all cursor-pointer"
      >
        {isPlaying ? <Square className="h-3 w-3 text-red-400" /> : <Play className="h-3 w-3 text-green-400" />}
      </button>

      <div className="w-[1px] h-3.5 bg-white/15" />

      {/* Mic Mute/Unmute */}
      <button
        onClick={toggleMute}
        title={isMuted ? "Unmute Mic" : "Mute Mic"}
        className="p-1.5 rounded-full hover:bg-white/10 text-white transition-all cursor-pointer"
      >
        {isMuted ? <MicOff className="h-3 w-3 text-red-400" /> : <Mic className="h-3 w-3 text-cyan-400" />}
      </button>

      <div className="w-[1px] h-3.5 bg-white/15" />

      {/* Persona Select */}
      <div className="flex items-center gap-1">
        <User className="h-3 w-3 text-white/50" />
        <select
          value={persona as string}
          onChange={(e) => setPersona(e.target.value as any)}
          className="bg-transparent border-none text-white text-[8px] font-bold font-sans uppercase tracking-widest outline-none cursor-pointer appearance-none -webkit-appearance-none text-left select-none pr-1 hover:text-cyan-400 transition-colors"
          title="Switch Persona"
        >
          <option value="friendly" className="bg-[#121824] text-white">Friendly</option>
          <option value="professional" className="bg-[#121824] text-white">Professional</option>
          <option value="energetic" className="bg-[#121824] text-white">Energetic</option>
          <option value="serious" className="bg-[#121824] text-white">Serious</option>
          <option value="sad" className="bg-[#121824] text-white">Sad</option>
        </select>
      </div>

      <div className="w-[1px] h-3.5 bg-white/15" />

      {/* Gender/Person Toggle */}
      <button
        onClick={() => setGender(gender === "male" ? "female" : "male")}
        title={`Switch to ${gender === "male" ? "Female" : "Male"} Avatar`}
        className="p-1 text-[10px] hover:bg-white/10 rounded-full transition-all cursor-pointer leading-none"
      >
        {gender === "male" ? "👩" : "👨"}
      </button>

      <div className="w-[1px] h-3.5 bg-white/15" />

      {/* AI Chat Bot toggle */}
      <button
        onClick={toggleChatBot}
        title="Toggle AI Chat Bot"
        className={`p-1.5 rounded-full hover:bg-white/10 transition-all cursor-pointer ${
          isChatBotOpen ? "text-[#7FFFD4]" : "text-white"
        }`}
      >
        <MessageSquare className="h-3 w-3" />
      </button>

      <div className="w-[1px] h-3.5 bg-white/15" />

      {/* Camera View toggle */}
      <div className="flex items-center gap-1">
        <Video className="h-3 w-3 text-white/50" />
        <select
          value={cameraView}
          onChange={(e) => setCameraView(e.target.value)}
          className="bg-transparent border-none text-white text-[8px] font-bold font-sans uppercase tracking-widest outline-none cursor-pointer appearance-none -webkit-appearance-none text-left select-none pr-1 hover:text-cyan-400 transition-colors"
          title="Adjust Camera"
        >
          <option value="full" className="bg-[#121824] text-white">Full</option>
          <option value="focus" className="bg-[#121824] text-white">Focus</option>
          <option value="close" className="bg-[#121824] text-white">Close</option>
        </select>
      </div>
    </div>
  );
};
