function val(row: any, ...keys: string[]): string {
  for (const k of keys) {
    const v = row[k];
    if (v !== undefined && v !== null && v !== "") return String(v).trim();
  }
  return "";
}

function num(row: any, ...keys: string[]): number {
  for (const k of keys) {
    const v = row[k];
    if (v !== undefined && v !== null && v !== "") return Number(v) || 0;
  }
  return 0;
}

export function aggregateRawTickets(rows: any[]) {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

  // --- First pass: discover all unique dimension values ---
  const queueSet = new Set<string>();
  const categorySet = new Set<string>();
  const colorGroupSet = new Set<string>();
  const reassignToSet = new Set<string>();
  const rejectReasonSet = new Set<string>();
  const resolutionReasonSet = new Set<string>();
  const countrySet = new Set<string>();
  const roamingCountries = new Set<string>();
  const reasonSet = new Set<string>();

  rows.forEach(r => {
    const q = val(r, "Ticket_Queue", "Queue");
    if (q) queueSet.add(q);

    const cat = val(r, "Issue_Category", "Category");
    if (cat) categorySet.add(cat);

    const cg = val(r, "Color_Group").toLowerCase();
    if (cg) colorGroupSet.add(cg);

    const status = val(r, "Ticket_Status", "Status");
    if (status === "Reassigned") {
      const rt = val(r, "Reassigned_To");
      if (rt) reassignToSet.add(rt);
    }
    if (status === "Rejected") {
      const rr = val(r, "Rejection_Reason");
      if (rr) rejectReasonSet.add(rr);
    }
    if (status === "Resolved") {
      const res = val(r, "Resolution_Reason", "Resolution_reason");
      if (res) resolutionReasonSet.add(res);
    }

    const dateParts = (r.Create_Date || "").split("-");
    let monthIdx = -1;
    if (dateParts.length === 3) {
      const dt = new Date(Number(dateParts[0]), Number(dateParts[1]) - 1, Number(dateParts[2]));
      if (!isNaN(dt.getTime())) {
        monthIdx = dt.getMonth();
      }
    }

    const country = val(r, "Country");
    if (country) {
      countrySet.add(country);
      if (monthIdx >= 0 && val(r, "Issue_Category", "Category") === "Roaming") {
        roamingCountries.add(country);
      }
    }

    const reason = val(r, "Reassignment_Reason");
    if (reason) {
      reasonSet.add(reason);
    }
  });

  const sortedQueues = [...queueSet].sort();
  const sortedCategories = [...categorySet].sort();
  const sortedColors = [...colorGroupSet].sort();
  const sortedReassignments = [...reassignToSet].sort();
  const sortedRejections = [...rejectReasonSet].sort();
  const sortedResolutions = [...resolutionReasonSet].sort();
  const sortedCountries = [...countrySet].sort();
  const sortedRoamingCountries = [...roamingCountries].sort();
  const sortedReasons = [...reasonSet].sort();

  // --- Initialize maps dynamically ---
  const monthlyDist = months.map(m => {
    const entry: Record<string, any> = { month: m };
    sortedColors.forEach(c => { entry[c] = 0; });
    return entry;
  });

  const queueTimesMap: Record<string, { closed: number; total: number; sumTime: number; complianceCount: number }> = {};
  sortedQueues.forEach(q => {
    queueTimesMap[q] = { closed: 0, total: 0, sumTime: 0, complianceCount: 0 };
  });

  const issueCatsMap: Record<string, { tickets: number; metPctCount: number; sumTime: number }> = {};
  sortedCategories.forEach(c => {
    issueCatsMap[c] = { tickets: 0, metPctCount: 0, sumTime: 0 };
  });

  const reasonsMap: Record<string, { tickets: number; metPctCount: number; sumTime: number }> = {};
  sortedReasons.forEach(re => {
    reasonsMap[re] = { tickets: 0, metPctCount: 0, sumTime: 0 };
  });

  const weeklyVolume = weekdays.map(d => {
    const entry: Record<string, any> = { day: d };
    sortedColors.forEach(c => { entry[c] = 0; });
    return entry;
  });

  const dates30d = Array.from({ length: 30 }, (_, i) => `Day ${i + 1}`);
  const tt30dMap: Record<string, { resolved: number; reassigned: number; rejected: number; sumTime: number; complianceCount: number; total: number }> = {};
  dates30d.forEach(d => {
    tt30dMap[d] = { resolved: 0, reassigned: 0, rejected: 0, sumTime: 0, complianceCount: 0, total: 0 };
  });

  const reassignmentsMap: Record<string, number> = {};
  sortedReassignments.forEach(r => { reassignmentsMap[r] = 0; });

  const rejectionsMap: Record<string, number> = {};
  sortedRejections.forEach(r => { rejectionsMap[r] = 0; });

  const resolutionsMap: Record<string, number> = {};
  sortedResolutions.forEach(r => { resolutionsMap[r] = 0; });

  const roamingMonths = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const roamingMap: Record<string, Record<string, number>> = {};
  roamingMonths.forEach(m => {
    roamingMap[m] = {};
    sortedRoamingCountries.forEach(c => { roamingMap[m][c] = 0; });
  });

  const queueWarnings: Record<string, { initials: string; queue: string; count: number; categories: Set<string> }> = {};
  sortedQueues.forEach(q => {
    queueWarnings[q] = { initials: q, queue: q, count: 0, categories: new Set() };
  });

  const dailyCounts: Record<string, number> = {};
  const weekdayDatesMap: Record<string, Set<string>> = {
    "Sunday": new Set(),
    "Monday": new Set(),
    "Tuesday": new Set(),
    "Wednesday": new Set(),
    "Thursday": new Set(),
    "Friday": new Set(),
    "Saturday": new Set()
  };

  // Determine latest month across all rows (for Trouble_Tickets_30d)
  const latestMonthIdx = Math.max(
    ...rows.map(r => {
      const parts = (r.Create_Date || "").split("-");
      if (parts.length === 3) {
        const dt = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        if (!isNaN(dt.getTime())) return dt.getMonth();
      }
      return -1;
    }),
    -1
  );

  // --- Second pass: aggregate ---
  rows.forEach(r => {
    const dateStr = r.Create_Date || "";
    if (dateStr) {
      dailyCounts[dateStr] = (dailyCounts[dateStr] || 0) + 1;
    }
    const dateParts = dateStr.split("-");
    let monthIdx = -1;
    let dayVal = -1;
    let weekdayStr = "";

    if (dateParts.length === 3) {
      const dt = new Date(Number(dateParts[0]), Number(dateParts[1]) - 1, Number(dateParts[2]));
      if (!isNaN(dt.getTime())) {
        monthIdx = dt.getMonth();
        dayVal = dt.getDate();
        weekdayStr = weekdays[dt.getDay()];
        weekdayDatesMap[weekdayStr].add(dateStr);
      }
    }

    const queue = val(r, "Ticket_Queue", "Queue");
    const status = val(r, "Ticket_Status", "Status");
    const category = val(r, "Issue_Category", "Category");
    const colorGroup = val(r, "Color_Group").toLowerCase();
    const responseTime = num(r, "Average_Time_spent_in_Mins", "First_Response_Time_Mins");
    const metSla = responseTime <= 120;

    // Monthly distribution by color group
    if (monthIdx >= 0 && monthIdx < 12 && colorGroup && monthlyDist[monthIdx][colorGroup] !== undefined) {
      monthlyDist[monthIdx][colorGroup]++;
    }

    // Queue times
    if (queue && queueTimesMap[queue] !== undefined) {
      queueTimesMap[queue].total++;
      if (status === "Resolved") {
        queueTimesMap[queue].closed++;
      }
      queueTimesMap[queue].sumTime += responseTime;
      if (metSla) {
        queueTimesMap[queue].complianceCount++;
      }
    }

    // Issue categories
    if (category && issueCatsMap[category] !== undefined) {
      issueCatsMap[category].tickets++;
      issueCatsMap[category].sumTime += responseTime;
      if (metSla) {
        issueCatsMap[category].metPctCount++;
      }
    }

    // Reassignment reasons
    const reason = val(r, "Reassignment_Reason");
    if (reason && reasonsMap[reason] !== undefined) {
      reasonsMap[reason].tickets++;
      reasonsMap[reason].sumTime += responseTime;
      if (metSla) {
        reasonsMap[reason].metPctCount++;
      }
    }

    // Weekly volume
    if (weekdayStr && colorGroup) {
      const matchedDay = weeklyVolume.find(d => d.day === weekdayStr);
      if (matchedDay && matchedDay[colorGroup] !== undefined) {
        matchedDay[colorGroup]++;
      }
    }

    // Trouble tickets 30 days (latest month only)
    if (latestMonthIdx >= 0 && monthIdx === latestMonthIdx && dayVal >= 1 && dayVal <= 30) {
      const bucket = `Day ${dayVal}`;

      if (bucket && tt30dMap[bucket]) {
        tt30dMap[bucket].total++;
        tt30dMap[bucket].sumTime += responseTime;
        if (metSla) {
          tt30dMap[bucket].complianceCount++;
        }
        if (status === "Resolved") tt30dMap[bucket].resolved++;
        else if (status === "Reassigned") tt30dMap[bucket].reassigned++;
        else if (status === "Rejected") tt30dMap[bucket].rejected++;
      }
    }

    // Reassignments
    if (status === "Reassigned") {
      const reassignedTo = (r.Reassigned_To || "").trim();
      if (reassignedTo && reassignmentsMap[reassignedTo] !== undefined) {
        reassignmentsMap[reassignedTo]++;
      }
    }

    // Rejections
    if (status === "Rejected") {
      const rejectionReason = (r.Rejection_Reason || "").trim();
      if (rejectionReason && rejectionsMap[rejectionReason] !== undefined) {
        rejectionsMap[rejectionReason]++;
      }
    }

    // Resolutions
    if (status === "Resolved") {
      const resolutionReason = val(r, "Resolution_Reason", "Resolution_reason").trim();
      if (resolutionReason && resolutionsMap[resolutionReason] !== undefined) {
        resolutionsMap[resolutionReason]++;
      }
    }

    // Roaming by country (only Issue_Category === "Roaming")
    if (monthIdx >= 0 && monthIdx < 12 && category === "Roaming") {
      const monthName = months[monthIdx];
      const country = (r.Country || "").trim();
      if (country && roamingMap[monthName] && roamingMap[monthName][country] !== undefined) {
        roamingMap[monthName][country]++;
      }
    }

    // Queue warnings
    if (queue && queueWarnings[queue] !== undefined) {
      if (!metSla || status !== "Resolved") {
        queueWarnings[queue].count++;
        if (category) {
          queueWarnings[queue].categories.add(category);
        }
      }
    }
  });

  // --- Build output structures ---
  const nocQueueTimes = sortedQueues.map(k => {
    const q = queueTimesMap[k];
    const avg = q.total > 0 ? Math.round(q.sumTime / q.total) : 0;
    const compliance = q.total > 0 ? Math.round((q.complianceCount / q.total) * 100) : 0;
    return {
      name: `${k} Queue`,
      closed: q.closed,
      total: q.total,
      avg: `${avg} mins`,
      compliance
    };
  });

  const grandTotalIssues = sortedCategories.reduce((acc, c) => acc + issueCatsMap[c].tickets, 0);
  const firstResponseIssues = sortedCategories.map(k => {
    const item = issueCatsMap[k];
    const metPct = item.tickets > 0 ? Math.round((item.metPctCount / item.tickets) * 100) : 0;
    const avgTime = item.tickets > 0 ? Math.round(item.sumTime / item.tickets) : 0;
    const share = grandTotalIssues > 0 ? Math.round((item.tickets / grandTotalIssues) * 100) : 0;
    return {
      name: k,
      tickets: `${item.tickets} (${share}%)`,
      count: item.tickets,
      share,
      metPct,
      avgTime: `${avgTime} min`,
      missPct: 100 - metPct
    };
  });

  const grandTotalReasons = sortedReasons.reduce((acc, re) => acc + reasonsMap[re].tickets, 0);
  const reassignmentReasonsList = sortedReasons.map(k => {
    const item = reasonsMap[k];
    const metPct = item.tickets > 0 ? Math.round((item.metPctCount / item.tickets) * 100) : 0;
    const avgTime = item.tickets > 0 ? Math.round(item.sumTime / item.tickets) : 0;
    const share = grandTotalReasons > 0 ? Math.round((item.tickets / grandTotalReasons) * 100) : 0;
    return {
      name: k,
      tickets: `${item.tickets} (${share}%)`,
      count: item.tickets,
      share,
      metPct,
      avgTime: `${avgTime} min`,
      missPct: 100 - metPct
    };
  });

  const troubleTickets30d = dates30d.map(k => {
    const item = tt30dMap[k];
    const rate = item.total > 0 ? Math.round((item.complianceCount / item.total) * 1000) / 10 : 0;
    return {
      date: k,
      resolved: item.resolved,
      reassigned: item.reassigned,
      rejected: item.rejected,
      rate
    };
  });

  const reassignmentsList = sortedReassignments
    .map(k => ({ Metric_Type: "Reassignment", Name: k, Tickets_Count: reassignmentsMap[k] }))
    .sort((a, b) => b.Tickets_Count - a.Tickets_Count)
    .slice(0, 5);
  const rejectionsList = sortedRejections
    .map(k => ({ Metric_Type: "Rejection_Reason", Name: k, Tickets_Count: rejectionsMap[k] }))
    .sort((a, b) => b.Tickets_Count - a.Tickets_Count)
    .slice(0, 5);
  const resolutionsList = sortedResolutions
    .map(k => ({ Metric_Type: "Resolution_Reason", Name: k, Tickets_Count: resolutionsMap[k] }))
    .sort((a, b) => b.Tickets_Count - a.Tickets_Count)
    .slice(0, 5);
  const reassignmentsRejections = [...reassignmentsList, ...rejectionsList, ...resolutionsList];

  const roamingByCountry = sortedRoamingCountries.length > 0
    ? roamingMonths.map(k => ({ day: k, ...roamingMap[k] }))
    : [];

  // Scale weekly volume to weekday averages
  const scaledWeeklyVolume = weeklyVolume.map(d => {
    const entry: Record<string, any> = { day: d.day };
    const occurrences = weekdayDatesMap[d.day].size || 1;
    sortedColors.forEach(c => {
      entry[c] = Math.round((d[c] || 0) / occurrences);
    });
    return entry;
  });

  const grandTotalQueues = sortedQueues.reduce((acc, q) => acc + queueTimesMap[q].total, 0);
  const nocTicketsDistribution = sortedQueues
    .map(k => {
      const item = queueTimesMap[k];
      const pct = grandTotalQueues > 0 ? Math.round((item.total / grandTotalQueues) * 100) : 0;
      return { Queue: k, Value: item.total, Percentage: pct };
    })
    .sort((a, b) => b.Value - a.Value);

  const uaeRegionalHotspots: { Hotspot_Name: string; Tickets_Count: number }[] = [];
  const hotspotsMap: Record<string, number> = {};
  rows.forEach(r => {
    const hotspot = (r.Hotspot_Name || "").trim();
    if (hotspot) {
      hotspotsMap[hotspot] = (hotspotsMap[hotspot] || 0) + 1;
    }
  });
  Object.keys(hotspotsMap).forEach(k => {
    uaeRegionalHotspots.push({ Hotspot_Name: k, Tickets_Count: hotspotsMap[k] });
  });

  const cardTemplates = sortedQueues.map((q, idx) => {
    const colorSchemes = [
      { bg: "bg-gradient-to-br from-[#E01A8A]/25 to-[#FF2A5F]/10 border-[#E01A8A]/55", badge: "bg-[#E01A8A]/20 text-[#FF6B9D] border-[#E01A8A]/50", cat: "text-[#FF6B9D]" },
      { bg: "bg-gradient-to-br from-[#7C3AED]/25 to-[#8B5CF6]/10 border-[#7C3AED]/55", badge: "bg-[#7C3AED]/20 text-[#A78BFA] border-[#7C3AED]/50", cat: "text-[#A78BFA]" },
      { bg: "bg-gradient-to-br from-[#00E5A3]/25 to-[#00F5A0]/10 border-[#00E5A3]/55", badge: "bg-[#00E5A3]/20 text-[#34D399] border-[#00E5A3]/50", cat: "text-[#34D399]" },
      { bg: "bg-gradient-to-br from-[#FFA800]/25 to-[#FFC700]/10 border-[#FFA800]/55", badge: "bg-[#FFA800]/20 text-[#FBBF24] border-[#FFA800]/50", cat: "text-[#FBBF24]" },
      { bg: "bg-gradient-to-br from-[#3B82F6]/25 to-[#60A5FA]/10 border-[#3B82F6]/55", badge: "bg-[#3B82F6]/20 text-[#60A5FA] border-[#3B82F6]/50", cat: "text-[#60A5FA]" },
      { bg: "bg-gradient-to-br from-[#EF4444]/25 to-[#F87171]/10 border-[#EF4444]/55", badge: "bg-[#EF4444]/20 text-[#F87171] border-[#EF4444]/50", cat: "text-[#F87171]" },
      { bg: "bg-gradient-to-br from-[#06B6D4]/25 to-[#22D3EE]/10 border-[#06B6D4]/55", badge: "bg-[#06B6D4]/20 text-[#22D3EE] border-[#06B6D4]/50", cat: "text-[#22D3EE]" },
      { bg: "bg-gradient-to-br from-[#F97316]/25 to-[#FB923C]/10 border-[#F97316]/55", badge: "bg-[#F97316]/20 text-[#FB923C] border-[#F97316]/50", cat: "text-[#FB923C]" },
      { bg: "bg-gradient-to-br from-[#EC4899]/25 to-[#F472B6]/10 border-[#EC4899]/55", badge: "bg-[#EC4899]/20 text-[#F472B6] border-[#EC4899]/50", cat: "text-[#F472B6]" },
      { bg: "bg-gradient-to-br from-[#14B8A6]/25 to-[#2DD4BF]/10 border-[#14B8A6]/55", badge: "bg-[#14B8A6]/20 text-[#2DD4BF] border-[#14B8A6]/50", cat: "text-[#2DD4BF]" },
    ];
    const s = colorSchemes[idx % colorSchemes.length];
    return {
      id: idx + 1,
      initials: q,
      queue: `${q} Queue`,
      qKey: q,
      className: s.bg + " text-white",
      timerColor: "bg-neutral-800/40 text-neutral-400 border-neutral-700/35",
      badgeColor: s.badge,
      catColor: s.cat,
      details: ["Waiting Time", "Unassigned Time"]
    };
  });

  const usedTicketIds = new Set<string>();

  const earlyWarningCards = cardTemplates
    .map((t, idx) => {
      const queueTickets = rows.filter(r => {
        const q = val(r, "Ticket_Queue", "Queue");
        return q === t.qKey;
      });

      const p1Tickets = queueTickets.filter(r => {
        const ticketId = r.Ticket_ID || "";
        if (usedTicketIds.has(ticketId)) return false;
        const responseTime = num(r, "Average_Time_spent_in_Mins", "First_Response_Time_Mins");
        const status = val(r, "Ticket_Status", "Status");
        return responseTime > 120 || status === "Reassigned" || status === "Rejected";
      });

      const p2Tickets = queueTickets.filter(r => {
        const ticketId = r.Ticket_ID || "";
        if (usedTicketIds.has(ticketId)) return false;
        return val(r, "Ticket_Status", "Status") !== "Resolved";
      });

      const p3Tickets = queueTickets.filter(r => {
        const ticketId = r.Ticket_ID || "";
        return !usedTicketIds.has(ticketId);
      });

      const selectedTicket = p1Tickets[0] || p2Tickets[0] || p3Tickets[0] || null;

      if (!selectedTicket) {
        return null;
      }

      const ticketId = selectedTicket.Ticket_ID || `TK-${10000 + idx + 200}`;
      usedTicketIds.add(ticketId);

      const responseTime = num(selectedTicket, "Average_Time_spent_in_Mins", "First_Response_Time_Mins");
      const status = val(selectedTicket, "Ticket_Status", "Status");
      const hotspot = selectedTicket.Country || "";
      const category = val(selectedTicket, "Issue_Category", "Category") || "General Issue";
      const categoryLabel = category;

      const ticketNum = parseInt(ticketId.replace(/\D/g, "")) || (idx * 17);
      const warningAgeMins = responseTime > 120 ? Math.min(59, responseTime - 120) : (ticketNum % 15) + 5;
      const seconds = (ticketNum % 50) + 10;
      const timeStr = `00:${warningAgeMins.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

      const descParts: string[] = [];
      if (responseTime > 120) {
        descParts.push(`SLA Breached by ${responseTime - 120} mins`);
      }
      if (status === "Reassigned") {
        descParts.push(`Reassigned to ${selectedTicket.Reassigned_To || "Support"}`);
      } else if (status === "Rejected") {
        descParts.push(`Rejected: ${selectedTicket.Rejection_Reason || "Invalid"}`);
      } else if (status === "Resolved") {
        descParts.push("Resolved");
      } else {
        descParts.push(`Status: ${status}`);
      }
      descParts.push(`Location: ${hotspot}`);

      const originalDetailTags = t.details.slice(0, 2);
      const displayDetails = [...originalDetailTags, ...descParts].join(", ");

      const getQueueDisplayName = (cleanQueue: string) => `${cleanQueue} Support`;

      return {
        id: t.id,
        initials: t.initials,
        queue: `${getQueueDisplayName(t.qKey)} (${ticketId})`,
        time: timeStr,
        category: categoryLabel,
        details: displayDetails,
        className: t.className,
        timerColor: t.timerColor,
        badgeColor: t.badgeColor,
        catColor: t.catColor
      };
    })
    .filter((card): card is NonNullable<typeof card> => card !== null);

  return {
    Monthly_Distribution: monthlyDist,
    NOC_Queue_Times: nocQueueTimes,
    First_Response_Issues: firstResponseIssues,
    Reassignment_Reasons: reassignmentReasonsList,
    Weekly_Volume: scaledWeeklyVolume,
    Trouble_Tickets_30d: troubleTickets30d,
    Reassignments_Rejections: reassignmentsRejections,
    Roaming_By_Country: roamingByCountry,
    NOC_Tickets_Distribution: nocTicketsDistribution,
    UAE_Regional_Hotspots: uaeRegionalHotspots,
    Early_Warning_Cards: earlyWarningCards,
    dailyCounts
  };
}
