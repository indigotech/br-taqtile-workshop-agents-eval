from app.evals.evaluators.base import EvaluationResult, Evaluator
from app.evals.evaluators.completed_without_errors_evaluator import (
    CompletedWithoutErrorsEvaluator,
)

# `make evaluate` runs every evaluator listed here. To add one: create a
# `*_evaluator.py` module in this package with an `Evaluator` subclass, then
# append an instance below.
EVALUATORS: list[Evaluator] = [
    CompletedWithoutErrorsEvaluator(),
]

__all__ = ["EVALUATORS", "EvaluationResult", "Evaluator"]
