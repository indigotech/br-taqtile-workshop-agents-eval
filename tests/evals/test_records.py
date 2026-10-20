import json
from datetime import UTC, date, datetime
from pathlib import Path

from app.evals.dataset import EvalCase, ExpectedTrip
from app.evals.records import RunRecord, load_run_records, save_run_records


class TestSaveRunRecords:
    def test_records_are_saved_as_an_indented_array_and_read_back(
        self, tmp_path: Path
    ) -> None:
        results_path = tmp_path / "results.json"
        records = [_record(run_index) for run_index in (1, 2)]

        save_run_records(results_path, records)

        text = results_path.read_text(encoding="utf-8")
        assert (
            text.startswith("[\n    {"),
            "São Paulo" in text,
            len(json.loads(text)),
            load_run_records(results_path),
        ) == (True, True, 2, records)


def _record(run_index: int) -> RunRecord:
    return RunRecord(
        case=EvalCase(
            id="c1",
            description="d",
            user_id=1,
            messages=["São Paulo dia 26/09"],
            expected_trip=ExpectedTrip(
                destination="São Paulo",
                start_date=date(2026, 9, 26),
                end_date=None,
                guests=2,
                budget_amount=None,
            ),
            required_agents=[],
            user_preferences=[],
            confirmation_message_index=None,
            max_lodging_total=None,
            reference_answer=None,
            itinerary_brief=None,
        ),
        run_index=run_index,
        session_id=f"eval-c1-{run_index}",
        run_date=date(2026, 9, 24),
        started_at=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
        model="gpt-6-luna",
        turns=[],
    )
