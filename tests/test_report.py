from lav.report import citation_rank, movement, share_of_voice

ANSWERS = [{"answer_key": f"a{i}", "category": "comparison", "status": "ok"} for i in range(4)]
MENTIONS = [
    {"answer_key": "a0", "category": "comparison", "brand": "Northwind Analytics", "rank": 1, "cited": 1},
    {"answer_key": "a1", "category": "comparison", "brand": "Northwind Analytics", "rank": 3, "cited": 0},
    {"answer_key": "a2", "category": "comparison", "brand": "Pathline", "rank": 2, "cited": 1},
]


def test_mention_rate_divides_by_eligible_answers():
    rows = {r["brand"]: r for r in share_of_voice(ANSWERS, MENTIONS)}
    assert rows["Northwind Analytics"]["mention_rate"] == 0.5
    assert rows["Pathline"]["mention_rate"] == 0.25


def test_avg_rank_and_cited_rate():
    rows = {r["brand"]: r for r in share_of_voice(ANSWERS, MENTIONS)}
    assert rows["Northwind Analytics"]["avg_rank"] == 2.0
    assert rows["Northwind Analytics"]["cited_rate"] == 0.5


def test_citation_rank_orders_by_volume():
    cites = [{"domain": "a.example", "position": 1}, {"domain": "a.example", "position": 3},
             {"domain": "b.example", "position": 2}]
    ranked = citation_rank(cites)
    assert ranked[0]["domain"] == "a.example"
    assert ranked[0]["avg_position"] == 2.0


def test_movement_reports_delta_and_handles_new_brands():
    cur = share_of_voice(ANSWERS, MENTIONS)
    prev = [{"scope": "all", "brand": "Northwind Analytics", "mention_rate": 0.25}]
    rows = {r["brand"]: r for r in movement(cur, prev)}
    assert rows["Northwind Analytics"]["delta"] == 0.25
    assert rows["Pathline"]["delta"] is None
