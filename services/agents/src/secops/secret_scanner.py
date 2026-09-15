from __future__ import annotations

import os
import re
import logging
from pathlib import Path

from secops.base import BaseSecOpsAgent, SecOpsFinding

logger = logging.getLogger("secops.secret_scanner")

SECRET_PATTERNS: list[tuple[str, str]] = [
    ("AWS Access Key", r"(?i)AKIA[0-9A-Z]{16}"),
    ("AWS Secret Key", r"(?i)(aws[_-]?secret[_-]?access[_-]?key|aws_secret_key)\s*[:=]\s*['\"][A-Za-z0-9\/+=]{40}['\"]"),
    ("GitHub Token", r"(?i)(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}"),
    ("GitHub App Token", r"(?i)(ghx|ghb)_[A-Za-z0-9_]{36,}"),
    ("OpenAI API Key", r"(?i)sk-[A-Za-z0-9]{32,}"),
    ("Generic Password", r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    ("Generic Secret", r"(?i)(secret|api[_-]?key|token|apikey)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    ("JWT Token", r"(?i)eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"),
    ("Private Key", r"-----BEGIN\s+(RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY-----"),
    ("Slack Token", r"(?i)xox[baprs]-[0-9a-zA-Z-]{10,}"),
    ("Google OAuth", r"(?i)[0-9]+-[a-zA-Z0-9_]{32,}\.apps\.googleusercontent\.com"),
    ("Heroku API Key", r"(?i)h[rl]ak-[0-9A-Fa-f]{36}"),
    ("Generic Connection String", r"(?i)(mongodb|postgresql|mysql|redis)://[^@\s]+:[^@\s]+@"),
]

EXCLUDED_DIRS: set[str] = {
    ".git", "__pycache__", ".venv", "node_modules", "chroma_db",
    ".tmp", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache",
}


class SecretScanner(BaseSecOpsAgent):
    def __init__(self):
        super().__init__(name="secret-scanner", schedule="0 */6 * * *")
        self.scanned_files = 0

    async def run(self) -> dict:
        logger.info("[SecretScanner] Starting scan...")
        repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent

        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for fname in files:
                if not self._is_scanable(fname):
                    continue
                fpath = Path(root) / fname
                try:
                    self._scan_file(fpath)
                except Exception as e:
                    logger.debug("Skipping %s: %s", fpath, e)

        logger.info(
            "[SecretScanner] Done. Scanned %d files, found %d secrets.",
            self.scanned_files, len(self.findings),
        )
        self.print_report()
        return self.report()

    def _is_scanable(self, fname: str) -> bool:
        if fname.startswith("."):
            return False
        exts = {".py", ".yaml", ".yml", ".json", ".env", ".toml", ".cfg",
                ".conf", ".ini", ".sh", ".tf", ".md", ".txt", ".xml"}
        return Path(fname).suffix in exts

    def _scan_file(self, fpath: Path) -> None:
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return
        self.scanned_files += 1
        for name, pattern in SECRET_PATTERNS:
            for match in re.finditer(pattern, text):
                line_num = text[:match.start()].count("\n") + 1
                rel_path = fpath.relative_to(fpath.anchor) if fpath.is_absolute() else fpath
                self.add_finding(SecOpsFinding(
                    severity="high",
                    category="secret_exposure",
                    title=f"Potential {name} detected",
                    description=f"Matched pattern: {pattern[:40]}...",
                    resource=f"{rel_path}:{line_num}",
                    recommendation="Remove hardcoded secret and use environment variables or a secrets manager.",
                    iso_control="A.8.2",
                ))
