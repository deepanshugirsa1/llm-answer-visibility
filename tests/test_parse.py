from lav.config import Brand
from lav.parse import extract_citations, extract_mentions, normalize_domain

BRANDS = [
    Brand("Northwind Analytics", ["Northwind Analytics", "Northwind"], ["northwind.example"]),
    Brand("Lumen Metrics", ["Lumen Metrics", "Lumen"], ["lumenmetrics.example"]),
    Brand("Pathline", ["Pathline"], ["pathline.example"]),
]


def test_normalize_domain_strips_www():
    assert normalize_domain("https://www.Northwind.example/docs") == "northwind.example"


def test_citations_ordered_and_deduped():
    text = ("See [docs](https://northwind.example/docs) and https://lumenmetrics.example/pricing. "
            "Again: https://northwind.example/docs")
    cites = extract_citations(text)
    assert [c.domain for c in cites] == ["northwind.example", "lumenmetrics.example"]
    assert [c.position for c in cites] == [1, 2]


def test_trailing_punctuation_not_part_of_url():
    cites = extract_citations("Read https://pathline.example/guide.")
    assert cites[0].url == "https://pathline.example/guide"


def test_longest_alias_wins_no_double_count():
    text = "Lumen Metrics is strong. Lumen also integrates well."
    m = {x.brand: x for x in extract_mentions(text, BRANDS)}
    assert m["Lumen Metrics"].mentions == 2


def test_word_boundary_blocks_substring_match():
    assert extract_mentions("Pathlines are not Pathline", BRANDS)[0].mentions == 1
    assert extract_mentions("Northwindy tooling", BRANDS) == []


def test_rank_follows_first_appearance():
    text = "Pathline leads here, though Northwind is close behind."
    ranks = {m.brand: m.rank for m in extract_mentions(text, BRANDS)}
    assert ranks == {"Pathline": 1, "Northwind Analytics": 2}


def test_cited_flag_links_brand_to_its_domain():
    text = "Northwind is best, see https://northwind.example/docs. Lumen is cheaper."
    cites = extract_citations(text)
    by_brand = {m.brand: m for m in extract_mentions(text, BRANDS, cites)}
    assert by_brand["Northwind Analytics"].cited is True
    assert by_brand["Lumen Metrics"].cited is False


def test_case_insensitive_matching():
    assert extract_mentions("northwind analytics is fine", BRANDS)[0].brand == "Northwind Analytics"
