"""Global Human-Readable Presentation & Terminology Resolver for FikraCore Telecom Brain.

Provides consistent, leadership-ready, human-readable terminology across CLI,
Markdown/JSON reports, UI presentation models, and Mark / Zaki assistant responses.
"""

from __future__ import annotations

import re
from typing import Any


KNOWN_ACRONYMS: dict[str, str] = {
    "UPF": "User Plane Function",
    "PGW": "Packet Gateway",
    "MME": "Mobility Management Entity",
    "DNN": "Data Network Name",
    "APN": "Access Point Name",
    "IMS": "IP Multimedia Subsystem",
    "OCS": "Online Charging System",
    "PCF": "Policy Control Function",
    "DRA": "Diameter Routing Agent",
    "SBC": "Session Border Controller",
    "OSS": "Operations Support System",
    "BSS": "Business Support System",
    "PE": "Provider Edge Router",
    "PE-RTR": "Provider Edge Router",
    "DC-GW": "Data Center Gateway",
    "NFVI": "Network Function Virtualization Infrastructure",
    "K8S": "Kubernetes Cluster",
    "DB": "Database Cluster",
    "LB": "Load Balancer",
    "FW": "Firewall",
    "AMF": "Access and Mobility Management Function",
    "SMF": "Session Management Function",
    "AUSF": "Authentication Server Function",
    "UDM": "Unified Data Management",
    "UDR": "Unified Data Repository",
    "NSSF": "Network Slice Selection Function",
    "NEF": "Network Exposure Function",
    "NRF": "Network Repository Function",
    "GNB": "Next Generation NodeB",
    "ENB": "Evolved NodeB",
    "RAN": "Radio Access Network",
    "VRF": "Virtual Routing and Forwarding Instance",
    "MPLS": "Multiprotocol Label Switching",
    "BGP": "Border Gateway Protocol",
    "SCTP": "Stream Control Transmission Protocol",
    "GTP": "GPRS Tunnelling Protocol",
    "CRM": "Customer Relationship Management",
    "IP": "Internet Protocol",
    "DC": "Data Center Facility",
    "POWER": "Power Feed",
    "RCA": "Root Cause Analysis",
    "NMS": "Network Management System",
    "CMDB": "Configuration Management Database",
    "SME": "Subject Matter Expert",
    "HITL": "Human In The Loop",
    "KPI": "Key Performance Indicator",
    "SLA": "Service Level Agreement",
}

VENDOR_PROTOCOL_TERMS: dict[str, str] = {
    "Gy": "Diameter Credit-Control Interface (Gy)",
    "Gx": "Diameter Policy Interface (Gx)",
    "Sy": "Diameter Spending Limit Interface (Sy)",
    "N3": "5G User Plane Interface (N3)",
    "N4": "Control and User Plane Separation Interface (N4)",
    "N6": "Data Network Interconnect Interface (N6)",
    "UGW": "Huawei User Gateway (UGW)",
    "GTP-U": "GTP User Plane Tunnel (GTP-U)",
    "GTP-C": "GTP Control Plane Protocol (GTP-C)",
    "BGP": "Border Gateway Protocol (BGP)",
    "MPLS": "Multiprotocol Label Switching (MPLS)",
    "SCTP": "Stream Control Transmission Protocol (SCTP)",
}

RELATIONSHIP_DISPLAY_NAMES: dict[str, str] = {
    "depends-on": "Depends on",
    "depends_on": "Depends on",
    "routes-through": "Routes through",
    "routes_through": "Routes through",
    "hosted-on": "Hosted on",
    "hosted_on": "Hosted on",
    "runs-on": "Runs on",
    "runs_on": "Runs on",
    "member-of": "Member of",
    "member_of": "Member of",
    "monitored-by": "Monitored by",
    "monitored_by": "Monitored by",
    "supports-service": "Supports service",
    "supports_service": "Supports service",
    "serves": "Serves",
    "fails-over-to": "Fails over to",
    "fails_over_to": "Fails over to",
    "powered-by": "Powered by",
    "powered_by": "Powered by",
    "connected-to": "Connected to",
    "connected_to": "Connected to",
    "carried-by": "Carried by",
    "carried_by": "Carried by",
    "backhauled-by": "Backhauled by",
    "backhauled_by": "Backhauled by",
    "charges-via": "Charges via",
    "charges_via": "Charges via",
    "authenticates-via": "Authenticates via",
    "authenticates_via": "Authenticates via",
    "resolves-via": "Resolves via",
    "resolves_via": "Resolves via",
    "timed-by": "Timed by",
    "timed_by": "Timed by",
    "uses-database": "Uses database",
    "uses_database": "Uses database",
    "uses-cache": "Uses cache",
    "uses_cache": "Uses cache",
    "uses-message-bus": "Uses message bus",
    "uses_message_bus": "Uses message bus",
    "provisioned-by": "Provisioned by",
    "provisioned_by": "Provisioned by",
}

EVIDENCE_DISPLAY_NAMES: dict[str, str] = {
    "prometheus_metric": "Performance Metric",
    "loki_log": "Network / Application Log",
    "grafana_alert": "Monitoring Alert",
    "tempo_trace": "Distributed Trace",
    "change_record": "Change Record",
    "customer_ticket": "Customer Ticket",
    "topology_neighbor": "Topology Neighbor Information",
    "routing_table": "Routing Table",
    "interface_counters": "Interface Counters",
    "traceroute": "Network Path Trace",
    "mpls_lsp": "MPLS Label Switched Path",
    "bgp_state": "Border Gateway Protocol State",
    "arp_table": "ARP / Neighbor Discovery Table",
    "alarms": "Network Alarm",
    "logs": "Network / Application Log",
    "metrics": "Performance Metric",
    "kpis": "Service Key Performance Indicator",
    "traces": "Distributed Protocol Trace",
    "changes": "Change Record",
    "tickets": "Customer Ticket",
    "recovery": "Service Recovery Signal",
}


class PresentationNamingResolver:
    """Stateful or stateless resolver mapping machine IDs to human-readable names."""

    def __init__(self) -> None:
        self._expanded_acronyms: set[str] = set()

    def reset_expansion_cache(self) -> None:
        """Clear cache of expanded acronyms (e.g. for a new document or session)."""
        self._expanded_acronyms.clear()

    def expand_acronym(self, acronym: str, force_expand: bool | None = None) -> str:
        """Expand acronym on first use: 'User Plane Function (UPF)'. Subsequent: 'UPF'.
        
        If force_expand is True, always expand. If force_expand is False, always return acronym.
        If unknown acronym, returns the original acronym without fabricating an expansion.
        """
        raw = acronym.upper().strip()
        full = KNOWN_ACRONYMS.get(raw)
        if not full:
            return acronym

        if force_expand is True:
            return f"{full} ({raw})"
        if force_expand is False:
            return raw

        if raw not in self._expanded_acronyms:
            self._expanded_acronyms.add(raw)
            return f"{full} ({raw})"
        return raw

    def format_protocol_term(self, term: str) -> str:
        """Format protocol/interface term with vendor/standard name."""
        return VENDOR_PROTOCOL_TERMS.get(term, term)

    def to_relation_label(self, link_type: str) -> str:
        """Convert machine relationship enum/string to human-readable label."""
        cleaned = link_type.strip().lower().replace("_", "-")
        if cleaned in RELATIONSHIP_DISPLAY_NAMES:
            return RELATIONSHIP_DISPLAY_NAMES[cleaned]
        # Fallback: clean title case
        return cleaned.replace("-", " ").capitalize()

    def to_evidence_label(self, evidence_type: str) -> str:
        """Convert evidence source/type to human-readable label."""
        cleaned = evidence_type.strip().lower()
        if cleaned in EVIDENCE_DISPLAY_NAMES:
            return EVIDENCE_DISPLAY_NAMES[cleaned]
        return cleaned.replace("_", " ").title()

    def to_display_name(self, canonical_id: str) -> str:
        """Translate machine or slug entity ID into a human-readable display name.
        
        Preserves original canonical ID in format_entity() for technical traceability.
        Never fabricates an expansion for unknown technical acronyms.
        """
        if not canonical_id or not isinstance(canonical_id, str):
            return "Unknown Entity"

        clean_id = canonical_id.strip()

        # Handle path-like slug: topology/transport/routers/ip-rtr-01
        if "/" in clean_id:
            parts = clean_id.split("/")
            leaf = parts[-1]
            category = parts[-2] if len(parts) >= 2 else ""
            if "router" in category or "rtr" in leaf:
                num_match = re.search(r"\d+", leaf)
                num = num_match.group(0) if num_match else leaf
                if "pe" in leaf:
                    return f"Provider Edge Router-{int(num):02d}" if num.isdigit() else f"Provider Edge Router-{num}"
                return f"Transport Router-{int(num):02d}" if num.isdigit() else f"Transport Router-{num}"
            if "upf" in leaf:
                num_match = re.search(r"\d+", leaf)
                num = num_match.group(0) if num_match else leaf
                return f"User Plane Function-{int(num):02d}" if num.isdigit() else f"User Plane Function-{num}"
            if "dc-gw" in leaf:
                num_match = re.search(r"\d+", leaf)
                num = num_match.group(0) if num_match else leaf
                return f"Data Center Gateway-{int(num):02d}" if num.isdigit() else f"Data Center Gateway-{num}"
            # Fallback for slug: preserve uppercase code like abc-17 -> ABC-17
            m = re.match(r"^([a-zA-Z]+)[-_](\d+)$", leaf)
            if m:
                return f"{m.group(1).upper()}-{m.group(2)}"
            return leaf.replace("-", " ").replace("_", " ").title()

        # Handle colon-separated identifiers: IP:PE:RTR-21, SA5G:UPF:003, INFRA:POWER:A
        if ":" in clean_id:
            tokens = clean_id.split(":")
            domain = tokens[0].upper()
            sub = tokens[1].upper() if len(tokens) >= 2 else ""
            leaf = tokens[-1]

            if "POWER" in tokens:
                feed = tokens[-1]
                return f"Power Feed {feed}"
            if "DC" in tokens:
                facility = tokens[-1]
                return f"Data Center Facility {facility}"
            if "UPF" in tokens or "UPF" in leaf:
                num_match = re.search(r"\d+", leaf)
                num = num_match.group(0) if num_match else leaf
                return f"User Plane Function-{int(num):02d}" if num.isdigit() else f"User Plane Function-{num}"
            if "PE" in tokens or "PE" in sub:
                num_match = re.search(r"\d+", leaf)
                num = num_match.group(0) if num_match else leaf
                return f"Provider Edge Router-{int(num):02d}" if num.isdigit() else f"Provider Edge Router-{num}"
            if "VRF" in tokens:
                return f"Virtual Routing and Forwarding ({leaf})"
            if "TICKET" in tokens:
                num_match = re.search(r"\d+", leaf)
                num = num_match.group(0) if num_match else leaf
                return f"Customer Ticket-{int(num):02d}" if num.isdigit() else f"Customer Ticket-{num}"
            if "RTR" in leaf or "ROUTER" in leaf:
                num_match = re.search(r"\d+", leaf)
                num = num_match.group(0) if num_match else leaf
                return f"Transport Router-{int(num):02d}" if num.isdigit() else f"Transport Router-{num}"

            # Fallback colon entity
            name_parts = [t.title() for t in tokens if t not in {domain}]
            return f"{domain} {' '.join(name_parts)}".strip()

        # Handle dash patterns: MPLS-PE7, IP-RTR-01, DC-GW-01
        upper = clean_id.upper()
        if "MPLS-PE" in upper or "MPLS_PE" in upper:
            num_match = re.search(r"\d+", clean_id)
            num = num_match.group(0) if num_match else clean_id
            return f"MPLS Edge Router-{int(num):02d}" if num.isdigit() else f"MPLS Edge Router-{num}"
        if "IP-RTR" in upper or "IP_RTR" in upper:
            num_match = re.search(r"\d+", clean_id)
            num = num_match.group(0) if num_match else clean_id
            return f"Transport Router-{int(num):02d}" if num.isdigit() else f"Transport Router-{num}"
        if "DC-GW" in upper or "DC_GW" in upper:
            num_match = re.search(r"\d+", clean_id)
            num = num_match.group(0) if num_match else clean_id
            return f"Data Center Gateway-{int(num):02d}" if num.isdigit() else f"Data Center Gateway-{num}"

        # Fallback Rule: clean up formatting without inventing unknown acronym meaning
        # e.g., vendor-x/abc-17 -> ABC-17
        return clean_id.replace("_", "-")

    def format_entity(self, canonical_id: str, include_canonical: bool = True) -> dict[str, str]:
        """Return structured display pattern with display_name and canonical_id."""
        display = self.to_display_name(canonical_id)
        result = {"display_name": display, "canonical_id": canonical_id}
        if include_canonical:
            result["formatted"] = f"{display} (canonical: {canonical_id})"
        else:
            result["formatted"] = display
        return result

    def format_text(self, text: str) -> str:
        """Format prose text by replacing raw relationship enums and evidence tags."""
        out = text
        for rel_machine, rel_human in RELATIONSHIP_DISPLAY_NAMES.items():
            out = re.sub(rf"\b{re.escape(rel_machine.upper())}\b", rel_human, out)
            out = re.sub(rf"\b{re.escape(rel_machine)}\b", rel_human.lower(), out)
        for ev_machine, ev_human in EVIDENCE_DISPLAY_NAMES.items():
            out = re.sub(rf"\b{re.escape(ev_machine)}\b", ev_human, out)
        return out


# Global singleton instance for presentation layer
default_naming_resolver = PresentationNamingResolver()

__all__ = [
    "KNOWN_ACRONYMS",
    "VENDOR_PROTOCOL_TERMS",
    "RELATIONSHIP_DISPLAY_NAMES",
    "EVIDENCE_DISPLAY_NAMES",
    "PresentationNamingResolver",
    "default_naming_resolver",
]
