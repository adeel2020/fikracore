"use client";

import { useState, useMemo, useDeferredValue } from "react";
import { ComplaintTelemetry } from "@/lib/api/qna";

const ITEMS_PER_PAGE = 15;

export function useTelemetryProcessor(telemetryList: ComplaintTelemetry[]) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTarget, setSelectedTarget] = useState("all");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [sortField, setSortField] = useState<keyof ComplaintTelemetry>("time_reported");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [currentPage, setCurrentPage] = useState(1);

  // Use deferred search query to offload CPU-heavy filtering from the typing thread
  const deferredSearchQuery = useDeferredValue(searchQuery);

  // Extract unique filter choices
  const assignmentTargets = useMemo(() => {
    if (!Array.isArray(telemetryList)) return [];
    return Array.from(new Set(telemetryList.map(t => t?.assignment_target).filter(Boolean)));
  }, [telemetryList]);
  
  const reassignmentCategories = useMemo(() => {
    if (!Array.isArray(telemetryList)) return [];
    return Array.from(new Set(telemetryList.map(t => t?.reassignment_category).filter(Boolean)));
  }, [telemetryList]);

  // Filter & Search Logic using deferred search query
  const filteredTelemetry = useMemo(() => {
    if (!Array.isArray(telemetryList)) return [];
    return telemetryList.filter((item) => {
      if (!item) return false;
      const compNum = item.complaint_number || "";
      const issueSum = item.issue_summary || "";
      const rawComp = item.raw_complaint || "";
      const assignTarget = item.assignment_target || "";
      const reassignCat = item.reassignment_category || "";

      const matchesSearch =
        compNum.toLowerCase().includes(deferredSearchQuery.toLowerCase()) ||
        issueSum.toLowerCase().includes(deferredSearchQuery.toLowerCase()) ||
        rawComp.toLowerCase().includes(deferredSearchQuery.toLowerCase());

      const matchesTarget = selectedTarget === "all" || assignTarget === selectedTarget;
      const matchesCategory = selectedCategory === "all" || reassignCat === selectedCategory;

      return matchesSearch && matchesTarget && matchesCategory;
    });
  }, [telemetryList, deferredSearchQuery, selectedTarget, selectedCategory]);

  // Sort Logic
  const sortedTelemetry = useMemo(() => {
    return [...filteredTelemetry].sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (aVal === null || aVal === undefined) return sortDirection === "asc" ? -1 : 1;
      if (bVal === null || bVal === undefined) return sortDirection === "asc" ? 1 : -1;

      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDirection === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      } else {
        return sortDirection === "asc"
          ? (aVal as number) - (bVal as number)
          : (bVal as number) - (aVal as number);
      }
    });
  }, [filteredTelemetry, sortField, sortDirection]);

  // Pagination calculations
  const totalItems = sortedTelemetry.length;
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE) || 1;
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const startIndex = (safeCurrentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  
  const paginatedTelemetry = useMemo(() => {
    return sortedTelemetry.slice(startIndex, endIndex);
  }, [sortedTelemetry, startIndex, endIndex]);

  const handleSort = (field: keyof ComplaintTelemetry) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
    setCurrentPage(1);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  };

  const handleTargetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedTarget(e.target.value);
    setCurrentPage(1);
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCategory(e.target.value);
    setCurrentPage(1);
  };

  const resetFilters = () => {
    setSearchQuery("");
    setSelectedTarget("all");
    setSelectedCategory("all");
    setCurrentPage(1);
  };

  return {
    searchQuery,
    setSearchQuery,
    selectedTarget,
    setSelectedTarget,
    selectedCategory,
    setSelectedCategory,
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
  };
}
