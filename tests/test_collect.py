from datetime import datetime, timezone

from lav.collect import answer_key, collect
from lav.config import Brand, Model, Prompt
from lav.store import OfflineStore

PROMPTS = [Prompt("p1", "comparison", "Best analytics platform?"),
           Prompt("p2", "research", "Who are the major vendors?")]
MODELS = [Model("model-a", "A", "offline"), Model("model-b", "B", "offline")]
BRANDS = [Brand("Northwind Analytics", ["Northwind Analytics", "Northwind"], ["northwind.example"]),
          Brand("Lumen Metrics", ["Lumen Metrics", "Lumen"], ["lumenmetrics.example"]),
          Brand("Castellan Data", ["Castellan Data", "Castellan"], ["castellan.example"]),
          Brand("Pathline", ["Pathline"], ["pathline.example"])]
AT = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)


def test_collect_covers_every_prompt_model_pair():
    answers, _, _ = collect(PROMPTS, MODELS, BRANDS, collected_at=AT)
    assert len({(a["prompt_id"], a["model_id"]) for a in answers}) == 4


def test_offline_provider_is_deterministic():
    first, _, _ = collect(PROMPTS, MODELS, BRANDS, collected_at=AT)
    second, _, _ = collect(PROMPTS, MODELS, BRANDS, collected_at=AT)
    assert [a["answer_text"] for a in first] == [a["answer_text"] for a in second]


def test_every_answer_yields_mentions_and_citations():
    answers, citations, mentions = collect(PROMPTS, MODELS, BRANDS, collected_at=AT)
    keys = {a["answer_key"] for a in answers}
    assert {m["answer_key"] for m in mentions} == keys
    assert {c["answer_key"] for c in citations} == keys


def test_answer_key_is_stable_and_unique():
    assert answer_key("r1", "p1", "m1") == answer_key("r1", "p1", "m1")
    assert answer_key("r1", "p1", "m1") != answer_key("r1", "p1", "m2")


def test_rerun_is_idempotent_after_dedupe(tmp_path):
    store = OfflineStore(tmp_path)
    for _ in range(2):
        answers, citations, mentions = collect(PROMPTS, MODELS, BRANDS, collected_at=AT)
        store.insert("raw_answers", answers)
        store.insert("brand_mentions", mentions)
    assert len(store.read("raw_answers")) == 8          # duplicated on purpose
    assert store.dedupe("raw_answers", ["answer_key"]) == 4
    assert store.dedupe("brand_mentions", ["answer_key", "brand"]) == len(
        {(m["answer_key"], m["brand"]) for m in mentions})
