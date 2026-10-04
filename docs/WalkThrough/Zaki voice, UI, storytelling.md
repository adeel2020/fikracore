# Walkthrough: Mark Conversational State, Context Retrieval & Prosody Engine

We enhanced Mark from a stateless verbatim text-to-speech responder into an intelligent, collegial telecom operational partner capable of multi-turn dialogue memory, grounded context retrieval from `story_context.json`, and natural speech prosody.

---

## 1. Key Accomplishments

### A. Conversational Dialogue State & Anaphora Memory
- **File**: [`services/agents/src/engine_stack/engines/telecom_brain/presentation/dialogue_state.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/presentation/dialogue_state.py)
- **Features**:
  - Maintains conversation turns (user & assistant) per `session_id`.
  - Tracks the `focused_entity` (e.g. `UPF-01`, `PE-RTR-01`) and active scenario/stage.
  - Resolves pronouns (*"it"*, *"that node"*, *"the culprit"*, *"its drop rate"*) to the focused entity.

### B. Multi-Step Decision & Grounded Context Retrieval
- **File**: [`services/agents/src/engine_stack/engines/telecom_brain/presentation/zaki_bridge.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/presentation/zaki_bridge.py)
- **Features**:
  - Detects user affirmations and collaborative offers (*"I can"*, *"let me check"*, *"I will look into that"*).
  - Multi-step logic: identifies target entity, queries pending diagnostic probes (`nextBestActions`), and formulates a collaborative operational response.
  - **Eliminated Robotic Boilerplate**: Suppressed the IVR-style preamble (`"Investigation focus: operational explanation and telemetry correlation."`) for conversational messages.
  - Connects to `StoryContextReader` to retrieve live story summaries directly from `operational/story_context.json`.

### C. Persistent Session Management in Voice Hooks & Backend API
- **Backend API**: [`services/agents/src/engine_stack/engines/telecom_brain/api/capability_api.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/api/capability_api.py)
  - `ZakiChatRequest` accepts `session_id` and forwards it to `ui_context`.
  - Returns `spoken_answer` in `zaki_v2` formatted specifically for executive voice playback.
- **Frontend Hook**: [`frontend/src/hooks/useMarkVoice.ts`](file:///Users/adeelarshad/kagent/frontend/src/hooks/useMarkVoice.ts)
  - Preserves a persistent `sessionIdRef` across voice turns so Mark retains dialogue memory throughout the live session.

### D. Natural Prosody, Digit Formatting & Clause-Level Breathing
- **File**: [`frontend/src/lib/voice.ts`](file:///Users/adeelarshad/kagent/frontend/src/lib/voice.ts)
  - **Digit & Unit Phrasing**: Translates HTTP codes and telemetry numbers into natural speech (e.g. `"HTTP 502"` $\rightarrow$ `"HTTP 5, 0, 2"`, `"18.4%"` $\rightarrow$ `"18 point 4 percent"`, `"14ms"` $\rightarrow$ `"14 milliseconds"`).
  - **Breathing Intervals**: Injects natural breathing pauses: `200ms` at comma/clause boundaries, `350ms` at periods, `420ms` for questions, `500ms` at paragraph shifts.

---

## 2. Verification Results

### Automated Tests
- **Dialogue State & Conversational Response Tests**:
  ```bash
  python3 -m pytest services/agents/tests/test_dialogue_state.py
  # Result: 2 passed in 0.60s
  ```
- **Zaki Core Harness Tests**:
  ```bash
  python3 -m pytest -c services/agents/pytest.ini services/agents/tests/test_zaki_v1_harness.py services/agents/tests/test_dialogue_state.py
  # Result: 11 passed in 2.30s
  ```

---

## 3. Experience Comparison

| Scenario | Previous Behavior | New Intelligent Behavior |
| :--- | :--- | :--- |
| **User says "I can"** | Spoke: *"Investigation focus: operational explanation and telemetry correlation. Under scenario SCN-001..."* | Speaks: *"Appreciate the support. If you check UPF-01, I'll continue correlating downstream telemetry across CORRELATING. Our current priority action is to dispatch UPF Drop Probe."* |
| **Follow-up: "What was its drop rate?"** | Lost context; returned generic disclaimer. | Resolves *"its"* to `UPF-01`, retrieves drop rate from `story_context.json`, and reports: *"The packet drop rate on UPF-01 peaked at 18 point 4 percent."* |
| **Speech Audio** | Flat, continuous monotone without breathing pauses. | Natural speech cadence with 200ms comma pauses, 350ms sentence pauses, and natural digit grouping. |

---

## 4. Simulation Readiness Guardrail & Live Flash Narration

### A. Pre-Simulation Oracle Guardrail
- When a scenario is staged in the `investigate` workspace but the simulation has not started yet (`status == "READY"` or 0 admitted events):
  - Mark **strictly halts all scenario detail / root cause leakage**.
  - Visual response clearly indicates:
    - Current Horizon: Stage H1 (Ready / Awaiting Start)
    - Admitted Observations: 0
    - Action Required: Click **Start Simulation** to begin telemetry emission.
  - Spoken response: *"The simulation for scenario SCN-001 has not been started yet. Please click Start Simulation to begin telemetry emission and observe live network behavior."*

### B. Stage-Gated Progressive Disclosure & Live Flash Narration
- When the simulation is active, Mark monitors stage advancement and structures responses into **Live Flash Narration**:
  - **Trigger (Stage 0-1)**:
    🎙️ *"Alert: P1 anomaly detected on transport PE-RTR-21. Correlating initial observations."*
  - **Propagation (Stage 2-3)**:
    🎙️ *"Update: Degradation has cascaded to User Plane Function 003. Mobile data sessions are dropping."*
  - **RCA Confirmed (Stage 4-5)**:
    🎙️ *"Root cause confirmed: PE-RTR-21 line card buffer saturation with 94.2% confidence. Playbook remediation dispatched."*
  - **Recovery (Stage 6-7)**:
    🎙️ *"Recovery verified: Traffic re-routed successfully. 5G throughput restored to nominal baseline."*
- **Unsolicited Push in UI**:
  - `story_context.json` compiles `flash_history` and active `flash_narration`.
  - In [`frontend/src/components/features/simulator/zaki/ZakiLiveStoryOverlay.tsx`](file:///Users/adeelarshad/kagent/frontend/src/components/features/simulator/zaki/ZakiLiveStoryOverlay.tsx), whenever stage advances, Mark automatically narrates the unsolicited flash message and renders the live feed with timestamps.

---

## 5. Streaming Response, Unified Chat & Rebranding to Zaki

### A. Progressive Streaming Response Engine
- **Eliminated One-Shot Flash/Dumps**: Responses are no longer abruptly dumped onto the screen in a jarring wall of text.
- **Dynamic Chunk/Typewriter Streaming**: Text streams smoothly at ~120–250 chars/second (`stepSize = max(2, floor(len/70))` every 18ms) into the active message bubble.
- **Blinking Cyan Cursor**: Displays an animated cursor (`▌`) while streaming is active.
- **Operator Skip Control**: Clicking the message bubble or the `Skip stream` button immediately renders the complete text.

### B. UI De-duplication: Replaced Old Detached Panel with Unified Voice & Chat Copilot
- **Removed Duplicate Right Panel**: Removed the heavy detached Zaki Copilot panel (`investigate/page.tsx` lines 6491–6825) that previously duplicated visualizers, inputs, and messages.
- **Replaced with Mark Chat UI (Renamed Zaki)**: Unified text chatting, live duplex voice, waveform visualizer, quick action chips, and audio controls into a single elegant glassmorphic component: [`ZakiVoiceFAB.tsx`](file:///Users/adeelarshad/kagent/frontend/src/components/features/simulator/zaki/ZakiVoiceFAB.tsx).

### C. Right-Side Alignment
- **Positioning**: Moved from bottom-left (`fixed bottom-6 left-6`) to bottom-right (`fixed bottom-6 right-6 z-50`).
- **Story Overlay Coordination**: Adjusted [`ZakiLiveStoryOverlay.tsx`](file:///Users/adeelarshad/kagent/frontend/src/components/features/simulator/zaki/ZakiLiveStoryOverlay.tsx) positioning to `right-60 z-40`, allowing both the Zaki Copilot pill and Live Story pill to sit neatly side-by-side without overlap.

### D. Renamed Mark to Zaki Across All UI Surfaces
- Header badge: **"ZAKI Voice Copilot"** (Full-Duplex / Standby).
- Collapsed orb: **"ZAKI"** with live status indicator.
- Message tags: **"Zaki"** with Bot icon.
- Audio synthesis welcome: *"Zaki voice online."*
- Full backward-compatibility alias exported for `MarkVoiceFAB` and `useZakiVoice`.

