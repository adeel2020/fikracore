"""Runtime / threading configuration for the voice ML stack (Phase 3E).

The two real backends load conflicting OpenMP runtimes when both are present:

* faster-whisper (CTranslate2) links its own OpenMP and **deadlocks** at
  ``OMP_NUM_THREADS > 1`` while torch (used by Kokoro) is also loaded — a
  verified failure even at model construction on macOS.
* Kokoro (torch) benefits substantially from more intra-op threads.

This module gives torch its threads through ``torch.set_num_threads`` (runtime
API, independent of the process-wide OMP variable) so it does **not** need
``OMP_NUM_THREADS > 1``. The process-wide OMP pin to ``1`` is therefore only
imposed where the conflict is known to occur and only if the operator has not
already chosen a value. ``configure_runtime()`` is idempotent and does not
repeatedly mutate global runtime state.
"""

from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)


def _pin_omp() -> int | None:
    """Return an OMP_NUM_THREADS pin for this platform, or ``None`` to leave it.

    The CTranslate2 + torch coexistence deadlock is only verified on macOS
    (``darwin``). On other platforms we do not impose ``OMP_NUM_THREADS=1``
    unless the operator explicitly asks via ``VOICE_FORCE_OMP=1``.
    """
    force = os.environ.get("VOICE_FORCE_OMP")
    if force is not None and force.strip() not in ("", "0", "false", "no"):
        return int(float(force))
    if sys.platform == "darwin":
        # torch(OpenMP/libiomp) + CTranslate2 conflict is real on macOS.
        return 1
    return None


def _apply_omp_pin() -> None:
    """Set OMP_NUM_THREADS and KMP_DUPLICATE_LIB_OK before any ML library imports."""
    if sys.platform == "darwin":
        os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    # Never override an operator-provided value.
    if "OMP_NUM_THREADS" in os.environ:
        return
    pin = _pin_omp()
    if pin is not None:
        os.environ["OMP_NUM_THREADS"] = str(pin)
        logger.info("voice: pinning OMP_NUM_THREADS=%d for ML runtime safety", pin)


# Runs at import time (before any lazy torch / ctranslate2 import) so the env is
# stable by the time the adapters call ``init()``.
_apply_omp_pin()

_configured = False


def configure_runtime() -> None:
    """Apply the runtime thread configuration. Idempotent.

    Sets torch's intra-op thread count via the torch API only (never the
    process-wide OMP variable). No-op if torch is not importable. Safe to call
    multiple times.
    """
    global _configured
    if _configured:
        return
    _configured = True

    try:
        import torch  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        logger.debug("voice: torch not importable; skipping thread config: %s", exc)
        return

    from .config import get_voice_settings  # noqa: PLC0415

    threads = int(get_voice_settings().voice_torch_threads)
    try:
        torch.set_num_threads(threads)
    except Exception as exc:  # noqa: BLE001
        logger.warning("voice: torch.set_num_threads failed: %s", exc)
        return
    logger.info("voice: torch intra-op threads set to %d", threads)


def reset_for_tests() -> None:
    """Allow reconfiguration in tests (idempotence check helper)."""
    global _configured
    _configured = False


__all__ = ["configure_runtime", "reset_for_tests"]