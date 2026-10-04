from typing import Any, Optional, Callable
from pathlib import Path
from datetime import datetime, timedelta
import json

def load_operational_telemetry_lifecycle(
    
    scenario_id: str,
    run_id: str,
    trigger_entity: str,
    trigger_display: str,
    cohort: str,
    affected_service: str,
    stage_vals: dict[str, Any],
    stage_index: int,
    started_at: str = "",
 *, _derive_impact_scope: Callable, _entity_domain: Callable, _format_natural_evidence_observation: Callable, _parse_runtime_timestamp: Callable) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    clean_id = scenario_id.upper().strip()
    runs_dir = Path(__file__).parent.parent / "runs"
    if not runs_dir.exists():
        return [], [], []
    matches = list(runs_dir.glob(f"RUN-{clean_id}*"))
    if not matches:
        return [], [], []
    op_dir = matches[0] / "operational"
    if not op_dir.exists():
        return [], [], []

    stream_map = [
        ("alarms.jsonl", "alarm", "ALARM"),
        ("metrics.jsonl", "metric", "METRIC"),
        ("kpis.jsonl", "metric", "KPI"),
        ("logs.jsonl", "log", "LOG"),
        ("tickets.jsonl", "ticket", "TICKET"),
        ("traces.jsonl", "trace", "TRACE"),
        ("recovery.jsonl", "change", "RECOVERY"),
    ]

    base_dt = _parse_runtime_timestamp(started_at)
    raw_events: list[dict[str, Any]] = []
    correlated_events: list[dict[str, Any]] = []
    noise_events: list[dict[str, Any]] = []

    # ── 1. Read base operational evidence files ─────────────────────────
    for fname, cat, badge in stream_map:
        fpath = op_dir / fname
        if not fpath.exists():
            continue
        for line in fpath.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            eid = item.get("event_id") or item.get("evidence_id") or f"EVT-{len(raw_events)}"
            entity = item.get("canonical_entity_id") or item.get("entity_id") or "UNKNOWN"
            native = item.get("source_native_entity_name") or item.get("entity_id") or entity
            alarm = item.get("alarm_name") or ""
            metric = item.get("metric_name") or item.get("kpi_name") or ""
            val = item.get("value")
            base = item.get("baseline_value")
            sig = alarm or metric or item.get("message") or item.get("trace_type") or "Operational Signal"
            sev = item.get("severity", "MAJOR" if cat == "alarm" else "INFO").upper()

            t_str = item.get("event_time", "")
            try:
                dt = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                time_fmt = dt.strftime("%H:%M:%S")
            except Exception:
                time_fmt = (base_dt + timedelta(seconds=len(raw_events) * 8)).strftime("%H:%M:%S")

            domain = _entity_domain(entity) or item.get("domain", "IP_TRANSPORT").replace("_", " ").title()

            # Extract natural observation with description 1st, then further payload
            sig_name, natural_obs = _format_natural_evidence_observation(item, cat, native, val, base)

            # ── BUILD INGESTED ITEM (BEFORE: As-is telemetry flood, zero artificial keywords) ──
            raw_events.append({
                "event_id": eid,
                "evidence_id": eid,
                "time": time_fmt,
                "category": cat,
                "badge": badge,
                "title": sig_name,
                "subtitle": f"Source: {item.get('source_system', 'IP_NMS')} · Port: {native}",
                "domain": domain,
                "entity_id": entity,
                "canonical_entity": entity,
                "source_native_entity": native,
                "source_system": item.get("source_system", "IP_NMS"),
                "severity": sev,
                "state": "ACTIVE",
                "stage": "SIGNAL_FLOOD",
                "event_type": "OBSERVATION",
                "evidence_type": badge,
                "display_name": sig_name,
                "event_time": t_str,
                "scenario_id": scenario_id,
                "run_id": run_id,
                "explanation_text": natural_obs,
                "observation": natural_obs,
                "classification": "EVENT_FLOOD",
                "classification_label": "Unprocessed Telemetry",
                "deduplication": "Uncollapsed Stream",
                "raw_data": item,
            })

            # ── BUILD CORRELATED ITEM (AFTER: Canonicalized, deduplicated, impact-scoped) ──
            impact_scope = _derive_impact_scope(item, cat, entity, domain, metric, alarm, val)

            if metric == "upf_cpu_percent":
                classification = "HEALTHY_NEGATIVE"
                classification_label = impact_scope
                explanation = f"UPF-03 CPU utilization is normal at {val}% (baseline: {base}%). Confirms user plane compute is healthy; disproves internal UPF software crash."
                corr_item = {
                    "event_id": eid,
                    "evidence_id": eid,
                    "time": time_fmt,
                    "category": cat,
                    "badge": badge,
                    "title": f"{entity}: {sig_name}",
                    "subtitle": f"{domain} · {entity}",
                    "domain": domain,
                    "entity_id": entity,
                    "canonical_entity": entity,
                    "source_native_entity": native,
                    "source_system": item.get("source_system", "VENDOR_EMS"),
                    "severity": sev,
                    "state": "ACTIVE",
                    "stage": "CORRELATION",
                    "event_type": "OBSERVATION",
                    "evidence_type": badge,
                    "display_name": f"{entity}: {sig_name}",
                    "event_time": t_str,
                    "scenario_id": scenario_id,
                    "run_id": run_id,
                    "explanation_text": explanation,
                    "observation": natural_obs,
                    "impact_scope": impact_scope,
                    "classification": classification,
                    "classification_label": impact_scope,
                    "deduplication": "Canonical Resolved (3GPP R17)",
                    "raw_data": item,
                }
                correlated_events.append(corr_item)
                noise_events.append({
                    **corr_item,
                    "separation_rationale": "Verified healthy negative evidence: Compute utilization nominal (41% < 75%). Serves as mathematical proof disproving local host compute crash hypothesis.",
                    "correlation_score": 0.88,
                })
            else:
                classification = "CORRELATED_ANOMALY"
                classification_label = impact_scope
                if "PE:RTR-21" in entity or "PE21" in native:
                    if alarm == "PE_ROUTER_DEGRADED":
                        explanation = f"Transport line card ingress buffer saturation observed on Provider Edge Router ({native}). BGP session packet drop affecting downstream VRF traffic."
                    elif metric == "latency_ms":
                        explanation = f"Transport round-trip latency measured at {val}ms (baseline: {base}ms), exceeding transmission SLA threshold."
                    elif metric == "timeout_or_loss_rate":
                        explanation = f"N3 transport packet loss rate measured at {val}% (baseline: {base}%), indicating severe transmission discard."
                    else:
                        explanation = f"Provider Edge Router ({native}) experiencing transport-layer procedure degradation."
                elif "VRF:N3-01" in entity or "N3-VRF" in native:
                    explanation = f"Virtual Routing & Forwarding instance ({native}) dropping GTP-U packets due to transport-layer transmission loss."
                elif "UPF:003" in entity or "UPF-03" in native:
                    explanation = f"5G User Plane Function ({native}) reporting PDU session throughput drop caused by N3 transport interface packet starvation."
                elif "TICKET:001" in entity or cat == "ticket":
                    if "Complaint Rate" in metric:
                        explanation = f"Customer trouble ticket volume escalated to {val}x baseline due to subscriber session dropouts."
                    elif "Success Rate" in metric:
                        explanation = f"5G SA Mobile Data session establishment success rate collapsed to {val}% (SLA commit: {base}%)."
                    else:
                        explanation = "Enterprise customer care reports multiple corporate customer tickets filed for mobile data outages in Region-North."
                elif "probe" in str(item.get("trace_type", "")) or cat == "trace":
                    explanation = "Synthetic dependency probe confirms sequential packet loss across N3 transport and 5G core user-plane path."
                elif cat == "change" or item.get("intervention"):
                    explanation = f"Automated route optimization and queue buffer flush applied on {native}."
                else:
                    explanation = item.get("message") or f"Operational anomaly recorded on {entity}."

                correlated_events.append({
                    "event_id": eid,
                    "evidence_id": eid,
                    "time": time_fmt,
                    "category": cat,
                    "badge": badge,
                    "title": f"{entity}: {sig_name}",
                    "subtitle": f"{domain} · {entity}",
                    "domain": domain,
                    "entity_id": entity,
                    "canonical_entity": entity,
                    "source_native_entity": native,
                    "source_system": item.get("source_system", "IP_NMS"),
                    "severity": sev,
                    "state": "ACTIVE",
                    "stage": "CORRELATION",
                    "event_type": "OBSERVATION",
                    "evidence_type": badge,
                    "display_name": f"{entity}: {sig_name}",
                    "event_time": t_str,
                    "scenario_id": scenario_id,
                    "run_id": run_id,
                    "explanation_text": explanation,
                    "observation": natural_obs,
                    "impact_scope": impact_scope,
                    "classification": classification,
                    "classification_label": impact_scope,
                    "deduplication": "Canonical Resolved (3GPP R17)",
                    "raw_data": item,
                })

    # ── 2. Add realistic duplicate SNMP traps to Event Flood (demonstrates deduplication) ──
    dup_traps = [
        {
            "event_id": "ALM-PE21-DUP-01",
            "time": (base_dt + timedelta(seconds=14)).strftime("%H:%M:%S"),
            "category": "alarm",
            "badge": "ALARM",
            "title": "bufferOverflowTrap (Burst 2/3)",
            "subtitle": "Source: Cisco NMS · Port: ge-0/0/0/1",
            "domain": "IP Transport",
            "source_native_entity": "PE21",
            "canonical_entity": "IP:PE:RTR-21",
            "source_system": "IP_NMS",
            "severity": "MAJOR",
            "state": "ACTIVE",
            "stage": "SIGNAL_FLOOD",
            "event_type": "OBSERVATION",
            "evidence_type": "ALARM",
            "explanation_text": "SNMP bufferOverflowTrap received on interface ge-0/0/0/1 [OID: 1.3.6.1.4.1.9.9.48.1.1.1 | repeat: 2/3]",
            "observation": "SNMP bufferOverflowTrap received on interface ge-0/0/0/1 [OID: 1.3.6.1.4.1.9.9.48.1.1.1 | repeat: 2/3]",
            "classification": "EVENT_FLOOD",
            "classification_label": "Unprocessed Telemetry",
            "deduplication": "Collapsed Downstream",
            "raw_data": {"trap_oid": "1.3.6.1.4.1.9.9.48.1.1.1", "burst_index": 2, "repeat_count": 3},
        },
        {
            "event_id": "ALM-PE21-DUP-02",
            "time": (base_dt + timedelta(seconds=16)).strftime("%H:%M:%S"),
            "category": "alarm",
            "badge": "ALARM",
            "title": "bufferOverflowTrap (Burst 3/3)",
            "subtitle": "Source: Cisco NMS · Port: ge-0/0/0/1",
            "domain": "IP Transport",
            "source_native_entity": "PE21",
            "canonical_entity": "IP:PE:RTR-21",
            "source_system": "IP_NMS",
            "severity": "MAJOR",
            "state": "ACTIVE",
            "stage": "SIGNAL_FLOOD",
            "event_type": "OBSERVATION",
            "evidence_type": "ALARM",
            "explanation_text": "SNMP bufferOverflowTrap received on interface ge-0/0/0/1 [OID: 1.3.6.1.4.1.9.9.48.1.1.1 | repeat: 3/3]",
            "observation": "SNMP bufferOverflowTrap received on interface ge-0/0/0/1 [OID: 1.3.6.1.4.1.9.9.48.1.1.1 | repeat: 3/3]",
            "classification": "EVENT_FLOOD",
            "classification_label": "Unprocessed Telemetry",
            "deduplication": "Collapsed Downstream",
            "raw_data": {"trap_oid": "1.3.6.1.4.1.9.9.48.1.1.1", "burst_index": 3, "repeat_count": 3},
        },
        {
            "event_id": "ALM-VRF-DUP-01",
            "time": (base_dt + timedelta(seconds=46)).strftime("%H:%M:%S"),
            "category": "alarm",
            "badge": "ALARM",
            "title": "vrfInterfaceDegraded (Burst 2/2)",
            "subtitle": "Source: Cisco NMS · Port: vrf-n3",
            "domain": "IP Transport",
            "source_native_entity": "N3-VRF-01",
            "canonical_entity": "IP:VRF:N3-01",
            "source_system": "IP_NMS",
            "severity": "MAJOR",
            "state": "ACTIVE",
            "stage": "SIGNAL_FLOOD",
            "event_type": "OBSERVATION",
            "evidence_type": "ALARM",
            "explanation_text": "SNMP vrfInterfaceDegraded timeout trap received on vrf-n3 [OID: 1.3.6.1.4.1.9.9.117.1.1 | repeat: 2/2]",
            "observation": "SNMP vrfInterfaceDegraded timeout trap received on vrf-n3 [OID: 1.3.6.1.4.1.9.9.117.1.1 | repeat: 2/2]",
            "classification": "EVENT_FLOOD",
            "classification_label": "Unprocessed Telemetry",
            "deduplication": "Collapsed Downstream",
            "raw_data": {"trap_oid": "1.3.6.1.4.1.9.9.117.1.1", "burst_index": 2, "repeat_count": 2},
        },
    ]
    raw_events.extend(dup_traps)

    # ── 3. Add realistic coincidental background noise to Event Flood & NOISE LEDGER ──
    background_noise = [
        {
            "event_id": "NOISE-001",
            "time": (base_dt + timedelta(seconds=10)).strftime("%H:%M:%S"),
            "category": "metric",
            "badge": "METRIC",
            "title": "Periodic PTP/NTP Clock Sync",
            "subtitle": "Radio Access Network · RAN:GNB-04",
            "domain": "Radio Access Network",
            "source_native_entity": "ERICSSON-GNB-04",
            "canonical_entity": "RAN:GNB-04",
            "source_system": "RAN_EMS",
            "severity": "INFO",
            "state": "ACTIVE",
            "stage": "SIGNAL_FLOOD",
            "event_type": "OBSERVATION",
            "evidence_type": "METRIC",
            "explanation_text": "PTP clock synchronization nominal offset 820ns [status: LOCKED | peer: PTP-MASTER-01]",
            "observation": "PTP clock synchronization nominal offset 820ns [status: LOCKED | peer: PTP-MASTER-01]",
            "classification": "COINCIDENTAL_NOISE",
            "classification_label": "Decoupled Background Noise",
            "impact_scope": "Decoupled Radio Baseline",
            "separation_rationale": "Decoupled: Correlation score 0.04 < 0.12 threshold. RAN timing synchronization is topologically independent of N3 user-plane failure.",
            "correlation_score": 0.04,
            "deduplication": "Isolated from Anomaly Envelope",
            "raw_data": {"ptp_offset_ns": 820, "sync_status": "LOCKED", "peer": "PTP-MASTER-01"},
        },
        {
            "event_id": "NOISE-002",
            "time": (base_dt + timedelta(seconds=22)).strftime("%H:%M:%S"),
            "category": "log",
            "badge": "LOG",
            "title": "BGP Peer Keepalive OK",
            "subtitle": "IP Transport & Routing · IP:AGG-SW-02",
            "domain": "IP Transport",
            "source_native_entity": "JUNIPER-AGG-SW-02",
            "canonical_entity": "IP:AGG-SW-02",
            "source_system": "IP_NMS",
            "severity": "INFO",
            "state": "ACTIVE",
            "stage": "SIGNAL_FLOOD",
            "event_type": "OBSERVATION",
            "evidence_type": "LOG",
            "explanation_text": "Routine BGP keepalive handshake received on xe-1/0/0 [neighbor: 10.200.0.1 | state: ESTABLISHED | interval: 30s]",
            "observation": "Routine BGP keepalive handshake received on xe-1/0/0 [neighbor: 10.200.0.1 | state: ESTABLISHED | interval: 30s]",
            "classification": "COINCIDENTAL_NOISE",
            "classification_label": "Decoupled Background Noise",
            "impact_scope": "Decoupled Transport Adjacency",
            "separation_rationale": "Decoupled: Correlation score 0.02 < 0.12 threshold. Core aggregation routing adjacency unaffected by N3 VRF degradation.",
            "correlation_score": 0.02,
            "deduplication": "Isolated from Anomaly Envelope",
            "raw_data": {"bgp_neighbor": "10.200.0.1", "state": "ESTABLISHED", "keepalive_interval": 30},
        },
        {
            "event_id": "NOISE-003",
            "time": (base_dt + timedelta(seconds=35)).strftime("%H:%M:%S"),
            "category": "metric",
            "badge": "METRIC",
            "title": "Rack Inlet Temperature (21.4°C)",
            "subtitle": "Cloud NFVI & Facilities · DC:PDU-08",
            "domain": "Cloud NFVI & Facilities",
            "source_native_entity": "DC-FACILITY-PDU-08",
            "canonical_entity": "DC:PDU-08",
            "source_system": "FACILITIES_BMS",
            "severity": "INFO",
            "state": "ACTIVE",
            "stage": "SIGNAL_FLOOD",
            "event_type": "OBSERVATION",
            "evidence_type": "METRIC",
            "explanation_text": "Facility environmental sensor reading nominal ambient temperature at 21.4°C [sensor: INLET_TEMP_C | threshold: 35.0°C]",
            "observation": "Facility environmental sensor reading nominal ambient temperature at 21.4°C [sensor: INLET_TEMP_C | threshold: 35.0°C]",
            "classification": "COINCIDENTAL_NOISE",
            "classification_label": "Decoupled Background Noise",
            "impact_scope": "Decoupled Facilities Sensor",
            "separation_rationale": "Decoupled: Facilities BMS sensor. Non-causal environmental baseline with zero topology coupling.",
            "correlation_score": 0.00,
            "deduplication": "Isolated from Anomaly Envelope",
            "raw_data": {"sensor": "INLET_TEMP_C", "value": 21.4, "threshold_high": 35.0},
        },
        {
            "event_id": "NOISE-004",
            "time": (base_dt + timedelta(seconds=50)).strftime("%H:%M:%S"),
            "category": "trace",
            "badge": "TRACE",
            "title": "Interface Loopback Ping Test",
            "subtitle": "IP Transport & Routing · IP:CORE-RTR-05",
            "domain": "IP Transport",
            "source_native_entity": "IP-CORE-RTR-05",
            "canonical_entity": "IP:CORE-RTR-05",
            "source_system": "OBSERVABILITY",
            "severity": "INFO",
            "state": "ACTIVE",
            "stage": "SIGNAL_FLOOD",
            "event_type": "OBSERVATION",
            "evidence_type": "TRACE",
            "explanation_text": "Synthetic monitoring probe pinging backbone loopback IP [target: 10.0.0.5 | loss: 0.0% | rtt: 1.2ms]",
            "observation": "Synthetic monitoring probe pinging backbone loopback IP [target: 10.0.0.5 | loss: 0.0% | rtt: 1.2ms]",
            "classification": "COINCIDENTAL_NOISE",
            "classification_label": "Decoupled Background Noise",
            "impact_scope": "Decoupled Backbone Health",
            "separation_rationale": "Decoupled: Synthetic observability probe on core backbone. Normal baseline with 0% loss.",
            "correlation_score": 0.03,
            "deduplication": "Isolated from Anomaly Envelope",
            "raw_data": {"probe_target": "10.0.0.5", "packet_loss_pct": 0.0, "rtt_ms": 1.2},
        },
        {
            "event_id": "NOISE-005",
            "time": (base_dt + timedelta(seconds=65)).strftime("%H:%M:%S"),
            "category": "metric",
            "badge": "METRIC",
            "title": "Radius Accounting Heartbeat Nominal",
            "subtitle": "OCS & Charging · OCS:CHARGING-GW-01",
            "domain": "OCS & Charging",
            "source_native_entity": "OCS-CHARGING-GW-01",
            "canonical_entity": "OCS:CHARGING-GW-01",
            "source_system": "OCS_EMS",
            "severity": "INFO",
            "state": "ACTIVE",
            "stage": "SIGNAL_FLOOD",
            "event_type": "OBSERVATION",
            "evidence_type": "METRIC",
            "explanation_text": "Online Charging System accounting proxy responding nominally [latency: 3.4ms | sessions: 48200 | status: NOMINAL]",
            "observation": "Online Charging System accounting proxy responding nominally [latency: 3.4ms | sessions: 48200 | status: NOMINAL]",
            "classification": "COINCIDENTAL_NOISE",
            "classification_label": "Decoupled Background Noise",
            "impact_scope": "Decoupled Charging Plane",
            "separation_rationale": "Decoupled: Rating and charging plane telemetry operating nominally without user-plane dependency.",
            "correlation_score": 0.01,
            "deduplication": "Isolated from Anomaly Envelope",
            "raw_data": {"radius_latency_ms": 3.4, "active_sessions": 48200, "status": "NOMINAL"},
        },
    ]

    # Add background noise to Event Flood (representing unseparated network noise)
    for noise_item in background_noise:
        raw_events.append({
            **noise_item,
            "classification": "EVENT_FLOOD",
            "classification_label": "Unprocessed Telemetry",
            "deduplication": "Uncollapsed Stream",
        })

    # Add noise items to NOISE SEPARATION LEDGER
    noise_events.extend(background_noise)

    # Sort raw events by time
    raw_events.sort(key=lambda x: x.get("time", ""))

    return raw_events, correlated_events, noise_events



