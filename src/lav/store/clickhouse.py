"""ClickHouse store.

Written against sql/clickhouse/schema.sql. Requires `clickhouse-connect`;
see the README for what has and has not been exercised against a live server.
"""
from __future__ import annotations

from typing import Dict, Iterable, List


class ClickHouseStore:
    def __init__(self, host: str = "localhost", port: int = 8123,
                 database: str = "lav", user: str = "default", password: str = ""):
        try:
            import clickhouse_connect
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ImportError(
                "clickhouse-connect is required for the ClickHouse store; "
                "use OfflineStore to run without a database"
            ) from exc
        self._client = clickhouse_connect.get_client(
            host=host, port=port, database=database, username=user, password=password
        )
        self.database = database

    def insert(self, table: str, rows: Iterable[Dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        columns = list(rows[0].keys())
        data: List[list] = [[row[c] for c in columns] for row in rows]
        self._client.insert(table, data, column_names=columns)
        return len(rows)

    def read(self, table: str) -> List[Dict]:
        result = self._client.query(f"SELECT * FROM {table}")
        return [dict(zip(result.column_names, row)) for row in result.result_rows]

    def optimize(self, table: str) -> None:
        """Force a merge so ReplacingMergeTree dedupe is visible immediately."""
        self._client.command(f"OPTIMIZE TABLE {table} FINAL")
