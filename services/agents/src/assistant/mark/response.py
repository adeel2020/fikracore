"""Per-turn presentation context, compatible with legacy text consumers."""

from typing import Any


class MarkResponse(str):
    spoken_reply: str | None
    presentation: dict[str, Any]

    def __new__(cls, text: str, *, spoken_reply: str | None = None,
                presentation: dict[str, Any] | None = None):
        response = super().__new__(cls, text)
        response.spoken_reply = spoken_reply
        response.presentation = presentation or {}
        return response
