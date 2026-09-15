"""Gated fixtures for the real ML backend integration suite.

Everything in ``tests/ml`` is *opt-in*: it runs only when ``VOICE_REAL_ML=1``
and the relevant backend + model are genuinely available. On default CI runs the
value is unset and every test here is skipped at fixture setup without touching
the ML stack, so normal runs stay fast and never download models.

When writing real-speech input we rely on established packages only
(``scipy.signal.resample_poly`` for the 24 kHz -> 16 kHz downsampling) and
generate the fixture with the real Kokoro TTS backend rather than committing
audio blobs.
"""

from __future__ import annotations

import os
import sys

# torch (used by Kokoro) and CTranslate2 (used by faster-whisper) bundle
# conflicting OpenMP runtimes. On macOS developers must pin these before either
# library loads. Linux/Docker builds are unaffected.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Make the storyteller package importable without relying on an installed copy.
_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src")
if os.path.isdir(_SRC) and _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import numpy as np  # noqa: E402
import pytest  # noqa: E402


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() not in ("", "0", "false", "no")


def _importable(pkg: str) -> bool:
    try:
        __import__(pkg)
        return True
    except Exception:  # noqa: BLE001
        return False


@pytest.fixture(scope="session")
def real_ml_enabled() -> bool:
    """True when the operator has opted in via ``VOICE_REAL_ML=1``."""
    return _flag("VOICE_REAL_ML")


def _reset_kmp(pkg: str) -> None:
    # Re-apply the macOS OpenMP workaround right before a heavy backend imports,
    # in case earlier modules (re)initialised the environment ordering.
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    os.environ.setdefault("OMP_NUM_THREADS", "1")


@pytest.fixture(scope="session")
def real_vad(real_ml_enabled):
    if not real_ml_enabled:
        pytest.skip("VOICE_REAL_ML not set - real VAD test is opt-in")
    if not _importable("silero_vad"):
        pytest.skip("silero-vad package is not installed")
    _reset_kmp("silero_vad")
    from storyteller.voice.vad import SileroVAD  # noqa: PLC0415

    vad = SileroVAD()
    try:
        vad.init()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Silero VAD unavailable at init: {exc}")
    return vad


@pytest.fixture(scope="session")
def real_stt(real_ml_enabled):
    if not real_ml_enabled:
        pytest.skip("VOICE_REAL_ML not set - real STT test is opt-in")
    if not _importable("faster_whisper"):
        pytest.skip("faster-whisper package is not installed")
    _reset_kmp("faster_whisper")
    from storyteller.voice.stt import FasterWhisperSTT  # noqa: PLC0415

    model = os.environ.get("STT_MODEL", "Systran/faster-whisper-tiny")
    stt = FasterWhisperSTT(model=model, device="cpu", compute_type="int8")
    try:
        stt.init()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"faster-whisper unavailable at init: {exc}")
    return stt


@pytest.fixture(scope="session")
def real_tts(real_ml_enabled):
    if not real_ml_enabled:
        pytest.skip("VOICE_REAL_ML not set - real TTS test is opt-in")
    if not _importable("kokoro"):
        pytest.skip("kokoro package is not installed")
    _reset_kmp("kokoro")
    from storyteller.voice.tts import KokoroTTS  # noqa: PLC0415

    tts = KokoroTTS(
        model=os.environ.get("TTS_MODEL", "hexgrad/Kokoro-82M"),
        voice=os.environ.get("TTS_VOICE", "af_heart"),
        device="cpu",
    )
    try:
        tts.init()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Kokoro TTS unavailable at init: {exc}")
    return tts


@pytest.fixture(scope="session")
def real_speech_16k(real_tts) -> np.ndarray:
    """A short, real, spoken phrase synthesised by Kokoro, downsampled to 16 kHz.

    Because the audio comes from the real TTS backend it is true human-like
    speech, which is exactly what Silero VAD expects to fire on, and what
    faster-whisper should transcribe to something non-empty.
    """
    from scipy import signal  # noqa: PLC0415

    result = real_tts.synthesize("The quick brown fox jumps over the lazy dog.")
    audio = np.asarray(result.audio, dtype=np.float32)
    # 24000 -> 16000 is a 2/3 downsampling: established package, not custom DSP.
    return np.ascontiguousarray(
        signal.resample_poly(audio, up=2, down=3), dtype=np.float32
    )
