from app.evals.evaluators import EVALUATORS
from app.evals.evaluators.completed_without_errors_evaluator import (
    CompletedWithoutErrorsEvaluator,
)
from tests.helpers import run_record


class TestCompletedWithoutErrorsEvaluator:
    def test_every_message_answered(self) -> None:
        result = CompletedWithoutErrorsEvaluator().evaluate(
            run_record(responses=("proposta", "roteiro"))
        )

        assert result.model_dump() == {
            "passed": True,
            "score": 1.0,
            "reason": "2 de 2 mensagens respondidas",
        }

    def test_run_cut_short_by_an_api_error(self) -> None:
        result = CompletedWithoutErrorsEvaluator().evaluate(
            run_record(responses=("proposta", ""), error="429 RESOURCE_EXHAUSTED")
        )

        assert (result.passed, result.score) == (False, 0.5)


class TestRegistry:
    def test_evaluator_names_are_unique(self) -> None:
        names = [evaluator.name for evaluator in EVALUATORS]

        assert len(names) == len(set(names))
