"""File-backed store: newline-delimited JSON, one file per table.

Mirrors the ClickHouse table layout in sql/clickhouse/schema.sql so the same
pipeline runs in CI with no database.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

TABLES = ("raw_answers", "answer_citations", "brand_mentions")


class OfflineStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, table: str) -> Path:
        if table not in TABLES:
            raise ValueError(f"unknown table: {table}")
        return self.root / f"{table}.jsonl"

    def insert(self, table: str, rows: Iterable[Dict]) -> int:
        n = 0
        with open(self._path(table), "a", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
                n += 1
        return n

    def read(self, table: str) -> List[Dict]:
        path = self._path(table)
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def dedupe(self, table: str, keys: Iterable[str]) -> int:
        """Keep the last row per key tuple — the offline equivalent of
        ReplacingMergeTree, so a re-run is idempotent."""
        keys = list(keys)
        latest: Dict[tuple, Dict] = {}
        for row in self.read(table):
            latest[tuple(row[k] for k in keys)] = row
        rows = list(latest.values())
        with open(self._path(table), "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        return len(rows)
