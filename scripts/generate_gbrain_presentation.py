#!/usr/bin/env python3
"""
Generates a comprehensive, professional PowerPoint presentation (.pptx)
detailing all use cases implemented using gbrain in the kagent / MARK platform.
Uses Python standard library (zipfile, xml.sax.saxutils) to produce
100% valid ECMA-376 OpenXML PPTX files with rich visual styling.
"""

import os
import sys
import zipfile
from xml.sax.saxutils import escape

# Slide dimensions in EMUs (16:9 widescreen: 13.333 x 7.5 inches)
SLIDE_WIDTH = 12192000
SLIDE_HEIGHT = 6858000

# Color Palette (HEX without #)
COLOR_NAVY_DARK = "0F172A"       # Slate 900
COLOR_NAVY_PRIMARY = "1E293B"    # Slate 800
COLOR_BLUE_ACCENT = "2563EB"     # Blue 600
COLOR_BLUE_LIGHT = "DBEAFE"      # Blue 100
COLOR_CYAN_ACCENT = "0284C7"     # Sky 600
COLOR_EMERALD = "059669"         # Emerald 600
COLOR_EMERALD_LIGHT = "D1FAE5"   # Emerald 100
COLOR_AMBER = "D97706"           # Amber 600
COLOR_AMBER_LIGHT = "FEF3C7"     # Amber 100
COLOR_PURPLE = "7C3AED"          # Violet 600
COLOR_PURPLE_LIGHT = "EDE9FE"    # Violet 100
COLOR_RED = "DC2626"             # Red 600
COLOR_BG_LIGHT = "F8FAFC"        # Slate 50
COLOR_CARD_BG = "FFFFFF"         # Pure White
COLOR_BORDER = "E2E8F0"          # Slate 200
COLOR_TEXT_DARK = "0F172A"       # Slate 900
COLOR_TEXT_MUTED = "475569"      # Slate 600
COLOR_TEXT_LIGHT = "94A3B8"      # Slate 400
COLOR_WHITE = "FFFFFF"


def pt(points: float) -> int:
    """Convert points to hundredths of a point for DrawingML font size."""
    return int(points * 100)


def inches(val: float) -> int:
    """Convert inches to EMUs."""
    return int(val * 914400)


class SlideBuilder:
    def __init__(self, slide_num: int, is_dark: bool = False):
        self.slide_num = slide_num
        self.is_dark = is_dark
        self.shapes = []
        self.shape_id = 2

    def next_id(self) -> int:
        self.shape_id += 1
        return self.shape_id

    def add_shape(self, shape_xml: str):
        self.shapes.append(shape_xml)

    def add_card(self, x: int, y: int, cx: int, cy: int, bg_color: str = COLOR_CARD_BG, border_color: str = COLOR_BORDER, border_width: int = 12700):
        s_id = self.next_id()
        line_xml = f'<a:ln w="{border_width}"><a:solidFill><a:srgbClr val="{border_color}"/></a:solidFill></a:ln>' if border_color else '<a:ln><a:noFill/></a:ln>'
        xml = f"""
        <p:sp>
          <p:nvSpPr>
            <p:cNvPr id="{s_id}" name="Card {s_id}"/>
            <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
            <p:nvPr/>
          </p:nvSpPr>
          <p:spPr>
            <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
            <a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 2000"/></a:avLst></a:prstGeom>
            <a:solidFill><a:srgbClr val="{bg_color}"/></a:solidFill>
            {line_xml}
          </p:spPr>
          <p:txBody>
            <a:bodyPr/>
            <a:lstStyle/>
            <a:p/>
          </p:txBody>
        </p:sp>
        """
        self.add_shape(xml)

    def add_header(self, category: str, title: str, subtitle: str = ""):
        # Category badge
        cat_id = self.next_id()
        cat_bg = COLOR_BLUE_ACCENT if not self.is_dark else COLOR_BLUE_LIGHT
        cat_tx = COLOR_WHITE if not self.is_dark else COLOR_NAVY_DARK
        xml_cat = f"""
        <p:sp>
          <p:nvSpPr>
            <p:cNvPr id="{cat_id}" name="Badge {cat_id}"/>
            <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
            <p:nvPr/>
          </p:nvSpPr>
          <p:spPr>
            <a:xfrm><a:off x="{inches(0.8)}" y="{inches(0.4)}"/><a:ext cx="{inches(2.8)}" cy="{inches(0.35)}"/></a:xfrm>
            <a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 5000"/></a:avLst></a:prstGeom>
            <a:solidFill><a:srgbClr val="{cat_bg}"/></a:solidFill>
            <a:ln><a:noFill/></a:ln>
          </p:spPr>
          <p:txBody>
            <a:bodyPr anchor="ctr" lIns="72000" rIns="72000" tIns="18000" bIns="18000"/>
            <a:lstStyle/>
            <a:p>
              <a:pPr algn="ctr"/>
              <a:r>
                <a:rPr lang="en-US" sz="{pt(11)}" b="1">
                  <a:solidFill><a:srgbClr val="{cat_tx}"/></a:solidFill>
                </a:rPr>
                <a:t>{escape(category.upper())}</a:t>
              </a:r>
            </a:p>
          </p:txBody>
        </p:sp>
        """
        self.add_shape(xml_cat)

        # Title and Subtitle text box
        title_id = self.next_id()
        t_color = COLOR_TEXT_DARK if not self.is_dark else COLOR_WHITE
        sub_color = COLOR_TEXT_MUTED if not self.is_dark else COLOR_TEXT_LIGHT
        xml_title = f"""
        <p:sp>
          <p:nvSpPr>
            <p:cNvPr id="{title_id}" name="Title {title_id}"/>
            <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
            <p:nvPr/>
          </p:nvSpPr>
          <p:spPr>
            <a:xfrm><a:off x="{inches(0.8)}" y="{inches(0.85)}"/><a:ext cx="{inches(11.7)}" cy="{inches(0.95)}"/></a:xfrm>
            <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
            <a:noFill/>
            <a:ln><a:noFill/></a:ln>
          </p:spPr>
          <p:txBody>
            <a:bodyPr tIns="0" bIns="0" lIns="0" rIns="0"/>
            <a:lstStyle/>
            <a:p>
              <a:r>
                <a:rPr lang="en-US" sz="{pt(24)}" b="1">
                  <a:solidFill><a:srgbClr val="{t_color}"/></a:solidFill>
                </a:rPr>
                <a:t>{escape(title)}</a:t>
              </a:r>
            </a:p>
            {f'''<a:p>
              <a:pPr spaceBefore="40000"/>
              <a:r>
                <a:rPr lang="en-US" sz="{pt(13)}" i="0">
                  <a:solidFill><a:srgbClr val="{sub_color}"/></a:solidFill>
                </a:rPr>
                <a:t>{escape(subtitle)}</a:t>
              </a:r>
            </a:p>''' if subtitle else ''}
          </p:txBody>
        </p:sp>
        """
        self.add_shape(xml_title)

        # Footer
        foot_id = self.next_id()
        foot_tx = COLOR_TEXT_LIGHT if not self.is_dark else COLOR_TEXT_MUTED
        xml_footer = f"""
        <p:sp>
          <p:nvSpPr>
            <p:cNvPr id="{foot_id}" name="Footer {foot_id}"/>
            <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
            <p:nvPr/>
          </p:nvSpPr>
          <p:spPr>
            <a:xfrm><a:off x="{inches(0.8)}" y="{inches(7.0)}"/><a:ext cx="{inches(11.7)}" cy="{inches(0.3)}"/></a:xfrm>
            <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
            <a:noFill/>
            <a:ln><a:noFill/></a:ln>
          </p:spPr>
          <p:txBody>
            <a:bodyPr tIns="0" bIns="0" lIns="0" rIns="0"/>
            <a:lstStyle/>
            <a:p>
              <a:pPr algn="l"/>
              <a:r>
                <a:rPr lang="en-US" sz="{pt(9)}">
                  <a:solidFill><a:srgbClr val="{foot_tx}"/></a:solidFill>
                </a:rPr>
                <a:t>Autonomous Telecom Operations with gbrain | KAgent MARK Architecture</a:t>
              </a:r>
            </a:p>
          </p:txBody>
        </p:sp>
        """
        self.add_shape(xml_footer)

    def add_textbox(self, x: int, y: int, cx: int, cy: int, paragraphs: list[dict]):
        """
        paragraphs is a list of dicts:
        {
            "bullets": bool,
            "space_before": int,
            "runs": [
                {"text": "...", "bold": True/False, "size": pt(14), "color": "000000", "italic": False}
            ]
        }
        """
        tb_id = self.next_id()
        p_xmls = []
        for p in paragraphs:
            runs_xml = []
            for r in p.get("runs", []):
                b_attr = ' b="1"' if r.get("bold") else ' b="0"'
                i_attr = ' i="1"' if r.get("italic") else ''
                sz = r.get("size", pt(13))
                col = r.get("color", COLOR_TEXT_DARK if not self.is_dark else COLOR_WHITE)
                runs_xml.append(f"""
                <a:r>
                  <a:rPr lang="en-US" sz="{sz}"{b_attr}{i_attr}>
                    <a:solidFill><a:srgbClr val="{col}"/></a:solidFill>
                  </a:rPr>
                  <a:t>{escape(r.get("text", ""))}</a:t>
                </a:r>
                """)
            
            p_pr_extras = []
            if p.get("space_before"):
                p_pr_extras.append(f'spaceBefore="{p["space_before"]}"')
            if p.get("algn"):
                p_pr_extras.append(f'algn="{p["algn"]}"')
            
            if p.get("bullets"):
                p_pr_str = " ".join(p_pr_extras)
                p_xmls.append(f"""
                <a:p>
                  <a:pPr {p_pr_str} marL="288000" indent="-288000">
                    <a:buClr><a:srgbClr val="{COLOR_BLUE_ACCENT}"/></a:buClr>
                    <a:buSzPct val="100000"/>
                    <a:buFont typeface="Arial"/>
                    <a:buChar char="•"/>
                  </a:pPr>
                  {''.join(runs_xml)}
                </a:p>
                """)
            else:
                p_pr_str = f' <a:pPr {" ".join(p_pr_extras)}/>' if p_pr_extras else ''
                p_xmls.append(f"""
                <a:p>{p_pr_str}
                  {''.join(runs_xml)}
                </a:p>
                """)

        xml = f"""
        <p:sp>
          <p:nvSpPr>
            <p:cNvPr id="{tb_id}" name="TextBox {tb_id}"/>
            <p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
            <p:nvPr/>
          </p:nvSpPr>
          <p:spPr>
            <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
            <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
            <a:noFill/>
            <a:ln><a:noFill/></a:ln>
          </p:spPr>
          <p:txBody>
            <a:bodyPr lIns="108000" rIns="108000" tIns="108000" bIns="108000" wrap="square"/>
            <a:lstStyle/>
            {''.join(p_xmls)}
          </p:txBody>
        </p:sp>
        """
        self.add_shape(xml)

    def to_xml(self) -> str:
        bg_xml = f"""
        <p:bg>
          <p:bgPr>
            <a:solidFill><a:srgbClr val="{COLOR_NAVY_DARK if self.is_dark else COLOR_BG_LIGHT}"/></a:solidFill>
          </p:bgPr>
        </p:bg>
        """
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/officeDocument/2006/presentationml">
  <p:cSld>
    {bg_xml}
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr/>
      {''.join(self.shapes)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def build_presentation(out_path: str):
    slides = []

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide (Dark Theme)
    # -------------------------------------------------------------
    s1 = SlideBuilder(1, is_dark=True)
    # Decorative backdrop shape
    s1.add_card(inches(0.8), inches(0.8), inches(11.73), inches(5.9), bg_color="1E293B", border_color="334155")
    # Title badge
    badge_id = s1.next_id()
    s1.add_shape(f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{badge_id}" name="B1"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>
      <p:spPr>
        <a:xfrm><a:off x="{inches(1.4)}" y="{inches(1.4)}"/><a:ext cx="{inches(3.5)}" cy="{inches(0.4)}"/></a:xfrm>
        <a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 5000"/></a:avLst></a:prstGeom>
        <a:solidFill><a:srgbClr val="{COLOR_BLUE_ACCENT}"/></a:solidFill>
      </p:spPr>
      <p:txBody>
        <a:bodyPr anchor="ctr" lIns="72000" rIns="72000" tIns="18000" bIns="18000"/>
        <a:lstStyle/>
        <a:p><a:pPr algn="ctr"/><a:r><a:rPr lang="en-US" sz="{pt(11)}" b="1"><a:solidFill><a:srgbClr val="{COLOR_WHITE}"/></a:solidFill></a:rPr><a:t>ENTERPRISE TELECOM AIOPS</a:t></a:r></a:p>
      </p:txBody>
    </p:sp>
    """)
    s1.add_textbox(inches(1.4), inches(2.0), inches(10.5), inches(4.2), [
        {"runs": [{"text": "Autonomous Telecom Operations\nwith gbrain", "bold": True, "size": pt(36), "color": COLOR_WHITE}]},
        {"space_before": 120000, "runs": [{"text": "Semantic Knowledge Graphs, Multi-Domain Correlation & Deterministic Storytelling", "bold": False, "size": pt(18), "color": COLOR_CYAN_ACCENT}]},
        {"space_before": 180000, "runs": [{"text": "Architecture, Integration Patterns & Production-Grade Implemented Use Cases", "bold": False, "size": pt(14), "color": COLOR_TEXT_LIGHT}]},
        {"space_before": 250000, "runs": [{"text": "KAgent Platform  |  MARK Intelligent Telecom Assistant  |  2026 Production Release", "bold": True, "size": pt(12), "color": COLOR_EMERALD}]},
    ])
    slides.append(s1)

    # -------------------------------------------------------------
    # SLIDE 2: Executive Summary & The Telecom Problem
    # -------------------------------------------------------------
    s2 = SlideBuilder(2)
    s2.add_header("Executive Summary", "The Challenge of Modern Telecom NOC Operations", "Why traditional alerting fails and how gbrain transforms cognitive incident management")
    # 3 Cards Layout
    card_w = inches(3.64)
    card_h = inches(4.8)
    card_y = inches(1.9)
    # Card 1
    s2.add_card(inches(0.8), card_y, card_w, card_h)
    s2.add_textbox(inches(0.8), card_y, card_w, card_h, [
        {"runs": [{"text": "The NOC Operational Crisis", "bold": True, "size": pt(15), "color": COLOR_RED}]},
        {"space_before": 80000, "bullets": True, "runs": [{"text": "Alarm Storms: ", "bold": True, "size": pt(11)}, {"text": "Over 100k alarms/day across RAN, Core, and Transport silos.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Fragmented Visibility: ", "bold": True, "size": pt(11)}, {"text": "Separate tooling for metrics, logs, tickets, and topology.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Tribal Knowledge: ", "bold": True, "size": pt(11)}, {"text": "Root cause expertise locked in senior engineers' heads.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "High MTTR: ", "bold": True, "size": pt(11)}, {"text": "Hours lost triaging symptoms instead of fixing real causes.", "size": pt(11)}]},
    ])
    # Card 2
    s2.add_card(inches(4.84), card_y, card_w, card_h)
    s2.add_textbox(inches(4.84), card_y, card_w, card_h, [
        {"runs": [{"text": "The Flaw of Generic LLMs", "bold": True, "size": pt(15), "color": COLOR_AMBER}]},
        {"space_before": 80000, "bullets": True, "runs": [{"text": "Hallucination Danger: ", "bold": True, "size": pt(11)}, {"text": "Inventing non-existent alarms or incorrect 3GPP causes.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Context Overload: ", "bold": True, "size": pt(11)}, {"text": "Dumping raw telemetry tokens causes prompt degradation.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Non-Deterministic: ", "bold": True, "size": pt(11)}, {"text": "Different answers for identical production outages.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Missing Provenance: ", "bold": True, "size": pt(11)}, {"text": "Inability to trace claims to exact Prometheus/Loki records.", "size": pt(11)}]},
    ])
    # Card 3
    s2.add_card(inches(8.88), card_y, card_w, card_h)
    s2.add_textbox(inches(8.88), card_y, card_w, card_h, [
        {"runs": [{"text": "The gbrain Semantic Paradigm", "bold": True, "size": pt(15), "color": COLOR_EMERALD}]},
        {"space_before": 80000, "bullets": True, "runs": [{"text": "Semantic Graph Hub: ", "bold": True, "size": pt(11)}, {"text": "Explicit graph of network functions, symptoms, and causality.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Deterministic Narratives: ", "bold": True, "size": pt(11)}, {"text": "Verifiable storytelling backed by structured graph traversal.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Protocol Interoperability: ", "bold": True, "size": pt(11)}, {"text": "Exposed as a Model Context Protocol (MCP) server.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Closed-Loop Learning: ", "bold": True, "size": pt(11)}, {"text": "FCAPS operational lens continually updates runbooks.", "size": pt(11)}]},
    ])
    slides.append(s2)

    # -------------------------------------------------------------
    # SLIDE 3: Architecture & Core Design Principle
    # -------------------------------------------------------------
    s3 = SlideBuilder(3)
    s3.add_header("Platform Architecture", "Core Principle: Semantic Brain vs. Raw Data Store", "Clean separation of concerns guarantees zero data duplication and instant graph scalability")
    # Top principle banner
    s3.add_card(inches(0.8), inches(1.9), inches(11.7), inches(1.0), bg_color="EFF6FF", border_color="93C5FD")
    s3.add_textbox(inches(0.8), inches(1.9), inches(11.7), inches(1.0), [
        {"runs": [{"text": "Architectural Golden Rule: ", "bold": True, "size": pt(14), "color": COLOR_BLUE_ACCENT},
                  {"text": "\"gbrain is the semantic telecom brain, NOT the raw source-of-truth store.\"", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 20000, "runs": [{"text": "Raw incidents stay in Incident Registry. Raw telemetry stays in Grafana/LGTM. Raw alarms stay in NMS. gbrain stores compact semantic projections, causal links, and domain ontologies.", "size": pt(11), "color": COLOR_TEXT_MUTED}]},
    ])
    # 2 Comparison Columns
    col_w = inches(5.7)
    col_h = inches(3.6)
    col_y = inches(3.1)
    # Left Column: Raw Operational Sources
    s3.add_card(inches(0.8), col_y, col_w, col_h)
    s3.add_textbox(inches(0.8), col_y, col_w, col_h, [
        {"runs": [{"text": "Raw Operational Layer (Systems of Record)", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 60000, "bullets": True, "runs": [{"text": "Grafana / LGTM Stack: ", "bold": True, "size": pt(11)}, {"text": "High-velocity metrics (Mimir), logs (Loki), traces (Tempo).", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "NMS / EMS / OSS: ", "bold": True, "size": pt(11)}, {"text": "Raw alarm feeds from Nokia NetAct, Ericsson ENM, Huawei U2000.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "ITSM & Incident Registry: ", "bold": True, "size": pt(11)}, {"text": "Remedy / ServiceNow tickets, SLA timers, operator queues.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Characteristics: ", "bold": True, "size": pt(11)}, {"text": "Petabyte-scale, high-frequency, unlinked, siloed schemas.", "size": pt(11)}]},
    ])
    # Right Column: gbrain Semantic Layer
    s3.add_card(inches(6.8), col_y, col_w, col_h)
    s3.add_textbox(inches(6.8), col_y, col_w, col_h, [
        {"runs": [{"text": "gbrain Semantic Brain (Cognitive Layer)", "bold": True, "size": pt(14), "color": COLOR_BLUE_ACCENT}]},
        {"space_before": 60000, "bullets": True, "runs": [{"text": "Compact Projections: ", "bold": True, "size": pt(11)}, {"text": "Stores semantic summaries (e.g. 'CPU @ 98%', 'RSR breach').", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Causal Graph Edges: ", "bold": True, "size": pt(11)}, {"text": "Explicit links (affects, has-hypothesis, supported-by, targets).", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Domain Knowledge: ", "bold": True, "size": pt(11)}, {"text": "3GPP functional models, standard procedures, service intents.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Deterministic Access: ", "bold": True, "size": pt(11)}, {"text": "Zero hallucination: only traversed facts enter the narrative.", "size": pt(11)}]},
    ])
    slides.append(s3)

    # -------------------------------------------------------------
    # SLIDE 4: MCP Hub & Transport Architecture
    # -------------------------------------------------------------
    s4 = SlideBuilder(4)
    s4.add_header("System Integration", "Model Context Protocol (MCP) Hub & Transport", "Standardized outbound client hub connecting MARK orchestrator to gbrain and external tools")
    card_w4 = inches(5.7)
    card_h4 = inches(4.8)
    # Left Card: MCP Hub Architecture
    s4.add_card(inches(0.8), inches(1.9), card_w4, card_h4)
    s4.add_textbox(inches(0.8), inches(1.9), card_w4, card_h4, [
        {"runs": [{"text": "Centralized MCP Client Hub", "bold": True, "size": pt(15), "color": COLOR_NAVY_DARK}]},
        {"space_before": 60000, "bullets": True, "runs": [{"text": "Single Outbound Gateway: ", "bold": True, "size": pt(11)}, {"text": "All services (Storyteller, Correlation, RCA) call gbrain through `mcp_client_hub`.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "No One-Off Clients: ", "bold": True, "size": pt(11)}, {"text": "Prevents ad-hoc socket connections and unmonitored API calls.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Connector Manifests: ", "bold": True, "size": pt(11)}, {"text": "YAML definitions governing permissions, rate limits, and audit policies.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "End-to-End Tracing: ", "bold": True, "size": pt(11)}, {"text": "Every tool call produces structured JSON traces for auditing.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Enterprise Tooling: ", "bold": True, "size": pt(11)}, {"text": "Exposes status via GET /api/jarvis/connectors/status.", "size": pt(11)}]},
    ])
    # Right Card: Multi-Tier Resilient Transport
    s4.add_card(inches(6.8), inches(1.9), card_w4, card_h4)
    s4.add_textbox(inches(6.8), inches(1.9), card_w4, card_h4, [
        {"runs": [{"text": "Four-Tier Resilient Transport", "bold": True, "size": pt(15), "color": COLOR_BLUE_ACCENT}]},
        {"space_before": 60000, "bullets": True, "runs": [{"text": "1. HTTP MCP (Primary): ", "bold": True, "size": pt(11)}, {"text": "JSON-RPC 2.0 over HTTP (`GBRAIN_MCP_URL=http://localhost:3131/mcp`) with bearer token authentication.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "2. Persistent Stdio MCP: ", "bold": True, "size": pt(11)}, {"text": "Process-bound stdio JSON lines for containerized environments.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "3. Subprocess CLI Fallback: ", "bold": True, "size": pt(11)}, {"text": "Direct execution via `/Users/adeelarshad/.bun/bin/gbrain call <tool>` when daemon is offline.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "4. Embedded In-Memory Graph: ", "bold": True, "size": pt(11)}, {"text": "Built-in mobile core fixture catalog ensuring zero downtime during network partitioning.", "size": pt(11)}]},
    ])
    slides.append(s4)

    # -------------------------------------------------------------
    # SLIDE 5: gbrain Knowledge Model & Namespace Hierarchy
    # -------------------------------------------------------------
    s5 = SlideBuilder(5)
    s5.add_header("Knowledge Taxonomy", "gbrain Namespace Hierarchy & Entity Model", "Structured domain partitioning prevents data pollution and maintains strict ontological boundaries")
    # 4 Cards in 2x2 Grid
    gw = inches(5.7)
    gh = inches(2.3)
    # Box 1: knowledge/
    s5.add_card(inches(0.8), inches(1.9), gw, gh)
    s5.add_textbox(inches(0.8), inches(1.9), gw, gh, [
        {"runs": [{"text": "knowledge/mobile-core/...", "bold": True, "size": pt(13), "color": COLOR_NAVY_DARK}, {"text": " (Stable Domain Knowledge)", "size": pt(11), "color": COLOR_TEXT_MUTED}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "3GPP Architecture: ", "bold": True, "size": pt(10)}, {"text": "AMF, SMF, UPF, gNodeB, MME, HSS, P-CSCF specifications.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Standard Topology: ", "bold": True, "size": pt(10)}, {"text": "Interface connections (N1, N2, N3, S1-MME, SGi, Diameter).", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Service Procedures: ", "bold": True, "size": pt(10)}, {"text": "Initial UE Registration, PDU Session Establishment, VoLTE Call.", "size": pt(10)}]},
    ])
    # Box 2: observations/
    s5.add_card(inches(6.8), inches(1.9), gw, gh)
    s5.add_textbox(inches(6.8), inches(1.9), gw, gh, [
        {"runs": [{"text": "observations/mobile-core/...", "bold": True, "size": pt(13), "color": COLOR_BLUE_ACCENT}, {"text": " (Semantic Facts)", "size": pt(11), "color": COLOR_TEXT_MUTED}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Projected Alarms: ", "bold": True, "size": pt(10)}, {"text": "Normalized alarms with domain, severity, and object ID.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "KPI Breaches: ", "bold": True, "size": pt(10)}, {"text": "RSR dropped to 94.7%, 4G_Attach_SR degraded to 88.2%.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Telemetry Evidence: ", "bold": True, "size": pt(10)}, {"text": "AMF-01 CPU 98%, S1AP message drops, SIP 503 timeouts.", "size": pt(10)}]},
    ])
    # Box 3: correlation/ & incidents/
    s5.add_card(inches(0.8), inches(4.4), gw, gh)
    s5.add_textbox(inches(0.8), inches(4.4), gw, gh, [
        {"runs": [{"text": "correlation/ & incidents/...", "bold": True, "size": pt(13), "color": COLOR_PURPLE}, {"text": " (Reasoning Entities)", "size": pt(11), "color": COLOR_TEXT_MUTED}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Correlation Clusters: ", "bold": True, "size": pt(10)}, {"text": "Multi-alarm grouping by time, topology, and service reachability.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Hypotheses: ", "bold": True, "size": pt(10)}, {"text": "Plausible causal assertions with confidence scores (0.0 - 1.0).", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Decisions & Incidents: ", "bold": True, "size": pt(10)}, {"text": "Promotion decisions and canonical incident pages.", "size": pt(10)}]},
    ])
    # Box 4: storytelling/ & learnings/
    s5.add_card(inches(6.8), inches(4.4), gw, gh)
    s5.add_textbox(inches(6.8), inches(4.4), gw, gh, [
        {"runs": [{"text": "storytelling/ & learnings/...", "bold": True, "size": pt(13), "color": COLOR_EMERALD}, {"text": " (Dissemination & Evolution)", "size": pt(11), "color": COLOR_TEXT_MUTED}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Audience Stories: ", "bold": True, "size": pt(10)}, {"text": "Executive, NOC technical, and customer-facing incident reports.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Spoken Briefs: ", "bold": True, "size": pt(10)}, {"text": "Voice-curated summaries stripped of technical syntax.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "FCAPS Learnings: ", "bold": True, "size": pt(10)}, {"text": "Operator-reviewed knowledge preventing recurrence.", "size": pt(10)}]},
    ])
    slides.append(s5)

    # -------------------------------------------------------------
    # SLIDE 6: Use Case 1 - Multi-Domain Alarm Correlation
    # -------------------------------------------------------------
    s6 = SlideBuilder(6)
    s6.add_header("Use Case 1", "Inter- & Intra-Domain Alarm Correlation Engine", "Ingesting raw alerts from disparate silos and clustering them into verified incident graphs")
    # Left Card: The Pipeline
    s6.add_card(inches(0.8), inches(1.9), inches(5.7), inches(4.8))
    s6.add_textbox(inches(0.8), inches(1.9), inches(5.7), inches(4.8), [
        {"runs": [{"text": "Correlation Engine Workflow", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 50000, "bullets": True, "runs": [{"text": "Multi-Domain Ingestion: ", "bold": True, "size": pt(11)}, {"text": "Ingests alarms across RAN, Transport, Mobile Core, and Site Power.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Deduplication & Normalization: ", "bold": True, "size": pt(11)}, {"text": "Removes duplicate events via stable fingerprint hash.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "10-Minute Sliding Window: ", "bold": True, "size": pt(11)}, {"text": "Groups alarms exhibiting temporal co-occurrence.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Topology & Service Traversal: ", "bold": True, "size": pt(11)}, {"text": "Checks reachability and shared service procedure impact.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Intent Evaluation: ", "bold": True, "size": pt(11)}, {"text": "Violations of service objectives (e.g. 4G Attach SR) increase candidate score.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "gbrain MCP Writer: ", "bold": True, "size": pt(11)}, {"text": "Upserts clusters, decisions, and hypotheses into gbrain.", "size": pt(11)}]},
    ])
    # Right Card: Classification & Scope
    s6.add_card(inches(6.8), inches(1.9), inches(5.7), inches(4.8))
    s6.add_textbox(inches(6.8), inches(1.9), inches(5.7), inches(4.8), [
        {"runs": [{"text": "Outcome Classification & Scoring", "bold": True, "size": pt(14), "color": COLOR_BLUE_ACCENT}]},
        {"space_before": 50000, "runs": [{"text": "Three Operational Classifications:", "bold": True, "size": pt(12), "color": COLOR_NAVY_DARK}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Standalone Event: ", "bold": True, "size": pt(11), "color": COLOR_TEXT_MUTED}, {"text": "Low severity or isolated alarm; retained for audit, no escalation.", "size": pt(11)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Candidate Incident: ", "bold": True, "size": pt(11), "color": COLOR_AMBER}, {"text": "Watch cluster gathering telemetry evidence (status: candidate).", "size": pt(11)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Confirmed Incident: ", "bold": True, "size": pt(11), "color": COLOR_RED}, {"text": "Validated correlation surpassing threshold; promoted for storytelling.", "size": pt(11)}]},
        {"space_before": 50000, "runs": [{"text": "Correlation Scope Separation:", "bold": True, "size": pt(12), "color": COLOR_NAVY_DARK}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Intra-Domain: ", "bold": True, "size": pt(11)}, {"text": "Contained inside one network area (e.g. 5G Core AMF-SMF or Power UPS).", "size": pt(11)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Inter-Domain: ", "bold": True, "size": pt(11)}, {"text": "Cross-boundary cascade (e.g. Transport jitter causing IMS SIP drops).", "size": pt(11)}]},
    ])
    slides.append(s6)

    # -------------------------------------------------------------
    # SLIDE 7: Use Case 2 - Deterministic Incident Storytelling
    # -------------------------------------------------------------
    s7 = SlideBuilder(7)
    s7.add_header("Use Case 2", "Deterministic Incident Storytelling (Data StoryTeller)", "Eliminating AI hallucinations by grounding all incident narratives in graph-traversed truth")
    # Left Card: The Problem & Method
    s7.add_card(inches(0.8), inches(1.9), inches(5.7), inches(4.8))
    s7.add_textbox(inches(0.8), inches(1.9), inches(5.7), inches(4.8), [
        {"runs": [{"text": "Graph-Grounded Narration", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 50000, "bullets": True, "runs": [{"text": "Zero Hallucination: ", "bold": True, "size": pt(11)}, {"text": "The LLM never invents network functions, timestamps, or root causes.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "MobileCoreKnowledge: ", "bold": True, "size": pt(11)}, {"text": "Directly queries gbrain through GbrainClient to assemble the verified fact set.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Strict Narrative Schema: ", "bold": True, "size": pt(11)}, {"text": "Standard 8-part incident structure: Executive Summary, Impact, Leading Hypothesis, Correlation, Grouping Rationale, Causal Chain, Timeline, Still Open.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Auditability: ", "bold": True, "size": pt(11)}, {"text": "Every statement links back to source alarm IDs, Prometheus metrics, or PCAPs.", "size": pt(11)}]},
    ])
    # Right Card: Multi-Audience Views
    s7.add_card(inches(6.8), inches(1.9), inches(5.7), inches(4.8))
    s7.add_textbox(inches(6.8), inches(1.9), inches(5.7), inches(4.8), [
        {"runs": [{"text": "Tri-Audience Tailored Briefs", "bold": True, "size": pt(14), "color": COLOR_BLUE_ACCENT}]},
        {"space_before": 50000, "bullets": True, "runs": [{"text": "1. Executive Brief: ", "bold": True, "size": pt(11), "color": COLOR_PURPLE}, {"text": "High-level summary of subscriber impact (14.2k users), business revenue risk, SLA breach status, and recovery ETA.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "2. NOC Technical Brief: ", "bold": True, "size": pt(11), "color": COLOR_NAVY_DARK}, {"text": "Deep technical diagnosis: node names (AMF-01, PGW-01), specific alarm codes (CPU_HIGH, S1AP_DROP), 3GPP causes (NAS Cause 22), and exact diagnostic steps.", "size": pt(11)}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "3. Customer Operations Update: ", "bold": True, "size": pt(11), "color": COLOR_EMERALD}, {"text": "Transparent, jargon-free notifications for enterprise clients and helpdesk teams explaining regional connectivity impact.", "size": pt(11)}]},
    ])
    slides.append(s7)

    # -------------------------------------------------------------
    # SLIDE 8: Production Golden Scenarios Implemented
    # -------------------------------------------------------------
    s8 = SlideBuilder(8)
    s8.add_header("Implemented Scenarios", "Production Golden Incident Scenarios in gbrain", "Four end-to-end multi-domain incident archetypes implemented, validated, and regression-tested")
    # 4 Cards in 2x2 Grid
    gw8 = inches(5.7)
    gh8 = inches(2.3)
    # Scenario 1: AMF Overload
    s8.add_card(inches(0.8), inches(1.9), gw8, gh8)
    s8.add_textbox(inches(0.8), inches(1.9), gw8, gh8, [
        {"runs": [{"text": "1. 5G Core AMF-01 Signaling Overload", "bold": True, "size": pt(13), "color": COLOR_RED}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Impact: ", "bold": True, "size": pt(10)}, {"text": "5G Initial UE Registration degradation across Dubai Core DC-1.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Causal Chain: ", "bold": True, "size": pt(10)}, {"text": "Signaling burst -> AMF CPU @ 98% -> NAS buffer drops (Cause 22).", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Remediation & Recovery: ", "bold": True, "size": pt(10)}, {"text": "Scaled AMF worker pods from 4 to 8; RSR recovered from 94.7% to 99.9%.", "size": pt(10)}]},
    ])
    # Scenario 2: LTE Attach Failure
    s8.add_card(inches(6.8), inches(1.9), gw8, gh8)
    s8.add_textbox(inches(6.8), inches(1.9), gw8, gh8, [
        {"runs": [{"text": "2. LTE Attach & S1-MME Path Degradation", "bold": True, "size": pt(13), "color": COLOR_AMBER}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Impact: ", "bold": True, "size": pt(10)}, {"text": "14,200 mobile subscribers across Dubai North eNodeBs.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Multi-Node Telemetry: ", "bold": True, "size": pt(10)}, {"text": "MME-01 attach rejects + HSS-01 Diameter ULR timeouts + eNodeB drops.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Leading Hypothesis: ", "bold": True, "size": pt(10)}, {"text": "S1-MME transport path degradation causing control-plane packet loss.", "size": pt(10)}]},
    ])
    # Scenario 3: IMS Voice Call Setup
    s8.add_card(inches(0.8), inches(4.4), gw8, gh8)
    s8.add_textbox(inches(0.8), inches(4.4), gw8, gh8, [
        {"runs": [{"text": "3. Cross-Domain IMS Voice Call Setup (CSSR)", "bold": True, "size": pt(13), "color": COLOR_PURPLE}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Cross-Boundary Cascade: ", "bold": True, "size": pt(10)}, {"text": "Correlates RAN (eNodeB-22), IMS (P-CSCF), and Backhaul.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Correlated Alarms: ", "bold": True, "size": pt(10)}, {"text": "RRC Setup Failures + SIP INVITE drop spike + Link Jitter.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Intent State: ", "bold": True, "size": pt(10)}, {"text": "Service intent `voice_call_drop` violated; correlation score: 92.", "size": pt(10)}]},
    ])
    # Scenario 4: User Plane Gi-LAN
    s8.add_card(inches(6.8), inches(4.4), gw8, gh8)
    s8.add_textbox(inches(6.8), inches(4.4), gw8, gh8, [
        {"runs": [{"text": "4. Gi-LAN Bottleneck & SGi Data Disruption", "bold": True, "size": pt(13), "color": COLOR_BLUE_ACCENT}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "User-Plane Outage: ", "bold": True, "size": pt(10)}, {"text": "Mobile broadband packet forwarding collapse.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "Evidence Chain: ", "bold": True, "size": pt(10)}, {"text": "PGW-01 throughput drop + NAT firewall session exhaustion + router discards.", "size": pt(10)}]},
        {"space_before": 20000, "bullets": True, "runs": [{"text": "RCA Diagnosis: ", "bold": True, "size": pt(10)}, {"text": "Gi-LAN perimeter NAT table saturation, not 3GPP Core failure.", "size": pt(10)}]},
    ])
    slides.append(s8)

    # -------------------------------------------------------------
    # SLIDE 9: Use Case 3 - Visual Explanation & Investigation Workspace
    # -------------------------------------------------------------
    s9 = SlideBuilder(9)
    s9.add_header("Use Case 3", "Visual Explanation & Interactive Investigation Workspace", "Translating complex graph relationships into actionable visual widgets for NOC operators")
    # Left Card: Visual Services
    s9.add_card(inches(0.8), inches(1.9), inches(5.7), inches(4.8))
    s9.add_textbox(inches(0.8), inches(1.9), inches(5.7), inches(4.8), [
        {"runs": [{"text": "Visual Explanation Service", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 50000, "bullets": True, "runs": [{"text": "Dedicated Visual Engine: ", "bold": True, "size": pt(11)}, {"text": "`VisualExplanationService` translates `gbrain` subgraphs into standardized frontend JSON contracts.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Inline Story Visuals: ", "bold": True, "size": pt(11)}, {"text": "Embedded directly inside chat response cards alongside text.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Expandable Evidence Drawer: ", "bold": True, "size": pt(11)}, {"text": "One-click inspection of supporting raw Prometheus/Loki claims without cluttering the chat view.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "HUD Highlight Orb: ", "bold": True, "size": pt(11)}, {"text": "Visual pulse indicating active incident severity in the MARK HUD.", "size": pt(11)}]},
    ])
    # Right Card: Investigation Workspace
    s9.add_card(inches(6.8), inches(1.9), inches(5.7), inches(4.8))
    s9.add_textbox(inches(6.8), inches(1.9), inches(5.7), inches(4.8), [
        {"runs": [{"text": "Interactive NOC Investigation Canvas", "bold": True, "size": pt(14), "color": COLOR_BLUE_ACCENT}]},
        {"space_before": 50000, "bullets": True, "runs": [{"text": "Topology Blast Radius: ", "bold": True, "size": pt(11)}, {"text": "Interactive node graph highlighting root node, cascade path, and unaffected neighboring nodes.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Side-by-Side Telemetry: ", "bold": True, "size": pt(11)}, {"text": "Synchronized time-series metrics from Grafana pinned next to graph nodes.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Operator Action Strip: ", "bold": True, "size": pt(11)}, {"text": "Dynamic action buttons (Acknowledge, Assign, Suppress, Merge, Scale Out) bound to the selected incident ID.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Full Audit Trail: ", "bold": True, "size": pt(11)}, {"text": "Records every operator interaction and state change in Incident Registry.", "size": pt(11)}]},
    ])
    slides.append(s9)

    # -------------------------------------------------------------
    # SLIDE 10: Use Case 4 - Mark Conversational Assistant & Voice
    # -------------------------------------------------------------
    s10 = SlideBuilder(10)
    s10.add_header("Use Case 4", "Mark Conversational Assistant & Curated Voice", "Hands-free operations in the NOC: low-latency speech synthesis tailored for operational dialogue")
    # Top rule banner
    s10.add_card(inches(0.8), inches(1.9), inches(11.7), inches(1.0), bg_color="F5F3FF", border_color="DDD6FE")
    s10.add_textbox(inches(0.8), inches(1.9), inches(11.7), inches(1.0), [
        {"runs": [{"text": "Core Voice Rule: ", "bold": True, "size": pt(14), "color": COLOR_PURPLE},
                  {"text": "\"Brain content is context, NOT a script to read aloud.\"", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 20000, "runs": [{"text": "Mark never reads raw markdown, incident slugs, UUIDs, punctuation, bullet characters, or table syntax over voice. Technical details stay on screen; speech is conversational and brief.", "size": pt(11), "color": COLOR_TEXT_MUTED}]},
    ])
    # 2 Columns
    s10.add_card(inches(0.8), inches(3.1), inches(5.7), inches(3.6))
    s10.add_textbox(inches(0.8), inches(3.1), inches(5.7), inches(3.6), [
        {"runs": [{"text": "Voice Curation Pipeline", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 50000, "bullets": True, "runs": [{"text": "Dual-Payload Generation: ", "bold": True, "size": pt(11)}, {"text": "Every turn outputs a rich technical written report and a separate spoken brief.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "VAD Noise Rejection: ", "bold": True, "size": pt(11)}, {"text": "Silero VAD thresholding (0.70) ignores noisy NOC background chatter.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Streaming WebSocket: ", "bold": True, "size": pt(11)}, {"text": "Sub-400ms audio delivery via ElevenLabs streaming synthesis.", "size": pt(11)}]},
    ])
    s10.add_card(inches(6.8), inches(3.1), inches(5.7), inches(3.6))
    s10.add_textbox(inches(6.8), inches(3.1), inches(5.7), inches(3.6), [
        {"runs": [{"text": "Example: Written vs. Spoken Output", "bold": True, "size": pt(14), "color": COLOR_PURPLE}]},
        {"space_before": 40000, "runs": [{"text": "On-Screen Written Report (Full Technical):", "bold": True, "size": pt(10), "color": COLOR_TEXT_MUTED}]},
        {"space_before": 10000, "runs": [{"text": "# Incident story — incidents/mobile-core/amf-overload-2026-08-09\nStatus: resolved | Severity: SEV-2 | Score: 0.94\nRoot cause: AMF-01 CPU saturation (98%) on worker process 104.\nRemediation: Pod replica count increased 4 -> 8.", "size": pt(9), "color": COLOR_NAVY_DARK}]},
        {"space_before": 30000, "runs": [{"text": "Curated Spoken Voice Brief (Audio Output):", "bold": True, "size": pt(10), "color": COLOR_PURPLE}]},
        {"space_before": 10000, "runs": [{"text": "\"UE Registration is currently severity two and resolved. The confirmed root cause was AMF-01 CPU saturation from a registration signaling burst. Capacity was scaled out and service recovered.\"", "italic": True, "size": pt(10), "color": COLOR_NAVY_DARK}]},
    ])
    slides.append(s10)

    # -------------------------------------------------------------
    # SLIDE 11: Use Case 5 & 6 - RCA Triage & Telemetry Projection
    # -------------------------------------------------------------
    s11 = SlideBuilder(11)
    s11.add_header("Use Cases 5 & 6", "RCA Triage Advisory & Live Telemetry Projection", "Hypothesis-driven root cause analysis coupled with high-speed Grafana LGTM data projection")
    s11.add_card(inches(0.8), inches(1.9), inches(5.7), inches(4.8))
    s11.add_textbox(inches(0.8), inches(1.9), inches(5.7), inches(4.8), [
        {"runs": [{"text": "Use Case 5: Root Cause Analysis (RCA)", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 50000, "bullets": True, "runs": [{"text": "Hypothesis Engine: ", "bold": True, "size": pt(11)}, {"text": "Evaluates candidate causal explanations against confirmed graph evidence.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Confidence Scoring: ", "bold": True, "size": pt(11)}, {"text": "Scores hypotheses (0.0 to 1.0) based on metric alignment, topology, and alarms.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Fact vs. Inference: ", "bold": True, "size": pt(11)}, {"text": "Explicitly separates confirmed facts from working inferences.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Diagnostic Next Steps: ", "bold": True, "size": pt(11)}, {"text": "Suggests the exact next test or command needed to confirm unproven hypotheses.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Remediation Advisory: ", "bold": True, "size": pt(11)}, {"text": "Proposes approved MOPs (Method of Procedure) with human approval gates.", "size": pt(11)}]},
    ])
    s11.add_card(inches(6.8), inches(1.9), inches(5.7), inches(4.8))
    s11.add_textbox(inches(6.8), inches(1.9), inches(5.7), inches(4.8), [
        {"runs": [{"text": "Use Case 6: Telemetry Evidence Projection", "bold": True, "size": pt(14), "color": COLOR_BLUE_ACCENT}]},
        {"space_before": 50000, "bullets": True, "runs": [{"text": "Grafana MCP Integration: ", "bold": True, "size": pt(11)}, {"text": "Connects Mark directly to Prometheus metrics, Loki logs, and Tempo traces via MCP.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Compact Projections: ", "bold": True, "size": pt(11)}, {"text": "Projects only salient threshold breaches into gbrain (`grafana/*` pages), avoiding database bloat.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "On-Demand Enrichment: ", "bold": True, "size": pt(11)}, {"text": "Storyteller queries live Grafana telemetry on demand when `include_live_telemetry` is requested.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Bidirectional Provenance: ", "bold": True, "size": pt(11)}, {"text": "Graph claims embed direct deep-links to Grafana dashboard time windows.", "size": pt(11)}]},
    ])
    slides.append(s11)

    # -------------------------------------------------------------
    # SLIDE 12: Use Case 7 - FCAPS Closed-Loop Learning
    # -------------------------------------------------------------
    s12 = SlideBuilder(12)
    s12.add_header("Use Case 7", "FCAPS Closed-Loop Learning & Knowledge Evolution", "Transforming resolved operational incidents into durable enterprise knowledge and runbooks")
    # 3 Cards Layout
    c_w = inches(3.64)
    c_h = inches(4.8)
    s12.add_card(inches(0.8), inches(1.9), c_w, c_h)
    s12.add_textbox(inches(0.8), inches(1.9), c_w, c_h, [
        {"runs": [{"text": "The FCAPS Operational Lens", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 60000, "bullets": True, "runs": [{"text": "F - Fault: ", "bold": True, "size": pt(11)}, {"text": "Alarms, link down, crash loops, timeouts.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "C - Configuration: ", "bold": True, "size": pt(11)}, {"text": "Change requests, MOP execution, rollbacks.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "A - Accounting: ", "bold": True, "size": pt(11)}, {"text": "Billing, charging gateway, quota limits.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "P - Performance: ", "bold": True, "size": pt(11)}, {"text": "Latency, throughput, CSSR, CPU saturation.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "S - Security: ", "bold": True, "size": pt(11)}, {"text": "Auth anomalies, certificate expiry, DDoS.", "size": pt(11)}]},
    ])
    s12.add_card(inches(4.84), inches(1.9), c_w, c_h)
    s12.add_textbox(inches(4.84), inches(1.9), c_w, c_h, [
        {"runs": [{"text": "Post-Incident Enrichment", "bold": True, "size": pt(14), "color": COLOR_BLUE_ACCENT}]},
        {"space_before": 60000, "bullets": True, "runs": [{"text": "Operator Feedback Loop: ", "bold": True, "size": pt(11)}, {"text": "NOC operators review and validate incident resolutions.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Gap Identification: ", "bold": True, "size": pt(11)}, {"text": "Detects missing telemetry metrics or incomplete alarm definitions.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Runbook Candidates: ", "bold": True, "size": pt(11)}, {"text": "Automatically proposes updated diagnostic runbooks in `learnings/`.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Review Gates: ", "bold": True, "size": pt(11)}, {"text": "Learnings require senior engineer signoff before becoming permanent knowledge.", "size": pt(11)}]},
    ])
    s12.add_card(inches(8.88), inches(1.9), c_w, c_h)
    s12.add_textbox(inches(8.88), inches(1.9), c_w, c_h, [
        {"runs": [{"text": "Durable Knowledge Evolution", "bold": True, "size": pt(14), "color": COLOR_EMERALD}]},
        {"space_before": 60000, "bullets": True, "runs": [{"text": "Preventing Recurrence: ", "bold": True, "size": pt(11)}, {"text": "Future correlation runs match known past incident signatures instantly.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Query Improvement: ", "bold": True, "size": pt(11)}, {"text": "Generates optimized PromQL/LogQL queries for emerging failure modes.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Asset Health Index: ", "bold": True, "size": pt(11)}, {"text": "Continuously refines component MTBF and risk profiles.", "size": pt(11)}]},
        {"space_before": 35000, "bullets": True, "runs": [{"text": "Autonomous Improvement: ", "bold": True, "size": pt(11)}, {"text": "System evolves with every shift without software code changes.", "size": pt(11)}]},
    ])
    slides.append(s12)

    # -------------------------------------------------------------
    # SLIDE 13: Summary Matrix of Implemented Capabilities
    # -------------------------------------------------------------
    s13 = SlideBuilder(13)
    s13.add_header("Capability Matrix", "Summary of Implemented gbrain Capabilities & Services", "Comprehensive overview of services, connectors, data consumed, and operational outputs")
    s13.add_card(inches(0.8), inches(1.9), inches(11.7), inches(4.8))
    s13.add_textbox(inches(0.8), inches(1.9), inches(11.7), inches(4.8), [
        {"runs": [{"text": "Implemented Service Capabilities in KAgent / MARK", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Correlation Service: ", "bold": True, "size": pt(11), "color": COLOR_BLUE_ACCENT}, {"text": "Groups alarms/KPIs via time-window, topology, and service intent. Writes correlation clusters & decisions to gbrain.", "size": pt(11)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Storytelling Service: ", "bold": True, "size": pt(11), "color": COLOR_PURPLE}, {"text": "Traverses gbrain graph to produce deterministic written stories, executive briefs, customer updates, and spoken audio.", "size": pt(11)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Visual Explanation Service: ", "bold": True, "size": pt(11), "color": COLOR_EMERALD}, {"text": "Converts gbrain incident graphs into visual widgets, HUD highlight orbs, evidence drawers, and mini-canvas investigation views.", "size": pt(11)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Telemetry Evidence Service: ", "bold": True, "size": pt(11), "color": COLOR_AMBER}, {"text": "Bridges Grafana LGTM with gbrain via MCP Hub, extracting facts and maintaining bidirectional deep-link provenance.", "size": pt(11)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "RCA & Triage Service: ", "bold": True, "size": pt(11), "color": COLOR_RED}, {"text": "Generates scored causal hypotheses, differentiates facts from inferences, and formulates diagnostic next steps.", "size": pt(11)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "FCAPS Learning Service: ", "bold": True, "size": pt(11), "color": COLOR_CYAN_ACCENT}, {"text": "Applies 5-dimension operational lens to capture reviewed learnings, playbook candidates, and query templates in gbrain.", "size": pt(11)}]},
    ])
    slides.append(s13)

    # -------------------------------------------------------------
    # SLIDE 14: Business Value & Operational Impact
    # -------------------------------------------------------------
    s14 = SlideBuilder(14)
    s14.add_header("Operational Impact", "Quantified Business Value & ROI for Telecom Operators", "Realizing dramatic MTTR reductions, alert fatigue elimination, and total reporting auditability")
    # 4 Metric Cards
    m_w = inches(2.7)
    m_h = inches(4.8)
    # Metric 1
    s14.add_card(inches(0.8), inches(1.9), m_w, m_h)
    s14.add_textbox(inches(0.8), inches(1.9), m_w, m_h, [
        {"runs": [{"text": "-75%", "bold": True, "size": pt(36), "color": COLOR_BLUE_ACCENT}]},
        {"space_before": 30000, "runs": [{"text": "MTTR Reduction", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Triages root causes in seconds instead of hours.", "size": pt(10)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Automates multi-domain correlation across Core, RAN, and Transport.", "size": pt(10)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Immediate next diagnostic action guidance for tier-1 engineers.", "size": pt(10)}]},
    ])
    # Metric 2
    s14.add_card(inches(3.8), inches(1.9), m_w, m_h)
    s14.add_textbox(inches(3.8), inches(1.9), m_w, m_h, [
        {"runs": [{"text": "-90%", "bold": True, "size": pt(36), "color": COLOR_EMERALD}]},
        {"space_before": 30000, "runs": [{"text": "Alert Fatigue", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Suppresses redundant symptom alarms into single incidents.", "size": pt(10)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Separates standalone noise from critical cluster promotions.", "size": pt(10)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Prevents catastrophic alarm storms during fiber cuts or power loss.", "size": pt(10)}]},
    ])
    # Metric 3
    s14.add_card(inches(6.8), inches(1.9), m_w, m_h)
    s14.add_textbox(inches(6.8), inches(1.9), m_w, m_h, [
        {"runs": [{"text": "100%", "bold": True, "size": pt(36), "color": COLOR_PURPLE}]},
        {"space_before": 30000, "runs": [{"text": "Deterministic Trust", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Zero AI hallucination in mission-critical NOC narratives.", "size": pt(10)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Complete audit trail from claim to raw Prometheus/Loki records.", "size": pt(10)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Compliant with telecom regulatory and SLA audit mandates.", "size": pt(10)}]},
    ])
    # Metric 4
    s14.add_card(inches(9.8), inches(1.9), m_w, m_h)
    s14.add_textbox(inches(9.8), inches(1.9), m_w, m_h, [
        {"runs": [{"text": "3x", "bold": True, "size": pt(36), "color": COLOR_AMBER}]},
        {"space_before": 30000, "runs": [{"text": "NOC Efficiency", "bold": True, "size": pt(14), "color": COLOR_NAVY_DARK}]},
        {"space_before": 40000, "bullets": True, "runs": [{"text": "Hands-free voice querying for incident commanders.", "size": pt(10)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Automated executive and customer notification generation.", "size": pt(10)}]},
        {"space_before": 30000, "bullets": True, "runs": [{"text": "Faster shift handovers with persistent incident storytelling.", "size": pt(10)}]},
    ])
    slides.append(s14)

    # -------------------------------------------------------------
    # SLIDE 15: Conclusion & Future Roadmap (Dark Theme)
    # -------------------------------------------------------------
    s15 = SlideBuilder(15, is_dark=True)
    s15.add_card(inches(0.8), inches(0.8), inches(11.73), inches(5.9), bg_color="1E293B", border_color="334155")
    s15.add_textbox(inches(1.4), inches(1.4), inches(10.5), inches(4.8), [
        {"runs": [{"text": "The Future of Autonomous Telecom with gbrain", "bold": True, "size": pt(28), "color": COLOR_WHITE}]},
        {"space_before": 60000, "runs": [{"text": "Next Development Horizons on the KAgent Platform", "bold": False, "size": pt(16), "color": COLOR_CYAN_ACCENT}]},
        {"space_before": 120000, "bullets": True, "runs": [{"text": "Autonomous Closed-Loop Remediation: ", "bold": True, "size": pt(13), "color": COLOR_WHITE}, {"text": "Linking gbrain root cause decisions to approved Automation Engine playbooks with canary rollback safety.", "size": pt(13), "color": COLOR_TEXT_LIGHT}]},
        {"space_before": 60000, "bullets": True, "runs": [{"text": "Audio-Visual Synchronized Playback: ", "bold": True, "size": pt(13), "color": COLOR_WHITE}, {"text": "Claim-level visual highlight synchronization with streaming spoken audio briefs in Mark HUD.", "size": pt(13), "color": COLOR_TEXT_LIGHT}]},
        {"space_before": 60000, "bullets": True, "runs": [{"text": "Live Digital Twin Ingestion: ", "bold": True, "size": pt(13), "color": COLOR_WHITE}, {"text": "Real-time topology synchronization streaming from network discovery engines into gbrain.", "size": pt(13), "color": COLOR_TEXT_LIGHT}]},
        {"space_before": 60000, "bullets": True, "runs": [{"text": "Multi-Operator Federated Knowledge: ", "bold": True, "size": pt(13), "color": COLOR_WHITE}, {"text": "Cross-network anomaly pattern exchange without leaking confidential subscriber metadata.", "size": pt(13), "color": COLOR_TEXT_LIGHT}]},
        {"space_before": 120000, "runs": [{"text": "Thank You  |  Q&A  |  adeel@kagent.dev", "bold": True, "size": pt(14), "color": COLOR_EMERALD}]},
    ])
    slides.append(s15)

    # -------------------------------------------------------------
    # Packaging into standard OpenXML PPTX
    # -------------------------------------------------------------
    z = zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED)

    # 1. [Content_Types].xml
    types_xml = ['''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>''']
    for i in range(1, len(slides) + 1):
        types_xml.append(f'  <Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
    types_xml.append('</Types>')
    z.writestr("[Content_Types].xml", "\n".join(types_xml))

    # 2. _rels/.rels
    z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>""")

    # 3. ppt/_rels/presentation.xml.rels
    pres_rels = ['''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>''']
    for i in range(1, len(slides) + 1):
        pres_rels.append(f'  <Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>')
    pres_rels.append('</Relationships>')
    z.writestr("ppt/_rels/presentation.xml.rels", "\n".join(pres_rels))

    # 4. ppt/presentation.xml
    pres_xml = ['''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/officeDocument/2006/presentationml">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>''']
    for i in range(1, len(slides) + 1):
        pres_xml.append(f'    <p:sldId id="{255+i}" r:id="rId{i+1}"/>')
    pres_xml.append('''  </p:sldIdLst>
  <p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>''')
    z.writestr("ppt/presentation.xml", "\n".join(pres_xml))

    # 5. ppt/theme/theme1.xml
    z.writestr("ppt/theme/theme1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1F2937"/></a:dk2>
      <a:lt2><a:srgbClr val="F3F4F6"/></a:lt2>
      <a:accent1><a:srgbClr val="2563EB"/></a:accent1>
      <a:accent2><a:srgbClr val="10B981"/></a:accent2>
      <a:accent3><a:srgbClr val="F59E0B"/></a:accent3>
      <a:accent4><a:srgbClr val="EF4444"/></a:accent4>
      <a:accent5><a:srgbClr val="8B5CF6"/></a:accent5>
      <a:accent6><a:srgbClr val="06B6D4"/></a:accent6>
      <a:hlink><a:srgbClr val="2563EB"/></a:hlink>
      <a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont><a:latin typeface="Segoe UI"/></a:majorFont>
      <a:minorFont><a:latin typeface="Segoe UI"/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>""")

    # 6. ppt/slideMasters/slideMaster1.xml
    z.writestr("ppt/slideMasters/slideMaster1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/officeDocument/2006/presentationml">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr/>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
  <p:txStyles>
    <p:titleStyle><a:lvl1pPr><a:defRPr sz="4400"/></a:lvl1pPr></p:titleStyle>
    <p:bodyStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:bodyStyle>
    <p:otherStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:otherStyle>
  </p:txStyles>
</p:sldMaster>""")

    # 7. ppt/slideMasters/_rels/slideMaster1.xml.rels
    z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>""")

    # 8. ppt/slideLayouts/slideLayout1.xml
    z.writestr("ppt/slideLayouts/slideLayout1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/officeDocument/2006/presentationml" type="blank">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr/>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>""")

    # 9. ppt/slideLayouts/_rels/slideLayout1.xml.rels
    z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>""")

    # 10. Each Slide and its rels
    for i, slide in enumerate(slides, start=1):
        z.writestr(f"ppt/slides/slide{i}.xml", slide.to_xml())
        z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>""")

    z.close()
    print(f"Successfully generated {out_path} with {len(slides)} slides! File size: {os.path.getsize(out_path)} bytes")


if __name__ == "__main__":
    out_file = "/Users/adeelarshad/kagent/gbrain_use_cases_presentation.pptx"
    if len(sys.argv) > 1:
        out_file = sys.argv[1]
    build_presentation(out_file)
