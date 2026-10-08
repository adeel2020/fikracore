from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from engine_stack.engines.telecom_brain.api import capability_api


app = FastAPI()
app.include_router(capability_api.router)
client = TestClient(app)


class FakeTTS:
    class Speech:
        class Stream:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def iter_bytes(self, chunk_size: int):
                assert chunk_size == 4096
                yield b"pcm-chunk-1"
                yield b"pcm-chunk-2"

        @property
        def with_streaming_response(self):
            return self

        def create(self, **kwargs):
            assert kwargs["model"] == "gpt-4o-mini-tts"
            assert kwargs["voice"] == "onyx"
            assert kwargs["input"] == "Zaki is ready."
            assert kwargs["response_format"] == "pcm"
            return self.Stream()

    def __init__(self) -> None:
        self.audio = SimpleNamespace(speech=self.Speech())


def test_zaki_speech_streams_neural_audio_chunks(monkeypatch):
    monkeypatch.setattr(capability_api, "_get_zaki_tts_client", lambda: FakeTTS())

    response = client.post(
        "/api/v1/fikracore/zaki/speech",
        json={"text": "Zaki is ready."},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/pcm"
    assert response.headers["x-audio-sample-rate"] == "24000"
    assert response.content == b"pcm-chunk-1pcm-chunk-2"