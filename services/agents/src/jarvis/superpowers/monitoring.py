"""
JARVIS Monitoring Engine - Real-time System Monitoring
Tracks system health, performance metrics, and alerts.
"""

from __future__ import annotations

import os
import psutil
import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncIterator

logger = logging.getLogger("jarvis.monitoring")


class MonitoringEngine:
    """JARVIS monitoring superpower - watch over the system."""

    def __init__(self, config):
        self.config = config
        self._alerts: list[dict] = []
        self._metrics_history: list[dict] = []

    async def initialize(self) -> None:
        """Initialize monitoring systems."""
        logger.info("[MonitoringEngine] Initialized.")

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Process monitoring queries."""
        lower_query = query.lower()
        
        # System health
        if "health" in lower_query or "status" in lower_query:
            return await self.get_system_health()
        
        # CPU metrics
        if "cpu" in lower_query:
            return await self.get_cpu_metrics()
        
        # Memory metrics
        if "memory" in lower_query or "ram" in lower_query:
            return await self.get_memory_metrics()
        
        # Disk metrics
        if "disk" in lower_query or "storage" in lower_query:
            return await self.get_disk_metrics()
        
        # Network metrics
        if "network" in lower_query or "connection" in lower_query:
            return await self.get_network_metrics()
        
        # Process list
        if "process" in lower_query or "running" in lower_query:
            return await self.get_running_processes()
        
        # Alerts
        if "alert" in lower_query or "warning" in lower_query:
            return await self.get_alerts()
        
        # Dashboard
        if "dashboard" in lower_query or "overview" in lower_query:
            return await self.get_dashboard()
        
        # Default: system health
        return await self.get_system_health()

    async def get_system_health(self) -> str:
        """Get comprehensive system health report."""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status = "HEALTHY" if cpu < 80 and memory.percent < 80 else "WARNING" if cpu < 95 else "CRITICAL"
        
        lines = [
            f"## System Health: {status}\n",
            f"**CPU:** {cpu}% ({psutil.cpu_count()} cores)",
            f"**Memory:** {memory.percent}% ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)",
            f"**Disk:** {disk.percent}% ({disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB)",
            f"**Uptime:** {self._get_uptime()}",
            f"**Timestamp:** {datetime.now().isoformat()}"
        ]
        
        return "\n".join(lines)

    async def get_cpu_metrics(self) -> str:
        """Get detailed CPU metrics."""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        
        lines = [
            "## CPU Metrics\n",
            f"**Overall Usage:** {psutil.cpu_percent(interval=0.5)}%",
            f"**Cores:** {psutil.cpu_count()}",
            f"**Frequency:** {cpu_freq.current:.0f}MHz" if cpu_freq else "",
            "\n**Per-Core Usage:**"
        ]
        for i, pct in enumerate(cpu_percent):
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            lines.append(f"Core {i}: {bar} {pct}%")
        
        return "\n".join(lines)

    async def get_memory_metrics(self) -> str:
        """Get detailed memory metrics."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        lines = [
            "## Memory Metrics\n",
            f"**RAM:** {memory.percent}% ({memory.used // (1024**2)}MB / {memory.total // (1024**2)}MB)",
            f"**Available:** {memory.available // (1024**2)}MB",
            f"**Cached:** {memory.cached // (1024**2)}MB",
            f"**Buffered:** {memory.buffers // (1024**2)}MB",
            f"\n**Swap:** {swap.percent}% ({swap.used // (1024**2)}MB / {swap.total // (1024**2)}MB)"
        ]
        
        return "\n".join(lines)

    async def get_disk_metrics(self) -> str:
        """Get detailed disk metrics."""
        disk = psutil.disk_usage('/')
        io = psutil.disk_io_counters()
        
        lines = [
            "## Disk Metrics\n",
            f"**Usage:** {disk.percent}% ({disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB)",
            f"**Free:** {disk.free // (1024**3):.1f}GB",
            f"\n**I/O Stats:**",
            f"Read: {io.read_bytes // (1024**2)}MB",
            f"Write: {io.write_bytes // (1024**2)}MB"
        ]
        
        return "\n".join(lines)

    async def get_network_metrics(self) -> str:
        """Get network metrics."""
        net_io = psutil.net_io_counters()
        
        lines = [
            "## Network Metrics\n",
            f"**Bytes Sent:** {net_io.bytes_sent // (1024**2)}MB",
            f"**Bytes Received:** {net_io.bytes_recv // (1024**2)}MB",
            f"**Packets Sent:** {net_io.packets_sent}",
            f"**Packets Received:** {net_io.packets_recv}",
            f"**Errors In:** {net_io.errin}",
            f"**Errors Out:** {net_io.errout}"
        ]
        
        return "\n".join(lines)

    async def get_running_processes(self) -> str:
        """Get top running processes."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
        
        lines = ["## Top Processes (by CPU)\n", f"{'PID':<8} {'Name':<25} {'CPU%':<8} {'MEM%':<8}", "-" * 50]
        
        for p in processes[:15]:
            lines.append(f"{p['pid']:<8} {(p['name'] or 'unknown')[:25]:<25} {p.get('cpu_percent', 0):<8.1f} {p.get('memory_percent', 0):<8.1f}")
        
        return "\n".join(lines)

    async def get_alerts(self) -> str:
        """Get active alerts."""
        if not self._alerts:
            return "No active alerts."
        
        lines = ["## Active Alerts\n"]
        for alert in self._alerts[-10:]:
            lines.append(f"- [{alert['level']}] {alert['message']} ({alert['time']})")
        
        return "\n".join(lines)

    async def get_dashboard(self) -> str:
        """Get monitoring dashboard overview."""
        health = await self.get_system_health()
        alerts = await self.get_alerts()
        
        return f"{health}\n\n{alerts}"

    def _get_uptime(self) -> str:
        """Get system uptime."""
        import time
        uptime_seconds = time.time() - psutil.boot_time()
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{days}d {hours}h {minutes}m"

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream monitoring data."""
        result = await self.process(query, session_id, context)
        yield result

    async def shutdown(self) -> None:
        """Cleanup monitoring resources."""
        self._alerts.clear()
        self._metrics_history.clear()
