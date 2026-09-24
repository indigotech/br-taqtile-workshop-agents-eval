import sqlite3
from pathlib import Path

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")
_SEED_PATH = Path(__file__).with_name("seed.sql")


def connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    # SQLite ships with foreign keys off for backwards compatibility.
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def reset_database(database_path: Path) -> None:
    """Delete the database file and rebuild it from schema.sql + seed.sql."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_path.unlink(missing_ok=True)
    connection = connect(database_path)
    try:
        connection.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.executescript(_SEED_PATH.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()
