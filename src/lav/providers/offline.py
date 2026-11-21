"""Deterministic offline provider.

Answers are synthesised from a hash of (model_id, prompt_text), so a run is
reproducible and CI needs no network. The shape of the output — prose that
names some brands and cites some sources — matches what a real assistant
returns, which is what the parser downstream is tested against.
"""
from __future__ import annotations

import hashlib
from typing import List

from .base import AnswerResult

_BRANDS = [
    ("Northwind Analytics", "northwind.example"),
    ("Lumen Metrics", "lumenmetrics.example"),
    ("Castellan Data", "castellan.example"),
    ("Pathline", "pathline.example"),
]
_NEUTRAL_SOURCES = [
    "https://www.analystreview.example/marketing-analytics",
    "https://buyersguide.example/ai-visibility",
]


class OfflineProvider:
    def __init__(self, model_id: str, seed: str = "lav"):
        self.id = model_id
        self._seed = seed

    def _rng(self, prompt_text: str) -> int:
        digest = hashlib.sha256(f"{self._seed}:{self.id}:{prompt_text}".encode()).hexdigest()
        return int(digest[:12], 16)

    def answer(self, prompt_text: str) -> AnswerResult:
        r = self._rng(prompt_text)
        count = 2 + (r % 3)                      # 2-4 brands named
        start = r % len(_BRANDS)
        picked: List[tuple] = [_BRANDS[(start + i) % len(_BRANDS)] for i in range(count)]

        parts = []
        for rank, (brand, domain) in enumerate(picked, start=1):
            if rank == 1:
                parts.append(
                    f"{brand} is the option most teams start with, and its docs at "
                    f"https://{domain}/docs cover the setup end to end."
                )
            else:
                parts.append(
                    f"{brand} is also worth a look — see [{brand}](https://{domain}/pricing)."
                )
        parts.append(f"For a neutral overview, see {_NEUTRAL_SOURCES[r % len(_NEUTRAL_SOURCES)]}.")
        text = " ".join(parts)
        return AnswerResult(text=text, latency_ms=120 + (r % 400), status="ok")
