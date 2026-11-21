"""Share-of-voice and citation-rank aggregates.

These mirror the dbt marts in dbt/models/marts so the offline run and the
warehouse run produce the same numbers.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List


def share_of_voice(answers: List[Dict], mentions: List[Dict],
                   by_category: bool = False) -> List[Dict]:
    """mention_rate = answers naming the brand / answers that could have."""
    scope = lambda row: (row["category"],) if by_category else ("all",)  # noqa: E731
    totals: Dict[tuple, int] = defaultdict(int)
    for a in answers:
        if a["status"] == "ok":
            totals[scope(a)] += 1

    named: Dict[tuple, int] = defaultdict(int)
    rank_sum: Dict[tuple, int] = defaultdict(int)
    cited: Dict[tuple, int] = defaultdict(int)
    for m in mentions:
        k = (*scope(m), m["brand"])
        named[k] += 1
        rank_sum[k] += m["rank"]
        cited[k] += int(m["cited"])

    rows = []
    for key, count in sorted(named.items(), key=lambda kv: -kv[1]):
        *scope_key, brand = key
        total = totals[tuple(scope_key)] or 1
        rows.append({
            "scope": scope_key[0],
            "brand": brand,
            "answers_naming_brand": count,
            "answers_total": totals[tuple(scope_key)],
            "mention_rate": round(count / total, 4),
            "avg_rank": round(rank_sum[key] / count, 2),
            "cited_rate": round(cited[key] / count, 4),
        })
    return rows


def citation_rank(citations: List[Dict]) -> List[Dict]:
    counts: Dict[str, int] = defaultdict(int)
    pos_sum: Dict[str, int] = defaultdict(int)
    for c in citations:
        counts[c["domain"]] += 1
        pos_sum[c["domain"]] += c["position"]
    return [
        {"domain": d, "citations": n, "avg_position": round(pos_sum[d] / n, 2)}
        for d, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


def movement(current: List[Dict], previous: List[Dict]) -> List[Dict]:
    prev = {(r["scope"], r["brand"]): r["mention_rate"] for r in previous}
    rows = []
    for r in current:
        before = prev.get((r["scope"], r["brand"]))
        rows.append({
            "scope": r["scope"], "brand": r["brand"],
            "mention_rate": r["mention_rate"],
            "prev_mention_rate": before,
            "delta": None if before is None else round(r["mention_rate"] - before, 4),
        })
    return rows
