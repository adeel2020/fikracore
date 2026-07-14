"use client";

import { useState, useEffect } from "react";
import type { DashboardFeedResponse } from "../../types/semantic-cloud.types";

import { getDashboardFeed } from "../../hooks/useDashboardFeedCache";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface UseStorytellerChatResult {
  loading: boolean;
  error: string | null;
}

export function useStorytellerChat(refreshKey: number): UseStorytellerChatResult {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setError(null);

    getDashboardFeed(refreshKey)
      .then(() => {
        if (!cancelled) {
          // data loaded successfully — ready for chat
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : "Failed to load narrative";
          if (msg.includes("Semantic cache not found") || msg.includes("cache has not been built")) {
            setError("Cache not built yet — upload operational data first.");
          } else {
            setError(msg);
          }
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return { loading, error };
}
