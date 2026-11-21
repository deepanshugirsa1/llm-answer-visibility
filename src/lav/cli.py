"""Command line entry point: run | report | check."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .collect import collect
from .config import load_brands, load_models, load_prompts
from .quality import (check_coverage, check_drift, check_freshness,
                      check_parse_yield, exit_code)
from .report import citation_rank, movement, share_of_voice
from .store import OfflineStore

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"


def _load():
    return (load_prompts(CONFIG / "prompts.yml"),
            load_models(CONFIG / "models.yml"),
            load_brands(CONFIG / "brands.yml"))


def cmd_run(args) -> int:
    prompts, models, brands = _load()
    store = OfflineStore(Path(args.data))
    answers, citations, mentions = collect(prompts, models, brands)
    store.insert("raw_answers", answers)
    store.insert("answer_citations", citations)
    store.insert("brand_mentions", mentions)
    store.dedupe("raw_answers", ["answer_key"])
    store.dedupe("answer_citations", ["answer_key", "position"])
    store.dedupe("brand_mentions", ["answer_key", "brand"])
    print(f"collected {len(answers)} answers, {len(citations)} citations, "
          f"{len(mentions)} brand mentions")
    return 0


def cmd_report(args) -> int:
    store = OfflineStore(Path(args.data))
    answers = store.read("raw_answers")
    mentions = store.read("brand_mentions")
    citations = store.read("answer_citations")
    out = {
        "share_of_voice": share_of_voice(answers, mentions),
        "share_of_voice_by_category": share_of_voice(answers, mentions, by_category=True),
        "citation_rank": citation_rank(citations),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    for row in out["share_of_voice"]:
        print(f"{row['brand']:<22} {row['mention_rate']:>7.1%}  "
              f"avg rank {row['avg_rank']:>4}  cited {row['cited_rate']:>6.1%}")
    print(f"\nwrote {args.out}")
    return 0


def cmd_check(args) -> int:
    prompts, models, _ = _load()
    store = OfflineStore(Path(args.data))
    answers = store.read("raw_answers")
    mentions = store.read("brand_mentions")

    findings = []
    findings += check_freshness(answers, now=datetime.now(timezone.utc))
    findings += check_coverage(answers, len(prompts), len(models))
    findings += check_parse_yield(answers, mentions)

    baseline = Path(args.baseline)
    if baseline.exists():
        previous = json.loads(baseline.read_text(encoding="utf-8")).get("share_of_voice", [])
        findings += check_drift(share_of_voice(answers, mentions), previous)

    for f in findings:
        print(f"[{f.severity}] {f.check}: {f.message}")
    if not findings:
        print("all checks passed")
    return exit_code(findings)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="lav", description=__doc__)
    p.add_argument("--data", default="data", help="offline store directory")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="collect answers and land rows").set_defaults(fn=cmd_run)
    r = sub.add_parser("report", help="write share-of-voice and citation marts")
    r.add_argument("--out", default="data/report.json")
    r.set_defaults(fn=cmd_report)
    c = sub.add_parser("check", help="run quality gates (exit 2 on P0, 1 on P1)")
    c.add_argument("--baseline", default="data/baseline.json")
    c.set_defaults(fn=cmd_check)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
