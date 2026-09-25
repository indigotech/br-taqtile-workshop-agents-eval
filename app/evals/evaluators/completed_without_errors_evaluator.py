from app.evals.evaluators.base import EvaluationResult, Evaluator
from app.evals.records import RunRecord


class CompletedWithoutErrorsEvaluator(Evaluator):
    """Example evaluator: every message of the case got a non-empty answer and
    no Gemini API error interrupted the run."""

    name = "completed_without_errors"

    def evaluate(self, record: RunRecord) -> EvaluationResult:
        answered = [
            turn
            for turn in record.turns
            if turn.error is None and turn.response.strip()
        ]
        total = len(record.case.messages)
        return EvaluationResult(
            passed=len(answered) == total,
            score=len(answered) / total,
            reason=f"{len(answered)} de {total} mensagens respondidas",
        )
