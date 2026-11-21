"""Provider interface.

A provider turns a prompt into an answer. The offline provider ships with the
repo so the pipeline runs with no network and no API keys; a real provider only
has to implement `answer()` and return the same AnswerResult.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AnswerResult:
    text: str
    latency_ms: int
    status: str = "ok"


class Provider(Protocol):
    id: str

    def answer(self, prompt_text: str) -> AnswerResult: ...


def get_provider(name: str, model_id: str, **kwargs) -> Provider:
    if name == "offline":
        from .offline import OfflineProvider

        return OfflineProvider(model_id=model_id, **kwargs)
    raise ValueError(f"unknown provider: {name}")
