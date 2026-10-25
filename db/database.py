import sqlite3

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "business_trips.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"
QUERIES_PATH = BASE_DIR / "sql" / "queries.sql"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Открыть подключение и обязательно закрыть его."""
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        yield connection
    finally:
        connection.close()


def load_queries() -> dict[str, str]:
    """Прочитать именованные запросы из SQL-файла."""
    text = QUERIES_PATH.read_text(encoding="utf-8")
    queries = {}

    for block in text.split("-- name: ")[1:]:
        name, sql = block.split("\n", 1)
        queries[name.strip()] = sql.strip()

    return queries


def fetch_all(
    query_name: str,
    parameters: tuple = (),
) -> list[sqlite3.Row]:
    """Выполнить SELECT и получить все строки."""
    query = load_queries()[query_name]

    with get_connection() as connection:
        cursor = connection.execute(query, parameters)
        return cursor.fetchall()