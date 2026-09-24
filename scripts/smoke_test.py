"""End-to-end run against the real Gemini API: a weekend request, then a
confirmation, on a throwaway database. Exits non-zero when no reservation is
written. Needs GEMINI_API_KEY in .env; costs a few dozen model calls."""

import logging
import sqlite3
import sys
import tempfile
import uuid
from datetime import date
from pathlib import Path

from google.genai import types

from app.agents.orchestrator_agent import build_orchestrator_agent
from app.core.agent import user_message
from app.core.config import settings
from app.core.gemini import GeminiClient
from app.core.logging import setup_logging
from app.core.observability import current_trace_id, flush, get_langfuse, observe_turn
from app.data.database import connect, reset_database
from app.data.http import build_http_client

logger = logging.getLogger(__name__)

_USER_ID = 1
_MESSAGES = (
    "Quero passar o próximo fim de semana em Paraty com meu namorado. "
    "Curtimos comida japonesa e trilhas.",
    "Pode reservar a hospedagem que você sugeriu.",
)


def main() -> None:
    setup_logging()
    with tempfile.TemporaryDirectory() as directory:
        database_path = Path(directory) / "smoke.db"
        reset_database(database_path)
        connection = connect(database_path)
        try:
            succeeded = _run_conversation(connection)
        finally:
            connection.close()
            flush()
    sys.exit(0 if succeeded else 1)


def _run_conversation(connection: sqlite3.Connection) -> bool:
    reservations_before = _count_reservations(connection)
    session_id = f"smoke-{uuid.uuid4()}"
    history: list[types.Content] = []
    with build_http_client() as http_client:
        agent = build_orchestrator_agent(
            GeminiClient(), connection, http_client, _USER_ID, date.today()
        )
        for message in _MESSAGES:
            print(f"\nusuário> {message}")
            with observe_turn(
                session_id=session_id, user_id=str(_USER_ID), user_message=message
            ) as span:
                result = agent.run([*history, user_message(message)])
                span.update(output=result.text)
                trace_id = current_trace_id()
            history = result.contents
            print(f"\nplanejador> {result.text}")
            print(
                f"  agentes chamados: {[execution.name for execution in result.tool_executions]}"
            )
            if settings.LANGFUSE_TRACING_ENABLED and trace_id:
                print(f"  trace: {get_langfuse().get_trace_url(trace_id=trace_id)}")

    new_reservations = _count_reservations(connection) - reservations_before
    if new_reservations == 0:
        logger.error("Smoke test failed: no reservation was written")
        return False
    logger.info("Smoke test passed: %s reservation(s) written", new_reservations)
    return True


def _count_reservations(connection: sqlite3.Connection) -> int:
    count: int = connection.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    return count


if __name__ == "__main__":
    main()
