from datetime import datetime, timedelta, timezone

from lav.quality import (check_coverage, check_drift, check_freshness,
                         check_parse_yield, exit_code)

NOW = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)


def _answer(pid, mid, hours_old=1, status="ok"):
    return {"answer_key": f"{pid}-{mid}", "prompt_id": pid, "model_id": mid,
            "status": status,
            "collected_at": (NOW - timedelta(hours=hours_old)).isoformat()}


def test_coverage_flags_missing_pairs():
    findings = check_coverage([_answer("p1", "m1")], 2, 2)
    assert findings and findings[0].severity == "P0"
    assert "3 of 4" in findings[0].message


def test_coverage_passes_when_complete():
    rows = [_answer(p, m) for p in ("p1", "p2") for m in ("m1", "m2")]
    assert check_coverage(rows, 2, 2) == []


def test_freshness_flags_stale_run():
    assert check_freshness([_answer("p1", "m1", hours_old=40)], now=NOW)[0].severity == "P0"


def test_freshness_passes_on_recent_run():
    assert check_freshness([_answer("p1", "m1", hours_old=2)], now=NOW) == []


def test_empty_run_is_p0():
    assert check_freshness([], now=NOW)[0].check == "freshness"


def test_parse_yield_flags_silent_parser_failure():
    answers = [_answer(f"p{i}", "m1") for i in range(4)]
    findings = check_parse_yield(answers, [{"answer_key": "p0-m1"}])
    assert findings and findings[0].severity == "P1"


def test_parse_yield_passes_with_enough_mentions():
    answers = [_answer(f"p{i}", "m1") for i in range(4)]
    mentions = [{"answer_key": f"p{i}-m1"} for i in range(3)]
    assert check_parse_yield(answers, mentions) == []


def test_drift_flags_large_swing():
    cur = [{"scope": "all", "brand": "Northwind Analytics", "mention_rate": 0.9}]
    prev = [{"scope": "all", "brand": "Northwind Analytics", "mention_rate": 0.4}]
    assert check_drift(cur, prev)[0].check == "drift"


def test_drift_ignores_new_brand():
    cur = [{"scope": "all", "brand": "Pathline", "mention_rate": 0.9}]
    assert check_drift(cur, []) == []


def test_exit_code_precedence():
    from lav.quality import Finding
    assert exit_code([]) == 0
    assert exit_code([Finding("drift", "P1", "x")]) == 1
    assert exit_code([Finding("drift", "P1", "x"), Finding("coverage", "P0", "y")]) == 2
