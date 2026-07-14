import { useEffect, useState, useRef } from "react";

let lastStoredRawGlobal: string | null = null;
let cachedParsedDataGlobal: any = null;
let lastStoredRawFiltered: string | null = null;
let cachedParsedDataFiltered: any = null;

function getCachedDashboardData() {
  if (typeof window === "undefined") return null;
  const isFiltered = localStorage.getItem("selected_date_filter");
  if (isFiltered) {
    const stored = localStorage.getItem("filtered_dashboard_data");
    if (!stored) return null;
    if (stored === lastStoredRawFiltered) {
      return cachedParsedDataFiltered;
    }
    try {
      const parsed = JSON.parse(stored);
      lastStoredRawFiltered = stored;
      cachedParsedDataFiltered = parsed;
      return parsed;
    } catch (e) {
      return null;
    }
  } else {
    const stored = localStorage.getItem("dashboard_data");
    if (!stored) return null;
    if (stored === lastStoredRawGlobal) {
      return cachedParsedDataGlobal;
    }
    try {
      const parsed = JSON.parse(stored);
      lastStoredRawGlobal = stored;
      cachedParsedDataGlobal = parsed;
      return parsed;
    } catch (e) {
      return null;
    }
  }
}


let cachedParsedGlobalOnly: any = null;
let lastStoredRawGlobalOnly: string | null = null;

function getGlobalParsedData() {
  if (typeof window === "undefined") return null;
  const stored = localStorage.getItem("dashboard_data");
  if (!stored) return null;
  if (stored === lastStoredRawGlobalOnly) {
    return cachedParsedGlobalOnly;
  }
  try {
    const parsed = JSON.parse(stored);
    lastStoredRawGlobalOnly = stored;
    cachedParsedGlobalOnly = parsed;
    return parsed;
  } catch (e) {
    return null;
  }
}

export function useGlobalLocalStorageData<T>(key: string, defaultValue: T): T {
  const [data, setData] = useState<T>(() => {
    const parsed = getGlobalParsedData();
    if (parsed && parsed[key] !== undefined) {
      return parsed[key];
    }
    return defaultValue;
  });
  const defaultValueRef = useRef(defaultValue);

  useEffect(() => {
    defaultValueRef.current = defaultValue;
  }, [defaultValue]);

  useEffect(() => {
    const loadData = () => {
      const parsed = getGlobalParsedData();
      if (parsed && parsed[key] !== undefined) {
        setData(parsed[key]);
        return;
      }
      setData(defaultValueRef.current);
    };

    loadData();

    window.addEventListener("storage", loadData);
    return () => {
      window.removeEventListener("storage", loadData);
    };
  }, [key]);

  return data;
}

export function useLocalStorageData<T>(key: string, defaultValue: T): T {
  const [data, setData] = useState<T>(() => {
    const parsed = getCachedDashboardData();
    if (parsed && parsed[key] !== undefined) {
      return parsed[key];
    }
    return defaultValue;
  });
  const defaultValueRef = useRef(defaultValue);

  useEffect(() => {
    defaultValueRef.current = defaultValue;
  }, [defaultValue]);

  useEffect(() => {
    const loadData = () => {
      const parsed = getCachedDashboardData();
      if (parsed && parsed[key] !== undefined) {
        setData(parsed[key]);
        return;
      }
      setData(defaultValueRef.current);
    };

    loadData();

    window.addEventListener("storage", loadData);
    return () => {
      window.removeEventListener("storage", loadData);
    };
  }, [key]);

  return data;
}

export function dispatchStorageEvent(key: string, newValue: string | null = null) {
  if (typeof window === "undefined") return;
  try {
    const event = new StorageEvent("storage", {
      key,
      newValue,
      storageArea: window.localStorage,
    });
    window.dispatchEvent(event);
  } catch (e) {
    const event = new Event("storage") as any;
    event.key = key;
    event.newValue = newValue;
    window.dispatchEvent(event);
  }
}

