Here is the implementation plan in Markdown format, ready to save as `MARK_PROSODY_IMPLEMENTATION_PLAN.md`.

# Mark — Production Prosody Implementation Plan

## 1. Objective

Transform Mark from a conventional voice assistant that reads LLM-generated responses into a **context-guided, natural, expressive enterprise voice assistant**.

The target behavior is:

> **Mark should sound like a knowledgeable human colleague thinking and communicating with you — not an LLM reading text aloud.**

Prosody must be driven by **meaning, context, intent, conversation state, and operational situation**, rather than by random pauses or fixed voice settings.

---

# 2. Target Architecture

```text
                         ┌─────────────────────┐
                         │        USER         │
                         │    Voice / Text     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Speech-to-Text   │
                         │   + Intent/Context  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                  ┌──────────────────────────────────┐
                  │        MARK CONTEXT ENGINE       │
                  │                                  │
                  │ Conversation │ User │ Task       │
                  │ Domain       │ State │ History    │
                  └────────────────┬─────────────────┘
                                   │
                                   ▼
                  ┌──────────────────────────────────┐
                  │       RESPONSE PLANNER           │
                  │                                  │
                  │ What should Mark say?            │
                  │ What should Mark omit?            │
                  │ How should information be        │
                  │ structured?                      │
                  └────────────────┬─────────────────┘
                                   │
                                   ▼
                  ┌──────────────────────────────────┐
                  │        PROSODY ENGINE             │
                  │                                  │
                  │ • Pace                           │
                  │ • Pauses                         │
                  │ • Emphasis                       │
                  │ • Pitch movement                 │
                  │ • Energy                         │
                  │ • Rhythm                         │
                  │ • Sentence length                │
                  │ • Turn-taking                    │
                  │ • Conversational fillers         │
                  └────────────────┬─────────────────┘
                                   │
                                   ▼
                  ┌──────────────────────────────────┐
                  │       SPEECH RENDERER / TTS      │
                  │                                  │
                  │ SSML / Native TTS Controls      │
                  └────────────────┬─────────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │      MARK VOICE     │
                         │  Natural + Dynamic  │
                         └─────────────────────┘
```

---

# 3. Core Design Principle

Do **not** try to make the LLM directly "sound human."

Separate:

```text
WHAT MARK SAYS
       ↓
HOW MARK SAYS IT
       ↓
HOW THE VOICE RENDERS IT
```

Therefore:

```text
Context
   ↓
Intent
   ↓
Response
   ↓
Prosody Plan
   ↓
Speech Rendering
   ↓
Audio
```

This separation makes Mark:

* more natural
* more controllable
* easier to test
* vendor independent
* easier to evolve
* suitable for enterprise deployment

---

# 4. Mark Voice Constitution

Define a permanent voice behavior contract.

| Dimension       | Mark behavior                             |
| --------------- | ----------------------------------------- |
| Pace            | Conversational and dynamically adjustable |
| Pauses          | Meaningful rather than mechanical         |
| Pitch           | Natural variation                         |
| Emphasis        | Important concepts only                   |
| Energy          | Context dependent                         |
| Emotion         | Subtle and controlled                     |
| Confidence      | Reflects evidence                         |
| Sentence length | Shorter during voice interaction          |
| Silence         | Allowed                                   |
| Fillers         | Occasional and intentional                |
| Repetition      | Avoid                                     |
| Ending          | Natural conversational cadence            |

## Mark should NOT

* read every sentence with the same rhythm
* pause at every comma
* emphasize every technical term
* use excessive emotional expression
* sound permanently excited
* sound permanently serious
* speak every answer at the same speed
* fill every silence
* produce unnecessarily long spoken responses
* sound like an IVR system

---

# 5. Prosody Dimensions

The Mark Prosody Engine should control at least:

```text
Pace
Pitch
Pitch variation
Energy
Volume
Pauses
Emphasis
Rhythm
Sentence boundaries
Paragraph transitions
Speaking density
Turn-taking
Silence
```

Optional advanced controls:

```text
Breath-like pauses
Disfluency control
Laughter / warmth
Whisper / low-energy modes
Emotional intensity
Speaking style
```

These advanced controls should only be introduced after the core system is stable.

---

# 6. Prosody Schema

Create a controlled internal representation rather than allowing the LLM to generate arbitrary TTS commands.

Example:

```json
{
  "tone": "calm_focused",
  "pace": 0.92,
  "energy": 0.65,
  "pitch_variation": 0.55,
  "segments": [
    {
      "text": "The transport alarm",
      "emphasis": "medium",
      "pause_after_ms": 350
    },
    {
      "text": "caused the Mobile Core issue.",
      "emphasis": "high",
      "pause_after_ms": 600
    }
  ]
}
```

## Controlled tone vocabulary

```text
neutral
warm
calm_focused
concerned
urgent
analytical
reassuring
curious
```

## Controlled emphasis

```text
none
low
medium
high
```

The schema becomes the contract between the reasoning layer and the TTS layer.

---

# 7. Context-Guided Prosody

Prosody should change based on context.

## Normal Conversation

```text
tone = warm
pace = 1.00
energy = 0.55
pause_frequency = low
```

## Incident Investigation

```text
tone = calm_focused
pace = 0.92
energy = 0.65
pause_frequency = medium
emphasis = evidence + conclusion
```

## Critical Outage

```text
tone = urgent
pace = 0.95
energy = 0.80
sentence_length = short
```

## Uncertain RCA

```text
tone = analytical
pace = 0.88
energy = 0.50
```

Mark should deliver uncertainty clearly.

For example:

```text
"Evidence currently points to a transport-side issue."

"But we haven't confirmed that yet."
```

The second statement should receive deliberate emphasis.

## Recovery / Resolution

```text
tone = reassuring
pace = 0.98
energy = 0.60
```

---

# 8. Semantic Prosody

Prosody should understand the semantic role of information.

Mark should distinguish:

```text
FACT
EVIDENCE
OBSERVATION
HYPOTHESIS
VALIDATION
ROOT_CAUSE
IMPACT
ACTION
UNCERTAINTY
WARNING
```

Example:

```text
FACT:
"The packet-loss KPI increased at 14:31."

HYPOTHESIS:
"This suggests a transport-side issue."

VALIDATION:
"We haven't confirmed that yet."

CONCLUSION:
"The transport failure is therefore supported by the available evidence."
```

The delivery style should change with the semantic role.

---

# 9. Meaningful Pauses

Avoid mechanical pause insertion.

Instead define pause categories:

```text
micro pause       100–250 ms
thought pause     300–600 ms
transition pause  400–800 ms
long pause        700–1200 ms
```

Use pauses for:

* transitions
* important evidence
* conclusions
* uncertainty
* changes in topic
* numbers
* customer impact
* root-cause statements

Example:

```text
"We have three alarms.

The first one started at 14:32.

And that's important...

because it precedes the Mobile Core alarm."
```

The pauses should communicate structure rather than simply slow speech down.

---

# 10. Emphasis Engine

The engine should identify words and phrases that carry meaning.

Potential emphasis candidates:

```text
root cause
first abnormal signal
customer impact
confirmed
not confirmed
critical
recovered
before
after
only
most likely
```

Avoid emphasizing every technical term.

Example:

```text
"The interesting part is that the Mobile Core alarm
was actually a symptom."
```

The emphasis should fall on the semantic contrast rather than every word.

---

# 11. Numbers and Technical Information

Technical voice assistants require special treatment for:

```text
timestamps
IP addresses
node names
KPIs
percentages
durations
error codes
alarm IDs
protocol names
network identifiers
```

For example:

```text
"The first abnormal signal appeared at 14:32."
```

Mark should slightly slow down the timestamp.

Likewise:

```text
"Packet loss increased to 18 percent."
```

The number should be delivered clearly rather than rushed through.

---

# 12. Conversational Turn-Taking

Prosody alone will not make Mark feel human.

Implement **streaming turn-taking and barge-in**.

Target flow:

```text
User speaks
    ↓
Streaming STT
    ↓
Intent detected
    ↓
Mark begins response
    ↓
LLM streams response
    ↓
Prosody engine processes chunks
    ↓
TTS streams audio
    ↓
User interrupts
    ↓
Mark immediately stops
```

Example:

```text
User:
"Mark, what's the root cause?"

Mark:
"The current evidence points to—"

User:
"Wait. Check transport first."

Mark:
"Sure. Checking transport."
```

The ability to stop immediately is one of the strongest contributors to natural interaction.

---

# 13. Streaming Architecture

Do not wait for the complete LLM response before starting TTS.

Use:

```text
Streaming STT
      ↓
Context / Intent
      ↓
LLM streaming
      ↓
Semantic chunking
      ↓
Prosody planning
      ↓
TTS streaming
      ↓
Audio playback
```

This reduces perceived latency.

The prosody engine should work on semantic chunks rather than individual tokens.

---

# 14. Prosody Decision Engine

Use deterministic rules together with LLM-generated semantic hints.

Recommended architecture:

```text
Context
   +
Response structure
   +
Conversation state
   ↓
Prosody Policy
   ↓
LLM Prosody Hints
   ↓
Validation / Normalization
   ↓
Prosody IR
   ↓
TTS
```

Example:

```python
if context.mode == "incident":
    pace = 0.92

if response.contains_root_cause:
    emphasize(root_cause)
    pause_before(root_cause)

if response.contains_uncertainty:
    reduce_energy()
    slow_down()

if response.contains_number:
    slow_down(number)

if user_is_interrupted:
    stop_audio()
```

The rules should override unsafe or excessive LLM-generated prosody instructions.

---

# 15. Prosody Engine API

Expose a simple internal interface.

Example:

```text
POST /prosody/plan
```

Input:

```json
{
  "text": "The transport alarm caused the Mobile Core issue.",
  "context": {
    "mode": "incident_investigation",
    "confidence": 0.86,
    "user_emotion": "neutral",
    "conversation_stage": "root_cause"
  }
}
```

Output:

```json
{
  "tone": "calm_focused",
  "pace": 0.92,
  "energy": 0.65,
  "segments": [
    {
      "text": "The transport alarm",
      "emphasis": "medium",
      "pause_after_ms": 350
    },
    {
      "text": "caused the Mobile Core issue.",
      "emphasis": "high",
      "pause_after_ms": 600
    }
  ]
}
```

The TTS adapter converts this representation into provider-specific speech controls.

---

# 16. Vendor Abstraction

Do not couple Mark's core architecture to a specific TTS provider.

```text
                 Mark Prosody IR
                       │
              ┌────────┴────────┐
              ▼                 ▼
         TTS Adapter A      TTS Adapter B
              │                 │
           Provider A        Provider B
```

The internal Mark representation remains stable.

Only the renderer changes.

This allows future migration between TTS providers without redesigning Mark.

---

# 17. Incident Storytelling Integration

This is particularly important for the FikraCore use case.

The storyteller structure should be:

```text
Event
  ↓
Timeline
  ↓
Evidence
  ↓
Correlation
  ↓
Hypothesis
  ↓
Validation
  ↓
Root Cause
  ↓
Impact
  ↓
Action
```

Each stage should have its own delivery behavior.

Example:

```text
EVENT
calm / factual

EVIDENCE
deliberate

HYPOTHESIS
cautious

VALIDATION
clear / precise

ROOT CAUSE
strong emphasis

IMPACT
serious / measured

ACTION
confident / concise
```

This allows Mark to tell an incident story naturally instead of reading an incident report.

---

# 18. Domain-Aware Prosody

Mark should eventually understand the operational significance of:

```text
CS
PS
VAS
RAN
IP Transport
IGW
IPTV
IoT
Wireless
```

Example:

A CS alarm by itself may be routine.

A CS alarm correlated with:

```text
transport packet loss
+
PS KPI degradation
+
topology relationship
+
customer impact
```

should cause Mark to shift into a more analytical delivery mode.

This means:

```text
Network Context
      ↓
Operational Meaning
      ↓
Prosody Context
      ↓
Voice
```

---

# 19. Mark Conversation States

Introduce explicit conversation states.

```text
IDLE
LISTENING
THINKING
RESPONDING
EXPLAINING
CLARIFYING
INTERRUPTED
VERIFYING
ESCALATING
COMPLETED
```

Each state can have a default prosody profile.

Example:

```text
THINKING:
slightly slower
short pause

EXPLAINING:
structured rhythm
moderate pace

VERIFYING:
analytical
measured

ESCALATING:
focused
clear
higher energy

COMPLETED:
short
confident
natural falling cadence
```

---

# 20. Pronunciation Layer

Create a dedicated technical pronunciation dictionary.

Example categories:

```text
3GPP
MME
AMF
SMF
UPF
GTP
GTP-C
GTP-U
Diameter
SCTP
SIGTRAN
VoLTE
5GC
vEPC
Kubernetes
Grafana
Kafka
FikraCore
```

The dictionary should support:

```text
canonical pronunciation
aliases
acronym expansion
TTS-specific pronunciation
domain-specific overrides
```

This should be independent of the prosody engine.

---

# 21. Phase-Based Implementation

## Phase 1 — Voice Foundation

Implement:

* Streaming STT
* Streaming TTS
* Audio pipeline
* Low-latency playback
* Barge-in
* TTS cancellation
* Conversation state

### Exit criteria

Mark can:

```text
listen
→ understand
→ respond
→ be interrupted
→ stop
→ continue naturally
```

---

## Phase 2 — Prosody Foundation

Implement:

* Prosody schema
* Semantic segmentation
* Pause engine
* Emphasis engine
* Pace control
* Pitch control
* Energy control
* TTS adapter

### Exit criteria

The same sentence should be capable of being delivered differently depending on context.

---

## Phase 3 — Context Integration

Connect:

```text
Conversation context
+
User intent
+
Task state
+
Domain context
+
Conversation history
```

to the Prosody Engine.

### Exit criteria

Prosody changes automatically according to the conversation.

---

## Phase 4 — Intelligence Integration

Introduce semantic categories:

```text
fact
evidence
hypothesis
validation
root cause
impact
action
uncertainty
warning
```

### Exit criteria

Mark sounds different when:

* reporting evidence
* proposing a hypothesis
* confirming an RCA
* communicating uncertainty
* reporting customer impact

---

## Phase 5 — Storytelling

Integrate the FikraCore incident narrative:

```text
Event
→ Timeline
→ Evidence
→ Correlation
→ Hypothesis
→ Validation
→ RCA
→ Impact
→ Action
```

### Exit criteria

Mark can tell a complete incident story conversationally rather than reading a report.

---

## Phase 6 — Production Hardening

Implement:

* latency monitoring
* TTS failure fallback
* pronunciation dictionary
* telemetry
* prosody regression tests
* voice-quality evaluation
* provider abstraction
* safety limits
* observability
* configuration management

---

# 22. Test Suite

Create approximately 50–100 scripted conversations.

## Conversation Tests

```text
Greeting
Follow-up
Clarification
Correction
Interruption
Disagreement
Incomplete question
Topic change
```

## Operations Tests

```text
Alarm
Incident
RCA
Escalation
Change activity
Customer impact
Recovery
```

## Information Tests

```text
Numbers
Timestamps
IP addresses
Node names
Acronyms
Technical terminology
Error codes
```

## Context Tests

```text
Calm
Urgent
Uncertain
Reassuring
Critical
Successful recovery
```

---

# 23. Evaluation Metrics

Track both technical and human-perception metrics.

## Technical

```text
Time to first audio
End-to-end latency
Barge-in latency
TTS cancellation latency
STT accuracy
Pronunciation accuracy
Prosody-plan validity
TTS failure rate
```

## Voice Quality

```text
Pause naturalness
Speech-rate naturalness
Pitch variation
Emphasis accuracy
Rhythm
Sentence cadence
```

## User Experience

```text
Naturalness
Clarity
Trustworthiness
Conversational quality
Perceived intelligence
Perceived responsiveness
```

Avoid optimizing solely for "human-like."

The enterprise target is:

> **Natural + controlled + intelligible + trustworthy.**

---

# 24. A/B Evaluation

Build three versions:

```text
A — Current Mark
B — Conversational Mark
C — Context + Prosody Mark
```

Use blind listening tests.

Ask evaluators:

```text
Does Mark sound natural?

Does Mark sound like a colleague?

Does Mark sound like it is reading?

Are pauses appropriate?

Is emphasis appropriate?

Does Mark adapt to the situation?

Does Mark respond naturally to interruption?

Is technical information easy to understand?
```

---

# 25. Recommended Initial MVP

Do not implement the entire architecture at once.

Start with:

```text
┌─────────────────────────────┐
│         MARK MVP            │
├─────────────────────────────┤
│ Streaming STT               │
│ Streaming TTS               │
│ Barge-in                    │
│ Conversation State          │
│ Semantic Sentence Splitter  │
│ Prosody Planner             │
│ Pause Control               │
│ Emphasis Control            │
│ Pace Control                │
│ Technical Pronunciation     │
│ TTS Adapter                 │
└─────────────────────────────┘
```

Then add:

```text
Context
   ↓
Operational semantics
   ↓
Incident storytelling
   ↓
Domain-aware prosody
   ↓
Advanced expressive speech
```

---

# 26. Final Architecture

```text
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │ Streaming   │
                    │    STT      │
                    └──────┬──────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Conversation      │
                 │ Manager           │
                 └─────────┬─────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
        Context          Intent         Memory
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                  ┌─────────────────┐
                  │ Response        │
                  │ Planner         │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Semantic        │
                  │ Analyzer        │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ MARK PROSODY    │
                  │ ENGINE           │
                  │                 │
                  │ Pace            │
                  │ Pitch           │
                  │ Energy          │
                  │ Pauses           │
                  │ Emphasis         │
                  │ Rhythm           │
                  │ Turn-taking      │
                  └────────┬────────┘
                           │
                     Prosody IR
                           │
                           ▼
                  ┌─────────────────┐
                  │ TTS Adapter     │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Streaming TTS   │
                  └────────┬────────┘
                           │
                           ▼
                         MARK
                           ▲
                           │
                       BARGE-IN
                           │
                         USER
```

# 27. Success Definition

Mark is ready for production when it no longer behaves like:

```text
LLM
 ↓
Text
 ↓
Robot voice
```

and instead behaves like:

```text
Context
 ↓
Understanding
 ↓
Reasoning
 ↓
Conversation
 ↓
Prosody
 ↓
Natural speech
 ↓
Adaptive interaction
```

The **Mark Prosody Engine** should therefore be treated as a first-class component of the voice-assistant architecture, not as a TTS configuration.
