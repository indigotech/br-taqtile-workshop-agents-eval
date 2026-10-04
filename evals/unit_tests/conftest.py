# Runs against the real configuration in .env, the opposite of tests/conftest.py.
# app.core.config builds its settings at import time and fails without
# MODEL_API_KEY, so the key is checked before anything under app/ is imported:
# without a real one, every test file here is skipped without being imported,
# and the fixtures import from app/ only inside their bodies.
import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from dotenv import load_dotenv

from evals.unit_tests.model_api_key import missing_model_api_key_reason
from evals.unit_tests.tracing import unit_test_trace

if TYPE_CHECKING:
    from app.core.model_client import ModelClient

# Without override, a variable already set in the shell wins over .env, the
# same precedence pydantic-settings gives them.
load_dotenv(Path(__file__).parents[2] / ".env")
_SKIP_REASON = missing_model_api_key_reason(os.environ.get("MODEL_API_KEY"))

_DEFAULT_RUNS = 3


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """A freshly seeded database per test, in a temporary file — never the
    local data/planner.db."""
    from app.data.database import connect, reset_database

    database_path = tmp_path / "test.db"
    reset_database(database_path)
    database_connection = connect(database_path)
    yield database_connection
    database_connection.close()


@pytest.fixture
def model_client() -> "ModelClient":
    from app.core.model_client import ModelClient

    return ModelClient()


@pytest.fixture(scope="session")
def runs() -> int:
    """How many times a test repeats a stochastic check: RUNS, default 3."""
    runs = int(os.environ.get("RUNS") or _DEFAULT_RUNS)
    if runs < 1:
        raise pytest.UsageError(f"RUNS must be at least 1, got {runs}")
    return runs


@pytest.fixture(autouse=True)
def trace_each_test(request: pytest.FixtureRequest) -> Iterator[None]:
    with unit_test_trace(request.node.nodeid):
        yield


@pytest.fixture(scope="session", autouse=True)
def flush_traces() -> Iterator[None]:
    from app.core.observability import flush

    yield
    flush()


def pytest_report_header() -> str | None:
    return f"evals/unit_tests pulados: {_SKIP_REASON}" if _SKIP_REASON else None


def pytest_pycollect_makemodule(
    module_path: Path, parent: pytest.Collector
) -> pytest.Collector | None:
    if _SKIP_REASON is None:
        return None
    return _SkippedTestFile.from_parent(parent, path=module_path)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    # Before anyone writes a test here there is no file to report as skipped,
    # and pytest would turn the reason already printed in the header into a
    # "no tests collected" failure.
    if _SKIP_REASON and exitstatus == pytest.ExitCode.NO_TESTS_COLLECTED:
        session.exitstatus = pytest.ExitCode.OK


class _SkippedTestFile(pytest.File):
    def collect(self) -> Iterator[pytest.Item]:
        pytest.skip(_SKIP_REASON or "")
