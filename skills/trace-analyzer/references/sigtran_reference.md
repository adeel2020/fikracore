# SIGTRAN and CAMEL Reference Manual

This reference guide provides deep protocol information about the telecommunication signaling layers parsed by the trace-analyzer skill.

---

## 📡 1. SIGTRAN Protocol Stack

SIGTRAN (Signaling Transport) describes a suite of protocols designed to carry SS7 signaling packets over standard IP networks. The stack parsed by the trace analyzer consists of:

*   **SCTP (Stream Control Transmission Protocol):** A transport layer protocol (IP protocol 132) that provides robust, multi-stream, connection-oriented packet delivery, replacing TCP/UDP for signaling.
*   **M2UA / M3UA (MTP User Adaptation):** Adaptation layers that sit on top of SCTP to transport SS7 MTP2/MTP3 payloads respectively.
*   **SCCP (Signaling Connection Control Part):** Provides network services such as Global Title Translation (GTT) and routing of database transactions.
*   **TCAP (Transaction Capabilities Application Part):** Manages transaction dialogues between remote network endpoints.
*   **CAMEL (Customized Applications for Mobile network Enhanced Logic):** The application layer protocol used to trigger value-added prepaid services inside the core switching network.

---

## 🗺️ 2. MTP3 Point Codes

The Routing Label in SIGTRAN holds the **Originating Point Code (OPC)** and **Destination Point Code (DPC)**. 

### ITU-T 14-bit Point Code Format
In ITU networks, point codes are represented as 14-bit integers. The routing label consists of a 32-bit little-endian value containing:
*   **DPC (Destination Point Code):** Bits 0-13 (14 bits)
*   **OPC (Originating Point Code):** Bits 14-27 (14 bits)
*   **SLS (Signaling Link Selection):** Bits 28-31 (4 bits)

Calculation formulas in Python:
```python
dpc = routing_label & 0x3FFF
opc = (routing_label >> 14) & 0x3FFF
sls = (routing_label >> 28) & 0x0F
```

---

## 🏷️ 3. TCAP and CAMEL/MAP Operation Codes

### TCAP Message Tags
*   `0x62` (98 decimal): **Begin** (Starts a signaling dialogue)
*   `0x65` (101 decimal): **Continue** (Maintains an active conversation)
*   `0x64` (100 decimal): **End** (Normally terminates a dialogue)
*   `0x67` (103 decimal): **Abort** (Abnormally tears down a dialogue)

### CAMEL Operation Codes (Local Integer Opcodes)
*   `0`: **`InitialDP`** (Trigger point starting the session)
*   `23` (`0x17`): **`RequestReportBCSMEvent`** (Instructs switch to monitor events)
*   `20` (`0x14`): **`Connect`** (Instructs switch to route the call)
*   `22` (`0x16`): **`ReleaseCall`** (Terminates the call)
*   `24` (`0x18`): **`EventReportBCSM`** (Reports monitored call events like Answer, Disconnect, or Failure)
*   `35` (`0x23`): **`ApplyCharging`** (Initiates billing parameters)
*   `36` (`0x24`): **`ApplyChargingReport`** (Sends billing report back to control server)
*   `31` (`0x1F`): **`Continue`** (Proceeds with normal routing)
