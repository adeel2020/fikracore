# Fix: Robust Data Extraction for Graphs (Direct Fields & Fallback Parsing)

## 🚨 The Issue
When the month toggle filter was selected, the Monthly Distribution chart incorrectly split the categories exactly 50/50. This occurred because the web worker (`telemetry.worker.ts`) attempted to parse fields like `Color_Group` and `Country` by running regex matches on `raw_complaint`. However, during data loading, the mapping process dropped the original fields and did not write them into `raw_complaint`. Consequently, the parsing failed, and the code fell back to index parity (even/odd ticket IDs), yielding a 50/50 split.

---

## 🔍 Root Cause Analysis
1. **Frontend Omitted Original Properties**:
   The telemetry mapping logic in `ComplaintDashboardView.tsx` and `useDataLoader.ts` created a mapped database-compatible object but did not preserve the original uploaded properties (like `Color_Group`, `Country`, `Average_Time_spent_in_Mins`, `Ticket_Queue`, etc.) on the object.
2. **Worker Solely Relied on Text Parsing**:
   The `parseDatabaseComplaints` function in `telemetry.worker.ts` parsed values exclusively from `raw_complaint` using regex patterns. If a custom uploaded sheet had a modified set of fields or layout, parsing failed and defaulted to generic fallback values.

---

## 🛠️ The Solution
1. **Spread Original Properties (`...r`)**:
   Updated the telemetry list mapping functions in both the frontend view and the data loader to spread the original input record onto the returned object. This ensures that any uploaded custom spreadsheet fields (such as `Color_Group` or `Country`) are preserved as properties on the objects in the ledger list:
   - [ComplaintDashboardView.tsx](file:///Users/adeelarshad/AgenticAIOPs/frontend/src/components/features/complaint-dashboard-view/ComplaintDashboardView.tsx)
   - [useDataLoader.ts](file:///Users/adeelarshad/AgenticAIOPs/frontend/src/components/features/data-loader-view/useDataLoader.ts) (both CSV & Excel log mapping blocks)

2. **Remove Unused Fallback Fields**:
   Cleaned up the mapping function parameters to only reference the active Source A spreadsheet keys (`r.Issue_Category`, `r.Ticket_Queue`, `r.Ticket_Status`, `r.Average_Time_spent_in_Mins`), removing references to Source B variables (like `r.Category`, `r.Queue`, `r.Hotspot_Name`, `r.First_Response_Time_Mins`) that are non-existent in the uploaded files.

3. **Direct Property Checks in Worker**:
   Modified `parseDatabaseComplaints` in [telemetry.worker.ts](file:///Users/adeelarshad/AgenticAIOPs/frontend/src/components/features/complaint-dashboard-view/workers/telemetry.worker.ts) to check for direct properties on the object first (supporting both camelCase and snake_case properties). If the direct property is present (e.g. `r.Color_Group` or `r.Color_group`), it uses it immediately. If not (for database-only chat complaints that only possess a `raw_complaint` string), it falls back to parsing the description text:
   - `Average_Time_spent_in_Mins` / `First_Response_Time_Mins`
   - `Country` / `country`
   - `Hotspot_Name` / `Hotspot` / `hotspot`
   - `Color_Group` / `Color_group` / `color_group`
   - `Ticket_Queue` / `Queue` / `queue` / `assignment_target`
   - `Issue_Category` / `Category` / `category` / `reassignment_category`
   - `Create_Date` / `CreateDate`

4. **Type safety updated**:
   Added `Color_Group?: string` to `ComplaintTelemetry` in [qna.ts](file:///Users/adeelarshad/AgenticAIOPs/frontend/src/lib/api/qna.ts).

5. **Isolate Source B (Live Database Telemetry):**
   Commented out the live DB telemetry fallback inside [ComplaintDashboardView.tsx](file:///Users/adeelarshad/AgenticAIOPs/frontend/src/components/features/complaint-dashboard-view/ComplaintDashboardView.tsx) to ensure only local spreadsheets and local JSON templates (Source A) are used for telemetry and graphics.
