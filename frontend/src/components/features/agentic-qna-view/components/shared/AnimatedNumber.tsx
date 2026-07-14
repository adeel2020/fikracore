"use client";

import React, { useEffect, useState } from "react";

interface AnimatedNumberProps {
  value: number;
}

export function AnimatedNumber({ value }: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(value);

  useEffect(() => {
    const start = displayValue;
    const end = value;
    if (start === end) return;

    const duration = 800; // ms
    const startTime = performance.now();

    let frameId: number;

    function update(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out quad
      const ease = progress * (2 - progress);
      const current = Math.round(start + (end - start) * ease);

      setDisplayValue(current);

      if (progress < 1) {
        frameId = requestAnimationFrame(update);
      }
    }

    frameId = requestAnimationFrame(update);

    return () => {
      cancelAnimationFrame(frameId);
    };
  }, [value]);

  return (
    <span className="transition-all duration-300 ease-out">
      {displayValue.toLocaleString()}
    </span>
  );
}
