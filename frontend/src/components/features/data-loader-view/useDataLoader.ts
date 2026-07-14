import { useState, useEffect, useCallback } from "react";
import * as XLSX from "xlsx";
import Papa from "papaparse";

export type DatasetFile = {
  id: string;
  name: string;
  size: string;
  format: string;
  rows: number;
  columns: string[];
  preview: Record<string, string | number>[];
  rawData?: any[];
  sheetData?: Record<string, any>;
};

function mapKeysToDashboardFormat(sheetName: string, rows: any[]) {
  if (sheetName === "Monthly_Distribution") {
    return rows.map(r => ({
      month: r.Month || r.month || "",
      blue: Number(r.BLUE_Tickets || r.blue || 0),
      brown: Number(r.BROWN_Tickets || r.brown || 0)
    }));
  }
  if (sheetName === "NOC_Queue_Times") {
    return rows.map(r => ({
      name: r.Queue_Name || r.name || "",
      closed: Number(r.Closed_Tickets || r.closed || 0),
      total: Number(r.Total_Tickets || r.total || 0),
      avg: `${r.Avg_Time_Mins || r.avg || 0} mins`,
      compliance: Number(r.SLA_Compliance_Pct || r.compliance || 0)
    }));
  }
  if (sheetName === "First_Response_Issues") {
    return rows.map(r => ({
      name: r.Issue_Category || r.name || "",
      tickets: `${r.Tickets || r.tickets || 0} (12%)`,
      metPct: Number(r.Met_SLA_Pct || r.metPct || 0),
      avgTime: `${r.Avg_Time_Mins || r.avgTime || 0} min`,
      missPct: 100 - Number(r.Met_SLA_Pct || r.metPct || 0)
    }));
  }
  if (sheetName === "Weekly_Volume") {
    return rows.map(r => ({
      day: r.Day || r.day || "",
      brown: Number(r.BROWN_Tickets || r.brown || 0),
      blue: Number(r.BLUE_Tickets || r.blue || 0)
    }));
  }
  if (sheetName === "Trouble_Tickets_30d") {
    return rows.map(r => ({
      date: r.Date || r.date || "",
      resolved: Number(r.Resolved || r.resolved || 0),
      reassigned: Number(r.Reassigned || r.reassigned || 0),
      rejected: Number(r.Rejected || r.rejected || 0),
      rate: Number(r.SLA_Compliance_Rate_Pct || r.rate || 0)
    }));
  }
  if (sheetName === "Reassignments_Rejections") {
    return rows.map(r => ({
      Metric_Type: r.Metric_Type || "",
      name: r.Name || r.name || "",
      value: Number(r.Tickets_Count || r.value || 0)
    }));
  }
  if (sheetName === "Roaming_By_Country") {
    return rows.map(r => ({
      day: r.Date || r.day || "",
      SaudiArabia: Number(r.SaudiArabia || r.saudiarabia || 0),
      UK: Number(r.UK || r.uk || 0),
      Germany: Number(r.Germany || r.germany || 0),
      US: Number(r.US || r.us || 0),
      Singapore: Number(r.Singapore || r.singapore || 0)
    }));
  }
  if (sheetName === "NOC_Tickets_Distribution") {
    return rows.map(r => ({
      name: r.Queue || r.name || "",
      value: Number(r.Value || r.value || 0),
      pct: Number(r.Percentage || r.pct || 0)
    }));
  }
  if (sheetName === "UAE_Regional_Hotspots") {
    return rows.map(r => ({
      name: r.Hotspot_Name || r.name || "",
      count: Number(r.Tickets_Count || r.count || 0)
    }));
  }
  return rows;
}

import { aggregateRawTickets } from "../complaint-dashboard-view/workers/aggregationUtils";
import { dispatchStorageEvent } from "@/lib/useLocalStorageData";
export { aggregateRawTickets };

function parseXlsxToFiles(buffer: ArrayBuffer): DatasetFile[] {
  const workbook = XLSX.read(new Uint8Array(buffer), { type: "array" });
  const files: DatasetFile[] = [];
  const sheetData: Record<string, any> = {};

  workbook.SheetNames.forEach((sheetName) => {
    const sheet = workbook.Sheets[sheetName];
    const rows: any[] = XLSX.utils.sheet_to_json(sheet, { defval: "" });
    if (rows.length === 0) return;

    const mapped = mapKeysToDashboardFormat(sheetName, rows);
    sheetData[sheetName] = mapped;

    const columns = Object.keys(rows[0]);
    const preview = rows.slice(0, 10) as Record<string, string | number>[];
    files.push({
      id: `Complaint_managment_dashboard_new.xlsx_${sheetName}`,
      name: `Complaint_managment_dashboard_new.xlsx [${sheetName}]`,
      size: `${(buffer.byteLength / (1024 * 1024)).toFixed(2)} MB`,
      format: "Excel Sheet",
      rows: rows.length,
      columns,
      preview,
      sheetData: { [sheetName]: mapped }
    });
  });

  localStorage.setItem("dashboard_data", JSON.stringify(sheetData));
  return files;
}

export function useDataLoader() {
  const [files, setFiles] = useState<DatasetFile[]>([]);
  const [selectedId, setSelectedIdState] = useState<string>("");
  const [isInitialized, setIsInitialized] = useState(false);

  const setSelectedId = useCallback((id: string) => {
    setSelectedIdState(id);
    try {
      localStorage.setItem("selected_dataset_id", id);
    } catch {}
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("selected_dataset_id");
    if (stored) {
      setSelectedIdState(stored);
    }
    setIsInitialized(true);
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("loader_files");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setFiles(parsed);
          return;
        }
      } catch (e) {}
    }

    fetch("/Complaint_managment_dashboard_new.xlsx")
      .then((res) => {
        if (!res.ok) throw new Error("not found");
        return res.arrayBuffer();
      })
      .then((buffer) => {
        const parsed = parseXlsxToFiles(buffer);
        if (parsed.length > 0) {
          setFiles(parsed);
          setSelectedId(parsed[0].id);
          localStorage.setItem("loader_files", JSON.stringify(parsed));
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (isInitialized && typeof window !== "undefined") {
      const lightweightFiles = files.map(({ rawData, sheetData, ...rest }) => rest);
      localStorage.setItem("loader_files", JSON.stringify(lightweightFiles));
    }
  }, [files, isInitialized]);

  useEffect(() => {
    if (!selectedId || files.length === 0) return;
    const active = files.find((f) => f.id === selectedId);
    if (!active) return;

    if (active.id.startsWith("Complaint_managment_dashboard_new.xlsx") && !active.sheetData && !active.rawData) {
      fetch("/Complaint_managment_dashboard_new.xlsx")
        .then((res) => {
          if (!res.ok) throw new Error("not found");
          return res.arrayBuffer();
        })
        .then((buffer) => {
          parseXlsxToFiles(buffer);
        })
        .catch(() => {});
      return;
    }

    if (active.rawData) {
      const aggregated = aggregateRawTickets(active.rawData);
      localStorage.setItem("dashboard_data", JSON.stringify(aggregated));
      localStorage.setItem("uploaded_telemetry", JSON.stringify(active.rawData));
      dispatchStorageEvent("dashboard_data", JSON.stringify(aggregated));
      dispatchStorageEvent("uploaded_telemetry", JSON.stringify(active.rawData));
    } else if (active.sheetData) {
      localStorage.setItem("dashboard_data", JSON.stringify(active.sheetData));
      localStorage.removeItem("uploaded_telemetry");
      dispatchStorageEvent("dashboard_data", JSON.stringify(active.sheetData));
      dispatchStorageEvent("uploaded_telemetry", null);
    }
  }, [selectedId, files]);

  useEffect(() => {
    if (isInitialized && files.length > 0 && !selectedId) {
      setSelectedId(files[0].id);
    }
  }, [files, selectedId, isInitialized]);

  const selected = files.find((f) => f.id === selectedId) ?? null;

  const handleRemoveFile = (id: string) => {
    localStorage.removeItem("dashboard_data");
    localStorage.removeItem("uploaded_telemetry");
    localStorage.removeItem("uploaded_session");
    dispatchStorageEvent("uploaded_telemetry", null);
    
    setFiles((prev) => {
      const filtered = prev.filter((f) => f.id !== id);
      if (selectedId === id) {
        setSelectedId(filtered.length > 0 ? filtered[0].id : "");
      }
      return filtered;
    });
  };

  const handleFileUpload = (file: File) => {
    const reader = new FileReader();
    const format = file.name.split(".").pop()?.toUpperCase() || "UNKNOWN";
    const size = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;

    if (format === "XLSX" || format === "XLS") {
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target?.result as ArrayBuffer);
          const workbook = XLSX.read(data, { type: "array" });
          
          const newDatasetFiles: DatasetFile[] = [];
          const dashboardDataStore: Record<string, any> = {};

          const existingData = localStorage.getItem("dashboard_data");
          if (existingData) {
            try {
              Object.assign(dashboardDataStore, JSON.parse(existingData));
            } catch (err) {}
          }

          const firstSheet = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[firstSheet];
          const rawRows = XLSX.utils.sheet_to_json(worksheet, { defval: "" });

          if (rawRows.length > 0 && (rawRows[0] as any).Ticket_ID !== undefined) {
            const aggregated = aggregateRawTickets(rawRows);
            localStorage.setItem("dashboard_data", JSON.stringify(aggregated));

            // Also format and store the raw ticket logs for TelemetryLedger!
            const telemetryList = rawRows.map((r: any, idx: number) => {
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
                session_id: "uploaded_session",
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
            localStorage.setItem("uploaded_telemetry", JSON.stringify(telemetryList));

            const columns = Object.keys(rawRows[0] as object);
            const preview = rawRows.slice(0, 10) as Record<string, string | number>[];
            newDatasetFiles.push({
              id: `${file.name.replace(/\s+/g, "_")}_raw`,
              name: `${file.name} [Ticket Logs]`,
              size,
              format: "Excel Log Sheet",
              rows: rawRows.length,
              columns,
              preview,
              rawData: telemetryList
            });
          } else {
            workbook.SheetNames.forEach((sheetName) => {
              const sheet = workbook.Sheets[sheetName];
              const sheetRows = XLSX.utils.sheet_to_json(sheet, { defval: "" });

              if (sheetRows.length > 0) {
                const mappedRows = mapKeysToDashboardFormat(sheetName, sheetRows);
                dashboardDataStore[sheetName] = mappedRows;

                const columns = Object.keys(sheetRows[0] as object);
                const preview = sheetRows.slice(0, 10) as Record<string, string | number>[];

                newDatasetFiles.push({
                  id: `${file.name.replace(/\s+/g, "_")}_${sheetName}`,
                  name: `${file.name} [${sheetName}]`,
                  size,
                  format: "Excel Sheet",
                  rows: sheetRows.length,
                  columns,
                  preview,
                  sheetData: { [sheetName]: mappedRows }
                });
              }
            });
            localStorage.setItem("dashboard_data", JSON.stringify(dashboardDataStore));
          }

          if (newDatasetFiles.length > 0) {
            setFiles((prev) => [...newDatasetFiles, ...prev]);
            setSelectedId(newDatasetFiles[0].id);
            dispatchStorageEvent("dashboard_data", JSON.stringify(dashboardDataStore));
          }
        } catch (error) {
          console.error("Error parsing Excel workbook:", error);
          alert("Error parsing Excel workbook. Please verify that the sheet matches the template layout.");
        }
      };
      reader.readAsArrayBuffer(file);
    } else if (format === "CSV") {
      reader.onload = (e) => {
        try {
          const csvText = e.target?.result as string;
          Papa.parse(csvText, {
            header: true,
            dynamicTyping: true,
            complete: (results) => {
              const rawRows = results.data;
              if (rawRows.length > 0) {
                const columns = Object.keys(rawRows[0] as object);
                const preview = rawRows.slice(0, 10) as Record<string, string | number>[];

                const newFile: DatasetFile = {
                  id: file.name.replace(/\s+/g, "_"),
                  name: file.name,
                  size,
                  format: "CSV",
                  rows: rawRows.length,
                  columns,
                  preview
                };

                setFiles((prev) => [newFile, ...prev]);
                setSelectedId(newFile.id);
              }
            }
          });
        } catch (error) {
          console.error("Error parsing CSV:", error);
          alert("Error parsing CSV file.");
        }
      };
      reader.readAsText(file);
    } else if (format === "JSON") {
      reader.onload = (e) => {
        try {
          const jsonText = e.target?.result as string;
          const rawRows = JSON.parse(jsonText);
          
          if (Array.isArray(rawRows) && rawRows.length > 0) {
            // Check if it's a raw ticket logs list
            if ((rawRows[0] as any).Ticket_ID !== undefined) {
              const worker = new Worker(
                new URL("../complaint-dashboard-view/workers/telemetry.worker.ts", import.meta.url)
              );
              worker.postMessage({
                type: "AGGREGATE_RAW_TICKETS",
                data: rawRows
              });
              worker.onmessage = (event: MessageEvent) => {
                const { type: resType, result } = event.data;
                if (resType === "AGGREGATE_RAW_TICKETS_SUCCESS") {
                  localStorage.setItem("dashboard_data", JSON.stringify(result));

                  // Map to telemetry ledger format
                  const telemetryList = rawRows.map((r: any, idx: number) => {
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
                      session_id: "uploaded_session",
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
                  localStorage.setItem("uploaded_telemetry", JSON.stringify(telemetryList));
                  dispatchStorageEvent("uploaded_telemetry", JSON.stringify(telemetryList));
                }
                worker.terminate();
              };

              const columns = Object.keys(rawRows[0] as object);
              const preview = rawRows.slice(0, 10) as Record<string, string | number>[];
              const newFile: DatasetFile = {
                id: `${file.name.replace(/\s+/g, "_")}_raw`,
                name: `${file.name} [Ticket Logs]`,
                size,
                format: "JSON Log Sheet",
                rows: rawRows.length,
                columns,
                preview
              };

              setFiles((prev) => [newFile, ...prev]);
              setSelectedId(newFile.id);
            } else {
              const columns = Object.keys(rawRows[0] as object);
              const preview = rawRows.slice(0, 10) as Record<string, string | number>[];
              const newFile: DatasetFile = {
                id: file.name.replace(/\s+/g, "_"),
                name: file.name,
                size,
                format: "JSON",
                rows: rawRows.length,
                columns,
                preview
              };

              setFiles((prev) => [newFile, ...prev]);
              setSelectedId(newFile.id);
            }
          } else if (!Array.isArray(rawRows) && typeof rawRows === "object" && rawRows !== null) {
            // Support JSON file upload with pre-aggregated dashboard sheet arrays
            const dashboardDataStore: Record<string, any> = {};
            const existingData = localStorage.getItem("dashboard_data");
            if (existingData) {
              try {
                Object.assign(dashboardDataStore, JSON.parse(existingData));
              } catch (err) {}
            }

            const sheetNames = Object.keys(rawRows);
            const newDatasetFiles: DatasetFile[] = [];

            sheetNames.forEach((sheetName) => {
              const sheetRows = rawRows[sheetName];
              if (Array.isArray(sheetRows) && sheetRows.length > 0) {
                const mappedRows = mapKeysToDashboardFormat(sheetName, sheetRows);
                dashboardDataStore[sheetName] = mappedRows;

                const columns = Object.keys(sheetRows[0] as object);
                const preview = sheetRows.slice(0, 10) as Record<string, string | number>[];

                newDatasetFiles.push({
                  id: `${file.name.replace(/\s+/g, "_")}_${sheetName}`,
                  name: `${file.name} [${sheetName}]`,
                  size,
                  format: "JSON Sheet",
                  rows: sheetRows.length,
                  columns,
                  preview
                });
              }
            });

            if (newDatasetFiles.length > 0) {
              localStorage.setItem("dashboard_data", JSON.stringify(dashboardDataStore));
              setFiles((prev) => [...newDatasetFiles, ...prev]);
              setSelectedId(newDatasetFiles[0].id);
              dispatchStorageEvent("dashboard_data", JSON.stringify(dashboardDataStore));
            }
          } else {
            alert("JSON data must be an array of objects or an object containing sheet arrays.");
          }
        } catch (error) {
          console.error("Error parsing JSON:", error);
          alert("Error parsing JSON file. Please verify it is correctly formatted.");
        }
      };
      reader.readAsText(file);
    } else {
      alert("Unsupported file format. Please upload a .xlsx, .xls, .csv, or .json file.");
    }
  };

  return {
    selectedId,
    setSelectedId,
    selected,
    files,
    handleFileUpload,
    handleRemoveFile
  };
}
