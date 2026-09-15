#!/usr/bin/env python3
import struct
import sys
import os
import json
from datetime import datetime

# Load dynamic protocol configurations
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOCOLS_CONFIG_PATH = os.path.join(SCRIPT_DIR, "..", "resources", "protocols.json")

# Default configurations in case file loading fails
DEFAULT_CAMEL_OPCODES = {
    # CAMEL Common Opcodes
    0: "InitialDP",
    4: "ActivityTest / sendRoutingInfo",
    20: "Connect",
    22: "ReleaseCall / sendRoutingInfoForSM",
    23: "RequestReportBCSMEvent / reportSM-DeliveryStatus",
    24: "EventReportBCSM",
    31: "Continue",
    35: "ApplyCharging",
    36: "ApplyChargingReport",
    
    # GSM MAP Common Opcodes
    2: "updateLocation",
    3: "cancelLocation",
    7: "insertSubscriberData",
    8: "deleteSubscriberData",
    9: "provideRoamingNumber",
    44: "anyTimeInterrogation",
    45: "sendParameters",
    46: "registerSS",
    56: "sendRoutingInfoForGprs",
    57: "failureReport",
    59: "processUnstructuredSS-Request",
    60: "unstructuredSS-Request",
    61: "unstructuredSS-Notify"
}

DEFAULT_TCAP_MSG_TYPES = {
    0x62: "Begin",
    0x64: "End",
    0x65: "Continue",
    0x67: "Abort"
}

DEFAULT_PPIDS = {
    1: "IUA",
    2: "M2UA",
    3: "M3UA",
    4: "SUA",
    5: "M2PA"
}

DEFAULT_PORT_MAPPINGS = {
    "tcp": {5060: "SIP", 5061: "SIP-TLS", 3868: "DIAMETER"},
    "udp": {5060: "SIP", 3868: "DIAMETER"}
}

DEFAULT_SIP_METHODS = [
    "INVITE", "ACK", "BYE", "CANCEL", "REGISTER", "OPTIONS", 
    "PRACK", "SUBSCRIBE", "NOTIFY", "PUBLISH", "INFO", "REFER", 
    "MESSAGE", "UPDATE"
]

class ProtocolConfig:
    def __init__(self):
        self.camel_opcodes = DEFAULT_CAMEL_OPCODES
        self.tcap_msg_types = DEFAULT_TCAP_MSG_TYPES
        self.ppids = DEFAULT_PPIDS
        self.port_mappings = DEFAULT_PORT_MAPPINGS
        self.sip_methods = DEFAULT_SIP_METHODS
        self.load_config()

    def load_config(self):
        if os.path.exists(PROTOCOLS_CONFIG_PATH):
            try:
                with open(PROTOCOLS_CONFIG_PATH, 'r') as f:
                    data = json.load(f)
                    
                # Load CAMEL Opcodes
                if "camel_opcodes" in data:
                    self.camel_opcodes = {int(k): v for k, v in data["camel_opcodes"].items()}
                    
                # Load TCAP Message Types
                if "tcap_msg_types" in data:
                    self.tcap_msg_types = {int(k): v for k, v in data["tcap_msg_types"].items()}
                    
                # Load SCTP PPIDs
                if "sctp_ppid_mappings" in data:
                    self.ppids = {int(k): v for k, v in data["sctp_ppid_mappings"].items()}
                    
                # Load Port Mappings
                if "port_mappings" in data:
                    self.port_mappings = {
                        proto: {int(port): svc for port, svc in mappings.items()}
                        for proto, mappings in data["port_mappings"].items()
                    }
                    
                # Load SIP Methods
                if "sip_methods" in data:
                    self.sip_methods = data["sip_methods"]
                    
            except Exception as e:
                print(f"Warning: Failed to load protocols.json ({e}). Using built-in defaults.")

    def save_config(self):
        try:
            data = {
                "camel_opcodes": {str(k): v for k, v in self.camel_opcodes.items()},
                "tcap_msg_types": {str(k): v for k, v in self.tcap_msg_types.items()},
                "sctp_ppid_mappings": {str(k): v for k, v in self.ppids.items()},
                "port_mappings": {
                    proto: {str(port): svc for port, svc in mappings.items()}
                    for proto, mappings in self.port_mappings.items()
                },
                "sip_methods": self.sip_methods
            }
            with open(PROTOCOLS_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"[Learning Engine] Successfully updated protocols config file at: {PROTOCOLS_CONFIG_PATH}")
        except Exception as e:
            print(f"Warning: Failed to save protocols.json ({e})")

    def learn_port(self, proto: str, port: int, service: str):
        if proto not in self.port_mappings:
            self.port_mappings[proto] = {}
        if port not in self.port_mappings[proto]:
            self.port_mappings[proto][port] = service
            print(f"[Learning Engine] Learned new port: {proto}/{port} ➔ {service}")
            self.save_config()

    def learn_ppid(self, ppid: int, name: str):
        if ppid not in self.ppids:
            self.ppids[ppid] = name
            print(f"[Learning Engine] Learned new SCTP PPID: {ppid} ➔ {name}")
            self.save_config()

CONFIG = ProtocolConfig()

# Utility to parse ASN.1 BER
def parse_ber(data):
    elements = []
    offset = 0
    while offset < len(data):
        if len(data) - offset < 2:
            break
        
        tag = data[offset]
        offset += 1
        
        # Multibyte tags
        if (tag & 0x1F) == 0x1F:
            tag_val = tag
            while offset < len(data):
                b = data[offset]
                offset += 1
                tag_val = (tag_val << 8) | b
                if not (b & 0x80):
                    break
            tag = tag_val
            
        if offset >= len(data):
            break
            
        length_byte = data[offset]
        offset += 1
        
        if length_byte == 0x80:
            # Indefinite length
            end_offset = offset
            depth = 1
            while end_offset < len(data) - 1:
                if data[end_offset] == 0x00 and data[end_offset+1] == 0x00:
                    depth -= 1
                    if depth == 0:
                        break
                end_offset += 1
            
            length = end_offset - offset
            value = data[offset:offset+length]
            offset = end_offset + 2 # skip 00 00
        elif length_byte & 0x80:
            # Long form definite length
            num_bytes = length_byte & 0x7F
            if offset + num_bytes > len(data):
                break
            length = 0
            for _ in range(num_bytes):
                length = (length << 8) | data[offset]
                offset += 1
            value = data[offset:offset+length]
            offset += length
        else:
            # Short form definite length
            length = length_byte
            value = data[offset:offset+length]
            offset += length
            
        elements.append((tag, value))
        
    return elements

def find_ber_element(elements, target_tag):
    for tag, val in elements:
        if tag == target_tag:
            return val
        if (tag & 0x20) == 0x20:
            try:
                sub_elements = parse_ber(val)
                result = find_ber_element(sub_elements, target_tag)
                if result is not None:
                    return result
            except Exception:
                pass
    return None


class BaseDissector:
    """Abstract interface for all protocol-specific dissectors."""
    def matches(self, packet_info) -> bool:
        raise NotImplementedError
        
    def dissect(self, packet_info, payload) -> dict:
        raise NotImplementedError


class SigtranDissector(BaseDissector):
    """Dissector for SS7/SIGTRAN (M2UA, M3UA, SCCP, TCAP, MAP/CAMEL) over SCTP."""
    def matches(self, packet_info) -> bool:
        return packet_info["protocol"] == 132 and packet_info.get("ppid") in (2, 3, 5)
        
    def dissect(self, packet_info, payload) -> dict:
        ppid = packet_info.get("ppid")
        opc = None
        dpc = None
        sccp_data = None
        calling_ssn = None
        called_ssn = None
        
        # M2UA (PPID 2)
        if ppid == 2:
            m2ua_len = len(payload)
            if m2ua_len >= 8:
                p_offset = 8
                while p_offset < m2ua_len:
                    if m2ua_len - p_offset < 4:
                        break
                    p_tag, p_len = struct.unpack('>HH', payload[p_offset:p_offset+4])
                    if p_tag == 0x0300: # Protocol Data
                        p_val = payload[p_offset+4 : p_offset+p_len]
                        if len(p_val) >= 5:
                            routing_label = struct.unpack('<I', p_val[1:5])[0]
                            dpc = routing_label & 0x3FFF
                            opc = (routing_label >> 14) & 0x3FFF
                            sccp_data = p_val[5:]
                            
                            # Parse SCCP headers to extract SSNs
                            if len(sccp_data) >= 4:
                                for i in range(min(len(sccp_data) - 1, 15)):
                                    if sccp_data[i] == 0x12 and i < len(sccp_data) - 1:
                                        called_ssn = sccp_data[i+1]
                                    elif sccp_data[i] == 0x43 and i < len(sccp_data) - 1:
                                        calling_ssn = sccp_data[i+1]
                        break
                    p_offset += ((p_len + 3) // 4) * 4
                    
        # M3UA (PPID 3)
        elif ppid == 3:
            m3ua_len = len(payload)
            if m3ua_len >= 8:
                p_offset = 8
                while p_offset < m3ua_len:
                    if m3ua_len - p_offset < 4:
                        break
                    p_tag, p_len = struct.unpack('>HH', payload[p_offset:p_offset+4])
                    if p_tag in (0x0210, 0x0310, 0x0300): # Protocol Data tags
                        p_val = payload[p_offset+4 : p_offset+p_len]
                        if len(p_val) >= 12:
                            opc = struct.unpack('>I', p_val[0:4])[0]
                            dpc = struct.unpack('>I', p_val[4:8])[0]
                            sccp_data = p_val[12:]
                            
                            # Parse SCCP headers to extract SSNs
                            if len(sccp_data) >= 4:
                                for i in range(min(len(sccp_data) - 1, 15)):
                                    if sccp_data[i] == 0x12 and i < len(sccp_data) - 1:
                                        called_ssn = sccp_data[i+1]
                                    elif sccp_data[i] == 0x43 and i < len(sccp_data) - 1:
                                        calling_ssn = sccp_data[i+1]
                        break
                    p_offset += ((p_len + 3) // 4) * 4
                    
        # M2PA (PPID 5)
        elif ppid == 5:
            m2pa_len = len(payload)
            if m2pa_len >= 8:
                msg_class = payload[2]
                msg_type = payload[3]
                if msg_class == 0x0B and msg_type == 0x01: # User Data message class & type
                    mtp3_data = payload[8:]
                    if len(mtp3_data) >= 4:
                        # Try 4-byte routing label (ITU/TTC) and 7-byte routing label (ANSI)
                        try_sccp_4 = mtp3_data[4:]
                        try_sccp_7 = mtp3_data[7:]
                        
                        has_tcap_4 = any(bytes([tag]) in try_sccp_4[:12] for tag in CONFIG.tcap_msg_types.keys())
                        has_tcap_7 = any(bytes([tag]) in try_sccp_7[:12] for tag in CONFIG.tcap_msg_types.keys())
                        
                        if has_tcap_7 and len(mtp3_data) >= 7:
                            # ANSI Routing Label: 3 bytes DPC, 3 bytes OPC, 1 byte SLS
                            dpc = (mtp3_data[0] << 16) | (mtp3_data[1] << 8) | mtp3_data[2]
                            opc = (mtp3_data[3] << 16) | (mtp3_data[4] << 8) | mtp3_data[5]
                            sccp_data = try_sccp_7
                        else:
                            # ITU/TTC Routing Label: 4 bytes
                            val = struct.unpack('>I', mtp3_data[0:4])[0]
                            dpc = val & 0x3FFF
                            opc = (val >> 14) & 0x3FFF
                            # Fallback to TTC 16-bit unpack if ITU yields 0
                            if dpc == 0 or opc == 0:
                                dpc = struct.unpack('>H', mtp3_data[0:2])[0]
                                opc = struct.unpack('>H', mtp3_data[2:4])[0]
                            sccp_data = try_sccp_4
                            
                        # Parse SCCP headers to extract SSNs
                        if sccp_data and len(sccp_data) >= 4:
                            for i in range(min(len(sccp_data) - 1, 15)):
                                if sccp_data[i] == 0x12 and i < len(sccp_data) - 1:
                                    called_ssn = sccp_data[i+1]
                                elif sccp_data[i] == 0x43 and i < len(sccp_data) - 1:
                                    calling_ssn = sccp_data[i+1]
                    
        if not sccp_data:
            return None
            
        # Store extracted SSN to support RANAP trigger
        packet_info["called_ssn"] = called_ssn
        packet_info["calling_ssn"] = calling_ssn
        
        # If SSN is 142 (RANAP), delegate to RANAP parser instead!
        if called_ssn == 142 or calling_ssn == 142:
            packet_info["ssn"] = 142
            ranap_start = -1
            for offset in (8, 10, 12, 14, 16, 6, 4):
                if offset < len(sccp_data):
                    val = (sccp_data[offset] >> 4) & 0x0F
                    if val in (0, 1, 2, 3):
                        ranap_start = offset
                        break
            if ranap_start != -1:
                ranap_payload = sccp_data[ranap_start:]
                return RanapDissector().dissect(packet_info, ranap_payload)
            
        # Parse TCAP & SCCP
        tcap_start = -1
        for tcap_tag in CONFIG.tcap_msg_types.keys():
            pos = sccp_data.find(bytes([tcap_tag]))
            if pos != -1:
                tcap_start = pos
                break
                
        if tcap_start == -1:
            return None
            
        tcap_payload = sccp_data[tcap_start:]
        tcap_info = self._decode_tcap(tcap_payload)
        
        return {
            "protocol_name": "SIGTRAN",
            "src_pc": opc,
            "dest_pc": dpc,
            "tcap_msg": tcap_info["msg_type"],
            "otid": tcap_info["otid"],
            "dtid": tcap_info["dtid"],
            "operations": tcap_info["op_names"],
            "components": tcap_info["components"]
        }
        
    def _decode_tcap(self, tcap_data) -> dict:
        details = {
            "msg_type": "Unknown",
            "otid": None,
            "dtid": None,
            "op_codes": [],
            "op_names": [],
            "components": []
        }
        
        try:
            tcap_elements = parse_ber(tcap_data)
            if not tcap_elements:
                return details
                
            top_tag, top_val = tcap_elements[0]
            details["msg_type"] = CONFIG.tcap_msg_types.get(top_tag, f"Type {hex(top_tag)}")
            
            # Extract Transaction IDs
            otid_bytes = find_ber_element(tcap_elements, 0x48)
            if otid_bytes:
                details["otid"] = otid_bytes.hex().upper()
                
            dtid_bytes = find_ber_element(tcap_elements, 0x49)
            if dtid_bytes:
                details["dtid"] = dtid_bytes.hex().upper()
                
            # ANSI TCAP Transaction ID (Tag 0xC7 / 199)
            ansi_tid_bytes = find_ber_element(tcap_elements, 0xC7)
            if ansi_tid_bytes:
                details["otid"] = ansi_tid_bytes.hex().upper()
                details["dtid"] = ansi_tid_bytes.hex().upper()
                
            # ITU Component Portion (0x6C) or ANSI Component Sequence (0xE8 / 232)
            component_portion = find_ber_element(tcap_elements, 0x6C) or find_ber_element(tcap_elements, 0xE8)
            if component_portion:
                comp_elements = parse_ber(component_portion)
                for c_tag, c_val in comp_elements:
                    # ITU Invoke (0xA1), Return Result (0xA2)
                    # ANSI Invoke (0xD1 / 209 or 0xD5 / 213), Return Result (0xD2 / 210 or 0xD6 / 214)
                    if c_tag in (0xA1, 0xA2, 0xD1, 0xD2, 0xD5, 0xD6):
                        c_sub = parse_ber(c_val)
                        inv_id = None
                        op_code = None
                        
                        ansi_inv_id = find_ber_element(c_sub, 0xCF)
                        if ansi_inv_id:
                            inv_id = int.from_bytes(ansi_inv_id, byteorder='big')
                        ansi_op_code = find_ber_element(c_sub, 0xF2)
                        if ansi_op_code:
                            op_code = int.from_bytes(ansi_op_code, byteorder='big')
                            
                        if inv_id is None or op_code is None:
                            for s_tag, s_val in c_sub:
                                if s_tag == 0x02:
                                    if inv_id is None:
                                        inv_id = int.from_bytes(s_val, byteorder='big')
                                    else:
                                        op_code = int.from_bytes(s_val, byteorder='big')
                                        
                        if op_code is not None:
                            op_name = CONFIG.camel_opcodes.get(op_code, f"Op-{op_code}")
                            details["op_codes"].append(op_code)
                            details["op_names"].append(op_name)
                            
                            comp_info = {
                                "type": "Invoke" if c_tag in (0xA1, 0xD1, 0xD5) else "ReturnResult", 
                                "id": inv_id, 
                                "op": op_code, 
                                "name": op_name
                            }
                            
                            if op_code == 24: # EventReportBCSM
                                args_bytes = find_ber_element(c_sub, 0x30)
                                if args_bytes:
                                    args = parse_ber(args_bytes)
                                    ev_type = find_ber_element(args, 0x80)
                                    if ev_type:
                                        ev_val = int.from_bytes(ev_type, byteorder='big')
                                        ev_names = {
                                            4: "routeSelectFailure", 5: "oCalledPartyBusy", 
                                            6: "oNoAnswer", 7: "oAnswer", 9: "oDisconnect"
                                        }
                                        comp_info["event_type"] = ev_names.get(ev_val, f"Event-{ev_val}")
                                        
                            details["components"].append(comp_info)
        except Exception:
            pass
            
        return details


class SipDissector(BaseDissector):
    """Dissector for Session Initiation Protocol (SIP) VoLTE/IMS call flows.
    
    Content-based detection: matches any TCP/UDP packet and verifies via
    payload inspection, so SIP on non-standard ports is automatically detected.
    """
    def matches(self, packet_info) -> bool:
        return packet_info["protocol"] in (6, 17)
        
    def _scan_for_sip(self, text: str) -> bool:
        """Scan entire payload for SIP protocol signatures."""
        if "SIP/2.0" in text:
            return True
        for method in CONFIG.sip_methods:
            # SIP methods appear at line boundaries: \r\nMETHOD , \nMETHOD , or start of text
            if (text.startswith(method + " ") or
                f"\r\n{method} " in text or
                f"\n{method} " in text):
                return True
        return False

    def _find_sip_line(self, lines):
        """Find the first line that looks like a SIP request/response."""
        for line in lines:
            stripped = line.strip()
            if "SIP/2.0" in stripped:
                return stripped
            for method in CONFIG.sip_methods:
                if stripped.startswith(method + " ") or stripped.startswith(method + "\t"):
                    return stripped
        return None

    def dissect(self, packet_info, payload) -> dict:
        try:
            # Quick scan: check first 2048 bytes for SIP patterns
            preview = payload[:2048].decode("utf-8", errors="replace")
            if not self._scan_for_sip(preview):
                return None

            # Full decode only if SIP is likely
            if len(payload) > 2048:
                text = preview + payload[2048:].decode("utf-8", errors="replace")
            else:
                text = preview

            lines = text.split("\r\n")
            if len(lines) == 1:
                lines = text.split("\n")

            # Find the first SIP-like line (skips leading non-SIP bytes/chaff)
            first_line = self._find_sip_line(lines)
            if not first_line:
                return None

            method = "SIP Message"
            call_id = "Unknown"

            if "SIP/2.0" in first_line:
                if first_line.startswith("SIP/2.0"):
                    # Response line: SIP/2.0 200 OK
                    method = first_line.split(" ", 2)[1] if len(first_line.split(" ", 2)) > 1 else first_line
                else:
                    # Request line: INVITE sip:user@domain SIP/2.0
                    method = first_line.split(" ", 1)[0]
            else:
                method = first_line.split(" ", 1)[0]

            for line in lines:
                if line.lower().startswith("call-id:"):
                    call_id = line.split(":", 1)[1].strip()
                    break
                    
            return {
                "protocol_name": "SIP",
                "method": method,
                "call_id": call_id,
                "summary": f"SIP {method}"
            }
        except Exception:
            return None


class DiameterDissector(BaseDissector):
    """Dissector for Diameter base protocol and Credit Control Applications (RFC 4006)."""
    def matches(self, packet_info) -> bool:
        src_port, dest_port = packet_info["src_port"], packet_info["dest_port"]
        tcp_map = CONFIG.port_mappings.get("tcp", {})
        udp_map = CONFIG.port_mappings.get("udp", {})
        
        is_diameter_port = src_port == 3868 or dest_port == 3868 or \
                           tcp_map.get(src_port) == "DIAMETER" or tcp_map.get(dest_port) == "DIAMETER" or \
                           udp_map.get(src_port) == "DIAMETER" or udp_map.get(dest_port) == "DIAMETER"
        return is_diameter_port

    def dissect(self, packet_info, payload) -> dict:
        if len(payload) < 20:
            return None
            
        version = payload[0]
        if version != 0x01:
            return None
            
        msg_len = struct.unpack('>I', b'\x00' + payload[1:4])[0]
        if msg_len > len(payload) + 100:
            return None
            
        flags = payload[4]
        is_request = bool(flags & 0x80)
        command_code = struct.unpack('>I', b'\x00' + payload[5:8])[0]
        app_id = struct.unpack('>I', payload[8:12])[0]
        hbh_id = struct.unpack('>I', payload[12:16])[0].to_bytes(4, 'big').hex().upper()
        e2e_id = struct.unpack('>I', payload[16:20])[0].to_bytes(4, 'big').hex().upper()
        
        cmd_names = {
            257: ("CER", "CEA", "Capabilities-Exchange"),
            280: ("DWR", "DWA", "Device-Watchdog"),
            282: ("DPR", "DPA", "Disconnect-Peer"),
            272: ("CCR", "CCA", "Credit-Control"),
            275: ("STR", "STA", "Session-Termination"),
            274: ("ASR", "ASA", "Abort-Session")
        }
        
        cmd_info = cmd_names.get(command_code, ("REQ", "ANS", f"Cmd-{command_code}"))
        msg_type_name = cmd_info[0] if is_request else cmd_info[1]
        
        result = {
            "protocol_name": "DIAMETER",
            "command_code": command_code,
            "app_id": app_id,
            "is_request": is_request,
            "msg_type": msg_type_name,
            "hbh_id": hbh_id,
            "e2e_id": e2e_id,
            "summary": f"Diameter {msg_type_name}"
        }
        
        if command_code == 272:
            avps = self._parse_avps(payload[20:msg_len])
            
            cc_req_type_val = avps.get(416)
            cc_req_type_names = {
                1: "INITIAL_REQUEST",
                2: "UPDATE_REQUEST",
                3: "TERMINATION_REQUEST",
                4: "EVENT_REQUEST"
            }
            if cc_req_type_val is not None and len(cc_req_type_val) >= 4:
                cc_type_int = struct.unpack('>I', cc_req_type_val[:4])[0]
                result["cc_request_type"] = cc_req_type_names.get(cc_type_int, f"Type-{cc_type_int}")
                result["summary"] += f" ({result['cc_request_type']})"
            
            sub_id_data = avps.get(443)
            if sub_id_data:
                sub_id_avps = self._parse_avps(sub_id_data)
                sub_id_val = sub_id_avps.get(444)
                if sub_id_val:
                    result["subscription_id"] = sub_id_val.decode('utf-8', errors='ignore')
                    result["summary"] += f" IMSI/MSISDN={result['subscription_id']}"
                    
            cc_num_val = avps.get(415)
            if cc_num_val and len(cc_num_val) >= 4:
                result["cc_request_number"] = struct.unpack('>I', cc_num_val[:4])[0]
                
            result_code_val = avps.get(268)
            if result_code_val and len(result_code_val) >= 4:
                res_code = struct.unpack('>I', result_code_val[:4])[0]
                res_names = {
                    2001: "Success",
                    4001: "Authentication Rejected",
                    5001: "User Unknown",
                    5030: "User In Congestion"
                }
                result["result_code"] = f"{res_code} {res_names.get(res_code, '')}".strip()
                if not is_request:
                    result["summary"] += f" Result={result['result_code']}"
                    
        return result

    def _parse_avps(self, data) -> dict:
        avps = {}
        offset = 0
        while offset < len(data) - 8:
            if len(data) - offset < 8:
                break
            avp_code, avp_flags_len = struct.unpack('>II', data[offset:offset+8])
            avp_flags = avp_flags_len >> 24
            avp_len = avp_flags_len & 0x00FFFFFF
            if avp_len < 8 or offset + avp_len > len(data):
                break
                
            header_size = 8
            if avp_flags & 0x80:
                header_size = 12
                
            val = data[offset+header_size : offset+avp_len]
            avps[avp_code] = val
            offset += ((avp_len + 3) // 4) * 4
        return avps


class RanapDissector(BaseDissector):
    """Dissector for Radio Access Network Application Part (RANAP) over SCCP (SSN 142)."""
    def matches(self, packet_info) -> bool:
        return packet_info.get("ssn") == 142 or packet_info.get("called_ssn") == 142 or packet_info.get("calling_ssn") == 142

    def dissect(self, packet_info, payload) -> dict:
        if len(payload) < 2:
            return None
            
        pdu_type_val = (payload[0] >> 4) & 0x0F
        pdu_types = {
            0: "InitiatingMessage",
            1: "SuccessfulOutcome",
            2: "UnsuccessfulOutcome",
            3: "Outcome"
        }
        pdu_type = pdu_types.get(pdu_type_val, f"Type-{pdu_type_val}")
        
        proc_code_val = payload[1]
        proc_codes = {
            0: "RAB-Assignment",
            1: "Iu-Release",
            2: "RelocationPreparation",
            3: "RelocationResourceAllocation",
            4: "RelocationCommit",
            5: "RelocationExecution",
            6: "RelocationFailure",
            7: "SRNS-ContextTransfer",
            9: "RelocationPreparation",
            13: "InitialUEMessage",
            14: "InitialUEMessage",
            19: "DirectTransfer",
            20: "OverloadControl",
            21: "ErrorIndication",
            22: "SRNS-DataForwarding",
            23: "ForwardSRNS-Context",
            24: "PrivateMessage",
            25: "CN-DeactivateTrace",
            26: "Reset",
            27: "CommonID",
            28: "SecurityModeControl",
            29: "LocationReportingControl",
            30: "LocationReport",
            31: "DataVolumeReport"
        }
        
        proc_name = proc_codes.get(proc_code_val)
        if not proc_name and len(payload) > 2:
            proc_name = proc_codes.get(payload[2], f"Proc-{proc_code_val}")
        else:
            proc_name = proc_name or f"Proc-{proc_code_val}"
            
        return {
            "protocol_name": "RANAP",
            "pdu_type": pdu_type,
            "procedure_code": proc_name,
            "summary": f"RANAP {pdu_type}: {proc_name}"
        }


class GtpDissector(BaseDissector):
    """Dissector for GTP (GPRS Tunneling Protocol) Control (GTP-C) and User (GTP-U) plane."""
    def matches(self, packet_info) -> bool:
        src_port, dest_port = packet_info["src_port"], packet_info["dest_port"]
        return src_port in (2123, 2152, 3386) or dest_port in (2123, 2152, 3386)

    def dissect(self, packet_info, payload) -> dict:
        if len(payload) < 8:
            return None
            
        flags = payload[0]
        version = (flags >> 5) & 0x07
        msg_type = payload[1]
        
        teid = None
        hdr_len = 8
        
        if version == 1:
            teid = struct.unpack('>I', payload[4:8])[0].to_bytes(4, 'big').hex().upper()
            if flags & 0x07:
                hdr_len = 12
        elif version == 2:
            has_teid = bool(flags & 0x08)
            if has_teid and len(payload) >= 12:
                teid = struct.unpack('>I', payload[4:8])[0].to_bytes(4, 'big').hex().upper()
                hdr_len = 12
            else:
                hdr_len = 8
                
        msg_types = {
            1: "Echo Request",
            2: "Echo Response",
            16: "Create Session Req",
            17: "Create Session Resp",
            18: "Modify Bearer Req",
            19: "Modify Bearer Resp",
            20: "Delete Session Req",
            21: "Delete Session Resp",
            255: "GTP-U User Data"
        }
        
        msg_name = msg_types.get(msg_type, f"MsgType-{msg_type}")
        proto_plane = "GTP-U" if packet_info["dest_port"] == 2152 or packet_info["src_port"] == 2152 else "GTP-C"
        
        result = {
            "protocol_name": f"{proto_plane}v{version}",
            "version": version,
            "msg_type": msg_name,
            "teid": teid,
            "summary": f"{proto_plane} {msg_name}" + (f" TEID=0x{teid}" if teid else "")
        }
        
        if msg_type == 255 and len(payload) > hdr_len:
            inner_payload = payload[hdr_len:]
            if len(inner_payload) >= 20 and (inner_payload[0] & 0xF0) == 0x40:
                inner_ihl = (inner_payload[0] & 0x0F) * 4
                inner_protocol = inner_payload[9]
                inner_src_ip = ".".join(map(str, inner_payload[12:16]))
                inner_dest_ip = ".".join(map(str, inner_payload[16:20]))
                
                inner_transport = inner_payload[inner_ihl:]
                if len(inner_transport) >= 8:
                    inner_src_port, inner_dest_port = struct.unpack('>HH', inner_transport[0:4])
                    inner_payload_data = inner_transport[8:]
                    
                    inner_packet_info = {
                        "src_ip": inner_src_ip,
                        "dest_ip": inner_dest_ip,
                        "src_port": inner_src_port,
                        "dest_port": inner_dest_port,
                        "protocol": inner_protocol
                    }
                    
                    encap_summary = None
                    for dissector in DISSECTOR_REGISTRY:
                        if isinstance(dissector, GtpDissector):
                            continue
                        if dissector.matches(inner_packet_info):
                            encap_res = dissector.dissect(inner_packet_info, inner_payload_data)
                            if encap_res:
                                encap_summary = f"{encap_res.get('protocol_name')} [{encap_res.get('summary')}]"
                                break
                                
                    if encap_summary:
                        result["summary"] += f" Tunneling: {encap_summary}"
                        result["encapsulated_traffic"] = encap_summary
                    else:
                        proto_name = "TCP" if inner_protocol == 6 else "UDP" if inner_protocol == 17 else f"IP-{inner_protocol}"
                        result["summary"] += f" Tunneling: {proto_name} {inner_src_ip}:{inner_src_port} ➔ {inner_dest_ip}:{inner_dest_port}"
                        
        return result


class HttpDissector(BaseDissector):
    """Dissector for HTTP/1.x, HTTP/2 RESTful APIs, and 5G SA Service-Based Architecture (SBA).
    
    Content-based detection: matches any TCP packet and verifies via
    payload inspection.
    """
    def matches(self, packet_info) -> bool:
        return packet_info["protocol"] == 6

    def dissect(self, packet_info, payload) -> dict:
        try:
            text = payload.decode("utf-8", errors="ignore").strip()
            if not text:
                return None
                
            lines = text.split("\r\n")
            first_line = lines[0]
            
            is_http = False
            is_request = False
            method = "HTTP Message"
            path = ""
            status = ""
            
            if "HTTP/1." in first_line or "HTTP/2" in first_line:
                is_http = True
                if first_line.startswith("HTTP/"):
                    status = first_line.split(" ", 1)[1]
                else:
                    is_request = True
                    parts = first_line.split(" ")
                    if len(parts) >= 2:
                        method = parts[0]
                        path = parts[1]
            else:
                if text.startswith("{") and text.endswith("}"):
                    is_http = True
                    method = "JSON Payload"
                    path = "5G SA Data Frame"
                    
            if not is_http:
                return None
                
            result = {
                "protocol_name": "HTTP",
                "is_request": is_request,
                "summary": f"HTTP {first_line}"
            }
            
            sba_services = {
                "/nsmf-": ("SMF", "AMF", "N11"),
                "/nausf-": ("AUSF", "AMF", "N12"),
                "/nudm-sdm": ("UDM", "AMF", "N8"),
                "/nudm-uecm": ("UDM", "AMF", "N8"),
                "/npcf-smpolicycontrol": ("PCF", "SMF", "N7"),
                "/npcf-am-policy-control": ("PCF", "AMF", "N15"),
                "/nnssf-": ("NSSF", "AMF", "N22"),
                "/nudm-ueau": ("UDM", "AUSF", "N13"),
                "/nudr-": ("UDR", "UDM", "N35")
            }
            
            is_5g_sba = False
            nf_dest = "5G NF"
            nf_src = "5G NF"
            n_interface = "SBA"
            
            for prefix, (dest, src, n_int) in sba_services.items():
                if prefix in path or prefix in text:
                    is_5g_sba = True
                    nf_dest = dest
                    nf_src = src
                    n_interface = n_int
                    break
                    
            if is_5g_sba:
                result["protocol_name"] = "5G SA SBA"
                result["n_interface"] = n_interface
                result["nf_src"] = nf_src
                result["nf_dest"] = nf_dest
                
                action_name = "Service Request"
                if is_request:
                    if "pdusession" in path:
                        action_name = "Create SM Context" if "create" in path or method == "POST" else "Update SM Context"
                    elif "auth" in path:
                        action_name = "Auth Request"
                    elif "sdm" in path:
                        action_name = "Get Subscription Data"
                    elif "nsselection" in path:
                        action_name = "Slice Selection"
                    result["summary"] = f"5G {n_interface}: {action_name} ({nf_src} ➔ {nf_dest})"
                else:
                    result["summary"] = f"5G {n_interface}: Response ({status})"
                    
                json_start = text.find("{")
                if json_start != -1:
                    json_str = text[json_start:]
                    try:
                        import json as std_json
                        payload_data = std_json.loads(json_str)
                        result["json_payload"] = payload_data
                        
                        ids = []
                        for key in ("supi", "suci", "imsi", "gpsi", "pduSessionId", "dnn", "sNssai"):
                            val = None
                            for k, v in payload_data.items():
                                if k.lower() == key.lower():
                                    val = v
                                    break
                            if val:
                                result[key] = str(val)
                                ids.append(f"{key}={val}")
                        if ids:
                            result["summary"] += " [" + ", ".join(ids) + "]"
                    except Exception:
                        pass
            else:
                if is_request:
                    result["summary"] = f"HTTP {method} {path}"
                else:
                    result["summary"] = f"HTTP Response: {status}"
                    
            return result
        except Exception:
            return None


class GenericIpFlowDissector(BaseDissector):
    """Fallback conversation flow dissector for generic TCP/UDP flows."""
    def matches(self, packet_info) -> bool:
        return packet_info["protocol"] in (6, 17)
        
    def dissect(self, packet_info, payload) -> dict:
        proto_name = "TCP" if packet_info["protocol"] == 6 else "UDP"
        
        src_port, dest_port = packet_info["src_port"], packet_info["dest_port"]
        tcp_map = CONFIG.port_mappings.get("tcp", {})
        udp_map = CONFIG.port_mappings.get("udp", {})
        
        svc = tcp_map.get(src_port) or tcp_map.get(dest_port) if proto_name == "TCP" else udp_map.get(src_port) or udp_map.get(dest_port)
        
        tcp_flags_desc = ""
        if packet_info["protocol"] == 6 and packet_info.get("tcp_flags") is not None:
            flags = packet_info["tcp_flags"]
            flag_parts = []
            if flags & 0x02: flag_parts.append("SYN")
            if flags & 0x10: flag_parts.append("ACK")
            if flags & 0x01: flag_parts.append("FIN")
            if flags & 0x04: flag_parts.append("RST")
            if flags & 0x08: flag_parts.append("PSH")
            
            if flag_parts:
                tcp_flags_desc = f" [{', '.join(flag_parts)}]"
                
        if svc:
            summary = f"{svc} Conversation{tcp_flags_desc}"
        else:
            summary = f"{proto_name} Port {src_port} ➔ {dest_port}{tcp_flags_desc}"
            
        return {
            "protocol_name": svc or proto_name,
            "summary": summary
        }


class RtpDissector(BaseDissector):
    """Dissector for Real-time Transport Protocol (RTP) media streams."""
    def matches(self, packet_info) -> bool:
        # RTP typically runs over UDP
        if packet_info["protocol"] != 17:
            return False
        # RTP ports are usually even and high (e.g., >= 1024)
        src_port, dest_port = packet_info["src_port"], packet_info["dest_port"]
        return src_port >= 1024 and dest_port >= 1024
        
    def dissect(self, packet_info, payload) -> dict:
        if len(payload) < 12:
            return None
            
        version = (payload[0] >> 6) & 0x03
        if version != 2:
            return None
            
        payload_type = payload[1] & 0x7F
        seq_num = struct.unpack('>H', payload[2:4])[0]
        timestamp = struct.unpack('>I', payload[4:8])[0]
        ssrc = struct.unpack('>I', payload[8:12])[0].to_bytes(4, 'big').hex().upper()
        
        # Standard RTP payload types
        rtp_types = {
            0: "PCMU", 3: "GSM", 4: "G723", 8: "PCMA", 9: "G722", 
            18: "G729", 96: "H263", 97: "H264", 98: "H265"
        }
        pt_name = rtp_types.get(payload_type, f"PT-{payload_type}")
        
        return {
            "protocol_name": "RTP",
            "payload_type": pt_name,
            "seq_num": seq_num,
            "timestamp": timestamp,
            "ssrc": ssrc,
            "summary": f"RTP Media ({pt_name}) Seq={seq_num}"
        }


# Global Dissector Registry
DISSECTOR_REGISTRY = [
    SigtranDissector(),
    RanapDissector(),
    GtpDissector(),
    DiameterDissector(),
    SipDissector(),
    HttpDissector(),
    RtpDissector(),
    GenericIpFlowDissector()
]

class ParserEngine:
    def __init__(self):
        self.packets = []
        self.diagnostics = {
            "link_type": None,
            "total_packets": 0,
            "skipped_non_ethernet": 0,
            "skipped_non_ip": 0,
            "skipped_no_payload": 0,
            "skipped_too_short": 0,
            "parsed_ok": 0,
        }

    def parse_file(self, filepath):
        self.packets = []
        self.diagnostics = {k: 0 for k in self.diagnostics}
        self.diagnostics["link_type"] = None
        if not os.path.exists(filepath):
            print(f"Error: File not found: {filepath}")
            return []
            
        with open(filepath, 'rb') as f:
            magic_bytes = f.read(4)
            if len(magic_bytes) < 4:
                return []
                
        if magic_bytes == b'\x0a\x0d\x0d\x0a':
            return self.parse_pcapng(filepath)
        else:
            return self.parse_pcap(filepath)

    def parse_pcap(self, filepath):
        with open(filepath, 'rb') as f:
            global_header = f.read(24)
            if len(global_header) < 24:
                return []
                
            magic, _, _, _, _, _, self.diagnostics["link_type"] = struct.unpack('IHHIIII', global_header)
            endian = '<' if magic in (0xa1b2c3d4, 0xa1b23c4d) else '>'
            network = self.diagnostics["link_type"]
            
            packet_num = 0
            while True:
                header_bytes = f.read(16)
                if not header_bytes or len(header_bytes) < 16:
                    break
                    
                ts_sec, ts_usec, incl_len, orig_len = struct.unpack(endian + 'IIII', header_bytes)
                packet_data = f.read(incl_len)
                if len(packet_data) < incl_len:
                    break
                    
                packet_num += 1
                timestamp = ts_sec + (ts_usec / 1000000.0)
                
                self.process_raw_packet(packet_num, timestamp, network, packet_data, self.packets)
                
            return self.packets

    def parse_pcapng(self, filepath):
        endian = '<'
        interfaces = []
        packet_num = 0
        
        with open(filepath, 'rb') as f:
            while True:
                block_hdr = f.read(8)
                if len(block_hdr) < 8:
                    break
                    
                block_type, block_len = struct.unpack(endian + 'II', block_hdr)
                
                if block_type == 0x0A0D0D0A:
                    bom = f.read(4)
                    if bom == b'\x1a\x2b\x3c\x4d':
                        endian = '>'
                    elif bom == b'\x4d\x3c\x2b\x1a':
                        endian = '<'
                    
                    block_len = struct.unpack(endian + 'I', block_hdr[4:8])[0]
                    f.read(block_len - 12)
                    continue
                    
                block_len = struct.unpack(endian + 'I', block_hdr[4:8])[0]
                
                block_body = f.read(block_len - 8)
                if len(block_body) < block_len - 8:
                    break
                    
                content = block_body[:-4]
                
                if block_type == 0x00000001:
                    if len(content) >= 8:
                        link_type, reserved = struct.unpack(endian + 'HH', content[0:4])
                        ts_resol = 6
                        offset = 8
                        while offset < len(content) - 4:
                            opt_code, opt_len = struct.unpack(endian + 'HH', content[offset:offset+4])
                            if opt_code == 0:
                                break
                            if opt_code == 9 and opt_len == 1:
                                ts_resol = content[offset+4]
                            offset += 4 + ((opt_len + 3) // 4) * 4
                        interfaces.append((link_type, ts_resol))
                        if self.diagnostics["link_type"] is None:
                            self.diagnostics["link_type"] = link_type
                        
                elif block_type == 0x00000006:
                    if len(content) >= 20:
                        interface_id, ts_high, ts_low, incl_len, orig_len = struct.unpack(endian + 'IIIII', content[0:20])
                        packet_data = content[20:20+incl_len]
                        
                        packet_num += 1
                        
                        link_type = 1
                        ts_resol = 6
                        if interface_id < len(interfaces):
                            link_type, ts_resol = interfaces[interface_id]
                            
                        timestamp_raw = (ts_high << 32) | ts_low
                        if ts_resol & 0x80:
                            factor = 1 << (ts_resol & 0x7F)
                            timestamp = timestamp_raw / factor
                        else:
                            factor = 10 ** ts_resol
                            timestamp = timestamp_raw / factor
                            
                        self.process_raw_packet(packet_num, timestamp, link_type, packet_data, self.packets)
                        
                elif block_type == 0x00000003:
                    if len(content) >= 4:
                        orig_len = struct.unpack(endian + 'I', content[0:4])[0]
                        incl_len = block_len - 16
                        packet_data = content[4:4+incl_len]
                        
                        packet_num += 1
                        
                        link_type = 1
                        if len(interfaces) > 0:
                            link_type, _ = interfaces[0]
                            
                        timestamp = 0.0
                        self.process_raw_packet(packet_num, timestamp, link_type, packet_data, self.packets)
                        
        return self.packets

    def _extract_l3_data(self, network, packet_data):
        """Extract L3 (IP) data and L3 protocol from a raw packet based on link type.
        Returns (l3_data, l3_protocol) or (None, None) on failure.
        """
        self.diagnostics["total_packets"] += 1

        # --- Link Type 0: NULL / Loopback ---
        if network == 0:
            if len(packet_data) < 4:
                self.diagnostics["skipped_too_short"] += 1
                return None, None
            af = struct.unpack('>I', packet_data[:4])[0]
            # BSD loopback: AF_INET=2, AF_INET6=24, or sometimes host byte order
            if af in (2, 0x02000000):
                return packet_data[4:], 0x0800
            elif af in (24, 0x18000000, 28, 30):
                return packet_data[4:], 0x86DD
            return packet_data[4:], 0x0800

        # --- Link Type 1: Ethernet ---
        elif network == 1:
            if len(packet_data) < 14:
                self.diagnostics["skipped_too_short"] += 1
                return None, None
            eth_type = struct.unpack('>H', packet_data[12:14])[0]
            # Skip VLAN tags (802.1Q, 802.1ad)
            offset = 14
            while eth_type == 0x8100 or eth_type == 0x88A8 or eth_type == 0x9100:
                if len(packet_data) < offset + 4:
                    return None, None
                eth_type = struct.unpack('>H', packet_data[offset + 2:offset + 4])[0]
                offset += 4
            return packet_data[offset:], eth_type

        # --- Link Type 101: RAW IP ---
        elif network == 101:
            return packet_data, 0x0800

        # --- Link Type 113: Linux SLL (Linux Cooked Capture) ---
        elif network == 113:
            if len(packet_data) < 16:
                self.diagnostics["skipped_too_short"] += 1
                return None, None
            # SLL header: 2 bytes pkttype, 2 bytes ARPHRD, 2 bytes LL addr len,
            # 8 bytes LL addr, 2 bytes protocol type (network byte order)
            eth_type = struct.unpack('>H', packet_data[14:16])[0]
            if eth_type <= 1500:
                eth_type = 0x0800
            return packet_data[16:], eth_type

        # --- Link Type 12: IP-over-FC, 228: IPMB --- try raw IP ---
        elif network in (12, 228):
            if len(packet_data) >= 1 and packet_data[0] & 0xF0 == 0x40:
                return packet_data, 0x0800
            self.diagnostics["skipped_non_ethernet"] += 1
            return None, None

        else:
            self.diagnostics["skipped_non_ethernet"] += 1
            return None, None

    def process_raw_packet(self, packet_num, timestamp, network, packet_data, packets):
        l3_data, l3_protocol = self._extract_l3_data(network, packet_data)
        if l3_data is None:
            return

        # Only process IPv4 (0x0800) for now
        if l3_protocol != 0x0800:
            self.diagnostics["skipped_non_ip"] += 1
            return

        ip_data = l3_data
        if len(ip_data) < 20:
            self.diagnostics["skipped_too_short"] += 1
            return
            
        ihl = (ip_data[0] & 0x0F) * 4
        protocol = ip_data[9]
        src_ip = ".".join(map(str, ip_data[12:16]))
        dest_ip = ".".join(map(str, ip_data[16:20]))
        
        transport_data = ip_data[ihl:]
        if len(transport_data) < 8:
            self.diagnostics["skipped_too_short"] += 1
            return
            
        src_port = 0
        dest_port = 0
        ppid = None
        payload = None
        tcp_flags = None
        
        if protocol == 132:
            if len(transport_data) < 12:
                self.diagnostics["skipped_too_short"] += 1
                return
            src_port, dest_port = struct.unpack('>HH', transport_data[0:4])
            
            offset = 12
            while offset < len(transport_data):
                if len(transport_data) - offset < 4:
                    break
                chunk_type, chunk_flags, chunk_len = struct.unpack('>BBH', transport_data[offset:offset+4])
                if chunk_type == 0:
                    chunk_val = transport_data[offset+4 : offset+chunk_len]
                    if len(chunk_val) >= 12:
                        _, _, _, ppid = struct.unpack('>IHHI', chunk_val[0:12])
                        payload = chunk_val[12:]
                        break
                offset += ((chunk_len + 3) // 4) * 4
                
        elif protocol == 6:
            src_port, dest_port = struct.unpack('>HH', transport_data[0:4])
            if len(transport_data) >= 14:
                tcp_flags = transport_data[13]
            if len(transport_data) >= 12:
                data_offset = (transport_data[12] >> 4) * 4
                payload = transport_data[data_offset:]
                
        elif protocol == 17:
            src_port, dest_port = struct.unpack('>HH', transport_data[0:4])
            payload = transport_data[8:]
            
        if payload is None:
            self.diagnostics["skipped_no_payload"] += 1
            return
            
        packet_info = {
            "num": packet_num,
            "time": timestamp,
            "src_ip": src_ip,
            "dest_ip": dest_ip,
            "src_port": src_port,
            "dest_port": dest_port,
            "protocol": protocol,
            "ppid": ppid,
            "tcp_flags": tcp_flags
        }
        
        if protocol in (6, 17) and src_port not in (5060, 5061) and dest_port not in (5060, 5061):
            tcp_map = CONFIG.port_mappings.get("tcp", {})
            udp_map = CONFIG.port_mappings.get("udp", {})
            proto_key = "tcp" if protocol == 6 else "udp"
            mappings_key = tcp_map if protocol == 6 else udp_map
            
            if src_port not in mappings_key and dest_port not in mappings_key:
                try:
                    text_peek = payload[:2048].decode("utf-8", errors="replace")
                    is_sip = "SIP/2.0" in text_peek or any(
                        (text_peek.startswith(m + " ") or
                         f"\r\n{m} " in text_peek or
                         f"\n{m} " in text_peek)
                        for m in CONFIG.sip_methods
                    )
                    if is_sip:
                        port_to_learn = src_port if src_port > 1024 else dest_port
                        CONFIG.learn_port(proto_key, port_to_learn, "SIP")
                except Exception:
                    pass
                    
        if protocol == 6 and src_port not in (80, 8080, 443) and dest_port not in (80, 8080, 443):
            tcp_map = CONFIG.port_mappings.get("tcp", {})
            if src_port not in tcp_map and dest_port not in tcp_map:
                try:
                    text_peek = payload[:2048].decode("utf-8", errors="replace")
                    is_http = (text_peek.startswith("GET ") or text_peek.startswith("POST ") or
                               text_peek.startswith("PUT ") or "HTTP/1." in text_peek or "HTTP/2" in text_peek)
                    if is_http:
                        port_to_learn = src_port if src_port > 1024 else dest_port
                        CONFIG.learn_port("tcp", port_to_learn, "HTTP")
                except Exception:
                    pass
                    
        if protocol == 132 and ppid is not None and ppid not in CONFIG.ppids:
            if len(payload) >= 4 and payload[0] == 0x01:
                has_tcap = False
                for tcap_tag in CONFIG.tcap_msg_types.keys():
                    if bytes([tcap_tag]) in payload:
                        has_tcap = True
                        break
                if has_tcap:
                    msg_class = payload[1]
                    learned_name = "M3UA" if msg_class in (1, 2, 3, 4) else "M2UA" if msg_class in (0, 11) else "SIGTRAN"
                    CONFIG.learn_ppid(ppid, learned_name)
                    
        for dissector in DISSECTOR_REGISTRY:
            if dissector.matches(packet_info):
                res = dissector.dissect(packet_info, payload)
                if res:
                    packet_info["dissection"] = res
                    packets.append(packet_info)
                    self.diagnostics["parsed_ok"] += 1
                    break


def generate_report(packets, filepath, diagnostics=None):
    if not packets:
        msg = "# Signaling Analysis Report\n\n## ❌ No Parsed Signaling Packets\n\nThe trace file did not contain any recognized signaling packets."
        if diagnostics:
            lt = diagnostics.get("link_type")
            lt_names = {0: "NULL/Loopback", 1: "Ethernet", 101: "RAW IP", 113: "Linux SLL (cooked)"}
            lt_name = lt_names.get(lt, f"Link Type {lt}" if lt is not None else "unknown")
            msg += f"\n\n### Pcap Diagnostics\n"
            msg += f"- **Link Layer**: `{lt_name}`\n"
            msg += f"- **Total packets in file**: `{diagnostics.get('total_packets', '?')}`\n"
            msg += f"- **Unsupported link type**: `{diagnostics.get('skipped_non_ethernet', 0)}`\n"
            msg += f"- **Non-IPv4 (IPv6, ARP, etc.)**: `{diagnostics.get('skipped_non_ip', 0)}`\n"
            msg += f"- **Too short / malformed**: `{diagnostics.get('skipped_too_short', 0)}`\n"
            msg += f"- **No payload (e.g. bare TCP SYN)**: `{diagnostics.get('skipped_no_payload', 0)}`\n"
            msg += f"- **Successfully dissected**: `{diagnostics.get('parsed_ok', 0)}`\n"
            if lt is not None and lt != 1:
                msg += f"\n> ⚠️ Link type `{lt}` is not Ethernet. The parser was recently updated to support more link types — try running again."
            if diagnostics.get("skipped_non_ip", 0) > 0:
                msg += f"\n> ℹ️ `{diagnostics.get('skipped_non_ip')}` packets are non-IPv4 (IPv6, ARP, etc.). IPv6 support is not yet implemented."
        return msg
        
    point_code_names = {}
    
    # Try mapping point codes based on SS7 traffic
    for p in packets:
        if p.get("dissection", {}).get("protocol_name") == "SIGTRAN":
            diss = p["dissection"]
            opc, dpc = diss["src_pc"], diss["dest_pc"]
            if opc is not None and dpc is not None:
                if "InitialDP" in diss["operations"]:
                    point_code_names[opc] = "gsmSSF"
                    point_code_names[dpc] = "gsmSCF"
                    
    # Generate generic names for point codes or IPs
    for p in packets:
        if p.get("dissection", {}).get("protocol_name") == "SIGTRAN":
            diss = p["dissection"]
            opc, dpc = diss["src_pc"], diss["dest_pc"]
            if opc is not None and opc not in point_code_names:
                point_code_names[opc] = f"PC-{opc}"
            if dpc is not None and dpc not in point_code_names:
                point_code_names[dpc] = f"PC-{dpc}"
                
    report = []
    report.append(f"# Signaling Call Flow Analysis Report")
    report.append(f"Generated at: **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**")
    report.append(f"Analyzed File: `{os.path.basename(filepath)}`  ")
    report.append(f"Parsed Signaling Packets: **{len(packets)}**\n")
    
    report.append("## 📊 Executive Signaling Summary")
    report.append("| Packet | Time (Relative) | Originating Node | Destination Node | Protocol | Message Type / Event |")
    report.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    
    base_time = packets[0]["time"]
    for p in packets:
        rel_time = f"{p['time'] - base_time:.3f}s"
        diss = p.get("dissection", {})
        proto = diss.get("protocol_name", "IP")
        
        if proto == "SIGTRAN":
            opc_name = point_code_names.get(diss['src_pc'], f"PC-{diss['src_pc']}")
            src = f"{opc_name} ({diss['src_pc']})"
            dpc_name = point_code_names.get(diss['dest_pc'], f"PC-{diss['dest_pc']}")
            dest = f"{dpc_name} ({diss['dest_pc']})"
            
            ops = []
            for c in diss["components"]:
                ev_det = f" ({c['event_type']})" if "event_type" in c else ""
                ops.append(f"`{c['name']}`{ev_det}")
            msg = f"**TCAP {diss['tcap_msg']}**: " + (", ".join(ops) if ops else "Signaling")
        else:
            src = f"{p['src_ip']}:{p['src_port']}"
            dest = f"{p['dest_ip']}:{p['dest_port']}"
            msg = diss.get("summary", "Conversation Packet")
            
        report.append(f"| #{p['num']} | {rel_time} | {src} | {dest} | **{proto}** | {msg} |")
        
    report.append("\n")
    report.append("## 🔄 Call Flow Diagram (Sequence Flow)")
    report.append("```mermaid")
    report.append("%%{init: {")
    report.append("  'themeVariables': {")
    report.append("    'actorLineColor': '#a5b4fc'")
    report.append("  },")
    report.append("  'themeCSS': '.actor-line { stroke: #a5b4fc !important; stroke-width: 2px !important; }'")
    report.append("}}%%")
    report.append("sequenceDiagram")
    report.append("    autonumber")
    
    # Track unique participants
    participants = set()
    for p in packets:
        diss = p.get("dissection", {})
        if diss.get("protocol_name") == "SIGTRAN":
            participants.add(point_code_names.get(diss["src_pc"]))
            participants.add(point_code_names.get(diss["dest_pc"]))
        else:
            participants.add(p["src_ip"])
            participants.add(p["dest_ip"])
            
    for part in sorted(list(participants)):
        report.append(f"    participant {part}")
        
    report.append("")
    
    for p in packets:
        diss = p.get("dissection", {})
        proto = diss.get("protocol_name", "IP")
        
        if proto == "SIGTRAN":
            src = point_code_names.get(diss["src_pc"])
            dest = point_code_names.get(diss["dest_pc"])
            ops = []
            for c in diss["components"]:
                ev_det = f" ({c['event_type']})" if "event_type" in c else ""
                ops.append(f"{c['name']}{ev_det}")
            msg = f"TCAP {diss['tcap_msg']}" + (f" [{', '.join(ops)}]" if ops else "")
        else:
            src = p["src_ip"]
            dest = p["dest_ip"]
            msg = diss.get("summary", f"{proto} Packet")
            
        report.append(f"    {src}->>{dest}: {msg}")
        
        # Add helpers notes
        if proto == "SIGTRAN":
            for c in diss["components"]:
                if c["name"] == "InitialDP":
                    report.append(f"    Note over {dest}: Service triggered! (InitialDP)")
                elif c["name"] == "ReleaseCall":
                    report.append(f"    Note over {dest}: Call Terminated! (ReleaseCall)")
                    
    report.append("```\n")
    
    report.append("## 🔍 Deep Protocol Packet Breakdown")
    for p in packets:
        rel_time = f"{p['time'] - base_time:.3f}s"
        diss = p.get("dissection", {})
        proto = diss.get("protocol_name", "IP")
        
        report.append(f"### Packet #{p['num']} - Timestamp `{rel_time}`")
        report.append(f"- **Network Layer**: IP: `{p['src_ip']}` ➔ `{p['dest_ip']}`")
        report.append(f"- **Transport Layer**: Port: `{p['src_port']}` ➔ `{p['dest_port']}` (Proto ID: `{p['protocol']}`)")
        
        if proto == "SIGTRAN":
            report.append(f"- **Signaling Layer**: OPC Point Code: `{diss['src_pc']}` (`{point_code_names.get(diss['src_pc'])}`) ➔ DPC Point Code: `{diss['dest_pc']}` (`{point_code_names.get(diss['dest_pc'])}`) [M2UA/M3UA]")
            report.append(f"- **TCAP Layer**: **{diss['tcap_msg']}**")
            if diss["otid"]:
                report.append(f"  - Originating Transaction ID: `{diss['otid']}`")
            if diss["dtid"]:
                report.append(f"  - Destination Transaction ID: `{diss['dtid']}`")
            if diss["components"]:
                report.append("  - **Component Portion**:")
                for c in diss["components"]:
                    report.append(f"    - Type: `{c['type']}` (ID: `{c['id']}`) | Operation: **`{c['name']}`** (Code: `{c['op']}`)")
                    if "event_type" in c:
                        report.append(f"      - Event Type: `{c['event_type']}`")
        else:
            report.append(f"- **Application Layer**: **{proto} Protocol**")
            for k, v in diss.items():
                if k not in ("protocol_name", "summary"):
                    report.append(f"  - {k.capitalize().replace('_', ' ')}: `{v}`")
                    
        report.append("---")
        
    return "\n".join(report)


def generate_html_report(packets, filepath, out_file):
    point_code_names = {}
    for p in packets:
        if p.get("dissection", {}).get("protocol_name") == "SIGTRAN":
            diss = p["dissection"]
            opc, dpc = diss["src_pc"], diss["dest_pc"]
            if opc is not None and dpc is not None:
                if "InitialDP" in diss["operations"]:
                    point_code_names[opc] = "gsmSSF"
                    point_code_names[dpc] = "gsmSCF"
                    
    for p in packets:
        if p.get("dissection", {}).get("protocol_name") == "SIGTRAN":
            diss = p["dissection"]
            opc, dpc = diss["src_pc"], diss["dest_pc"]
            if opc is not None and opc not in point_code_names:
                point_code_names[opc] = f"PC-{opc}"
            if dpc is not None and dpc not in point_code_names:
                point_code_names[dpc] = f"PC-{dpc}"

    participants = set()
    for p in packets:
        diss = p.get("dissection", {})
        if diss.get("protocol_name") == "SIGTRAN":
            participants.add(point_code_names.get(diss["src_pc"]))
            participants.add(point_code_names.get(diss["dest_pc"]))
        else:
            participants.add(p["src_ip"])
            participants.add(p["dest_ip"])
    participants_list = sorted(list(participants))

    formatted_packets = []
    base_time = packets[0]["time"] if packets else 0
    for p in packets:
        diss = p.get("dissection", {})
        proto = diss.get("protocol_name", "IP")
        
        if proto == "SIGTRAN":
            src = point_code_names.get(diss["src_pc"])
            dest = point_code_names.get(diss["dest_pc"])
            ops = []
            for c in diss["components"]:
                ev_det = f" ({c['event_type']})" if "event_type" in c else ""
                ops.append(f"{c['name']}{ev_det}")
            summary = f"TCAP {diss['tcap_msg']}" + (f" [{', '.join(ops)}]" if ops else "")
        else:
            src = p["src_ip"]
            dest = p["dest_ip"]
            summary = diss.get("summary", f"{proto} Conversation")

        formatted_packets.append({
            "num": p["num"],
            "rel_time": f"{p['time'] - base_time:.3f}s",
            "src": src,
            "dest": dest,
            "proto": proto,
            "summary": summary,
            "full_diss": diss,
            "raw_packet": {
                "src_ip": p["src_ip"],
                "dest_ip": p["dest_ip"],
                "src_port": p["src_port"],
                "dest_port": p["dest_port"],
                "protocol": p["protocol"],
                "ppid": p["ppid"]
            }
        })

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=initial-scale=1.0">
    <title>Call Flow Signaling Analyzer - {os.path.basename(filepath)}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-main: #0f172a;
            --bg-panel: #1e293b;
            --bg-hover: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.15);
            --border: #334155;
            --success: #10b981;
            --warning: #f59e0b;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}

        header {{
            background: linear-gradient(135deg, var(--bg-panel) 0%, #0f172a 100%);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(to right, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .file-info {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}

        .main-container {{
            flex: 1;
            display: grid;
            grid-template-columns: 3fr 2fr;
            overflow: hidden;
        }}

        .flow-container {{
            padding: 2rem;
            overflow-y: auto;
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            align-items: center;
            background-color: #0b0f19;
        }}

        .inspector-container {{
            background-color: var(--bg-panel);
            overflow-y: auto;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        .participants-header {{
            display: flex;
            position: sticky;
            top: 0;
            z-index: 10;
            width: 100%;
            max-width: 800px;
            justify-content: space-around;
            padding-bottom: 1.5rem;
            background-color: #0b0f19;
        }}

        .participant-card {{
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(8px);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            min-width: 120px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: border-color 0.3s;
        }}

        .participant-card:hover {{
            border-color: var(--accent);
        }}

        .flow-diagram {{
            width: 100%;
            max-width: 800px;
            position: relative;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            padding-top: 1rem;
        }}

        .lifelines-overlay {{
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            right: 0;
            display: flex;
            justify-content: space-around;
            pointer-events: none;
            z-index: 1;
        }}

        .lifeline {{
            width: 1px;
            border-left: 2px dashed rgba(255, 255, 255, 0.65);
            height: 100%;
        }}

        .msg-row {{
            display: flex;
            position: relative;
            z-index: 2;
            height: 60px;
            align-items: center;
            cursor: pointer;
            transition: transform 0.2s;
        }}

        .msg-row:hover {{
            transform: scale(1.01);
        }}

        .msg-arrow-container {{
            position: absolute;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .msg-label {{
            font-size: 0.8rem;
            font-weight: 500;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            text-align: center;
            background: rgba(15, 23, 42, 0.8);
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid transparent;
            transition: all 0.3s;
        }}

        .msg-row:hover .msg-label, .msg-row.active .msg-label {{
            border-color: var(--accent);
            color: #818cf8;
            box-shadow: 0 0 8px var(--accent-glow);
        }}

        .msg-line {{
            height: 2px;
            background-color: var(--text-muted);
            position: relative;
            width: 100%;
        }}

        .msg-row:hover .msg-line, .msg-row.active .msg-line {{
            background-color: var(--accent);
            box-shadow: 0 0 6px var(--accent);
        }}

        .msg-arrow-head {{
            position: absolute;
            top: -4px;
            width: 0;
            height: 0;
            border-top: 5px solid transparent;
            border-bottom: 5px solid transparent;
        }}

        .msg-arrow-right {{
            right: 0;
            border-left: 8px solid var(--text-muted);
        }}

        .msg-row:hover .msg-arrow-right, .msg-row.active .msg-arrow-right {{
            border-left-color: var(--accent);
        }}

        .msg-arrow-left {{
            left: 0;
            border-right: 8px solid var(--text-muted);
        }}

        .msg-row:hover .msg-arrow-left, .msg-row.active .msg-arrow-left {{
            border-right-color: var(--accent);
        }}

        .msg-timestamp {{
            position: absolute;
            left: 10px;
            font-size: 0.75rem;
            color: var(--text-muted);
            background: var(--bg-main);
            padding: 2px 6px;
            border-radius: 4px;
        }}

        .section-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            font-weight: 600;
            color: #f8fafc;
            border-left: 3px solid var(--accent);
            padding-left: 8px;
            margin-bottom: 1rem;
        }}

        .packet-card {{
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
        }}

        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.9rem;
        }}

        .info-row:last-child {{
            border-bottom: none;
        }}

        .info-label {{
            color: var(--text-muted);
            font-weight: 500;
        }}

        .info-value {{
            font-weight: 600;
        }}

        .tree-node {{
            margin-left: 1rem;
            border-left: 1px solid var(--border);
            padding-left: 0.75rem;
            margin-top: 0.5rem;
        }}

        .tree-header {{
            font-weight: 600;
            color: #818cf8;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.9rem;
            padding: 4px 0;
        }}

        .tree-body {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding: 6px 0;
        }}

        .badge {{
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .badge-sigtran {{
            background-color: rgba(99, 102, 241, 0.2);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.4);
        }}

        .badge-sip {{
            background-color: rgba(16, 185, 129, 0.2);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }}

        .placeholder-text {{
            color: var(--text-muted);
            text-align: center;
            padding: 3rem;
            font-size: 0.95rem;
            font-style: italic;
        }}
    </style>
</head>
<body>

    <header>
        <div>
            <h1>Call Flow Signaling Analyzer</h1>
            <div class="file-info">Analyzed File: <strong>{os.path.basename(filepath)}</strong></div>
        </div>
        <div class="file-info">Total Parsed Packets: <strong>{len(packets)}</strong></div>
    </header>

    <div class="main-container">
        <!-- Interactive Sequence Flow Container -->
        <div class="flow-container">
            <div class="participants-header" id="participants-list">
                <!-- Dynamically filled -->
            </div>

            <div class="flow-diagram">
                <div class="lifelines-overlay" id="lifelines-container">
                    <!-- Dynamically filled -->
                </div>
                <div id="messages-container">
                    <!-- Dynamically filled -->
                </div>
            </div>
        </div>

        <!-- Packet Details Inspector -->
        <div class="inspector-container">
            <div>
                <h3 class="section-title">Packet Inspector</h3>
                <div id="inspector-placeholder" class="placeholder-text">
                    Select a packet in the call flow diagram to inspect detailed layers.
                </div>
                <div id="inspector-content" style="display: none;">
                    <!-- Packet general meta -->
                    <div class="packet-card" style="margin-bottom: 1.5rem;">
                        <div class="info-row">
                            <span class="info-label">Packet ID</span>
                            <span class="info-value" id="meta-packet-id">#1</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Timestamp</span>
                            <span class="info-value" id="meta-timestamp">0.000s</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Protocol</span>
                            <span class="info-value" id="meta-protocol"><span class="badge badge-sigtran">SIGTRAN</span></span>
                        </div>
                    </div>

                    <!-- Decoded layers tree -->
                    <h3 class="section-title">Protocol Decoded Layers</h3>
                    <div class="packet-card" id="layers-tree">
                        <!-- Dynamic protocol tree elements -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const participants = {json.dumps(participants_list)};
        const packets = {json.dumps(formatted_packets)};

        // Render participant cards and lifelines
        const partListDiv = document.getElementById("participants-list");
        const lifelinesDiv = document.getElementById("lifelines-container");

        participants.forEach(p => {{
            const card = document.createElement("div");
            card.className = "participant-card";
            card.textContent = p;
            partListDiv.appendChild(card);

            const line = document.createElement("div");
            line.className = "lifeline";
            lifelinesDiv.appendChild(line);
        }});

        // Render messages
        const msgContainer = document.getElementById("messages-container");
        
        packets.forEach((p, idx) => {{
            const row = document.createElement("div");
            row.className = "msg-row";
            row.onclick = () => selectPacket(idx, row);

            const srcIdx = participants.indexOf(p.src);
            const destIdx = participants.indexOf(p.dest);

            if (srcIdx !== -1 && destIdx !== -1) {{
                const arrowDiv = document.createElement("div");
                arrowDiv.className = "msg-arrow-container";

                const left = Math.min(srcIdx, destIdx);
                const right = Math.max(srcIdx, destIdx);
                const widthPercent = ((right - left) / participants.length) * 100;
                const leftPercent = (left / participants.length) * 100 + (50 / participants.length);

                arrowDiv.style.left = leftPercent + "%";
                arrowDiv.style.width = widthPercent + "%";

                const label = document.createElement("div");
                label.className = "msg-label";
                label.textContent = `#${{p.num}} - ${{p.summary}}`;
                arrowDiv.appendChild(label);

                const line = document.createElement("div");
                line.className = "msg-line";
                arrowDiv.appendChild(line);

                const head = document.createElement("div");
                head.className = "msg-arrow-head";
                
                if (srcIdx < destIdx) {{
                    head.className += " msg-arrow-right";
                }} else {{
                    head.className += " msg-arrow-left";
                }}
                arrowDiv.appendChild(head);
                row.appendChild(arrowDiv);
                
                const timeSpan = document.createElement("span");
                timeSpan.className = "msg-timestamp";
                timeSpan.textContent = p.rel_time;
                row.appendChild(timeSpan);
            }}

            msgContainer.appendChild(row);
        }});

        function selectPacket(index, rowElement) {{
            // Set active class
            document.querySelectorAll(".msg-row").forEach(r => r.classList.remove("active"));
            rowElement.classList.add("active");

            const p = packets[index];
            document.getElementById("inspector-placeholder").style.display = "none";
            document.getElementById("inspector-content").style.display = "block";

            // Fill meta
            document.getElementById("meta-packet-id").textContent = "#" + p.num;
            document.getElementById("meta-timestamp").textContent = p.rel_time;
            
            const badge = document.getElementById("meta-protocol");
            badge.innerHTML = "";
            const span = document.createElement("span");
            span.className = "badge " + (p.proto === "SIGTRAN" ? "badge-sigtran" : "badge-sip");
            span.textContent = p.proto;
            badge.appendChild(span);

            // Fill Layer Tree
            const tree = document.getElementById("layers-tree");
            tree.innerHTML = "";

            // IP Layer
            const ipNode = createTreeNode("Network Layer (IPv4)", [
                `Source IP: ${{p.raw_packet.src_ip}}`,
                `Destination IP: ${{p.raw_packet.dest_ip}}`,
                `Protocol ID: ${{p.raw_packet.protocol}}`
            ]);
            tree.appendChild(ipNode);

            // Transport Layer
            const transportNode = createTreeNode(`Transport Layer (${{p.raw_packet.protocol === 132 ? 'SCTP' : p.raw_packet.protocol === 6 ? 'TCP' : 'UDP'}})`, [
                `Source Port: ${{p.raw_packet.src_port}}`,
                `Destination Port: ${{p.raw_packet.dest_port}}`,
                p.raw_packet.ppid ? `Payload Protocol Identifier (PPID): ${{p.raw_packet.ppid}}` : null
            ].filter(Boolean));
            tree.appendChild(transportNode);

            // Signaling / Application layers
            if (p.proto === "SIGTRAN") {{
                const sig = p.full_diss;
                const sigtranNode = createTreeNode("Signaling Connection Layer (M2UA/M3UA)", [
                    `Originating Point Code (OPC): ${{sig.src_pc}}`,
                    `Destination Point Code (DPC): ${{sig.dest_pc}}`
                ]);
                tree.appendChild(sigtranNode);

                const tcapNode = createTreeNode(`TCAP Layer (${{sig.tcap_msg}})`, [
                    sig.otid ? `Originating Transaction ID: ${{sig.otid}}` : null,
                    sig.dtid ? `Destination Transaction ID: ${{sig.dtid}}` : null
                ].filter(Boolean));
                
                if (sig.components && sig.components.length > 0) {{
                    const compsBody = document.createElement("div");
                    compsBody.className = "tree-node";
                    
                    sig.components.forEach(c => {{
                        const cNode = createTreeNode(`Component: ${{c.type}} (ID: ${{c.id}})`, [
                            `Operation: ${{c.name}} (Code: ${{c.op}})`,
                            c.event_type ? `Event Type: ${{c.event_type}}` : null
                        ].filter(Boolean));
                        compsBody.appendChild(cNode);
                    }});
                    tcapNode.appendChild(compsBody);
                }}
                tree.appendChild(tcapNode);
            }} else {{
                // Custom app payload variables
                const appLines = [];
                for (const [k, v] of Object.entries(p.full_diss)) {{
                    if (k !== "protocol_name" && k !== "summary") {{
                        appLines.push(`${{k.charAt(0).toUpperCase() + k.slice(1).replace('_', ' ')}}: ${{v}}`);
                    }}
                }}
                if (appLines.length > 0) {{
                    const appNode = createTreeNode(`${{p.proto}} Application Layer`, appLines);
                    tree.appendChild(appNode);
                }}
            }}
        }}

        function createTreeNode(title, items) {{
            const node = document.createElement("div");
            node.className = "tree-node";

            const header = document.createElement("div");
            header.className = "tree-header";
            header.innerHTML = `▼ ${{title}}`;
            node.appendChild(header);

            const body = document.createElement("div");
            body.className = "tree-body";
            
            items.forEach(item => {{
                const div = document.createElement("div");
                div.style.fontSize = "0.85rem";
                div.style.padding = "2px 0";
                div.style.color = "var(--text-main)";
                div.textContent = item;
                body.appendChild(div);
            }});

            node.appendChild(body);
            
            header.onclick = () => {{
                if (body.style.display === "none") {{
                    body.style.display = "flex";
                    header.innerHTML = `▼ ${{title}}`;
                }} else {{
                    body.style.display = "none";
                    header.innerHTML = `▶ ${{title}}`;
                }}
            }};

            return node;
        }}
    </script>

</body>
</html>
"""

    with open(out_file, 'w') as f:
        f.write(html_content)


def find_workspace_root() -> str:
    # Try traversing up from the current working directory to find a common project marker
    curr = os.getcwd()
    for _ in range(4):
        if (os.path.exists(os.path.join(curr, "pyproject.toml")) or 
            os.path.exists(os.path.join(curr, "uv.lock")) or 
            os.path.exists(os.path.join(curr, "skills"))):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    
    # Fallback: Traverse up from __file__
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
        return workspace_root
    except Exception:
        return os.getcwd()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_trace.py <pcap_file_name_or_path> [output_report_md]")
        sys.exit(1)
        
    pcap_input = sys.argv[1]
    pcap_file = pcap_input
    
    workspace_root = find_workspace_root()
    # Path resolution
    possible_paths = [
        pcap_input,
        os.path.join(workspace_root, pcap_input),
        os.path.join(workspace_root, "traces", pcap_input),
        os.path.join(workspace_root, ".tmp", "data", "traces", pcap_input),
        os.path.join(os.getcwd(), pcap_input),
        os.path.join(os.getcwd(), "traces", pcap_input),
        os.path.join(os.getcwd(), ".tmp", "data", "traces", pcap_input),
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            pcap_file = path
            break
            
    if not os.path.exists(pcap_file):
        print(f"Error: PCAP file '{pcap_input}' could not be located in current directory or workspace.")
        sys.exit(1)
        
    engine = ParserEngine()
    packets = engine.parse_file(pcap_file)
    
    if len(sys.argv) > 2:
        out_file = sys.argv[2]
        base_dir = os.path.dirname(os.path.abspath(out_file))
        base_name = os.path.splitext(os.path.basename(out_file))[0]
        out_html = os.path.join(base_dir, f"{base_name}_call_flow.html")
    else:
        base_dir = os.path.dirname(os.path.abspath(pcap_file))
        base_name = os.path.splitext(os.path.basename(pcap_file))[0]
        out_file = os.path.join(os.getcwd(), f"{base_name}_report.md")
        out_html = os.path.join(os.getcwd(), f"{base_name}_call_flow.html")
        
    report = generate_report(packets, pcap_file, engine.diagnostics)
    with open(out_file, 'w') as f:
        f.write(report)
        
    if packets:
        # Generate gorgeous interactive HTML report
        generate_html_report(packets, pcap_file, out_html)
        print(f"Successfully generated call flow report: {out_file}")
        print(f"Successfully generated interactive HTML dashboard: {out_html}")
        print("\nPreview of parsed packets:")
        for p in packets:
            diss = p.get("dissection", {})
            proto = diss.get("protocol_name")
            if proto == "SIGTRAN":
                print(f"Packet #{p['num']}: OPC={diss['src_pc']} -> DPC={diss['dest_pc']} | TCAP={diss['tcap_msg']} | Ops={diss['operations']}")
            else:
                print(f"Packet #{p['num']}: {p['src_ip']} -> {p['dest_ip']} | {proto} | {diss.get('summary')}")
    else:
        diag = engine.diagnostics
        lt = diag.get("link_type")
        lt_names = {0: "NULL/Loopback", 1: "Ethernet", 101: "RAW IP", 113: "Linux SLL (cooked)"}
        lt_name = lt_names.get(lt, f"Link Type {lt}" if lt is not None else "unknown")
        print(f"\n❌ No packets parsed. Diagnostics:")
        print(f"   Link layer type: {lt_name}")
        print(f"   Total packets in file: {diag.get('total_packets', 0)}")
        if diag.get("skipped_non_ethernet", 0):
            print(f"   Skipped (unsupported link type): {diag['skipped_non_ethernet']}")
        if diag.get("skipped_non_ip", 0):
            print(f"   Skipped (non-IPv4): {diag['skipped_non_ip']}")
        if diag.get("skipped_too_short", 0):
            print(f"   Skipped (too short): {diag['skipped_too_short']}")
        if diag.get("skipped_no_payload", 0):
            print(f"   Skipped (no payload): {diag['skipped_no_payload']}")
        print(f"   Written report: {out_file}")

if __name__ == '__main__':
    main()
