"""Tool Gateway for Zaki v1 Dark NOC."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from ..contracts.tool import ToolContract, ToolMetadata, ToolSpec
from ..enums import AuthorityLevel, ToolInterface, ToolType


class ToolGateway:
    """Provides controlled, policy-checked access to operational tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolContract] = {}
        self._handlers: Dict[str, Callable] = {}
        self._bootstrap_tools()

    def register_tool(
        self,
        tool: ToolContract,
        handler: Optional[Callable] = None,
    ) -> None:
        self._tools[tool.metadata.id] = tool
        if handler:
            self._handlers[tool.metadata.id] = handler

    def get_tool(self, tool_id: str) -> Optional[ToolContract]:
        return self._tools.get(tool_id)

    def list_tools(self, tool_type: Optional[ToolType] = None) -> List[ToolContract]:
        tools = list(self._tools.values())
        if tool_type:
            tools = [t for t in tools if t.spec.type == tool_type]
        return tools

    def invoke_tool(
        self,
        tool_id: str,
        params: Dict[str, Any],
        caller_authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE,
    ) -> Dict[str, Any]:
        tool = self.get_tool(tool_id)
        if not tool:
            return {"status": "ERROR", "message": f"Tool {tool_id} not found"}

        # Authority level check
        if caller_authority < tool.spec.required_authority:
            return {
                "status": "DENIED",
                "message": f"Required authority {tool.spec.required_authority} exceeds caller authority {caller_authority}",
            }

        # Invoke handler or fallback simulation handler
        handler = self._handlers.get(tool_id)
        if handler:
            return handler(params)

        return {
            "status": "SUCCESS",
            "tool_id": tool_id,
            "message": f"Tool {tool_id} executed successfully",
            "result": {"echo": params},
        }

    def _bootstrap_tools(self) -> None:
        read_tools = [
            ("alarm.query", "Query active and historical alarms"),
            ("metric.query", "Query telemetry metrics and counters"),
            ("log.query", "Query operational syslogs and service logs"),
            ("trace.query", "Query call flow traces and PCAPs"),
            ("kpi.query", "Query network and service KPIs"),
            ("topology.query", "Query network topology and neighbor adjacency"),
            ("inventory.query", "Query physical and virtual asset inventory"),
            ("change.query", "Query recent change orders and maintenance events"),
            ("ticket.query", "Query ITSM trouble tickets"),
            ("routing.query", "Query BGP/OSPF routing tables and FIB"),
            ("service-impact.query", "Query affected customer services and blast radius"),
        ]
        for tid, desc in read_tools:
            self.register_tool(
                ToolContract(
                    metadata=ToolMetadata(id=tid, name=tid, description=desc),
                    spec=ToolSpec(
                        type=ToolType.READ,
                        interface=ToolInterface.INTERNAL,
                        required_authority=AuthorityLevel.LEVEL_0_OBSERVE,
                        risk_level="LOW",
                    ),
                )
            )

        analysis_tools = [
            ("trace.analyze", "Perform deep packet inspection and protocol decoding"),
            ("path.analyze", "Trace end-to-end packet and signaling pathway"),
            ("kpi.analyze", "Analyze KPI degradation signatures"),
            ("protocol.analyze", "Analyze protocol error codes and release causes"),
            ("customer-journey.analyze", "Analyze subscriber session lifecycle"),
        ]
        for tid, desc in analysis_tools:
            self.register_tool(
                ToolContract(
                    metadata=ToolMetadata(id=tid, name=tid, description=desc),
                    spec=ToolSpec(
                        type=ToolType.ANALYZE,
                        interface=ToolInterface.INTERNAL,
                        required_authority=AuthorityLevel.LEVEL_1_ANALYZE,
                        risk_level="LOW",
                    ),
                )
            )

        fikracore_tools = [
            ("fikracore.correlate", "Execute 4-dimension cross-domain correlation"),
            ("fikracore.rank_hypotheses", "Evaluate and rank causal hypotheses"),
            ("fikracore.test_hypothesis", "Run 12-factor synthesis core hypothesis test"),
            ("fikracore.detect_gap", "Detect unmodelled propagation residuals and knowledge gaps"),
            ("fikracore.get_blast_radius", "Calculate service impact and affected blast radius"),
            ("fikracore.get_attribution", "Determine root domain and contributing domains"),
        ]
        for tid, desc in fikracore_tools:
            self.register_tool(
                ToolContract(
                    metadata=ToolMetadata(id=tid, name=tid, description=desc),
                    spec=ToolSpec(
                        type=ToolType.FIKRACORE,
                        interface=ToolInterface.INTERNAL,
                        required_authority=AuthorityLevel.LEVEL_1_ANALYZE,
                        risk_level="LOW",
                    ),
                )
            )

        action_tools = [
            ("change.create", "Create ITSM change record"),
            ("change.approve", "Approve ITSM emergency change"),
            ("network.action", "Apply network configuration change"),
            ("service.restart", "Restart degraded network function or container"),
            ("traffic.reroute", "Shift traffic to redundant transport path or UPF"),
        ]
        for tid, desc in action_tools:
            self.register_tool(
                ToolContract(
                    metadata=ToolMetadata(id=tid, name=tid, description=desc),
                    spec=ToolSpec(
                        type=ToolType.ACTION,
                        interface=ToolInterface.INTERNAL,
                        required_authority=AuthorityLevel.LEVEL_4_HITL_EXECUTE,
                        risk_level="HIGH",
                    ),
                )
            )


default_tool_gateway = ToolGateway()
