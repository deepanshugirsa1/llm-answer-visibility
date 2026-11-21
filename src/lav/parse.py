"""Turn answer text into rows: citations and brand mentions.

This is the core transform — unstructured model prose in, structured rows out.
Everything downstream (share of voice, citation rank, movement) is built on it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List
from urllib.parse import urlparse

from .config import Brand

_MD_LINK = re.compile(r"\[[^\]]*\]\((https?://[^\s)]+)\)")
_BARE_URL = re.compile(r"(?<!\()(?<!\]\()https?://[^\s)\]]+")
_TRAILING = ".,;:!?'\"”’"


@dataclass(frozen=True)
class Citation:
    position: int          # 1-based order of appearance in the answer
    char_offset: int
    url: str
    domain: str


@dataclass(frozen=True)
class Mention:
    brand: str
    mentions: int
    char_offset: int       # first appearance
    rank: int              # 1-based order of first appearance among brands
    cited: bool            # a citation points at one of the brand's domains


def normalize_domain(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _clean(url: str) -> str:
    return url.rstrip(_TRAILING)


def extract_citations(text: str) -> List[Citation]:
    """Markdown links first, then bare URLs, deduped by URL, ordered by appearance."""
    found: dict[str, int] = {}
    for m in _MD_LINK.finditer(text):
        found.setdefault(_clean(m.group(1)), m.start())
    for m in _BARE_URL.finditer(text):
        found.setdefault(_clean(m.group(0)), m.start())

    ordered = sorted(found.items(), key=lambda kv: kv[1])
    return [
        Citation(position=i, char_offset=off, url=url, domain=normalize_domain(url))
        for i, (url, off) in enumerate(ordered, start=1)
    ]


def _alias_pattern(alias: str) -> re.Pattern:
    return re.compile(rf"(?<!\w){re.escape(alias)}(?!\w)", re.IGNORECASE)


def extract_mentions(text: str, brands: Iterable[Brand],
                     citations: Iterable[Citation] | None = None) -> List[Mention]:
    """Count brand mentions and rank brands by where each is first named.

    Aliases are matched longest-first so "Lumen Metrics" is not double counted
    as both "Lumen Metrics" and "Lumen".
    """
    cited_domains = {c.domain for c in (citations or [])}
    rows = []
    for brand in brands:
        spans: list[tuple[int, int]] = []
        for alias in sorted(brand.aliases, key=len, reverse=True):
            for m in _alias_pattern(alias).finditer(text):
                if any(s <= m.start() < e for s, e in spans):
                    continue
                spans.append((m.start(), m.end()))
        if not spans:
            continue
        rows.append(
            Mention(
                brand=brand.name,
                mentions=len(spans),
                char_offset=min(s for s, _ in spans),
                rank=0,
                cited=any(d in cited_domains for d in brand.domains),
            )
        )

    rows.sort(key=lambda r: r.char_offset)
    return [
        Mention(r.brand, r.mentions, r.char_offset, i, r.cited)
        for i, r in enumerate(rows, start=1)
    ]
