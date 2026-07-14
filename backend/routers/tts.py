import base64
import re
import io
import struct
import math
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from backend.config import settings

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TTSInput(BaseModel):
    ssml: str = ""


class TTSVoice(BaseModel):
    languageCode: str = "en-US"
    name: str = "alloy"


class TTSAudioConfig(BaseModel):
    audioEncoding: str = "MP3"
    speakingRate: float = 1.0
    pitch: float = 0.0
    volumeGainDb: float = 0.0


class TTSRequest(BaseModel):
    input: TTSInput
    voice: TTSVoice = TTSVoice()
    audioConfig: TTSAudioConfig = TTSAudioConfig()
    enableTimePointing: list[int] = [1]


def extract_text_from_ssml(ssml: str) -> str:
    text = re.sub(r"<[^>]+>", "", ssml)
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
    )
    return text.strip()


def parse_ssml_words(ssml: str) -> list[str]:
    text = extract_text_from_ssml(ssml)
    words = re.split(r"\s+", text) if text else []
    return [w for w in words if w]


def estimate_mp3_duration(data: bytes) -> float:
    if len(data) < 100:
        return 0.0
    bitrate_kbps = 128
    for i in range(len(data) - 1):
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            header = struct.unpack(">I", data[i : i + 4])[0]
            bitrate_idx = (header >> 12) & 0x0F
            bitrate_table = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
            if bitrate_idx < len(bitrate_table) and bitrate_table[bitrate_idx] > 0:
                bitrate_kbps = bitrate_table[bitrate_idx]
            break
    duration_sec = (len(data) * 8) / (bitrate_kbps * 1000)
    return duration_sec


@router.post("")
async def text_to_speech(request: TTSRequest):
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    client = OpenAI(api_key=settings.openai_api_key)

    ssml = request.input.ssml or ""
    text = extract_text_from_ssml(ssml)

    if not text:
        raise HTTPException(status_code=400, detail="No text to synthesize")

    voice_raw = request.voice.name or "nova"
    voice_name = voice_raw.split("-")[0].lower()
    valid_voices = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}
    if voice_name not in valid_voices:
        voice_name = "alloy"

    speed = max(0.25, min(4.0, request.audioConfig.speakingRate))

    response = client.audio.speech.create(
        model="tts-1",
        input=text,
        voice=voice_name,
        response_format="mp3",
        speed=speed,
    )

    audio_bytes = response.content
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    words = parse_ssml_words(ssml)
    duration_sec = estimate_mp3_duration(audio_bytes)
    sec_per_char = duration_sec / max(len(text), 1)

    timepoints = []
    cumulative = 0.0
    for i, word in enumerate(words):
        word_dur = len(word) * sec_per_char
        cumulative += word_dur
        timepoints.append(
            {
                "markName": str(i),
                "timeSeconds": round(cumulative, 4),
            }
        )

    return {
        "audioContent": audio_b64,
        "timepoints": timepoints,
    }
