"""
JARVIS Security Engine - Security Guardrails & Validation
Protects against malicious inputs and ensures data sovereignty.
"""

from __future__ import annotations

import re
import json
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger("jarvis.security")


class SecurityEngine:
    """JARVIS security superpower - protect and serve."""

    def __init__(self, config):
        self.config = config
        self._blocked_patterns: list[str] = [
            r"(?i)(drop\s+table|delete\s+from|truncate|alter\s+table)",
            r"(?i)(exec\(|eval\(|os\.system|subprocess\.call)",
            r"(?i)(\.\.\/|\.\.\\)",
            r"(?i)(password|secret|token|api_key)\s*=\s*['\"][^'\"]+['\"]",
        ]
        self._rate_limit: dict[str, list[float]] = {}
        self._max_requests_per_minute = 60

    async def initialize(self) -> None:
        """Initialize security systems."""
        logger.info("[SecurityEngine] Initialized.")
        logger.info(f"[SecurityEngine] Security level: {self.config.security_level}")
        logger.info(f"[SecurityEngine] Data residency: {self.config.data_residency}")

    async def validate_query(self, query: str) -> bool:
        """Validate query for security concerns."""
        # SQL injection check
        if self._detect_sql_injection(query):
            logger.warning(f"[SecurityEngine] SQL injection detected: {query[:50]}...")
            return False
        
        # Code injection check
        if self._detect_code_injection(query):
            logger.warning(f"[SecurityEngine] Code injection detected: {query[:50]}...")
            return False
        
        # Path traversal check
        if self._detect_path_traversal(query):
            logger.warning(f"[SecurityEngine] Path traversal detected: {query[:50]}...")
            return False
        
        # Secret exposure check
        if self._detect_secret_exposure(query):
            logger.warning(f"[SecurityEngine] Secret exposure detected: {query[:50]}...")
            return False
        
        # Rate limiting
        if not self._check_rate_limit("default"):
            logger.warning("[SecurityEngine] Rate limit exceeded.")
            return False
        
        # Data residency check
        if not self._check_data_residency(query):
            logger.warning("[SecurityEngine] Data residency violation.")
            return False
        
        return True

    def _detect_sql_injection(self, query: str) -> bool:
        """Detect SQL injection attempts."""
        sql_patterns = [
            r"(?i)union\s+select",
            r"(?i)insert\s+into",
            r"(?i)delete\s+from",
            r"(?i)drop\s+(table|database)",
            r"(?i)truncate\s+table",
            r"(?i)alter\s+table",
            r"(?i)exec\s*\(",
            r"(?i)execute\s*\(",
        ]
        return any(re.search(pattern, query) for pattern in sql_patterns)

    def _detect_code_injection(self, query: str) -> bool:
        """Detect code injection attempts."""
        code_patterns = [
            r"(?i)eval\s*\(",
            r"(?i)exec\s*\(",
            r"(?i)os\.system\s*\(",
            r"(?i)subprocess\.call\s*\(",
            r"(?i)subprocess\.run\s*\(",
            r"(?i)import\s+os",
            r"(?i)from\s+os\s+import",
            r"(?i)__import__",
        ]
        return any(re.search(pattern, query) for pattern in code_patterns)

    def _detect_path_traversal(self, query: str) -> bool:
        """Detect path traversal attempts."""
        traversal_patterns = [
            r"\.\.\/",
            r"\.\.\\",
            r"(?i)/etc/passwd",
            r"(?i)/etc/shadow",
            r"(?i)c:\\windows",
        ]
        return any(re.search(pattern, query) for pattern in traversal_patterns)

    def _detect_secret_exposure(self, query: str) -> bool:
        """Detect attempts to expose secrets."""
        secret_patterns = [
            r"(?i)password\s*=\s*['\"][^'\"]+['\"]",
            r"(?i)secret\s*=\s*['\"][^'\"]+['\"]",
            r"(?i)api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
            r"(?i)token\s*=\s*['\"][^'\"]+['\"]",
            r"(?i)aws[_-]?(access|secret)\s*[_-]?key",
        ]
        return any(re.search(pattern, query) for pattern in secret_patterns)

    def _check_rate_limit(self, client_id: str) -> bool:
        """Check rate limiting."""
        import time
        now = time.time()
        
        if client_id not in self._rate_limit:
            self._rate_limit[client_id] = []
        
        # Remove old entries
        self._rate_limit[client_id] = [
            t for t in self._rate_limit[client_id]
            if now - t < 60
        ]
        
        # Check limit
        if len(self._rate_limit[client_id]) >= self._max_requests_per_minute:
            return False
        
        self._rate_limit[client_id].append(now)
        return True

    def _check_data_residency(self, query: str) -> bool:
        """Check data residency compliance."""
        # UAE data residency - ensure no sensitive data leaves UAE
        if self.config.data_residency == "UAE":
            # Check for PII patterns that should stay in UAE
            pii_patterns = [
                r"\b\d{10}\b",  # Phone numbers
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Emails
            ]
            # For now, allow all queries - in production, would route to UAE servers
            return True
        
        return True

    def sanitize_input(self, query: str) -> str:
        """Sanitize user input."""
        # Remove potentially dangerous characters
        sanitized = re.sub(r"[<>'\";]", "", query)
        # Limit length
        sanitized = sanitized[:10000]
        return sanitized

    def get_security_status(self) -> dict:
        """Get security system status."""
        return {
            "security_level": self.config.security_level,
            "data_residency": self.config.data_residency,
            "blocked_patterns": len(self._blocked_patterns),
            "rate_limit": self._max_requests_per_minute,
        }

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Process security-related queries."""
        lower_query = query.lower()
        
        if "status" in lower_query:
            status = self.get_security_status()
            return json.dumps(status, indent=2)
        
        if "validate" in lower_query:
            is_safe = await self.validate_query(query)
            return f"Query validation: {'SAFE' if is_safe else 'BLOCKED'}"
        
        return "Security engine ready. All systems nominal."

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream security status."""
        result = await self.process(query, session_id, context)
        yield result

    async def shutdown(self) -> None:
        """Cleanup security resources."""
        self._rate_limit.clear()
