"""Observability and Tracing for Zaki v1 Agent Harness."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class Span:
    def __init__(self, name: str, trace_id: str, parent_span_id: Optional[str] = None) -> None:
        self.name = name
        self.trace_id = trace_id
        self.span_id = f"span-{int(time.time() * 1000)}"
        self.parent_span_id = parent_span_id
        self.start_time = time.perf_counter()
        self.end_time: Optional[float] = None
        self.duration_ms: float = 0.0
        self.attributes: Dict[str, Any] = {}

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def finish(self) -> None:
        self.end_time = time.perf_counter()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)


class Tracer:
    """Lightweight in-memory OpenTelemetry/TM Forum-aligned tracer."""

    def __init__(self) -> None:
        self._spans: List[Span] = []

    def start_span(self, name: str, trace_id: str, parent_span_id: Optional[str] = None) -> Span:
        span = Span(name=name, trace_id=trace_id, parent_span_id=parent_span_id)
        self._spans.append(span)
        return span

    def get_spans(self, trace_id: Optional[str] = None) -> List[Span]:
        if trace_id:
            return [s for s in self._spans if s.trace_id == trace_id]
        return list(self._spans)


default_tracer = Tracer()
