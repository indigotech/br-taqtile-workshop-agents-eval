from app.evals.evaluators.base import EvaluationResult, Evaluator
from app.evals.records import RunRecord
from app.evals.report import evaluate_records, summarize
from tests.helpers import run_record


class PassesOddRunsEvaluator(Evaluator):
    name = "odd_runs"

    def evaluate(self, record: RunRecord) -> EvaluationResult:
        passed = record.run_index % 2 == 1
        return EvaluationResult(passed=passed, score=float(passed), reason="")


class BrokenEvaluator(Evaluator):
    name = "broken"

    def evaluate(self, record: RunRecord) -> EvaluationResult:
        raise KeyError("missing")


class TestEvaluateRecords:
    def test_each_evaluator_judges_each_run_with_its_traces(self) -> None:
        evaluations = evaluate_records(
            [run_record(run_index=1), run_record(run_index=2)],
            [PassesOddRunsEvaluator()],
        )

        assert [
            (
                evaluation.run_index,
                evaluation.session_id,
                evaluation.trace_ids,
                evaluation.result.passed,
            )
            for evaluation in evaluations
        ] == [
            (1, "eval-paraty-1", ["trace-paraty-1-0"], True),
            (2, "eval-paraty-2", ["trace-paraty-2-0"], False),
        ]

    def test_evaluator_that_raises_fails_only_its_own_result(self) -> None:
        [evaluation] = evaluate_records([run_record()], [BrokenEvaluator()])

        assert evaluation.result.model_dump() == {
            "passed": False,
            "score": 0.0,
            "reason": "evaluator error: 'missing'",
        }


class TestSummarize:
    def test_pass_at_k_needs_one_success_and_pass_hat_k_needs_all(self) -> None:
        records = [
            run_record(case_id="flaky", run_index=1),
            run_record(case_id="flaky", run_index=2),
            run_record(case_id="flaky", run_index=3),
            run_record(case_id="solid", run_index=1),
            run_record(case_id="solid", run_index=3),
            run_record(case_id="broken", run_index=2),
        ]

        summaries = summarize(evaluate_records(records, [PassesOddRunsEvaluator()]))

        assert [
            (
                summary.case_id,
                summary.passed_runs,
                summary.runs,
                summary.pass_at_k,
                summary.pass_hat_k,
            )
            for summary in summaries
        ] == [
            ("broken", 0, 1, False, False),
            ("flaky", 2, 3, True, False),
            ("solid", 2, 2, True, True),
        ]
        assert summaries[1].mean_score == 2 / 3
