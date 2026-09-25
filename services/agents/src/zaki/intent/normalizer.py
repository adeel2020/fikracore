"""Operator Intent Normalizer for Zaki v1."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from ..domain.contracts.intent import FCAPSClassification, IntentSpec, OperatorIntentContract
from ..domain.enums import AuthorityLevel, FCAPSCategory, RiskMode


class IntentNormalizer:
    """Normalizes natural language statements into structured TM Forum-aligned intent."""

    DOMAIN_KEYWORDS = {
        "IP_TRANSPORT": ["transport", "router", "bgp", "mpls", "interface", "link", "switch", "ospf", "pe-router", "dc-gw"],
        "PS": ["ps", "packet core", "upf", "smf", "amf", "5g core", "pdu", "pfcp", "user plane", "data session", "gtp"],
        "CS": ["cs", "circuit", "msc", "mgw", "voice", "isup", "tcap", "call drop"],
        "RAN": ["ran", "gnb", "gnodeb", "enodeb", "cell", "rf", "antenna", "handover", "coverage", "sector"],
        "IN_OCS": ["in", "ocs", "charging", "billing", "rating", "diameter", "quota", "balance"],
        "VAS": ["vas", "smsc", "mms", "ussd", "voicemail"],
        "IGW": ["igw", "international", "gateway", "peering", "roaming"],
        "INFRA": ["infra", "power", "hvac", "ups", "generator", "chassis", "temperature", "rack"],
        "IT": ["it", "crm", "ldap", "server", "database", "portal"],
    }

    FCAPS_RULES = [
        (FCAPSCategory.FAULT, ["alarm", "fail", "degrad", "outage", "down", "error", "drop", "broken", "issue", "anomaly", "investigate"]),
        (FCAPSCategory.CHANGE, ["change", "upgrade", "deploy", "patch", "maintenance", "reconfig", "rollback", "update"]),
        (FCAPSCategory.PERFORMANCE, ["slow", "latency", "jitter", "kpi", "throughput", "packet loss", "congestion", "capacity", "utilization"]),
        (FCAPSCategory.ACCEPTANCE, ["verify", "test", "check", "accept", "validate", "audit", "compliance", "inspection"]),
        (FCAPSCategory.SECURITY, ["breach", "unauthorized", "attack", "ddos", "intrusion", "firewall", "cve", "vulnerability"]),
    ]

    def normalize(
        self,
        query: str,
        requested_by: str = "operator",
        requested_authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE,
        risk_mode: RiskMode = RiskMode.ANALYZE_ONLY,
    ) -> OperatorIntentContract:
        q_clean = query.strip()
        q_lower = q_clean.lower()

        # Domain classification
        detected_domain = "PS"
        for dom, keywords in self.DOMAIN_KEYWORDS.items():
            if any(re.search(rf"\b{re.escape(kw)}\b", q_lower) for kw in keywords):
                detected_domain = dom
                break

        # FCAPS classification
        primary_fcaps = FCAPSCategory.FAULT
        secondary_fcaps: List[FCAPSCategory] = []
        for cat, kw_list in self.FCAPS_RULES:
            if any(re.search(rf"\b{re.escape(kw)}\b", q_lower) for kw in kw_list):
                if primary_fcaps == FCAPSCategory.FAULT and cat != FCAPSCategory.FAULT:
                    primary_fcaps = cat
                elif cat not in secondary_fcaps and cat != primary_fcaps:
                    secondary_fcaps.append(cat)

        # Region / Scope extraction
        region_match = re.search(r"\b(region[-\s]?\d+|site[-\s]?\w+|cluster[-\s]?\w+|dc[-\s]?\w+)\b", q_lower)
        scope = {"region": region_match.group(1).upper()} if region_match else {"region": "ALL"}

        # Subject extraction
        subject = {"domain": detected_domain}
        if "mobile data" in q_lower or "data service" in q_lower or "5g" in q_lower:
            subject["service"] = "Mobile Data"
        elif "voice" in q_lower or "volte" in q_lower:
            subject["service"] = "VoLTE"
        else:
            subject["service"] = "General Telecommunications"

        # Objective extraction
        objective = "identify probable causal driver and affected dependencies"
        if "why" in q_lower or "explain" in q_lower:
            intent_type = "EXPLAIN_HYPOTHESIS"
            objective = "explain causal ranking and evidence basis"
        elif "missing" in q_lower or "gap" in q_lower:
            intent_type = "DISCOVER_KNOWLEDGE_GAPS"
            objective = "detect unmodelled propagation and knowledge gaps"
        elif "remediat" in q_lower or "fix" in q_lower or "action" in q_lower:
            intent_type = "PREPARE_REMEDIATION"
            objective = "propose governed remediation actions"
        elif "handover" in q_lower or "shift" in q_lower:
            intent_type = "SHIFT_HANDOVER"
            objective = "transfer operational context across shifts"
        else:
            intent_type = "INVESTIGATE_SERVICE_DEGRADATION"

        spec = IntentSpec(
            type=intent_type,
            natural_language=q_clean,
            subject=subject,
            scope=scope,
            objective=objective,
            requested_authority=requested_authority,
            risk_mode=risk_mode,
            requested_by=requested_by,
            fcaps=FCAPSClassification(
                primary=primary_fcaps,
                secondary=secondary_fcaps,
                domain=detected_domain,
                confidence=0.92,
                clarification_required=False,
            ),
        )

        return OperatorIntentContract(spec=spec)
