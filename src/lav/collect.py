"""Run the prompt set against every model and land rows in the store."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple

from .config import Brand, Model, Prompt
from .parse import extract_citations, extract_mentions
from .providers import get_provider


def run_id_for(collected_at: datetime) -> str:
    return collected_at.strftime("%Y%m%dT%H%M%SZ")


def answer_key(run_id: str, prompt_id: str, model_id: str) -> str:
    return hashlib.sha256(f"{run_id}|{prompt_id}|{model_id}".encode()).hexdigest()[:16]


def collect(prompts: Iterable[Prompt], models: Iterable[Model], brands: Iterable[Brand],
            collected_at: datetime | None = None,
            ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Returns (raw_answers, answer_citations, brand_mentions).

    The answer_key makes a re-run of the same (run, prompt, model) idempotent:
    the store replaces on that key rather than appending a duplicate.
    """
    collected_at = collected_at or datetime.now(timezone.utc)
    run_id = run_id_for(collected_at)
    ts = collected_at.isoformat()

    answers: List[Dict] = []
    citations: List[Dict] = []
    mentions: List[Dict] = []
    brands = list(brands)

    for model in models:
        provider = get_provider(model.provider, model.id)
        for prompt in prompts:
            result = provider.answer(prompt.text)
            key = answer_key(run_id, prompt.id, model.id)
            answers.append({
                "answer_key": key,
                "run_id": run_id,
                "collected_at": ts,
                "prompt_id": prompt.id,
                "category": prompt.category,
                "prompt_text": prompt.text,
                "model_id": model.id,
                "answer_text": result.text,
                "latency_ms": result.latency_ms,
                "status": result.status,
            })
            if result.status != "ok":
                continue

            cites = extract_citations(result.text)
            for c in cites:
                citations.append({
                    "answer_key": key, "run_id": run_id, "collected_at": ts,
                    "prompt_id": prompt.id, "model_id": model.id,
                    "position": c.position, "url": c.url, "domain": c.domain,
                })
            for m in extract_mentions(result.text, brands, cites):
                mentions.append({
                    "answer_key": key, "run_id": run_id, "collected_at": ts,
                    "prompt_id": prompt.id, "category": prompt.category,
                    "model_id": model.id, "brand": m.brand, "mentions": m.mentions,
                    "rank": m.rank, "cited": int(m.cited),
                })

    return answers, citations, mentions
