"use client";

import React, { useEffect, useRef, useState } from "react";

interface CameraStreamProps {
  onStreamReady?: (stream: MediaStream) => void;
  onStreamEnd?: () => void;
}

export function CameraStream({ onStreamReady, onStreamEnd }: CameraStreamProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [active, setActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let disposed = false;
    const start = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: 320, height: 240 },
        });
        if (disposed) { stream.getTracks().forEach(t => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setActive(true);
        onStreamReady?.(stream);
      } catch (err: any) {
        setError(err?.message || "Camera access denied");
      }
    };
    start();
    return () => {
      disposed = true;
      streamRef.current?.getTracks().forEach(t => t.stop());
      streamRef.current = null;
      setActive(false);
      onStreamEnd?.();
    };
  }, []);

  if (error) return null;

  return (
    <video
      ref={videoRef}
      autoPlay
      playsInline
      muted
      className="hidden"
    />
  );
}
