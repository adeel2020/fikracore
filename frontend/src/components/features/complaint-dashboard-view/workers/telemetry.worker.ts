import { aggregateRawTickets } from "./aggregationUtils";

function parseDatabaseComplaints(data: any[]) {
  return data.map((r: any) => {
    // 1. First Response Time
    const rawTime = r.Average_Time_spent_in_Mins !== undefined ? r.Average_Time_spent_in_Mins : r.First_Response_Time_Mins;
    const respMatch = (r.raw_complaint || "").match(/First response time:\s*(\d+)/i);
    const responseTime = rawTime !== undefined ? Number(rawTime) : (respMatch ? Number(respMatch[1]) : 45);

    // 2. Country
    const rawCountryVal = r.Country || r.country;
    const countryMatch = (r.raw_complaint || "").match(/Country:\s*([A-Za-z\s]+)/i);
    const rawCountry = rawCountryVal ? String(rawCountryVal).trim() : (countryMatch ? countryMatch[1].trim() : "");
    const country = rawCountry && rawCountry !== "Local" ? rawCountry : "";

    // 3. Hotspot
    const rawHotspot = r.Hotspot_Name || r.Hotspot || r.hotspot;
    const hotspotMatch = (r.raw_complaint || "").match(/in\s+([A-Za-z\s\/]+?)\s*\(/i);
    const hotspot = rawHotspot ? String(rawHotspot).trim() : (hotspotMatch ? hotspotMatch[1].trim() : "Dubai Core");

    // 4. Color Group
    const rawColor = r.Color_Group || r.Color_group || r.color_group;
    const colorMatch = (r.raw_complaint || "").match(/Color_Group:\s*([A-Za-z]+)/i);
    const colorGroup = rawColor ? String(rawColor).trim().toUpperCase() : (colorMatch ? colorMatch[1].trim().toUpperCase() : (r.id % 2 === 0 ? "BLUE" : "BROWN"));

    // 5. Queue / Target
    const rawQueue = r.Ticket_Queue || r.Queue || r.queue || r.assignment_target;
    let mappedQueue = "CS";
    if (rawQueue) {
      const qStr = String(rawQueue).replace(/\s*Queue$/i, "").trim();
      mappedQueue = qStr || "CS";
    } else {
      const lowerTarget = (r.assignment_target || "").toLowerCase();
      if (lowerTarget.includes("smcs") || lowerTarget.includes("mobile core")) {
        mappedQueue = "PS";
      } else if (lowerTarget.includes("cs core") || lowerTarget.includes("core_cs")) {
        mappedQueue = "CS";
      } else if (lowerTarget.includes("vas") || lowerTarget.includes("vas_core")) {
        mappedQueue = "VAS";
      } else if (lowerTarget.includes("ocs") || lowerTarget.includes("in_ocs") || lowerTarget.includes("in support") || lowerTarget.includes("in queue")) {
        mappedQueue = "IN";
      } else if (lowerTarget.includes("provisioning") || lowerTarget.includes("it_prov") || lowerTarget.includes("ran")) {
        mappedQueue = "RAN";
      } else if (lowerTarget.includes("billing") || lowerTarget.includes("bscs") || lowerTarget.includes("ei")) {
        mappedQueue = "EI";
      } else if (lowerTarget.includes("bss") || lowerTarget.includes("ireg")) {
        mappedQueue = "IREG";
      } else {
        const queues = ["CS", "PS", "IN", "RAN", "IREG", "EI", "VAS"];
        mappedQueue = queues[r.id % queues.length];
      }
    }

    // 6. Category
    const rawCategory = r.Issue_Category || r.Category || r.category || r.reassignment_category;
    const category = rawCategory || "Other";

    const dateObj = new Date(r.time_reported * 1000);
    const createDate = r.Create_Date || r.CreateDate || `${dateObj.getFullYear()}-${(dateObj.getMonth() + 1).toString().padStart(2, "0")}-${dateObj.getDate().toString().padStart(2, "0")}`;

    return {
      Ticket_ID: r.complaint_number || r.Ticket_ID,
      Create_Date: createDate,
      Queue: mappedQueue,
      Status: r.Ticket_Status || r.Status || r.status || r.resolution_category,
      Category: category,
      Color_Group: colorGroup,
      First_Response_Time_Mins: responseTime,
      Country: country,
      Hotspot_Name: hotspot,
      Reassigned_To: r.Reassigned_To || r.reassigned_to_raw || (r.resolution_category === "Reassigned" ? "IT" : ""),
      Rejection_Reason: r.Rejection_Reason || r.rejection_reason_raw || (r.resolution_category === "Rejected" ? "Missing Info" : "")
    };
  });
}

self.onmessage = (e: MessageEvent) => {
  const { type, data, filter } = e.data;
  try {
    if (type === "PARSE_AND_AGGREGATE_DB") {
      const parsedRows = parseDatabaseComplaints(data);
      const aggregated = aggregateRawTickets(parsedRows);
      self.postMessage({ type: "PARSE_AND_AGGREGATE_DB_SUCCESS", result: aggregated });
    } else if (type === "AGGREGATE_RAW_TICKETS") {
      const result = aggregateRawTickets(data);
      self.postMessage({ type: "AGGREGATE_RAW_TICKETS_SUCCESS", result });
    } else if (type === "AGGREGATE_FILTERED_TICKETS") {
      const parsedRows = parseDatabaseComplaints(data);

      const filtered = parsedRows.filter((r: any) => {
        if (!filter) return true;
        if (filter.length === 7) return r.Create_Date.startsWith(filter);
        return r.Create_Date === filter;
      });

      const result = aggregateRawTickets(filtered);

      self.postMessage({ type: "AGGREGATE_FILTERED_TICKETS_SUCCESS", result });
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    self.postMessage({ type: "ERROR", error: errorMsg });
  }
};
