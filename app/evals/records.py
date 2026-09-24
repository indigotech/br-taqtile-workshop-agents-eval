from datetime import date, datetime

from pydantic import BaseModel

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
    run_date: date
    started_at: datetime
    model: str
    turns: list[TurnRecord]
