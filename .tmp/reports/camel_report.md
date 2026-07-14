# Signaling Call Flow Analysis Report
Generated at: **2026-06-27 18:11:36**
Analyzed File: `camel.pcap`  
Parsed Signaling Packets: **5**

## 📊 Executive Signaling Summary
| Packet | Time (Relative) | Originating Node | Destination Node | Protocol | Message Type / Event |
| :--- | :--- | :--- | :--- | :--- | :--- |
| #1 | 0.000s | gsmSSF (10) | gsmSCF (100) | **SIGTRAN** | **TCAP Begin**: `InitialDP` |
| #2 | 0.000s | gsmSCF (100) | gsmSSF (10) | **SIGTRAN** | **TCAP Continue**: `RequestReportBCSMEvent`, `ApplyCharging`, `Continue` |
| #3 | 1.000s | gsmSSF (10) | gsmSCF (100) | **SIGTRAN** | **TCAP Continue**: `EventReportBCSM` (oAnswer) |
| #4 | 75.000s | gsmSSF (10) | gsmSCF (100) | **SIGTRAN** | **TCAP Continue**: `ApplyChargingReport`, `EventReportBCSM` (oDisconnect) |
| #5 | 75.000s | gsmSCF (100) | gsmSSF (10) | **SIGTRAN** | **TCAP End**: `ReleaseCall` |


## 🔄 Call Flow Diagram (Sequence Flow)
```mermaid
%%{init: {
  'themeVariables': {
    'actorLineColor': '#a5b4fc'
  },
  'themeCSS': '.actor-line { stroke: #a5b4fc !important; stroke-width: 2px !important; }'
}}%%
sequenceDiagram
    autonumber
    participant gsmSCF
    participant gsmSSF

    gsmSSF->>gsmSCF: TCAP Begin [InitialDP]
    Note over gsmSCF: Service triggered! (InitialDP)
    gsmSCF->>gsmSSF: TCAP Continue [RequestReportBCSMEvent, ApplyCharging, Continue]
    gsmSSF->>gsmSCF: TCAP Continue [EventReportBCSM (oAnswer)]
    gsmSSF->>gsmSCF: TCAP Continue [ApplyChargingReport, EventReportBCSM (oDisconnect)]
    gsmSCF->>gsmSSF: TCAP End [ReleaseCall]
    Note over gsmSSF: Call Terminated! (ReleaseCall)
```

## 🔍 Deep Protocol Packet Breakdown
### Packet #1 - Timestamp `0.000s`
- **Network Layer**: IP: `1.1.1.1` ➔ `2.2.2.2`
- **Transport Layer**: Port: `2904` ➔ `2904` (Proto ID: `132`)
- **Signaling Layer**: OPC Point Code: `10` (`gsmSSF`) ➔ DPC Point Code: `100` (`gsmSCF`) [M2UA/M3UA]
- **TCAP Layer**: **Begin**
  - Originating Transaction ID: `06F7`
  - **Component Portion**:
    - Type: `Invoke` (ID: `1`) | Operation: **`InitialDP`** (Code: `0`)
---
### Packet #2 - Timestamp `0.000s`
- **Network Layer**: IP: `1.1.1.1` ➔ `2.2.2.2`
- **Transport Layer**: Port: `2904` ➔ `2904` (Proto ID: `132`)
- **Signaling Layer**: OPC Point Code: `100` (`gsmSCF`) ➔ DPC Point Code: `10` (`gsmSSF`) [M2UA/M3UA]
- **TCAP Layer**: **Continue**
  - Originating Transaction ID: `13B8`
  - Destination Transaction ID: `06F7`
  - **Component Portion**:
    - Type: `Invoke` (ID: `1`) | Operation: **`RequestReportBCSMEvent`** (Code: `23`)
    - Type: `Invoke` (ID: `2`) | Operation: **`ApplyCharging`** (Code: `35`)
    - Type: `Invoke` (ID: `3`) | Operation: **`Continue`** (Code: `31`)
---
### Packet #3 - Timestamp `1.000s`
- **Network Layer**: IP: `1.1.1.1` ➔ `2.2.2.2`
- **Transport Layer**: Port: `2904` ➔ `2904` (Proto ID: `132`)
- **Signaling Layer**: OPC Point Code: `10` (`gsmSSF`) ➔ DPC Point Code: `100` (`gsmSCF`) [M2UA/M3UA]
- **TCAP Layer**: **Continue**
  - Originating Transaction ID: `06F7`
  - Destination Transaction ID: `13B8`
  - **Component Portion**:
    - Type: `Invoke` (ID: `2`) | Operation: **`EventReportBCSM`** (Code: `24`)
      - Event Type: `oAnswer`
---
### Packet #4 - Timestamp `75.000s`
- **Network Layer**: IP: `1.1.1.1` ➔ `2.2.2.2`
- **Transport Layer**: Port: `2904` ➔ `2904` (Proto ID: `132`)
- **Signaling Layer**: OPC Point Code: `10` (`gsmSSF`) ➔ DPC Point Code: `100` (`gsmSCF`) [M2UA/M3UA]
- **TCAP Layer**: **Continue**
  - Originating Transaction ID: `EC0F`
  - Destination Transaction ID: `0D7C`
  - **Component Portion**:
    - Type: `Invoke` (ID: `3`) | Operation: **`ApplyChargingReport`** (Code: `36`)
    - Type: `Invoke` (ID: `4`) | Operation: **`EventReportBCSM`** (Code: `24`)
      - Event Type: `oDisconnect`
---
### Packet #5 - Timestamp `75.000s`
- **Network Layer**: IP: `1.1.1.1` ➔ `2.2.2.2`
- **Transport Layer**: Port: `2904` ➔ `2904` (Proto ID: `132`)
- **Signaling Layer**: OPC Point Code: `100` (`gsmSCF`) ➔ DPC Point Code: `10` (`gsmSSF`) [M2UA/M3UA]
- **TCAP Layer**: **End**
  - Destination Transaction ID: `EC0F`
  - **Component Portion**:
    - Type: `Invoke` (ID: `4`) | Operation: **`ReleaseCall`** (Code: `22`)
---