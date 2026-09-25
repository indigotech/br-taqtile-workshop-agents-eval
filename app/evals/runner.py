import logging
import sqlite3
import tempfile
import time
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
from google.genai import errors, types

from app.agents.orchestrator_agent import build_orchestrator_agent
from app.core.agent import Agent, user_message
from app.core.gemini import GeminiClient
from app.core.observability import current_trace_id, observe_turn
from app.core.tools import ToolExecution
from app.data.database import connect, reset_database
from app.data.reservation_data_source import ReservationDataSource
from app.evals.dataset import EvalCase
from app.evals.records import AgentCall, RunRecord, TurnRecord

logger = logging.getLogger(__name__)


def run_case(
    case: EvalCase,
    run_index: int,
    gemini: GeminiClient,
    http_client: httpx.Client,
    today: date,
) -> RunRecord:
    """Play every message of the case against the orchestrator, on a freshly
    seeded throwaway database so runs never see each other's reservations.

    A Gemini API error ends the run early and is recorded on its turn instead
    of aborting the whole dataset."""
    started_at = datetime.now(UTC)
    session_id = f"eval-{case.id}-{run_index}-{uuid.uuid4().hex[:8]}"
    with tempfile.TemporaryDirectory() as directory:
        database_path = Path(directory) / "eval.db"
        reset_database(database_path)
        connection = connect(database_path)
        try:
            turns = _play_messages(
                case, session_id, gemini, http_client, today, connection
            )
        finally:
            connection.close()
    return RunRecord(
        case=case,
        run_index=run_index,
        session_id=session_id,
        run_date=today,
        started_at=started_at,
        model=gemini.model,
        turns=turns,
    )


def _play_messages(
    case: EvalCase,
    session_id: str,
    gemini: GeminiClient,
    http_client: httpx.Client,
    today: date,
    connection: sqlite3.Connection,
) -> list[TurnRecord]:
    agent = build_orchestrator_agent(
        gemini, connection, http_client, case.user_id, today
    )
    reservation_data_source = ReservationDataSource(connection)
    history: list[types.Content] = []
    turns: list[TurnRecord] = []
    for message in case.messages:
        turn, history = _play_turn(
            agent, case, session_id, message, history, reservation_data_source
        )
        turns.append(turn)
        if turn.error is not None:
            break
    return turns


def _play_turn(
    agent: Agent,
    case: EvalCase,
    session_id: str,
    message: str,
    history: list[types.Content],
    reservation_data_source: ReservationDataSource,
) -> tuple[TurnRecord, list[types.Content]]:
    reservation_ids_before = {
        reservation.id
        for reservation in reservation_data_source.list_by_user(case.user_id)
    }
    started_at = time.perf_counter()
    with observe_turn(
        session_id=session_id,
        user_id=str(case.user_id),
        user_message=message,
        tags=["dataset", case.id],
    ) as span:
        trace_id = current_trace_id()
        try:
            result = agent.run([*history, user_message(message)])
        except errors.APIError as error:
            logger.error("Case %s stopped by a Gemini API error: %s", case.id, error)
            span.update(output=str(error), level="ERROR")
            failed_turn = TurnRecord(
                user_message=message,
                response="",
                agent_calls=[],
                reservations_created=[],
                trace_id=trace_id,
                latency_seconds=time.perf_counter() - started_at,
                stopped_by_iteration_limit=False,
                error=f"{error.code} {error.status}: {error.message}",
            )
            return failed_turn, history
        span.update(output=result.text)

    turn = TurnRecord(
        user_message=message,
        response=result.text,
        agent_calls=[_agent_call(execution) for execution in result.tool_executions],
        reservations_created=[
            reservation
            for reservation in reservation_data_source.list_by_user(case.user_id)
            if reservation.id not in reservation_ids_before
        ],
        trace_id=trace_id,
        latency_seconds=time.perf_counter() - started_at,
        stopped_by_iteration_limit=result.stopped_by_iteration_limit,
        error=None,
    )
    return turn, result.contents


def _agent_call(execution: ToolExecution) -> AgentCall:
    output = execution.output or {}
    response = output.get("response")
    return AgentCall(
        name=execution.name,
        instructions=str(execution.arguments.get("instructions", "")),
        response=str(response) if response is not None else None,
        error=execution.error,
    )
