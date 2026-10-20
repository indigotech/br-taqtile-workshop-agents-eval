from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from app.data.models import ReservationDetails
from app.evals.dataset import EvalCase


class AgentCall(BaseModel):
    """One delegation from the orchestrator to a specialist agent."""

    name: str
    instructions: str
    response: str | None
    error: str | None


class TurnRecord(BaseModel):
    user_message: str
    response: str
    agent_calls: list[AgentCall]
    reservations_created: list[ReservationDetails]
    trace_id: str | None
    latency_seconds: float
    stopped_by_iteration_limit: bool
    error: str | None


class RunRecord(BaseModel):
    case: EvalCase
    run_index: int
    session_id: str
    run_date: date
    started_at: datetime
    model: str
    turns: list[TurnRecord]


def save_run_records(path: Path, records: list[RunRecord]) -> None:
    """Write the records as one indented JSON array, like evals/dataset.json, so
    it reads well on screen in class. The runner rewrites the whole file after
    every run, so an interrupted dataset run keeps every record finished so far."""
    path.write_bytes(_RUN_RECORDS.dump_json(records, indent=4) + b"\n")


def load_run_records(path: Path) -> list[RunRecord]:
    return _RUN_RECORDS.validate_json(path.read_bytes())


_RUN_RECORDS = TypeAdapter(list[RunRecord])
