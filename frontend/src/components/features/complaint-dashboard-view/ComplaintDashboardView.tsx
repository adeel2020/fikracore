"use client";

import React, { useState, useEffect, useRef } from "react";
import { ShieldAlert, Activity, List, RefreshCw, Eye, EyeOff, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { GlassCardContext } from "@/components/ui/glass-card";
import { fetchComplaintsTelemetry, ComplaintTelemetry } from "@/lib/api/qna";
import { AnalyticsView } from "./components/AnalyticsView";
import { TelemetryLedger } from "./components/TelemetryLedger";
import { dispatchStorageEvent } from "@/lib/useLocalStorageData";
import { aggregateRawTickets } from "./workers/aggregationUtils";
import * as XLSX from "xlsx";

const getTelemetryDateStr = (timeReported: number) => {
  const dateObj = new Date(timeReported * 1000);
  const year = dateObj.getFullYear();
  const month = (dateObj.getMonth() + 1).toString().padStart(2, "0");
  const day = dateObj.getDate().toString().padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const isDateInFilter = (timeReported: number, filter: string): boolean => {
  if (!filter) return true;
  const dateStr = getTelemetryDateStr(timeReported);
  if (filter.length === 7) {
    return dateStr.startsWith(filter);
  }
  return dateStr === filter;
};

export function ComplaintDashboardView() {
  const [activeTab, setActiveTab] = useState<"analytics" | "ledger">("analytics");
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    try {
      const saved = localStorage.getItem("dashboard_theme");
      if (saved) return saved as 'dark' | 'light';
    } catch (e) {}
    return 'dark';
  });
  const isLight = theme === 'light';
  const [telemetryList, setTelemetryList] = useState<ComplaintTelemetry[]>([]);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [ledgerEnabled, setLedgerEnabled] = useState(true);
  const workerRef = useRef<Worker | null>(null);

  useEffect(() => {
    setMounted(true);

    const initialDate = localStorage.getItem("selected_date_filter");
    if (initialDate) {
      setSelectedDate(initialDate);
    }

    const storedLedger = localStorage.getItem("ledger_enabled");
    if (storedLedger !== null) {
      setLedgerEnabled(storedLedger === "true");
    }

    // Instantiate background Web Worker for regex database mappings and aggregation
    workerRef.current = new Worker(
      new URL("./workers/telemetry.worker.ts", import.meta.url)
    );

    workerRef.current.onmessage = (e: MessageEvent) => {
      const { type, result, error } = e.data;
      if (type === "PARSE_AND_AGGREGATE_DB_SUCCESS" || type === "AGGREGATE_RAW_TICKETS_SUCCESS") {
        const aggregatedStr = JSON.stringify(result);
        const existingStr = localStorage.getItem("dashboard_data");
        if (aggregatedStr !== existingStr) {
          localStorage.setItem("dashboard_data", aggregatedStr);
          dispatchStorageEvent("dashboard_data", aggregatedStr);
        }
        setLoading(false);
      } else if (type === "AGGREGATE_FILTERED_TICKETS_SUCCESS") {
        const aggregatedStr = JSON.stringify(result);
        localStorage.setItem("filtered_dashboard_data", aggregatedStr);
        dispatchStorageEvent("filtered_dashboard_data", aggregatedStr);
        setLoading(false);
      } else if (type === "ERROR") {
        console.error("Worker mapping/aggregation error:", error);
        setLoading(false);
      }
    };

    loadTelemetry();

    // xlsx auto-load runs independently (overwrites dashboard_data with fresh xlsx data if no custom files are loaded)
    const hasUploaded = localStorage.getItem("uploaded_telemetry") || localStorage.getItem("dashboard_data");
    if (!hasUploaded) {
      fetch("/Complaint_managment_dashboard_new.xlsx")
        .then((res) => {
          if (!res.ok) throw new Error("not found");
          return res.arrayBuffer();
        })
        .then((buffer) => {
          const workbook = XLSX.read(new Uint8Array(buffer), { type: "array" });
          const sheet = workbook.Sheets[workbook.SheetNames[0]];
          const rows = XLSX.utils.sheet_to_json(sheet, { defval: "" });
          if (rows.length > 0 && (rows[0] as any).Ticket_ID !== undefined) {
            const aggregated = aggregateRawTickets(rows);
            localStorage.setItem("dashboard_data", JSON.stringify(aggregated));
            dispatchStorageEvent("dashboard_data", JSON.stringify(aggregated));
          }
          // xlsx success does NOT setLoading here — loadTelemetry owns final loading state
        })
        .catch(() => { /* xlsx fetch failed, loadTelemetry will unset loading */ });
    }

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "dashboard_data") {
        return;
      }
      if (!e.key || e.key === "uploaded_telemetry" || e.key === "loader_files") {
        loadTelemetry();
      }
    };

    window.addEventListener("storage", handleStorageChange as EventListener);
    return () => {
      window.removeEventListener("storage", handleStorageChange as EventListener);
      if (workerRef.current) {
        workerRef.current.terminate();
      }
    };
  }, []);

  const loadTelemetry = async () => {
    setLoading(true);
    try {
      const stored = localStorage.getItem("uploaded_telemetry");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setTelemetryList(parsed);
            if (workerRef.current) {
              workerRef.current.postMessage({
                type: "AGGREGATE_RAW_TICKETS",
                data: parsed
              });
              const activeFilter = localStorage.getItem("selected_date_filter");
              if (activeFilter) {
                workerRef.current.postMessage({
                  type: "AGGREGATE_FILTERED_TICKETS",
                  data: parsed,
                  filter: activeFilter
                });
              }
            } else {
              setLoading(false);
            }
            return;
          }
        } catch (e) {
          console.error("Error parsing uploaded telemetry:", e);
        }
      }

      // If there is custom aggregated dashboard data but no telemetry logs, keep it and do not overwrite!
      const hasCustomDashboardData = localStorage.getItem("dashboard_data");
      if (hasCustomDashboardData) {
        setLoading(false);
        return;
      }

      // api_telemetry_cache is intentionally NOT sent through the worker here.
      // The JSON template path below handles aggregation via AGGREGATE_RAW_TICKETS
      // (raw rows → correct). Sending it through PARSE_AND_AGGREGATE_DB would run
      // parseDatabaseComplaints on already-structured fields, mangling queue mappings.
      const cachedTelemetry = localStorage.getItem("api_telemetry_cache");

      // Try to fetch static JSON template file first
      let data: any[] = [];
      let isJsonTemplate = false;
      try {
        const res = await fetch("/Operations_Dashboard_Data_Template.json");
        if (res.ok) {
          const json = await res.json();
          if (Array.isArray(json) && json.length > 0) {
            data = json;
            isJsonTemplate = true;
          }
        }
      } catch (err) {
        console.error("Failed to fetch default JSON telemetry template:", err);
      }

      // Fallback to database complaints if static file fetch failed (Isolated for later use)
      /*
      if (data.length === 0) {
        data = await fetchComplaintsTelemetry();
      }
      */

      const hasUploadedTelemetry = localStorage.getItem("uploaded_telemetry");
      if (!hasUploadedTelemetry && data.length > 0) {
        const dataStr = JSON.stringify(data);
        const dataChanged = dataStr !== cachedTelemetry;

        if (dataChanged) {
          localStorage.setItem("api_telemetry_cache", dataStr);
        }

        if (workerRef.current) {
          if (isJsonTemplate) {
            // Map the JSON rows into telemetry ledger list format
            const mappedList = data.map((r: any, idx: number) => {
              let timestamp = Math.floor(Date.now() / 1000);
              if (r.Create_Date) {
                const parts = r.Create_Date.split("-");
                if (parts.length === 3) {
                  const dt = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
                  if (!isNaN(dt.getTime())) {
                    timestamp = Math.floor(dt.getTime() / 1000);
                  }
                }
              }
              return {
                ...r,
                id: idx + 1,
                session_id: "default_session",
                complaint_number: r.Ticket_ID || `TK-${10000 + idx}`,
                time_reported: timestamp,
                issue_summary: `${r.Issue_Category || "Incident"} - Queue: ${r.Ticket_Queue || "NOC"}`,
                assignment_target: r.Ticket_Queue || "CS",
                assignment_queue: r.Ticket_Queue ? `${r.Ticket_Queue} Queue` : "CS Queue",
                reassignment_category: r.Issue_Category || "Other",
                resolution_category: r.Ticket_Status || "Open",
                reassigned_to_raw: r.Reassigned_To || "",
                rejection_reason_raw: r.Rejection_Reason || "",
                raw_complaint: `Subscriber reported issue under category ${r.Issue_Category || "general"} (Country: ${r.Country || "Local"}). Status: ${r.Ticket_Status || "Open"}. First response time: ${r.Average_Time_spent_in_Mins || 0} mins.`
              };
            });
            setTelemetryList(mappedList);

            // Always post to worker to ensure cached data is up to date with code changes
            workerRef.current.postMessage({
              type: "AGGREGATE_RAW_TICKETS",
              data
            });

            const activeFilter = localStorage.getItem("selected_date_filter");
            if (activeFilter) {
              workerRef.current.postMessage({
                type: "AGGREGATE_FILTERED_TICKETS",
                data: mappedList,
                filter: activeFilter
              });
            }
          } else {
            // DB complaints format needs regex parsing first
            setTelemetryList(data);

            // Always post to worker to ensure cached data is up to date with code changes
            workerRef.current.postMessage({
              type: "PARSE_AND_AGGREGATE_DB",
              data
            });

            const activeFilter = localStorage.getItem("selected_date_filter");
            if (activeFilter) {
              workerRef.current.postMessage({
                type: "AGGREGATE_FILTERED_TICKETS",
                data: data,
                filter: activeFilter
              });
            }
          }
        } else {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    } catch (error) {
      console.error("Error loading complaints telemetry:", error);
      setLoading(false);
    }
  };

  const handleSelectDate = (dateStr: string | null) => {
    setSelectedDate(dateStr);
    if (dateStr) {
      localStorage.setItem("selected_date_filter", dateStr);
      dispatchStorageEvent("selected_date_filter", dateStr);
      
      if (workerRef.current) {
        workerRef.current.postMessage({
          type: "AGGREGATE_FILTERED_TICKETS",
          data: telemetryList,
          filter: dateStr
        });
      }
    } else {
      localStorage.removeItem("selected_date_filter");
      localStorage.removeItem("filtered_dashboard_data");
      dispatchStorageEvent("selected_date_filter", null);
    }
  };

  const displayedTelemetryList = selectedDate
    ? telemetryList.filter(item => isDateInFilter(item.time_reported, selectedDate))
    : telemetryList;

  if (!mounted) return null;

  return (
    <GlassCardContext.Provider value={{ isEditing: false, isLight: isLight }}>
      <div className={cn(
        "flex flex-col h-full overflow-y-auto p-6 relative custom-scrollbar transition-colors duration-500",
        isLight ? "bg-[#F8FAFC] text-slate-800" : "bg-[#0B0F19] text-white",
        `theme-${theme}`
      )}>
        {/* Translucent Minimalist Scrollbar CSS Injection */}
        <style dangerouslySetInnerHTML={{ __html: `
          .custom-scrollbar::-webkit-scrollbar {
            width: 6px;
            height: 6px;
          }
          .custom-scrollbar::-webkit-scrollbar-track {
            background: rgba(19, 25, 38, 0.3);
            border-radius: 9999px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(34, 211, 238, 0.25);
            border-radius: 9999px;
            border: 1px solid rgba(11, 15, 25, 0.4);
            transition: background 0.2s ease-in-out;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(34, 211, 238, 0.45);
          }

          /* ========================================================
             LIGHT MODE OVERRIDES FOR CUSTOMER OPERATIONS ANALYTICS
             ======================================================== */
          .theme-light [id*="-card"], 
          .theme-light .glass-card,
          .theme-light [class*="glassSurfaceStatic"],
          .theme-light [class*="bg-[#131926]"] {
            background-color: rgba(248, 250, 252, 0.95) !important;
            border-color: rgba(226, 232, 240, 0.9) !important;
            color: #1e293b !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
          }

          /* General text overrides inside light-theme cards */
          .theme-light [id*="-card"] .text-white,
          .theme-light .glass-card .text-white,
          .theme-light [id*="-card"] span[class*="text-white"],
          .theme-light .glass-card span[class*="text-white"],
          .theme-light [id*="-card"] div[class*="text-white"],
          .theme-light .glass-card div[class*="text-white"],
          .theme-light [id*="-card"] text[fill*="white"] {
            color: #0f172a !important;
          }
          
          .theme-light [id*="-card"] .text-neutral-300,
          .theme-light .glass-card .text-neutral-300,
          .theme-light [id*="-card"] span[class*="text-neutral-300"],
          .theme-light .glass-card span[class*="text-neutral-300"],
          .theme-light [id*="-card"] div[class*="text-neutral-300"] {
            color: #334155 !important;
          }

          .theme-light [id*="-card"] .text-neutral-400,
          .theme-light .glass-card .text-neutral-400,
          .theme-light [id*="-card"] span[class*="text-neutral-400"],
          .theme-light .glass-card span[class*="text-neutral-400"],
          .theme-light [id*="-card"] div[class*="text-neutral-400"] {
            color: #475569 !important;
          }

          .theme-light [id*="-card"] .text-neutral-500,
          .theme-light .glass-card .text-neutral-500,
          .theme-light [id*="-card"] span[class*="text-neutral-500"],
          .theme-light .glass-card span[class*="text-neutral-500"],
          .theme-light [id*="-card"] p[class*="text-neutral-500"] {
            color: #64748b !important;
          }

          /* SVG Text colors */
          .theme-light [id*="-card"] text,
          .theme-light .glass-card text {
            fill: #334155 !important;
          }
          .theme-light [id*="-card"] text[fill="rgba(255, 255, 255, 0.5)"] {
            fill: rgba(51, 65, 85, 0.6) !important;
          }

          /* Borders & dividers inside cards */
          .theme-light [id*="-card"] .border-b,
          .theme-light .glass-card .border-b,
          .theme-light [id*="-card"] .border-t,
          .theme-light .glass-card .border-t,
          .theme-light [id*="-card"] [class*="border-[#242F41]/45"] {
            border-color: rgba(226, 232, 240, 0.9) !important;
          }

          /* Tooltip popups bg and arrow overrides */
          .theme-light [class*="bg-[#131926]/95"],
          .theme-light [class*="bg-[#131926]"] {
            background-color: rgba(255, 255, 255, 0.98) !important;
            border-color: rgba(6, 182, 212, 0.3) !important;
          }
          .theme-light [class*="bg-[#131926]/95"] [class*="bg-[#131926]"] {
            background-color: #f8fafc !important;
            border-color: rgba(226, 232, 240, 0.9) !important;
          }
          .theme-light [class*="bg-[#131926]/95"] .text-white,
          .theme-light [class*="bg-[#131926]/95"] .text-neutral-200,
          .theme-light [class*="bg-[#131926]/95"] .text-neutral-300 {
            color: #0f172a !important;
          }
          .theme-light [class*="bg-[#131926]/95"] .text-neutral-400 {
            color: #475569 !important;
          }

          /* Recharts Tooltip overrides */
          .theme-light .recharts-default-tooltip {
            background-color: rgba(255, 255, 255, 0.98) !important;
            border-color: rgba(226, 232, 240, 0.9) !important;
            color: #0f172a !important;
          }

          /* Diagnostic Card sub-elements */
          .theme-light [id*="-card"] [class*="bg-neutral-900/20"],
          .theme-light [id*="-card"] [class*="border-neutral-800"],
          .theme-light [id*="-card"] [class*="bg-white/5"],
          .theme-light [id*="-card"] [class*="bg-white/[0.02]"],
          .theme-light [id*="-card"] [class*="bg-white/[0.01]"],
          .theme-light [id*="-card"] [class*="bg-white/[0.04]"],
          .theme-light [id*="-card"] [class*="border-white/5"] {
            background-color: rgba(241, 245, 249, 0.6) !important;
            border-color: rgba(226, 232, 240, 0.8) !important;
          }

          /* Active option highlights */
          .theme-light [id*="-card"] [class*="bg-white/[0.04]"] {
            background-color: rgba(0, 0, 0, 0.04) !important;
          }
          .theme-light [id*="-card"] [class*="border-white/15"] {
            border-color: rgba(6, 182, 212, 0.25) !important;
          }

          /* Progress tracks & bar backgrounds */
          .theme-light [id*="-card"] [class*="bg-[#1A2333]"] {
            background-color: rgba(226, 232, 240, 0.7) !important;
          }

          /* Calendar month selector buttons and headers */
          .theme-light [id*="telemetry-calendar-card"] button[class*="bg-[#1f2937]/50"],
          .theme-light [id*="telemetry-calendar-card"] button[class*="bg-cyan-500/10"] {
            background-color: rgba(241, 245, 249, 0.9) !important;
            border-color: rgba(226, 232, 240, 0.9) !important;
            color: #334155 !important;
          }
          .theme-light [id*="telemetry-calendar-card"] span[class*="text-neutral-200"] {
            color: #0f172a !important;
          }

          /* Calendar day buttons */
          .theme-light [id*="telemetry-calendar-card"] button[class*="bg-[#131926]"],
          .theme-light [id*="telemetry-calendar-card"] button[class*="bg-cyan-500/10"] {
            background-color: rgba(255, 255, 255, 0.9) !important;
            border-color: rgba(226, 232, 240, 0.9) !important;
            color: #334155 !important;
          }
          .theme-light [id*="telemetry-calendar-card"] button[class*="bg-cyan-500/10"] {
            background-color: rgba(34, 211, 238, 0.1) !important;
            border-color: rgba(34, 211, 238, 0.8) !important;
            color: #0ea5e9 !important;
          }
          .theme-light [id*="telemetry-calendar-card"] button[class*="text-neutral-500"] {
            background-color: rgba(241, 245, 249, 0.3) !important;
            border-color: rgba(226, 232, 240, 0.3) !important;
            color: #94a3b8 !important;
          }
          .theme-light [id*="telemetry-calendar-card"] button:hover {
            background-color: rgba(241, 245, 249, 0.9) !important;
            color: #0f172a !important;
          }

          /* Table spreadsheet & filter dropdowns overrides */
          .theme-light select,
          .theme-light input {
            background-color: rgba(255, 255, 255, 0.95) !important;
            border-color: rgba(226, 232, 240, 0.9) !important;
            color: #334155 !important;
          }
          .theme-light option {
            background-color: #ffffff !important;
            color: #334155 !important;
          }
          .theme-light select + [class*="text-neutral-500"] {
            color: #475569 !important;
          }
          .theme-light table,
          .theme-light tr,
          .theme-light th,
          .theme-light td,
          .theme-light [class*="border-[#242F41]"] {
            border-color: rgba(226, 232, 240, 0.9) !important;
          }
          .theme-light thead tr {
            background-color: rgba(241, 245, 249, 0.95) !important;
            color: #475569 !important;
          }
          .theme-light tbody tr {
            background-color: rgba(255, 255, 255, 0.8) !important;
          }
          .theme-light tbody tr:nth-child(even) {
            background-color: rgba(248, 250, 252, 0.6) !important;
          }
          .theme-light tbody tr:hover {
            background-color: rgba(241, 245, 249, 0.8) !important;
          }
          .theme-light td {
            color: #334155 !important;
          }
          .theme-light th {
            color: #0f172a !important;
          }
          .theme-light [class*="bg-black/30"] {
            background-color: rgba(255, 255, 255, 0.8) !important;
          }

          /* Title gradient override */
          .theme-light h1 {
            background-image: linear-gradient(to right, #0f172a, #334155, #475569) !important;
            color: transparent !important;
          }

          /* Custom scrollbar adjustments in light mode */
          .theme-light.custom-scrollbar::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.03) !important;
          }
          .theme-light.custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(14, 165, 233, 0.2) !important;
            border-color: rgba(255, 255, 255, 0.8) !important;
          }
          .theme-light.custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(14, 165, 233, 0.4) !important;
          }
        ` }} />

      {/* Header section */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-[#242F41] pb-5 mb-6 z-10">
        <div>
          <div className="flex items-center gap-3">
            <ShieldAlert className="h-6 w-6 text-cyan-400" />
            <h1 className="text-xl md:text-2xl font-bold tracking-tight bg-gradient-to-r from-white via-neutral-100 to-neutral-400 bg-clip-text text-transparent">
              Customer Operations Analytics
            </h1>
          </div>
          <p className="text-xs text-neutral-400 mt-1">
            Futuristic telemetry portal for near real-time mobile subscriber troubleshooting
          </p>
        </div>

        {/* Tab switcher & refresh controls */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex p-0.5 rounded-lg border border-[#242F41] bg-[#131926]/60">
            <button
              onClick={() => setActiveTab("analytics")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-300 ${
                activeTab === "analytics"
                  ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                  : "text-neutral-400 hover:text-white"
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
              Operations Analytics
            </button>
            {ledgerEnabled && (
              <button
                onClick={() => setActiveTab("ledger")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-300 ${
                  activeTab === "ledger"
                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                    : "text-neutral-400 hover:text-white"
                }`}
              >
                <List className="h-3.5 w-3.5" />
                Telemetry Ledger
              </button>
            )}
          </div>

          <button
            onClick={() => {
              const next = !ledgerEnabled;
              setLedgerEnabled(next);
              localStorage.setItem("ledger_enabled", String(next));
              if (!next && activeTab === "ledger") setActiveTab("analytics");
            }}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-medium border border-[#242F41] bg-[#131926]/60 text-neutral-400 hover:text-white transition-all duration-300"
            title={ledgerEnabled ? "Hide Telemetry Ledger" : "Show Telemetry Ledger"}
          >
            {ledgerEnabled ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
            <span className="hidden sm:inline">{ledgerEnabled ? "Hide Ledger" : "Show Ledger"}</span>
          </button>

          {/* Theme Toggle */}
          <button 
            onClick={() => {
              const nextTheme = isLight ? 'dark' : 'light';
              setTheme(nextTheme);
              try {
                localStorage.setItem("dashboard_theme", nextTheme);
              } catch (e) {}
            }}
            className={cn(
              "p-2 rounded-full border transition-all duration-300 hover:scale-105 shadow-sm flex items-center justify-center cursor-pointer",
              isLight ? "bg-slate-100 border-slate-200 text-slate-600" : "bg-[#131926]/40 border-[#242F41] text-white hover:bg-white/5"
            )}
            title={isLight ? "Use Dark Theme" : "Use Light Theme"}
          >
            {isLight ? <Moon size={14} /> : <Sun size={14} />}
          </button>

          <Button
            size="sm"
            variant="ghost"
            onClick={loadTelemetry}
            className="h-8 w-8 p-0 border border-[#242F41] bg-[#131926]/40 hover:bg-white/5"
            title="Refresh database records"
          >
            <RefreshCw className="h-3.5 w-3.5 text-cyan-400" />
          </Button>
        </div>
      </div>

      <div className="flex-1" id="complaint-dashboard-content">
        <div className={activeTab === "analytics" ? "block" : "hidden"}>
          <AnalyticsView selectedDate={selectedDate} onSelectDate={handleSelectDate} />
        </div>
        {ledgerEnabled && (
          <div className={activeTab === "ledger" ? "block" : "hidden"}>
            <TelemetryLedger telemetryList={displayedTelemetryList} loading={loading} />
          </div>
        )}
      </div>
      </div>
    </GlassCardContext.Provider>
  );
}
