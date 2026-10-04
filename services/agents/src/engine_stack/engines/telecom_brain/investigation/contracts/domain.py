"""
Domain Contracts & Operational Jurisdictions
============================================
This module defines the operational jurisdiction boundaries for telecom engineering domains.

Each domain specifies:
- The standard DomainCode enum for canonical identification across gbrain.
- Managed network entity types (e.g., PE routers, UPFs, gNodeBs).
- Responsible engineering role (e.g., IP Transport SME, Core Network Engineer).
- 3GPP and standard telecommunication interfaces within its operational scope.
"""

from enum import Enum
from pydantic import Field
from .base import Contract


class DomainCode(str, Enum):
    """
    Standard telecommunications operational domains.
    Corresponds to organizational silos and technical operational boundaries in Tier-1 MNOs.
    """
    IP_TRANSPORT = "IP_TRANSPORT"             # Backhaul/Midhaul/Fronthaul IP/MPLS, SRv6, BGP routing
    PS_CORE = "PS_CORE"                       # 4G EPC (MME/SGW/PGW) & 5G SA Core (AMF/SMF/UPF)
    RAN = "RAN"                               # Radio Access Network (eNodeB, gNodeB, CU/DU, RU)
    CLOUD_INFRA = "CLOUD_INFRA"               # NFVI, OpenStack, Kubernetes, SmartNICs, Bare Metal
    IMS_VOICE = "IMS_VOICE"                   # VoLTE, VoNR, P-CSCF, S-CSCF, TAS, HSS/UDM
    SECURITY = "SECURITY"                     # Gi-LAN firewalls, DDoS scrubbers, SEPP, IPsec security gateways
    OPTICAL_TRANSPORT = "OPTICAL_TRANSPORT"   # DWDM, ROADM, OTN photonic layers
    CHARGING_BILLING = "CHARGING_BILLING"     # Online Charging System (OCS), CHF, PCRF/PCFA
    OSS_MANAGEMENT = "OSS_MANAGEMENT"         # Network Management Systems, Element Management Systems, Netconf/YANG


class DomainContract(Contract):
    """
    Specification of an operational network domain within the telecom topology.

    Attributes:
        domain_id: Unique semantic identifier (e.g., 'DOMAIN_IP_TRANSPORT').
        code: DomainCode enum value.
        display_name: Human-friendly name displayed in Zaki's UI.
        description: Functional description of the technical domain.
        managed_entity_types: List of network element classes (e.g. ['PE_ROUTER', 'IP_FABRIC_SWITCH']).
        lead_engineering_role: Primary human engineering stakeholder responsible for this domain.
        interfaces_in_scope: Standard telecom interfaces (e.g. ['N3', 'N4', 'N6', 'S1-U', 'SGi']).
    """
    domain_id: str = Field(description="Unique semantic domain identifier (e.g., 'DOMAIN_IP_TRANSPORT')")
    code: DomainCode = Field(description="Standardized domain enumeration code")
    display_name: str = Field(description="Display label formatted for NOC SME user interfaces")
    description: str = Field(default="", description="Detailed functional description of the domain scope")
    managed_entity_types: list[str] = Field(default_factory=list, description="Network element types belonging to this domain")
    lead_engineering_role: str = Field(default="", description="Primary engineering role responsible for domain governance")
    interfaces_in_scope: list[str] = Field(default_factory=list, description="3GPP or IETF protocol interfaces governed by this domain")


STANDARD_DOMAINS: dict[str, DomainContract] = {
    DomainCode.IP_TRANSPORT.value: DomainContract(
        domain_id="DOMAIN_IP_TRANSPORT",
        code=DomainCode.IP_TRANSPORT,
        display_name="IP Transport",
        description="Backhaul, midhaul, and fronthaul IP/MPLS, SRv6, and BGP routing network",
        managed_entity_types=["PE_ROUTER", "IP_FABRIC_SWITCH", "VRF"],
        lead_engineering_role="IP Transport SME",
        interfaces_in_scope=["N3", "S1-U", "BGP", "MPLS"],
    ),
    DomainCode.PS_CORE.value: DomainContract(
        domain_id="DOMAIN_PS_CORE",
        code=DomainCode.PS_CORE,
        display_name="5G Core",
        description="4G EPC and 5G Standalone mobile packet core functions",
        managed_entity_types=["UPF", "AMF", "SMF", "MME", "PGW"],
        lead_engineering_role="Mobile Packet Core SME",
        interfaces_in_scope=["N3", "N4", "N6", "S1-MME"],
    ),
    DomainCode.RAN.value: DomainContract(
        domain_id="DOMAIN_RAN",
        code=DomainCode.RAN,
        display_name="Radio Access Network",
        description="4G LTE eNodeB and 5G NR gNodeB radio cell sites and baseband units",
        managed_entity_types=["ENODEB", "GNODEB", "CELL_SECTOR"],
        lead_engineering_role="RAN Performance Engineer",
        interfaces_in_scope=["Uu", "X2", "Xn", "S1-U"],
    ),
    DomainCode.CLOUD_INFRA.value: DomainContract(
        domain_id="DOMAIN_CLOUD_INFRA",
        code=DomainCode.CLOUD_INFRA,
        display_name="Cloud Infrastructure",
        description="NFVI, Kubernetes clusters, bare metal servers, and carrier virtualization",
        managed_entity_types=["K8S_CLUSTER", "DATABASE_CLUSTER", "HYPERVISOR"],
        lead_engineering_role="Cloud Infrastructure Engineer",
        interfaces_in_scope=["CNI", "CSI", "Kubelet"],
    ),
    DomainCode.IMS_VOICE.value: DomainContract(
        domain_id="DOMAIN_IMS_VOICE",
        code=DomainCode.IMS_VOICE,
        display_name="IMS Voice Core",
        description="IP Multimedia Subsystem powering VoLTE, VoNR, and SIP telephony",
        managed_entity_types=["PCSCF", "SCSCF", "HSS", "TAS"],
        lead_engineering_role="Voice & IMS Engineer",
        interfaces_in_scope=["SIP", "Diameter", "Cx", "Gm"],
    ),
    DomainCode.CHARGING_BILLING.value: DomainContract(
        domain_id="DOMAIN_CHARGING_BILLING",
        code=DomainCode.CHARGING_BILLING,
        display_name="Charging & Billing",
        description="Online Charging System (OCS), CHF, and convergent rating engines",
        managed_entity_types=["OCS", "CHF", "RATING_ENGINE"],
        lead_engineering_role="Revenue Management SME",
        interfaces_in_scope=["Gy", "Sy", "N40"],
    ),
    DomainCode.SECURITY.value: DomainContract(
        domain_id="DOMAIN_SECURITY",
        code=DomainCode.SECURITY,
        display_name="Network Security",
        description="Gi-LAN firewalls, security gateways, and carrier NAT systems",
        managed_entity_types=["FIREWALL", "CGNAT", "SEPP"],
        lead_engineering_role="SecOps Telecom Specialist",
        interfaces_in_scope=["SGi", "N6", "IPsec"],
    ),
    DomainCode.OPTICAL_TRANSPORT.value: DomainContract(
        domain_id="DOMAIN_OPTICAL_TRANSPORT",
        code=DomainCode.OPTICAL_TRANSPORT,
        display_name="Optical Transport",
        description="DWDM photonic rings, transponders, and fiber routes",
        managed_entity_types=["DWDM_ROADM", "TRANSPONDER"],
        lead_engineering_role="Optical Transmission Engineer",
        interfaces_in_scope=["OTU4", "100GbE"],
    ),
    DomainCode.OSS_MANAGEMENT.value: DomainContract(
        domain_id="DOMAIN_OSS_MANAGEMENT",
        code=DomainCode.OSS_MANAGEMENT,
        display_name="Customer & OSS Operations",
        description="Operations Support Systems, ticketing systems, and NMS portals",
        managed_entity_types=["NMS", "CRM_TICKET", "EMS"],
        lead_engineering_role="NOC Shift Supervisor",
        interfaces_in_scope=["REST", "SNMP", "Netconf"],
    ),
}

DOMAIN_ALIASES: dict[str, str] = {
    "IP_TRANSPORT": DomainCode.IP_TRANSPORT.value,
    "TRANSPORT": DomainCode.IP_TRANSPORT.value,
    "IP": DomainCode.IP_TRANSPORT.value,
    "BACKHAUL": DomainCode.IP_TRANSPORT.value,
    "PS_CORE": DomainCode.PS_CORE.value,
    "SA_5G_CORE": DomainCode.PS_CORE.value,
    "5GC": DomainCode.PS_CORE.value,
    "CORE": DomainCode.PS_CORE.value,
    "5G_CORE": DomainCode.PS_CORE.value,
    "RAN": DomainCode.RAN.value,
    "RADIO": DomainCode.RAN.value,
    "CLOUD_INFRA": DomainCode.CLOUD_INFRA.value,
    "IT_CLOUD_INFRA": DomainCode.CLOUD_INFRA.value,
    "INFRA": DomainCode.CLOUD_INFRA.value,
    "IMS_VOICE": DomainCode.IMS_VOICE.value,
    "IMS": DomainCode.IMS_VOICE.value,
    "VOICE": DomainCode.IMS_VOICE.value,
    "CHARGING_BILLING": DomainCode.CHARGING_BILLING.value,
    "CHARGING": DomainCode.CHARGING_BILLING.value,
    "OCS": DomainCode.CHARGING_BILLING.value,
    "SECURITY": DomainCode.SECURITY.value,
    "OPTICAL_TRANSPORT": DomainCode.OPTICAL_TRANSPORT.value,
    "OPTICAL": DomainCode.OPTICAL_TRANSPORT.value,
    "OSS_MANAGEMENT": DomainCode.OSS_MANAGEMENT.value,
    "CRM": DomainCode.OSS_MANAGEMENT.value,
    "TICKET": DomainCode.OSS_MANAGEMENT.value,
    "OSS": DomainCode.OSS_MANAGEMENT.value,
}


def resolve_domain_contract(domain_key: str | None) -> DomainContract:
    """Resolve a raw domain key or alias into an authoritative DomainContract."""
    if not domain_key:
        return STANDARD_DOMAINS[DomainCode.IP_TRANSPORT.value]
    raw = str(domain_key).strip().upper().replace(" ", "_").replace("-", "_")
    canonical_code = DOMAIN_ALIASES.get(raw)
    if canonical_code and canonical_code in STANDARD_DOMAINS:
        return STANDARD_DOMAINS[canonical_code]
    if raw in STANDARD_DOMAINS:
        return STANDARD_DOMAINS[raw]
    return DomainContract(
        domain_id=f"DOMAIN_{raw}",
        code=DomainCode.OSS_MANAGEMENT,
        display_name=raw.replace("_", " ").title(),
        description=f"Operational domain {raw}",
    )

