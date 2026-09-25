"""Run every registered evaluator (app/evals/evaluators/__init__.py) over the
results of `make run-dataset`, print a per-case report with pass@k and pass^k,
and save evaluations.jsonl next to the results. With --langfuse, each score is
also attached to the run's Langfuse session."""

import argparse
import logging
from pathlib import Path

from app.core.logging import setup_logging
from app.core.observability import flush, get_langfuse
from app.evals.evaluators import EVALUATORS
from app.evals.records import RunRecord
from app.evals.report import CaseSummary, Evaluation, evaluate_records, summarize

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    arguments = _parse_arguments()
    records = [
        RunRecord.model_validate_json(line)
        for line in arguments.results.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    evaluations = evaluate_records(records, EVALUATORS)

    output_path = arguments.results.with_name("evaluations.jsonl")
    output_path.write_text(
        "".join(evaluation.model_dump_json() + "\n" for evaluation in evaluations),
        encoding="utf-8",
    )
    _print_report(summarize(evaluations))
    print(f"\nAvaliações em {output_path}")

    if arguments.langfuse:
        _send_scores(evaluations)


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--langfuse", action="store_true")
    return parser.parse_args()


def _print_report(summaries: list[CaseSummary]) -> None:
    for evaluator in sorted({summary.evaluator for summary in summaries}):
        rows = [summary for summary in summaries if summary.evaluator == evaluator]
        print(f"\n== {evaluator} ==")
        print(f"{'caso':<34} {'passou':>8} {'score':>6} {'pass@k':>7} {'pass^k':>7}")
        for row in rows:
            print(
                f"{row.case_id:<34} {row.passed_runs:>4}/{row.runs:<3}"
                f" {row.mean_score:>6.2f} {_mark(row.pass_at_k):>7} {_mark(row.pass_hat_k):>7}"
            )
        runs = sum(row.runs for row in rows)
        passed = sum(row.passed_runs for row in rows)
        print(
            f"total: {passed}/{runs} execuções ({passed / runs:.0%}),"
            f" pass@k em {sum(row.pass_at_k for row in rows)}/{len(rows)} casos,"
            f" pass^k em {sum(row.pass_hat_k for row in rows)}/{len(rows)} casos"
        )


def _mark(value: bool) -> str:
    return "sim" if value else "não"


def _send_scores(evaluations: list[Evaluation]) -> None:
    langfuse = get_langfuse()
    for evaluation in evaluations:
        langfuse.create_score(
            session_id=evaluation.session_id,
            name=evaluation.evaluator,
            value=evaluation.result.score,
            data_type="NUMERIC",
            comment=evaluation.result.reason,
        )
    flush()
    logger.info("Sent %s scores to Langfuse", len(evaluations))


if __name__ == "__main__":
    main()
