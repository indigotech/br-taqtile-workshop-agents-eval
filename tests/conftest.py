# Loaded before anything under app/ is imported: app.core.config builds its
# settings at import time, and test.env must win over a developer's .env (which
# would otherwise send test traces to Langfuse with real keys).
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "test.env", override=True)

import sqlite3  # noqa: E402
from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402

from app.data.database import connect, reset_database  # noqa: E402


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """A freshly seeded database per test, in a temporary file — never the
    local data/planner.db."""
    database_path = tmp_path / "test.db"
    reset_database(database_path)
    database_connection = connect(database_path)
    yield database_connection
    database_connection.close()
