import type { DashboardFeedResponse } from "../types/semantic-cloud.types";
import { API_BASE } from "../../../../../../lib/api/config";
const CACHE_KEY = "semantic_cloud_feed_cache";

let globalFeedPromise: Promise<DashboardFeedResponse> | null = null;
let globalRefreshKey = 0;

export async function getDashboardFeed(refreshKey: number): Promise<DashboardFeedResponse> {
  if (refreshKey !== globalRefreshKey || !globalFeedPromise) {
    // If refreshKey changed, we are forcing an update. Clear session cache.
    const isRefresh = refreshKey !== globalRefreshKey;
    globalRefreshKey = refreshKey;

    if (isRefresh && typeof window !== "undefined") {
      sessionStorage.removeItem(CACHE_KEY);
    }

    globalFeedPromise = (async () => {
      // Only check session storage if this isn't a forced refresh
      if (!isRefresh && typeof window !== "undefined") {
        try {
          const cached = sessionStorage.getItem(CACHE_KEY);
          if (cached) {
            return JSON.parse(cached) as DashboardFeedResponse;
          }
        } catch (e) {
          console.warn("Failed to read from session storage", e);
        }
      }

      // Fetch from network
      const res = await fetch(`${API_BASE}/api/datastory/dashboard-feed`);
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? res.statusText);
      }
      const data = (await res.json()) as DashboardFeedResponse;

      // Save to sessionStorage
      if (typeof window !== "undefined") {
        try {
          sessionStorage.setItem(CACHE_KEY, JSON.stringify(data));
        } catch (e) {
          console.warn("Failed to write to session storage", e);
        }
      }
      return data;
    })();

    // Clear promise on failure to allow retry
    globalFeedPromise.catch(() => {
      if (globalRefreshKey === refreshKey) {
        globalFeedPromise = null;
      }
    });
  }

  return globalFeedPromise;
}
