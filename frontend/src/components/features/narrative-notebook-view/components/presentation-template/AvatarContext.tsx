"use client";

import React, { createContext, useContext, useState, useRef, useCallback } from "react";
import { TalkingAvatarHandle, Persona } from "./TalkingAvatar";

interface AvatarContextType {
  isPlaying: boolean;
  isMuted: boolean;
  persona: Persona;
  gender: "male" | "female";
  cameraView: string;
  isChatBotOpen: boolean;
  registerAvatar: (handle: TalkingAvatarHandle | null) => void;
  speak: (text: string) => void;
  stop: () => void;
  setPersona: (p: Persona) => void;
  setGender: (g: "male" | "female") => void;
  setCameraView: (view: string) => void;
  setIsPlaying: (playing: boolean) => void;
  toggleMute: () => void;
  setIsMuted: (muted: boolean) => void;
  toggleChatBot: () => void;
}

export const AvatarContext = createContext<AvatarContextType | undefined>(undefined);

export const AvatarProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isPlaying, setIsPlayingState] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [persona, setPersonaState] = useState<Persona>("friendly");
  const [gender, setGenderState] = useState<"male" | "female">("male");
  const [cameraView, setCameraViewState] = useState("full");
  const [isChatBotOpen, setIsChatBotOpen] = useState(false);
  
  const avatarRef = useRef<TalkingAvatarHandle | null>(null);

  const registerAvatar = useCallback((handle: TalkingAvatarHandle | null) => {
    avatarRef.current = handle;
    if (handle) {
      handle.setPersona(persona);
    }
  }, [persona]);

  const speak = useCallback((text: string) => {
    if (avatarRef.current) {
      avatarRef.current.speak(text);
      setIsPlayingState(true);
    }
  }, []);

  const stop = useCallback(() => {
    if (avatarRef.current) {
      avatarRef.current.stop();
      setIsPlayingState(false);
    }
  }, []);

  const setPersona = useCallback((p: Persona) => {
    setPersonaState(p);
    if (avatarRef.current) {
      avatarRef.current.setPersona(p);
    }
  }, []);

  const setGender = useCallback((g: "male" | "female") => {
    setGenderState(g);
  }, []);

  const setCameraView = useCallback((view: string) => {
    setCameraViewState(view);
  }, []);

  const toggleMute = useCallback(() => {
    setIsMuted((prev) => !prev);
  }, []);

  const toggleChatBot = useCallback(() => {
    setIsChatBotOpen((prev) => !prev);
  }, []);

  const setIsPlaying = useCallback((playing: boolean) => {
    setIsPlayingState(playing);
  }, []);

  return (
    <AvatarContext.Provider
      value={{
        isPlaying,
        isMuted,
        persona,
        gender,
        cameraView,
        isChatBotOpen,
        registerAvatar,
        speak,
        stop,
        setPersona,
        setGender,
        setCameraView,
        setIsPlaying,
        toggleMute,
        setIsMuted,
        toggleChatBot,
      }}
    >
      {children}
    </AvatarContext.Provider>
  );
};

export const useAvatar = () => {
  const context = useContext(AvatarContext);
  if (context === undefined) {
    throw new Error("useAvatar must be used within an AvatarProvider");
  }
  return context;
};
