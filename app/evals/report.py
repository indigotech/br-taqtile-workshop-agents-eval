import logging
from collections.abc import Sequence
from itertools import groupby

from pydantic import BaseModel, ConfigDict

from app.evals.evaluators.base import EvaluationResult, Evaluator
from app.evals.records import RunRecord

logger = logging.getLogger(__name__)


class Evaluation(BaseModel):
    model_config = ConfigDict(frozen=True)

    evaluator: str
    case_id: str
    run_index: int
    session_id: str
    trace_ids: list[str]
    result: EvaluationResult


class CaseSummary(BaseModel):
    """How one evaluator judged the k runs of one case. `pass_at_k` holds when
    at least one run passed (capability) and `pass_hat_k` when every run passed
    (consistency)."""

    model_config = ConfigDict(frozen=True)

    evaluator: str
    case_id: str
    runs: int
    passed_runs: int
    mean_score: float
    pass_at_k: bool
    pass_hat_k: bool


def evaluate_records(
    records: Sequence[RunRecord], evaluators: Sequence[Evaluator]
) -> list[Evaluation]:
    return [
        Evaluation(
            evaluator=evaluator.name,
            case_id=record.case.id,
            run_index=record.run_index,
            session_id=record.session_id,
            trace_ids=[turn.trace_id for turn in record.turns if turn.trace_id],
            result=_safe_evaluate(evaluator, record),
        )
        for evaluator in evaluators
        for record in records
    ]


def summarize(evaluations: Sequence[Evaluation]) -> list[CaseSummary]:
    def key(evaluation: Evaluation) -> tuple[str, str]:
        return evaluation.evaluator, evaluation.case_id

    summaries: list[CaseSummary] = []
    for (evaluator, case_id), group in groupby(sorted(evaluations, key=key), key=key):
        results = [evaluation.result for evaluation in group]
        passed_runs = sum(result.passed for result in results)
        summaries.append(
            CaseSummary(
                evaluator=evaluator,
                case_id=case_id,
                runs=len(results),
                passed_runs=passed_runs,
                mean_score=sum(result.score for result in results) / len(results),
                pass_at_k=passed_runs > 0,
                pass_hat_k=passed_runs == len(results),
            )
        )
    return summaries


def _safe_evaluate(evaluator: Evaluator, record: RunRecord) -> EvaluationResult:
    # A buggy evaluator should cost its own column, not the whole report.
    try:
        return evaluator.evaluate(record)
    except Exception as error:
        logger.exception(
            "Evaluator %s failed on %s #%s",
            evaluator.name,
            record.case.id,
            record.run_index,
        )
        return EvaluationResult(
            passed=False, score=0.0, reason=f"evaluator error: {error}"
        )
