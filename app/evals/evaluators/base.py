from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, Field

from app.evals.records import RunRecord


class EvaluationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    passed: bool
    score: float = Field(ge=0, le=1)
    reason: str


class Evaluator(ABC):
    """Judges one run of one dataset case.

    `evaluate` gets the whole `RunRecord` — the resolved case with its
    references, and per turn the response, the delegations to each specialist,
    the reservations created and the trace id — and returns a pass/fail with a
    0-1 score and a human-readable reason."""

    name: str

    @abstractmethod
    def evaluate(self, record: RunRecord) -> EvaluationResult: ...
