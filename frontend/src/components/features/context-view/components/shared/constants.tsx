import React from "react";
import {
  HelpCircle,
  Wifi,
  Database,
  Shield,
  AlertCircle,
  Radio,
  User,
  Smartphone,
  Brain,
  Users,
  TrendingUp,
  AlertTriangle,
  BarChart3,
  Network,
  Phone,
  Search,
} from "lucide-react";
import { ThemeConfig, GraphNode, GraphLink } from "../../types/context.types";

export const THEMES: Record<string, ThemeConfig> = {
  cyberpunk: {
    id: "cyberpunk",
    name: "Neon Cyberpunk",
    isDark: true,
    gridBackground:
      "radial-gradient(circle at center, rgba(0, 229, 255, 0.04) 0%, transparent 70%), radial-gradient(circle at center, transparent 99px, rgba(0, 229, 255, 0.015) 100px, transparent 101px), radial-gradient(circle at center, transparent 199px, rgba(0, 229, 255, 0.01) 200px, transparent 201px), radial-gradient(circle at center, transparent 299px, rgba(0, 229, 255, 0.005) 300px, transparent 301px), linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px)",
    inactiveLinkColor: "rgba(255, 255, 255, 0.52)",
    inactiveNodeAlpha: 0.2,
    nodeColors: {
      Intent: "#00E5FF", // Neon Cyan
      Service: "#CCFF00", // Neon Chartreuse
      Platform: "#FF00FF", // Neon Magenta
      Precondition: "#00FF88", // Neon Green
      Error: "#FF3366", // Neon Rose
      Channel: "#9933FF", // Neon Purple
      CustomerProfile: "#FF9900", // Neon Orange
      AppType: "#0088FF", // Neon Blue
      FAQ: "#FF007F", // Neon Pink
      Hub: "#888888",
      Fallback: "#888888",
    },
    labelTextColor: "rgba(255, 255, 255, 0.8)",
    labelTextBackground: "rgba(10, 10, 10, 0.9)",
    labelTextBorder: "rgba(255, 255, 255, 0.15)",
  },
  nordic: {
    id: "nordic",
    name: "Nordic Frost",
    isDark: true,
    gridBackground:
      "radial-gradient(circle at center, rgba(147, 197, 253, 0.05) 0%, transparent 75%), radial-gradient(circle at center, transparent 99px, rgba(147, 197, 253, 0.02) 100px, transparent 101px), radial-gradient(circle at center, transparent 199px, rgba(147, 197, 253, 0.015) 200px, transparent 201px), linear-gradient(rgba(148, 163, 184, 0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(148, 163, 184, 0.015) 1px, transparent 1px)",
    inactiveLinkColor: "rgba(148, 163, 184, 0.45)",
    inactiveNodeAlpha: 0.25,
    nodeColors: {
      Intent: "#93C5FD", // Ice Blue
      Service: "#A7F3D0", // Soft Mint
      Platform: "#F3E8FF", // Soft Lilac
      Precondition: "#D1FAE5", // Soft Green
      Error: "#FECACA", // Soft Crimson
      Channel: "#E9D5FF", // Soft Lavender
      CustomerProfile: "#FFEDD5", // Soft Peach
      AppType: "#BAE6FD", // Soft Steel Blue
      FAQ: "#F472B6", // Soft Pink
      Hub: "#888888",
      Fallback: "#888888",
    },
    labelTextColor: "rgba(203, 213, 225, 0.9)",
    labelTextBackground: "rgba(15, 23, 42, 0.95)",
    labelTextBorder: "rgba(148, 163, 184, 0.2)",
  },
  gotham: {
    id: "gotham",
    name: "Palantir Gotham",
    isDark: true,
    gridBackground:
      "radial-gradient(circle at center, rgba(59, 130, 246, 0.04) 0%, transparent 70%), radial-gradient(circle at center, transparent 99px, rgba(59, 130, 246, 0.02) 100px, transparent 101px), radial-gradient(circle at center, transparent 199px, rgba(59, 130, 246, 0.01) 200px, transparent 201px), linear-gradient(rgba(30, 58, 138, 0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(30, 58, 138, 0.015) 1px, transparent 1px)",
    inactiveLinkColor: "rgba(71, 85, 105, 0.55)",
    inactiveNodeAlpha: 0.22,
    nodeColors: {
      Intent: "#3B82F6", // Deep Blue
      Service: "#10B981", // Tactical Green
      Platform: "#F97316", // Signal Orange
      Precondition: "#64748B", // Tactical Muted Slate
      Error: "#EF4444", // Warning Red
      Channel: "#06B6D4", // Cyan Info
      CustomerProfile: "#E2E8F0", // Tactical Light Gray
      AppType: "#F59E0B", // Hazard Yellow
      FAQ: "#EC4899", // Tactical Pink
      Hub: "#888888",
      Fallback: "#888888",
    },
    labelTextColor: "rgba(241, 245, 249, 0.9)",
    labelTextBackground: "rgba(9, 15, 29, 0.95)",
    labelTextBorder: "rgba(71, 85, 105, 0.3)",
  },
  obsidian: {
    id: "obsidian",
    name: "Obsidian Ink",
    isDark: true,
    gridBackground:
      "radial-gradient(circle at center, rgba(168, 85, 247, 0.03) 0%, transparent 75%), linear-gradient(rgba(63, 63, 70, 0.012) 1px, transparent 1px), linear-gradient(90deg, rgba(63, 63, 70, 0.012) 1px, transparent 1px)",
    inactiveLinkColor: "rgba(113, 113, 122, 0.45)",
    inactiveNodeAlpha: 0.18,
    nodeColors: {
      Intent: "#A855F7", // Obsidian Purple
      Service: "#71717A", // Graphite Gray
      Platform: "#F4F4F5", // Paper White
      Precondition: "#3F3F46", // Slate Zinc
      Error: "#E11D48", // Rose Warning
      Channel: "#C084FC", // Light Purple
      CustomerProfile: "#D4D4D8", // Light Zinc
      AppType: "#52525B", // Dark Zinc
      FAQ: "#F43F5E", // Obsidian Pink-Red
      Hub: "#888888",
      Fallback: "#888888",
    },
    labelTextColor: "rgba(228, 228, 231, 0.85)",
    labelTextBackground: "rgba(9, 9, 11, 0.95)",
    labelTextBorder: "rgba(63, 63, 70, 0.25)",
  },
  amber: {
    id: "amber",
    name: "Solarized Amber",
    isDark: true,
    gridBackground:
      "radial-gradient(circle at center, rgba(245, 158, 11, 0.04) 0%, transparent 70%), radial-gradient(circle at center, transparent 99px, rgba(245, 158, 11, 0.02) 100px, transparent 101px), radial-gradient(circle at center, transparent 199px, rgba(245, 158, 11, 0.01) 200px, transparent 201px), linear-gradient(rgba(217, 119, 6, 0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(217, 119, 6, 0.015) 1px, transparent 1px)",
    inactiveLinkColor: "rgba(217, 119, 6, 0.4)",
    inactiveNodeAlpha: 0.22,
    nodeColors: {
      Intent: "#F59E0B", // Warm Amber
      Service: "#FBBF24", // Gold
      Platform: "#F97316", // Copper / Orange
      Precondition: "#84CC16", // Olive
      Error: "#EF4444", // Terracotta / Red
      Channel: "#D97706", // Dark Ochre
      CustomerProfile: "#EA580C", // Rust
      AppType: "#10B981", // Sage Green
      FAQ: "#F43F5E", // Solarized Pink
      Hub: "#888888",
      Fallback: "#888888",
    },
    labelTextColor: "rgba(253, 230, 138, 0.85)",
    labelTextBackground: "rgba(24, 18, 10, 0.95)",
    labelTextBorder: "rgba(217, 119, 6, 0.25)",
  },
  neo4jLight: {
    id: "neo4jLight",
    name: "Neo4j Bloom (Light)",
    isDark: false,
    gridBackground:
      "radial-gradient(circle at center, rgba(0, 164, 180, 0.03) 0%, transparent 75%), linear-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 0, 0, 0.03) 1px, transparent 1px)",
    inactiveLinkColor: "rgba(100, 116, 139, 0.45)",
    inactiveNodeAlpha: 0.25,
    nodeColors: {
      Intent: "#00A4B4", // Neo4j Teal
      Service: "#5C6BC0", // Indigo
      Platform: "#F25F5C", // Coral
      Precondition: "#FFE066", // Ochre
      Error: "#E76F51", // Terracotta
      Channel: "#7209B7", // Purple
      CustomerProfile: "#2A9D8F", // Emerald
      AppType: "#4361EE", // Royal Blue
      FAQ: "#FF70A6", // Bloom Pink
      Hub: "#888888",
      Fallback: "#888888",
    },
    labelTextColor: "rgba(15, 23, 42, 0.85)",
    labelTextBackground: "rgba(255, 255, 255, 0.95)",
    labelTextBorder: "rgba(100, 116, 139, 0.2)",
  },
  springer: {
    id: "springer",
    name: "Springer Nature",
    isDark: false,
    gridBackground:
      "radial-gradient(circle at center, rgba(162, 28, 71, 0.015) 0%, transparent 80%), linear-gradient(rgba(0, 0, 0, 0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 0, 0, 0.015) 1px, transparent 1px)",
    inactiveLinkColor: "rgba(140, 140, 140, 0.5)",
    inactiveNodeAlpha: 0.2,
    nodeColors: {
      Intent: "#A21C47", // Springer Burgundy
      Service: "#2F575D", // Deep Slate Green
      Platform: "#E05A47", // Soft Terracotta
      Precondition: "#797A7E", // Muted Slate
      Error: "#C84B31", // Crimson
      Channel: "#506D84", // Steel Blue
      CustomerProfile: "#6E85B7", // Light Corporate Blue
      AppType: "#89B5AF", // Muted Teal
      FAQ: "#D8005A", // Burgundy Pink
      Hub: "#888888",
      Fallback: "#888888",
    },
    labelTextColor: "rgba(40, 40, 40, 0.9)",
    labelTextBackground: "rgba(255, 253, 250, 0.95)",
    labelTextBorder: "rgba(0, 0, 0, 0.1)",
  },
  linkedin: {
    id: "linkedin",
    name: "LinkedIn Tech",
    isDark: false,
    gridBackground:
      "radial-gradient(circle at center, rgba(10, 102, 194, 0.02) 0%, transparent 75%), linear-gradient(rgba(10, 102, 194, 0.012) 1px, transparent 1px), linear-gradient(90deg, rgba(10, 102, 194, 0.012) 1px, transparent 1px)",
    inactiveLinkColor: "rgba(120, 120, 120, 0.5)",
    inactiveNodeAlpha: 0.22,
    nodeColors: {
      Intent: "#0A66C2", // LinkedIn Blue
      Service: "#00B4D8", // Vibrant Cyan
      Platform: "#FF8500", // Orange
      Precondition: "#00F5D4", // Bright Teal
      Error: "#D90429", // Alert Red
      Channel: "#7B2CBF", // Tech Purple
      CustomerProfile: "#2D6A4F", // Dark Green
      AppType: "#FFB703", // Warm Gold
      FAQ: "#FF4D6D", // LinkedIn Pink
      Hub: "#888888",
      Fallback: "#888888",
    },
    labelTextColor: "rgba(20, 24, 33, 0.9)",
    labelTextBackground: "rgba(255, 255, 255, 0.95)",
    labelTextBorder: "rgba(10, 102, 194, 0.15)",
  },
  nature: {
    id: "nature",
    name: "Nature Scientific",
    isDark: false,
    gridBackground:
      "radial-gradient(circle at center, rgba(0, 120, 130, 0.015) 0%, transparent 80%), linear-gradient(rgba(0, 0, 0, 0.01) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 0, 0, 0.01) 1px, transparent 1px)",
    inactiveLinkColor: "rgba(160, 160, 160, 0.45)",
    inactiveNodeAlpha: 0.25,
    nodeColors: {
      Intent: "#007A82", // Deep Sea Teal
      Service: "#2EC4B6", // Bright Turquoise
      Platform: "#E71D36", // Vibrant Crimson
      Precondition: "#FF9F1C", // Deep Yellow Gold
      Error: "#FF4A5A", // Scientific Pink-Red
      Channel: "#9B5DE5", // Orchid Purple
      CustomerProfile: "#F15BB5", // Nature Magenta
      AppType: "#00F5D4", // Mint Neon
      FAQ: "#FF70A6", // Nature Pink
      Hub: "#888888",
      Fallback: "#888888",
    },
    labelTextColor: "rgba(33, 37, 41, 0.9)",
    labelTextBackground: "rgba(255, 255, 255, 0.95)",
    labelTextBorder: "rgba(0, 120, 130, 0.1)",
  },
};

export const TYPE_ICONS: Record<string, React.ReactNode> = {
  Intent: <HelpCircle className="h-4 w-4 text-cyan-400" />,
  Service: <Wifi className="h-4 w-4 text-lime-400" />,
  Platform: <Database className="h-4 w-4 text-fuchsia-400" />,
  Precondition: <Shield className="h-4 w-4 text-emerald-400" />,
  Error: <AlertCircle className="h-4 w-4 text-rose-400" />,
  Channel: <Radio className="h-4 w-4 text-purple-400" />,
  CustomerProfile: <User className="h-4 w-4 text-amber-400" />,
  AppType: <Smartphone className="h-4 w-4 text-blue-400" />,
  FAQ: <HelpCircle className="h-4 w-4 text-pink-400" />,
};

export const INITIAL_NODES: GraphNode[] = [
  // User Intents / Complaints
  { id: "intent_voice_drops", label: "Voice Call Drops", type: "Intent" },
  { id: "intent_slow_5g", label: "5G Speed Degradation", type: "Intent" },
  { id: "intent_esim_fail", label: "eSIM Activation Failure", type: "Intent" },
  { id: "intent_roaming_fail", label: "Roaming Connection Fail", type: "Intent" },

  // Affected Mobile Services
  { id: "service_ims_volte", label: "IMS VoLTE Signaling Core", type: "Service" },
  { id: "service_5g_upf", label: "5G Packet Router (UPF)", type: "Service" },
  { id: "service_esim_sm_dp", label: "SM-DP+ eSIM Server", type: "Service" },
  { id: "service_roaming_vlr", label: "VLR Roaming Gateway", type: "Service" },

  // Platforms (Diagnostic Support Escalation Teams)
  { id: "platform_ran_team", label: "Radio Access Network (RAN) Team", type: "Platform" },
  { id: "platform_core_team", label: "Core Switching & IMS Team", type: "Platform" },
  { id: "platform_provisioning_team", label: "eSIM & Provisioning Support", type: "Platform" },
  { id: "platform_roaming_desk", label: "Carrier Inter-Roaming Support", type: "Platform" },
  { id: "platform_crm", label: "Unified CRM System", type: "Platform" },

  // Preconditions (Subscriber Registry Checks)
  { id: "precondition_device_volte", label: "VoLTE Device Support", type: "Precondition" },
  { id: "precondition_5g_sim", label: "5G Provisioned SIM", type: "Precondition" },
  { id: "precondition_sim_status", label: "SIM Active Registry", type: "Precondition" },
  { id: "precondition_partner_sla", label: "Roaming Agreement", type: "Precondition" },

  // Specific Diagnostics Failures & Error Codes
  { id: "error_low_sinr", label: "Low SINR (RF Noise)", type: "Error" },
  { id: "error_profile_mismatch", label: "eSIM Profile Mismatch", type: "Error" },
  { id: "error_insufficient_funds", label: "Insufficient balance code", type: "Error" },
  { id: "error_plmn_forbidden", label: "PLMN Forbidden Error", type: "Error" },

  // Intake Channels
  { id: "channel_mobile_app", label: "Subscriber Mobile App", type: "Channel" },
  { id: "channel_ussd", label: "USSD Code Dial", type: "Channel" },

  // Customer Profiles
  { id: "profile_prepaid_subscriber", label: "Prepaid Subscriber", type: "CustomerProfile" },
  { id: "profile_postpaid_subscriber", label: "Postpaid Corporate", type: "CustomerProfile" },

  // App Types
  { id: "apptype_ios_native", label: "iOS App Client", type: "AppType" },
  { id: "apptype_android_native", label: "Android App Client", type: "AppType" },

  // FAQ Nodes
  {
    id: "faq_amazon_prime_cancel",
    label: "Cancel Amazon Prime Subscription",
    type: "FAQ",
    url: "https://www.du.ae/support-articledetail?artid=PROD-52779&lang=en-GB&version=6.0&tagname=dutopic_amazonprime&userType=consumer",
    prechecks: ["Check BSS profile status", "Verify subscription is postpaid"],
    target: "Billing & Accounts L2",
    prohibited: ["Network L2 Core", "RAN Engineering"],
  },
  {
    id: "faq_amazon_prime_activate",
    label: "Activate 12 Months Free Amazon Prime",
    type: "FAQ",
    url: "https://www.du.ae/support-articledetail?artid=PROD-52779&lang=en-GB&version=6.0&tagname=dutopic_amazonprime&userType=consumer",
    prechecks: ["Check BSS profile status", "Verify plan eligibility"],
    target: "eSIM & Provisioning Support",
    prohibited: ["RAN Engineering", "Billing L2"],
  },
  {
    id: "faq_call_barring",
    label: "Call Barring Management",
    type: "FAQ",
    url: "https://www.du.ae/support-articledetail?artid=PROD-12490&lang=en-GB&version=4.0&tagname=dutopic_callbarring&userType=consumer",
    prechecks: ["Verify HLR subscriber voice status", "Check BSS profile status"],
    target: "Network L2 Core Support",
    prohibited: ["Billing & Accounts L2"],
  },
  {
    id: "faq_call_forwarding",
    label: "Call Forwarding Activation",
    type: "FAQ",
    url: "https://www.du.ae/support-articledetail?artid=PROD-12489&lang=en-GB&version=4.0&tagname=dutopic_callforwarding&userType=consumer",
    prechecks: ["Verify HLR subscriber voice status"],
    target: "Network L2 Core Support",
    prohibited: ["eSIM & Provisioning Support"],
  },
  {
    id: "faq_caller_id",
    label: "Caller Number Presentation (CNAP)",
    type: "FAQ",
    url: "https://www.du.ae/support-articledetail?artid=PROD-12491&lang=en-GB&version=4.0&tagname=dutopic_callerid&userType=consumer",
    prechecks: ["Check BSS profile status", "Check VoLTE handset settings"],
    target: "eSIM & Provisioning Support",
    prohibited: ["RAN Engineering"],
  },
  {
    id: "faq_caller_tune",
    label: "Caller Tune Activation & Cancellation",
    type: "FAQ",
    url: "https://www.du.ae/support-articledetail?artid=PROD-12492&lang=en-GB&version=4.0&tagname=dutopic_callertunes&userType=consumer",
    prechecks: ["Check BSS profile status"],
    target: "VAS & Charging Ops",
    prohibited: ["Network L2 Core"],
  },
  {
    id: "faq_dncr",
    label: "Do Not Call Registry (DNCR)",
    type: "FAQ",
    url: "https://www.du.ae/do-not-call-registry",
    prechecks: ["Check BSS profile status"],
    target: "eSIM & Provisioning Support",
    prohibited: ["RAN Engineering"],
  },
  {
    id: "faq_esim_replacement",
    label: "eSIM Replacement & Multi-device Watch",
    type: "FAQ",
    url: "https://www.du.ae/personal/esim",
    prechecks: ["Check SM-DP+ Server status for EID profile", "Verify device WiFi connectivity"],
    target: "eSIM & Provisioning Support",
    prohibited: ["Network L2 Core", "Billing L2"],
  },
];

export const INITIAL_LINKS: GraphLink[] = [
  // Intake Channels trigger complaints (and connect the clusters)
  { source: "channel_mobile_app", target: "intent_voice_drops", label: "TRIGGERS" },
  { source: "channel_mobile_app", target: "intent_slow_5g", label: "TRIGGERS" },
  { source: "channel_mobile_app", target: "intent_esim_fail", label: "TRIGGERS" },
  { source: "channel_ussd", target: "intent_roaming_fail", label: "TRIGGERS" },
  { source: "channel_ussd", target: "intent_voice_drops", label: "TRIGGERS" },

  // App Clients trigger eSIM Activation
  { source: "apptype_ios_native", target: "intent_esim_fail", label: "TRIGGERS" },
  { source: "apptype_android_native", target: "intent_esim_fail", label: "TRIGGERS" },

  // Intents executing via services
  { source: "intent_voice_drops", target: "service_ims_volte", label: "TRIGGERS" },
  { source: "intent_slow_5g", target: "service_5g_upf", label: "TRIGGERS" },
  { source: "intent_esim_fail", target: "service_esim_sm_dp", label: "TRIGGERS" },
  { source: "intent_roaming_fail", target: "service_roaming_vlr", label: "TRIGGERS" },

  // Services routing to platforms (teams)
  { source: "service_ims_volte", target: "platform_core_team", label: "EXECUTES_VIA" },
  { source: "service_5g_upf", target: "platform_ran_team", label: "EXECUTES_VIA" },
  { source: "service_esim_sm_dp", target: "platform_provisioning_team", label: "EXECUTES_VIA" },
  { source: "service_roaming_vlr", target: "platform_roaming_desk", label: "EXECUTES_VIA" },

  // Platforms sync to Unified CRM (Shared Back-Office Portal)
  { source: "platform_core_team", target: "platform_crm", label: "SYNC_STATUS" },
  { source: "platform_ran_team", target: "platform_crm", label: "SYNC_STATUS" },
  { source: "platform_provisioning_team", target: "platform_crm", label: "SYNC_STATUS" },
  { source: "platform_roaming_desk", target: "platform_crm", label: "SYNC_STATUS" },

  // Customer Profiles linked to complaints (acting as bridges)
  { source: "profile_prepaid_subscriber", target: "intent_voice_drops", label: "ASSOCIATED_WITH" },
  { source: "profile_prepaid_subscriber", target: "intent_roaming_fail", label: "ASSOCIATED_WITH" },
  { source: "profile_postpaid_subscriber", target: "intent_slow_5g", label: "ASSOCIATED_WITH" },
  { source: "profile_postpaid_subscriber", target: "intent_esim_fail", label: "ASSOCIATED_WITH" },

  // Specific warning error codes triggering escalations
  { source: "intent_voice_drops", target: "error_low_sinr", label: "CAN_FAIL_WITH" },
  { source: "intent_slow_5g", target: "error_low_sinr", label: "CAN_FAIL_WITH" },
  { source: "intent_esim_fail", target: "error_profile_mismatch", label: "CAN_FAIL_WITH" },
  { source: "intent_roaming_fail", target: "error_plmn_forbidden", label: "CAN_FAIL_WITH" },
  { source: "intent_roaming_fail", target: "error_insufficient_funds", label: "CAN_FAIL_WITH" },

  { source: "error_low_sinr", target: "platform_ran_team", label: "EXECUTES_VIA" },
  { source: "error_plmn_forbidden", target: "platform_roaming_desk", label: "EXECUTES_VIA" },
  { source: "error_profile_mismatch", target: "platform_provisioning_team", label: "EXECUTES_VIA" },
  { source: "error_insufficient_funds", target: "platform_crm", label: "EXECUTES_VIA" },

  // Preconditions required
  { source: "intent_voice_drops", target: "precondition_device_volte", label: "REQUIRES_PREREQUISITE" },
  { source: "intent_slow_5g", target: "precondition_5g_sim", label: "REQUIRES_PREREQUISITE" },
  { source: "intent_esim_fail", target: "precondition_sim_status", label: "REQUIRES_PREREQUISITE" },
  { source: "intent_slow_5g", target: "precondition_sim_status", label: "REQUIRES_PREREQUISITE" },
  { source: "intent_roaming_fail", target: "precondition_partner_sla", label: "REQUIRES_PREREQUISITE" },

  // FAQ edge links
  { source: "profile_postpaid_subscriber", target: "faq_amazon_prime_cancel", label: "ASSOCIATED_WITH" },
  { source: "profile_postpaid_subscriber", target: "faq_amazon_prime_activate", label: "ASSOCIATED_WITH" },
  { source: "channel_mobile_app", target: "faq_amazon_prime_cancel", label: "TRIGGERS" },
  { source: "channel_mobile_app", target: "faq_caller_tune", label: "TRIGGERS" },
  { source: "channel_mobile_app", target: "faq_esim_replacement", label: "TRIGGERS" },
  { source: "channel_ussd", target: "faq_call_barring", label: "TRIGGERS" },
  { source: "channel_ussd", target: "faq_call_forwarding", label: "TRIGGERS" },

  { source: "faq_esim_replacement", target: "precondition_sim_status", label: "REQUIRES_PREREQUISITE" },
  { source: "faq_call_barring", target: "precondition_device_volte", label: "REQUIRES_PREREQUISITE" },
  { source: "faq_caller_id", target: "precondition_device_volte", label: "REQUIRES_PREREQUISITE" },

  { source: "faq_call_barring", target: "platform_core_team", label: "EXECUTES_VIA" },
  { source: "faq_call_forwarding", target: "platform_core_team", label: "EXECUTES_VIA" },
  { source: "faq_caller_tune", target: "platform_core_team", label: "EXECUTES_VIA" },
  { source: "faq_amazon_prime_cancel", target: "platform_core_team", label: "EXECUTES_VIA" },

  { source: "faq_amazon_prime_activate", target: "platform_provisioning_team", label: "EXECUTES_VIA" },
  { source: "faq_caller_id", target: "platform_provisioning_team", label: "EXECUTES_VIA" },
  { source: "faq_dncr", target: "platform_provisioning_team", label: "EXECUTES_VIA" },
  { source: "faq_esim_replacement", target: "platform_provisioning_team", label: "EXECUTES_VIA" },
];

export const INTENT_WORKFLOWS: Record<
  string,
  {
    label: string;
    channels: string[];
    prechecks: string[];
    dependencies: string[];
    target: string;
    prohibited: string[];
    fallback: string;
    description: string;
  }
> = {
  intent_voice_drops: {
    label: "Voice Call Drops",
    channels: ["Subscriber Mobile App", "USSD Code Dial"],
    prechecks: ["Check VoLTE handset settings", "Verify HLR subscriber voice status"],
    dependencies: ["flexible_minutes_wallet", "national_idd_minutes", "cug_minutes_bucket"],
    target: "Core Switching & IMS Team",
    prohibited: ["Provisioning Support", "Billing L2"],
    fallback: "Network",
    description:
      "Escalation protocol for voice call drops. Verify handset VoLTE capability and HLR subscriber database voice registration flags before dispatching.",
  },
  intent_slow_5g: {
    label: "5G Speed Degradation",
    channels: ["Subscriber Mobile App"],
    prechecks: [
      "Check 5G Provisioning status in CRM",
      "Check Sector signal quality in Home 5G Router Status Portal",
      "Verify bundle speed cap status in BSS",
      "Verify speedtest throughput vs agreed speed",
      "Check coverage at customer location",
    ],
    dependencies: ["data_bundles"],
    target: "RAN Engineering Team",
    prohibited: ["Billing & Accounts L2", "Core Team L2"],
    fallback: "Network",
    description:
      "Escalation protocol for mobile speed drops. Check cellular coverage status and BSS quota status before assigning to the RAN team.",
  },
  intent_esim_fail: {
    label: "eSIM Activation Failure",
    channels: ["Subscriber Mobile App", "iOS App Client", "Android App Client"],
    prechecks: ["Check SM-DP+ Server status for EID profile", "Verify device WiFi connectivity"],
    dependencies: ["prepaid_wallet_balance"],
    target: "eSIM & Provisioning Support",
    prohibited: ["Network L2 Core", "Billing L2"],
    fallback: "Provisioning",
    description:
      "Escalation protocol for eSIM registration errors. Verify device local internet/WiFi connection and SM-DP+ server status.",
  },
  intent_roaming_fail: {
    label: "Roaming Connection Fail",
    channels: ["USSD Code Dial"],
    prechecks: ["Check BSS profile status", "Verify inter-carrier Roaming Agreement status"],
    dependencies: ["roaming_data_bundle", "prepaid_wallet_balance"],
    target: "Carrier Inter-Roaming Support",
    prohibited: ["RAN Engineering"],
    fallback: "Network",
    description:
      "Escalation protocol for international roaming connection failures. Confirm network carrier agreements and local 3G shutdown states.",
  },
};
