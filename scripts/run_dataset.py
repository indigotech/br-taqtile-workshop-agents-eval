"""Run every dataset case N times against the real model API and save one
RunRecord per run to evals/runs/<timestamp>/results.jsonl — the input for
`make evaluate`. Each run makes a dozen or more model calls, so mind the quota:
narrow with --cases while iterating."""

import argparse
import logging
from datetime import UTC, date, datetime
from pathlib import Path

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.model_client import ModelClient
from app.core.observability import flush, get_langfuse
from app.core.terminal import Style, paint
from app.data.http import build_http_client
from app.evals.dataset import load_dataset
from app.evals.records import RunRecord
from app.evals.runner import run_case

logger = logging.getLogger(__name__)

_DEFAULT_DATASET = Path("evals/dataset.jsonl")
_RUNS_DIRECTORY = Path("evals/runs")


def main() -> None:
    setup_logging()
    arguments = _parse_arguments()
    today = date.today()
    cases = load_dataset(arguments.dataset, today)
    if arguments.cases:
        wanted = set(arguments.cases.split(","))
        cases = [case for case in cases if case.id in wanted]
    if not cases:
        raise SystemExit("No dataset case matched --cases")

    output_directory = _RUNS_DIRECTORY / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    output_directory.mkdir(parents=True)
    results_path = output_directory / "results.jsonl"
    model_client = ModelClient()
    try:
        with build_http_client() as http_client, results_path.open("w") as results:
            for case in cases:
                for run_index in range(1, arguments.runs + 1):
                    logger.info(
                        "Running %s (%s/%s)", case.id, run_index, arguments.runs
                    )
                    record = run_case(case, run_index, model_client, http_client, today)
                    results.write(record.model_dump_json() + "\n")
                    results.flush()
                    _print_summary(record)
    finally:
        flush()
    print(f"\n{paint(f'Resultados em {results_path}', Style.SYSTEM)}")
    print(paint(f"Avalie com: make evaluate RESULTS={results_path}", Style.SYSTEM))


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=1, help="Runs per case")
    parser.add_argument("--cases", default="", help="Comma-separated case ids")
    parser.add_argument("--dataset", type=Path, default=_DEFAULT_DATASET)
    return parser.parse_args()


def _print_summary(record: RunRecord) -> None:
    agents = [call.name for turn in record.turns for call in turn.agent_calls]
    reservations = sum(len(turn.reservations_created) for turn in record.turns)
    errors = [turn.error for turn in record.turns if turn.error]
    summary = paint(
        f"  {record.case.id} #{record.run_index}: {len(record.turns)} turno(s),"
        f" agentes={agents}, reservas={reservations}",
        Style.AUXILIARY,
    )
    print(summary + (paint(f", ERRO={errors[0]}", Style.API_ERROR) if errors else ""))
    if settings.LANGFUSE_TRACING_ENABLED:
        for turn in record.turns:
            if turn.trace_id:
                trace_url = get_langfuse().get_trace_url(trace_id=turn.trace_id)
                print(paint(f"    trace: {trace_url}", Style.AUXILIARY))


if __name__ == "__main__":
    main()
