"use client";

import React from "react";
import { Search, Download, SlidersHorizontal, ArrowUpDown, RefreshCw, ChevronLeft, ChevronRight } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { ComplaintTelemetry } from "@/lib/api/qna";
import { useTelemetryProcessor } from "../hooks/useTelemetryProcessor";

interface TelemetryLedgerProps {
  telemetryList: ComplaintTelemetry[];
  loading: boolean;
}

const ITEMS_PER_PAGE = 15;

export const TelemetryLedger = React.memo(function TelemetryLedger({ telemetryList, loading }: TelemetryLedgerProps) {
  const {
    searchQuery,
    selectedTarget,
    selectedCategory,
    sortField,
    sortDirection,
    currentPage,
    setCurrentPage,
    handleSort,
    handleSearchChange,
    handleTargetChange,
    handleCategoryChange,
    resetFilters,
    assignmentTargets,
    reassignmentCategories,
    sortedTelemetry,
    paginatedTelemetry,
    totalItems,
    totalPages,
    startIndex,
    endIndex,
    safeCurrentPage
  } = useTelemetryProcessor(telemetryList);

  const formatDubaiTime = (timestamp: number) => {
    if (!timestamp) return "-";
    return new Date(timestamp * 1000).toLocaleString("en-US", {
      timeZone: "Asia/Dubai",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false
    });
  };

  const exportToCSV = () => {
    if (sortedTelemetry.length === 0) return;
    const headers = [
      "Complaint Number",
      "Time Reported (Dubai GMT+4)",
      "Issue Summary",
      "Assignment Target",
      "Assignment Queue",
      "Reassignment Category",
      "Resolution Category",
      "Raw Complaint"
    ];

    const csvRows = sortedTelemetry.map((t) => [
      t.complaint_number,
      formatDubaiTime(t.time_reported),
      `"${t.issue_summary.replace(/"/g, '""')}"`,
      t.assignment_target,
      t.assignment_queue || "-",
      t.reassignment_category,
      t.resolution_category,
      `"${t.raw_complaint.replace(/"/g, '""')}"`
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...csvRows.map((r) => r.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `complaints_telemetry_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderPageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 5;
    let start = Math.max(1, safeCurrentPage - Math.floor(maxVisiblePages / 2));
    let end = Math.min(totalPages, start + maxVisiblePages - 1);

    if (end - start + 1 < maxVisiblePages) {
      start = Math.max(1, end - maxVisiblePages + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => setCurrentPage(i)}
          className={`w-7 h-7 flex items-center justify-center rounded text-[11px] font-mono font-bold transition-all border ${
            safeCurrentPage === i
              ? "bg-cyan-500/20 text-cyan-400 border-cyan-500/35 shadow-lg"
              : "bg-transparent text-neutral-400 border-[#242F41]/65 hover:text-white hover:border-neutral-600"
          }`}
        >
          {i}
        </button>
      );
    }
    return pages;
  };

  return (
    <GlassCard className="flex-1 p-4 rounded-xl flex flex-col min-h-[500px] z-10" hover={false}>
      {/* Controls bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 mb-4">
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Search box */}
          <div className="relative w-full sm:w-[220px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-neutral-500" />
            <input
              type="text"
              placeholder="Search complaint log..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="w-full pl-8 pr-3 py-1.5 text-xs text-white placeholder-neutral-500 bg-black/40 border border-[#242F41] rounded-lg focus:outline-none focus:border-cyan-500/60"
            />
          </div>

          {/* Filter target */}
          <div className="relative">
            <select
              value={selectedTarget}
              onChange={handleTargetChange}
              className="appearance-none bg-black/40 border border-[#242F41] text-xs text-neutral-300 rounded-lg pl-3 pr-8 py-1.5 focus:outline-none focus:border-cyan-500/60 cursor-pointer"
            >
              <option value="all">All Targets</option>
              {assignmentTargets.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <SlidersHorizontal className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-neutral-500 pointer-events-none" />
          </div>

          {/* Filter category */}
          <div className="relative">
            <select
              value={selectedCategory}
              onChange={handleCategoryChange}
              className="appearance-none bg-black/40 border border-[#242F41] text-xs text-neutral-300 rounded-lg pl-3 pr-8 py-1.5 focus:outline-none focus:border-cyan-500/60 cursor-pointer"
            >
              <option value="all">All Categories</option>
              {reassignmentCategories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <SlidersHorizontal className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-neutral-500 pointer-events-none" />
          </div>

          {/* Clear filters button */}
          {(searchQuery !== "" || selectedTarget !== "all" || selectedCategory !== "all") && (
            <button
              onClick={resetFilters}
              className="text-neutral-400 hover:text-white text-[11px] underline"
            >
              Reset
            </button>
          )}
        </div>

        {/* Export & total count display */}
        <div className="flex items-center justify-between md:justify-end gap-4">
          <span className="text-[11px] text-neutral-400">
            Found <span className="font-bold text-cyan-400">{sortedTelemetry.length}</span> rows
          </span>

          <Button
            onClick={exportToCSV}
            disabled={sortedTelemetry.length === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25 disabled:opacity-50 disabled:pointer-events-none transition-all duration-300"
          >
            <Download className="h-3.5 w-3.5" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Interactive Excel style spreadsheet */}
      <div className="flex-1 overflow-x-auto border border-[#242F41] rounded-lg bg-black/30 custom-scrollbar">
        <table className="w-full text-left border-collapse text-xs select-none">
          <thead>
            <tr className="bg-[#131926]/90 border-b border-[#242F41] text-neutral-400 font-semibold uppercase tracking-wider text-[10px]">
              <th
                className="p-3 border-r border-[#242F41] cursor-pointer hover:bg-white/5 transition-colors w-[150px]"
                onClick={() => handleSort("complaint_number")}
              >
                <div className="flex items-center justify-between">
                  <span>Complaint Number</span>
                  <ArrowUpDown className="h-3 w-3 text-neutral-500" />
                </div>
              </th>
              <th
                className="p-3 border-r border-[#242F41] cursor-pointer hover:bg-white/5 transition-colors w-[180px]"
                onClick={() => handleSort("time_reported")}
              >
                <div className="flex items-center justify-between">
                  <span>Time Reported (Dubai)</span>
                  <ArrowUpDown className="h-3 w-3 text-neutral-500" />
                </div>
              </th>
              <th className="p-3 border-r border-[#242F41] w-[250px]">Issue Summary</th>
              <th
                className="p-3 border-r border-[#242F41] cursor-pointer hover:bg-white/5 transition-colors w-[160px]"
                onClick={() => handleSort("assignment_target")}
              >
                <div className="flex items-center justify-between">
                  <span>Assignment Target</span>
                  <ArrowUpDown className="h-3 w-3 text-neutral-500" />
                </div>
              </th>
              <th
                className="p-3 border-r border-[#242F41] cursor-pointer hover:bg-white/5 transition-colors w-[130px]"
                onClick={() => handleSort("assignment_queue")}
              >
                <div className="flex items-center justify-between">
                  <span>Queue</span>
                  <ArrowUpDown className="h-3 w-3 text-neutral-500" />
                </div>
              </th>
              <th
                className="p-3 border-r border-[#242F41] cursor-pointer hover:bg-white/5 transition-colors w-[160px]"
                onClick={() => handleSort("reassignment_category")}
              >
                <div className="flex items-center justify-between">
                  <span>Reassignment Category</span>
                  <ArrowUpDown className="h-3 w-3 text-neutral-500" />
                </div>
              </th>
              <th className="p-3 border-r border-[#242F41] w-[180px]">Resolution Category</th>
              <th className="p-3">Raw complaint</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#242F41]/60">
            {loading ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-neutral-500">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <RefreshCw className="h-5 w-5 text-cyan-400" />
                    <span>Fetching complaint logs...</span>
                  </div>
                </td>
              </tr>
            ) : paginatedTelemetry.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-neutral-500 italic">
                  No complaint records found matching current query filters.
                </td>
              </tr>
            ) : (
              paginatedTelemetry.map((row) => (
                <tr
                  key={row.id}
                  className="hover:bg-cyan-500/5 hover:text-white text-neutral-300 font-mono transition-colors border-b border-[#242F41]/30"
                >
                  <td className="p-3 border-r border-[#242F41]/40 font-semibold text-cyan-400 whitespace-nowrap">
                    {row.complaint_number}
                  </td>
                  <td className="p-3 border-r border-[#242F41]/40 text-neutral-400 whitespace-nowrap">
                    {formatDubaiTime(row.time_reported)}
                  </td>
                  <td className="p-3 border-r border-[#242F41]/40 font-sans truncate max-w-[250px]" title={row.issue_summary}>
                    {row.issue_summary}
                  </td>
                  <td className="p-3 border-r border-[#242F41]/40 font-sans font-semibold text-neutral-200">
                    {row.assignment_target}
                  </td>
                  <td className="p-3 border-r border-[#242F41]/40 text-center text-amber-400 font-bold whitespace-nowrap">
                    {row.assignment_queue || "-"}
                  </td>
                  <td className="p-3 border-r border-[#242F41]/40 font-sans text-neutral-300">
                    {row.reassignment_category}
                  </td>
                  <td className="p-3 border-r border-[#242F41]/40 font-sans text-neutral-300">
                    {row.resolution_category}
                  </td>
                  <td className="p-3 font-sans truncate max-w-[300px]" title={row.raw_complaint}>
                    {row.raw_complaint}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-[#242F41]/45 shrink-0">
          <span className="text-[11px] text-neutral-400">
            Showing <span className="font-bold text-neutral-300">{startIndex + 1}</span> to{" "}
            <span className="font-bold text-neutral-300">{Math.min(endIndex, totalItems)}</span> of{" "}
            <span className="font-bold text-neutral-300">{totalItems}</span> entries
          </span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setCurrentPage(1)}
              disabled={safeCurrentPage === 1}
              className="px-2 py-1 rounded bg-[#131926]/40 border border-[#242F41]/65 text-[10px] font-bold uppercase tracking-wider text-neutral-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
            >
              First
            </button>
            <button
              onClick={() => setCurrentPage((prev: number) => Math.max(1, prev - 1))}
              disabled={safeCurrentPage === 1}
              className="w-7 h-7 flex items-center justify-center rounded bg-[#131926]/40 border border-[#242F41]/65 text-neutral-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>

            {renderPageNumbers()}

            <button
              onClick={() => setCurrentPage((prev: number) => Math.min(totalPages, prev + 1))}
              disabled={safeCurrentPage === totalPages}
              className="w-7 h-7 flex items-center justify-center rounded bg-[#131926]/40 border border-[#242F41]/65 text-neutral-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => setCurrentPage(totalPages)}
              disabled={safeCurrentPage === totalPages}
              className="px-2 py-1 rounded bg-[#131926]/40 border border-[#242F41]/65 text-[10px] font-bold uppercase tracking-wider text-neutral-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none transition-colors"
            >
              Last
            </button>
          </div>
        </div>
      )}
    </GlassCard>
  );
});
