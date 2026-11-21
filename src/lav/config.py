"""Config loading for prompts, brands and models."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


@dataclass(frozen=True)
class Prompt:
    id: str
    category: str
    text: str


@dataclass(frozen=True)
class Brand:
    name: str
    aliases: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Model:
    id: str
    label: str
    provider: str


def _read(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_prompts(path: Path) -> List[Prompt]:
    rows = _read(path).get("prompts", [])
    prompts = [Prompt(id=r["id"], category=r["category"], text=r["text"]) for r in rows]
    ids = [p.id for p in prompts]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate prompt id in prompt set")
    return prompts


def load_brands(path: Path) -> List[Brand]:
    rows = _read(path).get("brands", [])
    brands = []
    for r in rows:
        aliases = r.get("aliases") or [r["name"]]
        if r["name"] not in aliases:
            aliases = [r["name"], *aliases]
        brands.append(Brand(name=r["name"], aliases=aliases, domains=r.get("domains") or []))
    return brands


def load_models(path: Path) -> List[Model]:
    rows = _read(path).get("models", [])
    return [Model(id=r["id"], label=r["label"], provider=r["provider"]) for r in rows]
