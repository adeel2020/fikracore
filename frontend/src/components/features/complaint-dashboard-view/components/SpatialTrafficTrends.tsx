"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Globe, BarChart2, ChevronLeft, ChevronRight, CalendarRange } from "lucide-react";
import { useLocalStorageData, useGlobalLocalStorageData } from "@/lib/useLocalStorageData";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip
} from "recharts";
import { GlassCard } from "@/components/ui/glass-card";

const LINE_COLORS = [
  "#00F0FF", "#FF1493", "#FFD700", "#3B82F6", "#00FF7F",
  "#FF0044", "#A855F7", "#00FFA0", "#FF6B00", "#00E5FF",
  "#FF1744", "#00E6A0", "#FFEA00", "#7C3AED", "#FF4400",
];

const COMMON_LABEL_KEYS = new Set([
  "day", "month", "date", "year", "period", "week", "label", "name",
  "category", "time", "period", "weekday", "quarter", "hour",
]);

function inferXAxisKey(data: Record<string, unknown>[]): string {
  if (!data || data.length === 0) return "day";
  const first = data[0];
  for (const key of COMMON_LABEL_KEYS) {
    if (key in first) return key;
  }
  for (const [key, val] of Object.entries(first)) {
    if (typeof val === "string") return key;
  }
  return Object.keys(first)[0];
}

function inferDataSeriesKeys(data: Record<string, unknown>[], xAxisKey: string): string[] {
  if (!data || data.length === 0) return [];
  const first = data[0];
  return Object.keys(first).filter(
    (k) => k !== xAxisKey && typeof first[k] === "number"
  );
}

function normalizeData<T extends Record<string, unknown>>(
  data: T[],
  xAxisKey: string,
  seriesKeys: string[]
): Record<string, unknown>[] {
  return data.map((item) => {
    const entry: Record<string, unknown> = { [xAxisKey]: item[xAxisKey] };
    for (const key of seriesKeys) {
      entry[key] = Number(item[key]) || 0;
    }
    return entry;
  });
}

// UAE Coordinates for SVG path outline (Stylized silhouette of UAE coastline and borders)
// Abu Dhabi (West), Dubai, Sharjah, RAK (North East), Fujairah (East Coast)
const UAE_SVG_PATH = "M 5 60 C 15 58, 25 55, 30 52 C 35 48, 45 42, 52 42 C 58 40, 62 38, 68 32 C 75 25, 82 18, 88 15 L 92 12 L 95 18 L 92 25 C 92 25, 93 30, 93 35 L 94 48 L 88 52 C 86 54, 82 58, 82 62 C 82 68, 85 75, 85 80 L 84 90 L 75 90 L 70 85 C 65 82, 55 82, 50 82 C 40 82, 30 85, 20 85 C 10 85, 5 78, 5 70 Z";

// // UAE regional hotspots representing complaint telemetry volume
// const UAE_HOTSPOTS = [
//   { name: "Dubai Core", x: 68, y: 32, size: 10, color: COLORS.cyan, count: 142 },
//   { name: "Abu Dhabi Central", x: 42, y: 52, size: 12, color: COLORS.pink, count: 210 },
//   { name: "Al Ain", x: 74, y: 64, size: 8, color: COLORS.amber, count: 88 },
//   { name: "Sharjah / Ajman", x: 78, y: 24, size: 9, color: COLORS.green, count: 122 },
//   { name: "Fujairah East", x: 88, y: 40, size: 7, color: COLORS.magenta, count: 54 },
//   { name: "Ras Al Khaimah", x: 88, y: 15, size: 6, color: COLORS.cyan, count: 42 }
// ];

export function TopRoamingComplaints() {
  const raw = useLocalStorageData<Record<string, unknown>[]>("Roaming_By_Country", []);

  const xAxisKey = useMemo(() => inferXAxisKey(raw), [raw]);
  const seriesKeys = useMemo(() => inferDataSeriesKeys(raw, xAxisKey), [raw, xAxisKey]);
  const data = useMemo(() => normalizeData(raw, xAxisKey, seriesKeys), [raw, xAxisKey, seriesKeys]);
  const isEmpty = raw.length === 0;

  return (
    <GlassCard id="roaming-complaints-card" className="p-4 flex flex-col justify-between h-[200px] z-10" hover={true}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-neutral-400 tracking-wider uppercase">Top Roaming Complaints</span>
        <Globe className="h-4 w-4 text-cyan-400" />
      </div>

      {isEmpty ? (
        <div className="flex-1 flex items-center justify-center text-[10px] text-neutral-500">
          No data uploaded
        </div>
      ) : (
        <>
          <div className="flex-1 w-full h-[95px] overflow-visible">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 15, left: -10, bottom: 5 }}>
                <XAxis dataKey={xAxisKey} stroke="#4b5563" fontSize={7} tickLine={false} />
                <YAxis stroke="#4b5563" fontSize={7} tickLine={false} width={25} />
                <Tooltip
                  wrapperStyle={{ zIndex: 9999 }}
                  contentStyle={{
                    backgroundColor: "rgba(19, 25, 38, 0.95)",
                    borderColor: "#242F41",
                    borderRadius: "8px",
                    fontSize: "9px",
                    color: "white"
                  }}
                />
                {seriesKeys.map((key, i) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={LINE_COLORS[i % LINE_COLORS.length]}
                    strokeWidth={1.5}
                    dot={false}
                    name={key.replace(/([A-Z])/g, " $1").trim()}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="flex flex-wrap gap-x-2 gap-y-1 text-[8px] text-neutral-400 border-t border-[#242F41]/35 pt-1.5 mt-1">
            {seriesKeys.map((key, i) => (
              <div key={key} className="flex items-center gap-1">
                <div
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: LINE_COLORS[i % LINE_COLORS.length] }}
                />
                <span>{key.replace(/([A-Z])/g, " $1").trim()}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </GlassCard>
  );
}

export function WeeklyComplaintVolume() {
  const raw = useLocalStorageData<Record<string, unknown>[]>("Weekly_Volume", []);

  const xAxisKey = useMemo(() => inferXAxisKey(raw), [raw]);
  const seriesKeys = useMemo(() => inferDataSeriesKeys(raw, xAxisKey), [raw, xAxisKey]);
  const data = useMemo(() => {
    const normalized = normalizeData(raw, xAxisKey, seriesKeys);
    return normalized.map((item) => {
      const val = item[xAxisKey];
      const label = typeof val === "string" ? val.substring(0, 3) : String(val);
      return { ...item, [xAxisKey]: label };
    });
  }, [raw, xAxisKey, seriesKeys]);
  const isEmpty = raw.length === 0;

  return (
    <GlassCard id="weekly-volume-card" className="p-4 flex flex-col justify-between h-[240px]" hover={true}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-neutral-400 tracking-wider uppercase">Weekly Volume</span>
        <div className="flex items-center gap-3">
          {seriesKeys.map((key, i) => (
            <div key={key} className="flex items-center gap-1">
              <div
                className="w-2 h-2 rounded"
                style={{ backgroundColor: LINE_COLORS[i % LINE_COLORS.length] }}
              />
              <span className="text-[8px] text-neutral-400 font-bold uppercase">
                {key.replace(/([A-Z])/g, " $1").trim()}
              </span>
            </div>
          ))}
          <BarChart2 className="h-4 w-4 text-cyan-400" />
        </div>
      </div>
      {isEmpty ? (
        <div className="flex-1 flex items-center justify-center text-[10px] text-neutral-500">
          No data uploaded
        </div>
      ) : (
        <div className="flex-1 w-full h-[150px]">
          <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 15, left: -10, bottom: 5 }}>
            <XAxis dataKey={xAxisKey} stroke="#4b5563" fontSize={8} tickLine={false} />
            <YAxis stroke="#4b5563" fontSize={8} tickLine={false} width={25} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "rgba(19, 25, 38, 0.95)",
                  borderColor: "#242F41",
                  borderRadius: "8px",
                  fontSize: "10px",
                  color: "white"
                }}
              />
              {seriesKeys.map((key, i) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={LINE_COLORS[i % LINE_COLORS.length]}
                  radius={[4, 4, 4, 4]}
                  name={key.replace(/([A-Z])/g, " $1").trim()}
                  isAnimationActive={false}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </GlassCard>
  );
}

interface TelemetryCalendarProps {
  selectedDate: string | null;
  onSelectDate: (dateStr: string | null) => void;
}

export function TelemetryCalendar({ selectedDate, onSelectDate }: TelemetryCalendarProps) {
  const dailyCounts = useGlobalLocalStorageData<Record<string, number>>("dailyCounts", {});

  const [currentDate, setCurrentDate] = useState(() => {
    if (selectedDate) {
      const parts = selectedDate.split("-");
      if (parts.length === 2) {
        return new Date(Number(parts[0]), Number(parts[1]) - 1, 1);
      }
      const parsed = new Date(selectedDate);
      if (!isNaN(parsed.getTime())) return parsed;
    }
    return new Date();
  });

  useEffect(() => {
    if (selectedDate) {
      const parts = selectedDate.split("-");
      if (parts.length === 2) {
        setCurrentDate(new Date(Number(parts[0]), Number(parts[1]) - 1, 1));
      } else {
        const parsed = new Date(selectedDate);
        if (!isNaN(parsed.getTime())) {
          setCurrentDate(parsed);
        }
      }
    }
  }, [selectedDate]);

  const isMonthSelected = selectedDate && selectedDate.length === 7;

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth();

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const startDayOffset = new Date(year, month, 1).getDay();

  const monthsList = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const handlePrevMonth = () => {
    if (year > 2020 || (year === 2020 && month > 0)) {
      const newDate = new Date(year, month - 1, 1);
      setCurrentDate(newDate);
      if (isMonthSelected) {
        const ny = newDate.getFullYear();
        const nm = (newDate.getMonth() + 1).toString().padStart(2, "0");
        onSelectDate(`${ny}-${nm}`);
      }
    }
  };

  const handleNextMonth = () => {
    if (year < currentYear || (year === currentYear && month < currentMonth)) {
      const newDate = new Date(year, month + 1, 1);
      setCurrentDate(newDate);
      if (isMonthSelected) {
        const ny = newDate.getFullYear();
        const nm = (newDate.getMonth() + 1).toString().padStart(2, "0");
        onSelectDate(`${ny}-${nm}`);
      }
    }
  };

  const isPrevDisabled = year === 2020 && month === 0;
  const isNextDisabled = year === currentYear && month === currentMonth;

  const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  // Generate grid days
  const gridCells = [];
  for (let i = 0; i < startDayOffset; i++) {
    gridCells.push(null);
  }
  for (let d = 1; d <= daysInMonth; d++) {
    gridCells.push(d);
  }

  const handleDayClick = (day: number) => {
    if (isMonthSelected) return;
    const dateStr = `${year}-${(month + 1).toString().padStart(2, "0")}-${day.toString().padStart(2, "0")}`;
    if (selectedDate === dateStr) {
      onSelectDate(null);
    } else {
      onSelectDate(dateStr);
    }
  };

  const handleSelectMonth = () => {
    const monthStr = `${year}-${(month + 1).toString().padStart(2, "0")}`;
    if (selectedDate === monthStr) {
      onSelectDate(null);
    } else {
      onSelectDate(monthStr);
    }
  };

  return (
    <GlassCard id="telemetry-calendar-card" className="p-4 flex flex-col justify-between h-[280px]" hover={true}>
      <div className="flex items-center justify-between mb-2 pb-1 border-b border-[#242F41]/45">
        <span className="text-xs font-semibold text-neutral-400 tracking-wider uppercase">
          Ticket Calendar
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevMonth}
            disabled={isPrevDisabled}
            className={`p-1 rounded bg-[#1f2937]/50 hover:bg-[#374151]/50 border border-[#374151]/30 transition-colors ${
              isPrevDisabled ? "opacity-30 cursor-not-allowed" : "cursor-pointer"
            }`}
          >
            <ChevronLeft className="h-3 w-3 text-cyan-400" />
          </button>
          <span className="text-[10px] font-bold text-neutral-200 min-w-[95px] text-center uppercase tracking-wider">
            {monthsList[month]} {year}
          </span>
          <button
            onClick={handleNextMonth}
            disabled={isNextDisabled}
            className={`p-1 rounded bg-[#1f2937]/50 hover:bg-[#374151]/50 border border-[#374151]/30 transition-colors ${
              isNextDisabled ? "opacity-30 cursor-not-allowed" : "cursor-pointer"
            }`}
          >
            <ChevronRight className="h-3 w-3 text-cyan-400" />
          </button>
          <button
            onClick={handleSelectMonth}
            className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border transition-colors ${
              isMonthSelected
                ? "bg-cyan-500/10 border-cyan-400 text-cyan-300"
                : "bg-[#1f2937]/50 border-[#374151]/30 text-neutral-400 hover:text-white hover:bg-[#374151]/50"
            }`}
          >
            <CalendarRange className="h-3 w-3" />
            Month
          </button>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center mt-1">
        {/* Weekdays header */}
        <div className="grid grid-cols-7 gap-1 text-[8px] font-bold text-neutral-400 text-center uppercase tracking-wider mb-1.5">
          {weekdays.map(d => (
            <div key={d} className="w-[28px] py-0.5">{d}</div>
          ))}
        </div>

        {/* Calendar days grid */}
        <div className="grid grid-cols-7 gap-1">
          {gridCells.map((day, idx) => {
            if (day === null) {
              return <div key={`empty-${idx}`} className="w-[28px] h-[24px]" />;
            }

            const dateStr = `${year}-${(month + 1).toString().padStart(2, "0")}-${day.toString().padStart(2, "0")}`;
            const isSelected = !isMonthSelected && selectedDate === dateStr;
            const count = dailyCounts[dateStr] || 0;

            let dotColorClass = "";
            if (count > 10) {
              dotColorClass = "bg-[#FF0844]";
            } else if (count >= 5 && count <= 10) {
              dotColorClass = "bg-[#00F5A0]";
            }

            return (
              <button
                key={`day-${day}`}
                onClick={() => handleDayClick(day)}
                className={`relative flex items-center justify-center w-[28px] h-[24px] rounded transition-all duration-200 group ${
                  isSelected
                    ? "bg-cyan-500/10 border border-cyan-400 text-cyan-300 shadow-[0_0_8px_rgba(34,211,238,0.2)]"
                    : isMonthSelected
                      ? "bg-[#131926]/20 border border-cyan-400/10 text-neutral-500"
                      : "bg-[#131926]/40 hover:bg-neutral-800/40 border border-[#242F41]/30 text-neutral-300 hover:text-white"
                }`}
              >
                <span className="text-[9px] font-bold">{day}</span>
                {dotColorClass && (
                  <div
                    className={`w-1 h-1 rounded-full absolute top-0.5 right-0.5 ${dotColorClass} `}
                  />
                )}
                <div className="absolute bottom-full mb-1 bg-[#131926] border border-[#242F41] rounded px-1.5 py-0.5 text-[7px] text-white hidden group-hover:block whitespace-nowrap z-30 shadow-2xl">
                  <span className="font-bold">{dateStr}</span>: {count} complaints
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="text-[8px] text-neutral-500 border-t border-[#242F41]/35 pt-1.5 flex justify-between mt-2 w-full">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-[#FF0844]" />
            <span>High (&gt;10/day)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00F5A0]" />
            <span>Avg (5-10/day)</span>
          </div>
        </div>
        <span>{isMonthSelected ? "Month selected" : "Select day to filter"}</span>
      </div>
    </GlassCard>
  );
}
