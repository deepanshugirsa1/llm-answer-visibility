"""Quality gates over a run: coverage, freshness, parse yield, drift.

Severity follows the same convention as a paging policy: P0 pages, P1 opens a
ticket, P2 is informational. `exit_code` turns findings into a CI result.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Finding:
    check: str
    severity: str   # P0 | P1 | P2
    message: str


def _parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def check_coverage(answers: List[Dict], expected_prompts: int, expected_models: int) -> List[Finding]:
    expected = expected_prompts * expected_models
    actual = len({(a["prompt_id"], a["model_id"]) for a in answers})
    if actual < expected:
        return [Finding("coverage", "P0",
                        f"{expected - actual} of {expected} prompt-model pairs missing")]
    return []


def check_freshness(answers: List[Dict], max_age_hours: int = 26,
                    now: Optional[datetime] = None) -> List[Finding]:
    if not answers:
        return [Finding("freshness", "P0", "no answers collected")]
    now = now or datetime.now(timezone.utc)
    newest = max(_parse_ts(a["collected_at"]) for a in answers)
    age = now - newest
    if age > timedelta(hours=max_age_hours):
        return [Finding("freshness", "P0",
                        f"newest answer is {age.total_seconds() / 3600:.1f}h old "
                        f"(limit {max_age_hours}h)")]
    return []


def check_parse_yield(answers: List[Dict], mentions: List[Dict],
                      min_rate: float = 0.5) -> List[Finding]:
    """A parser that silently stops matching looks like a brand disappearing.
    Guard it: most answers should yield at least one mention."""
    ok = [a for a in answers if a["status"] == "ok"]
    if not ok:
        return [Finding("parse_yield", "P0", "no successful answers to parse")]
    with_mentions = len({m["answer_key"] for m in mentions})
    rate = with_mentions / len(ok)
    if rate < min_rate:
        return [Finding("parse_yield", "P1",
                        f"only {rate:.0%} of answers produced a brand mention "
                        f"(floor {min_rate:.0%}) — check alias config before trusting the marts")]
    return []


def check_drift(current: List[Dict], previous: List[Dict],
                max_delta: float = 0.35) -> List[Finding]:
    prev = {(r["scope"], r["brand"]): r["mention_rate"] for r in previous}
    findings = []
    for r in current:
        before = prev.get((r["scope"], r["brand"]))
        if before is None:
            continue
        delta = r["mention_rate"] - before
        if abs(delta) > max_delta:
            findings.append(Finding(
                "drift", "P1",
                f"{r['brand']} mention rate moved {delta:+.0%} in {r['scope']} "
                f"— verify before reporting"))
    return findings


def exit_code(findings: List[Finding]) -> int:
    if any(f.severity == "P0" for f in findings):
        return 2
    if any(f.severity == "P1" for f in findings):
        return 1
    return 0
