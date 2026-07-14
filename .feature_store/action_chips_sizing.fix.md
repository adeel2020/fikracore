# Fix: Action Chips Sizing & Vertical Expansion Optimization

## 🚨 The Issue
Following the addition of the new multi-agent cognitive guides and telecom signaling pages in the suggested prompts carousel, the suggested prompt cards ("action chips") expanded vertically, causing the layout to lose its compact, sleek proportion compared to the original design in [agentic-qna-view-old.tsx](file:///Users/adeelarshad/DataEngine/frontend/src/components/agentic-qna-view-old.tsx).

---

## 🔍 Root Cause Analysis
In the original old layout, suggested prompt paragraph elements were restricted using CSS line-clamping:
`className="text-xs text-neutral-400 line-clamp-2 ..."`

During the recent carousel refactoring and guide screen integrations, the `line-clamp-2` Tailwind utility class was inadvertently omitted from both the standard prompt card views and the newly generated 3-column Page 0 guide cards. Without a clamp boundary, longer network and trace-analytical prompts expanded the cards to their full content height, pushing down adjacent items and altering the design scale.

---

## 🛠️ The Solution

### 1. Clamping Constraints Restoration
- **File Modified:** [agentic-qna-view.tsx](file:///Users/adeelarshad/DataEngine/frontend/src/components/features/agentic-qna-view.tsx)
- **Standard Pages (1-5):** Added `line-clamp-2` back to the prompt text class list:
  ```typescript
  className="text-xs text-neutral-400 line-clamp-2 transition-colors group-hover:text-neutral-300 leading-relaxed mt-1"
  ```
- **Cognitive Guide Page (0):** Implemented `line-clamp-2` across all three guide columns (Analysis & Narrative, Search & Diagnostics, and Metrics & Protocol) to ensure even sizing across the grid.

### 2. Proportional Layout Safeguard
- Preserved the clean `p-4` padding, responsive column snaps, and interactive hover shifts, ensuring cards are neatly proportioned regardless of prompt text density.

---

## 🔬 Verification
- **Compilation Check:** Triggered Next.js compiler build inside `frontend/`.
- **Result:** ✓ **Compiled successfully** in 8.6 seconds with 0 TS errors.
