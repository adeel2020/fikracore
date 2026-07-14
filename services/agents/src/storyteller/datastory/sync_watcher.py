"""Background file watcher for knowledge_graph_state.yaml.

Polls the file modification time every 30s and triggers sync_story()
when a change is detected, with a 60s debounce to avoid rapid writes."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from .sync_story import sync_story

logger = logging.getLogger(__name__)

_DATA = Path(__file__).resolve().parent / "data"
_KG_PATH = _DATA / "knowledge_graph_state.yaml"

_POLL_INTERVAL = 30
_DEBOUNCE = 60


async def watch_kg_state() -> None:
    """Background task: poll KG file mtime, trigger sync_story() on change."""
    last_mtime = _KG_PATH.stat().st_mtime if _KG_PATH.exists() else 0
    last_sync = 0.0

    logger.info("KG watcher started — polling every %ds", _POLL_INTERVAL)

    while True:
        await asyncio.sleep(_POLL_INTERVAL)

        if not _KG_PATH.exists():
            continue

        try:
            current_mtime = _KG_PATH.stat().st_mtime
        except OSError:
            continue

        if current_mtime == last_mtime:
            continue

        # File changed — check debounce
        now = time.time()
        if now - last_sync < _DEBOUNCE:
            logger.debug("KG changed but debounce active — skipping")
            last_mtime = current_mtime
            continue

        logger.info("KG state file changed — running sync_story()")
        last_mtime = current_mtime
        last_sync = now

        try:
            warnings = await asyncio.to_thread(sync_story)
            if warnings:
                logger.info("sync_story applied %d changes", len(warnings))
        except Exception as exc:
            logger.exception("sync_story failed: %s", exc)
