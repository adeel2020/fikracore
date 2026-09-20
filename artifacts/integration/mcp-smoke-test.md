# Live gbrain MCP Integration Smoke Test Report

- **Endpoint**: `http://localhost:3131/mcp`
- **Timestamp**: `2026-09-20T04:13:38.034679+00:00`
- **Duration**: `8.942s`
- **Overall Decision**: **`LIVE_MCP_SMOKE_SUPPORTED`**
- **Checks Passed**: `16/16`
- **Hidden Truth Leakage**: `0`

## 1. Validation Results Summary

| Check | Description | Status |
| :--- | :--- | :--- |
| **Smoke Test 1** | MCP Endpoint Reachability | **PASS** |
| **Smoke Test 2** | MCP Authentication & Session | **PASS** |
| **Smoke Test 3** | Tool Discovery | **PASS** |
| **Smoke Test 4** | Active Schema Pack Read | **PASS** |
| **Smoke Test 5** | Read Known telecombrain Pages | **PASS** |
| **Smoke Test 6** | Read Links & Backlinks | **PASS** |
| **Smoke Test 7** | Graph Traversal (1-hop bidirectional) | **PASS** |
| **Smoke Test 8** | Canonical Resolution (Alias Mapping) | **PASS** |
| **Smoke Test 9** | Live KnowledgeProvider Contract | **PASS** |
| **Smoke Test 10** | Live vs Snapshot Provider Parity | **PASS** |
| **Smoke Test 11** | H1 Live Investigation Smoke | **PASS** |
| **Smoke Test 12** | H2 Live Knowledge-Gap Check | **PASS** |
| **Smoke Test 13** | H4 Live What-If Simulation | **PASS** |
| **Smoke Test 14** | Mark / Zaki State Grounding | **PASS** |
| **Smoke Test 15** | Hidden Truth Boundary Isolation | **PASS** |

## 2. Telecombrain Environment Details

- **Active Schema**: `mobile-core@0.1.0+2eea5e14`
- **Page Types**: `27` | **Link Types**: `25`
- **Source Tier**: `home-config`

## 3. Failure Report

Zero failures detected across all 15 integration dimensions.

---
*Generated automatically by FikraCore Step 4.5 Integration Harness at 2026-09-20T04:13:38.034679+00:00*