"""Unit tests for ``voice.runtime`` (thread/OMP configuration).

These are lightweight and do not require any ML backend or model download, so
they run in the default suite. They verify idempotency and that the platform
aware OMP scoping never overrides an operator-provided value.
"""

from __future__ import annotations

import os
import sys

import pytest

import storyteller.voice.runtime as runtime
from storyteller.voice.runtime import _pin_omp, configure_runtime, reset_for_tests


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    reset_for_tests()
    yield
    reset_for_tests()


def test_configure_runtime_is_idempotent(monkeypatch):
    calls = []

    class _FakeTorch:
        @staticmethod
        def set_num_threads(n):
            calls.append(n)

    monkeypatch.setitem(sys.modules, "torch", _FakeTorch())
    monkeypatch.setenv("VOICE_TORCH_THREADS", "4")

    configure_runtime()
    configure_runtime()
    configure_runtime()

    # set_num_threads must be applied exactly once (idempotent).
    assert calls == [4]


def test_runtime_does_not_override_operator_omp(monkeypatch):
    # Operator explicitly chose a value -> runtime must leave it untouched.
    monkeypatch.setenv("OMP_NUM_THREADS", "2")
    runtime._apply_omp_pin()
    assert os.environ["OMP_NUM_THREADS"] == "2"


def test_force_omp_override_respected(monkeypatch):
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)
    monkeypatch.setenv("VOICE_FORCE_OMP", "2")
    assert _pin_omp() == 2


@pytest.mark.skipif(sys.platform != "darwin", reason="darwin-only pin default")
def test_darwin_default_omp_pin(monkeypatch):
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)
    monkeypatch.delenv("VOICE_FORCE_OMP", raising=False)
    assert _pin_omp() == 1