# Fix: Correct Day-of-Week Volume & Monthly Distribution on Calendar Date Selection

## 🚨 The Issue
The "DAY OF THE WEEK VOLUME" (weekly volume) chart showed an incorrect, high count when no calendar date filter was selected (i.e. unfiltered state), but showed the correct, low count when a specific day filter was selected on the calendar.

---

## 🔍 Root Cause Analysis
The weekly volume was scaled in `aggregationUtils.ts` by dividing the total counts per weekday by `uniqueMonthsCount` (number of months, which was 12 for unfiltered data):
```typescript
entry[c] = Math.round((d[c] || 0) / uniqueMonthsCount);
```
Dividing the total complaints on a specific weekday (e.g. Sunday) by the number of months (12) yields the average number of complaints on Sundays *per month* (e.g., Sunday blue showed `25`). However, the chart title is "DAY OF THE WEEK VOLUME" and the user expects to see the actual average count *per day* (or per individual weekday, which should be around `6` for Sundays, since there are 4-5 Sundays in a month). Showing the monthly sum on each weekday bar resulted in a count that was ~4x too high.

When a calendar date was selected, the filtered dataset had only a single day, so the divisor was `1`, showing the correct count for that single day (e.g., 6).

---

## 🛠️ The Solution
Modified the aggregation logic in [aggregationUtils.ts](file:///Users/adeelarshad/AgenticAIOPs/frontend/src/components/features/complaint-dashboard-view/workers/aggregationUtils.ts) to scale the weekly volume by the actual number of occurrences of each weekday in the filtered dataset, instead of dividing by the month count:
1. Created `weekdayDatesMap` to track unique dates representing each day of the week in the loop.
2. Divided each weekday's total count by the size of the unique dates set for that weekday:
```typescript
const occurrences = weekdayDatesMap[d.day].size || 1;
entry[c] = Math.round((d[c] || 0) / occurrences);
```

This ensures that:
- When unfiltered: Sunday counts are divided by the number of Sundays in the year (48 or 52), yielding the correct daily weekday average (~6).
- When filtered by a month (e.g. April 2025): Sunday counts are divided by the number of Sundays in April (4 or 5), yielding the correct daily weekday average (~10).
- When filtered by a specific day (e.g., April 3rd, 2025): Thursday counts are divided by 1, yielding the correct day's count (6).

---

## 🔬 Verification & Correctness
Tested the new scaling logic using a node script:
- **Unfiltered**: Average weekly volume per weekday scaled down to `6` (blue) and `4` (brown) on Sundays, matching the daily average.
- **Month Selected**: Weekday average in April scaled to `5` (blue) and `6` (brown) on Sundays.
- **Specific Day Selected**: Thursday count scaled to the exact number of tickets on that day (6).
