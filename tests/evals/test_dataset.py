from datetime import date
from pathlib import Path

from app.evals.dataset import date_placeholders, load_dataset


class TestDatePlaceholders:
    def test_next_weekend_from_a_thursday(self) -> None:
        placeholders = date_placeholders(date(2026, 9, 24))

        assert placeholders == {
            "today": "2026-09-24",
            "today_br": "24/09",
            "next_saturday": "2026-09-26",
            "next_saturday_br": "26/09",
            "next_sunday": "2026-09-27",
            "next_sunday_br": "27/09",
            "saturday_in_5_weeks": "2026-10-31",
            "saturday_in_5_weeks_br": "31/10",
            "sunday_in_5_weeks": "2026-11-01",
            "sunday_in_5_weeks_br": "01/11",
        }

    def test_on_a_saturday_the_next_weekend_is_a_week_away(self) -> None:
        placeholders = date_placeholders(date(2026, 9, 26))

        assert placeholders["next_saturday"] == "2026-10-03"


class TestLoadDataset:
    def test_placeholders_are_resolved_before_validation(self, tmp_path: Path) -> None:
        dataset_path = tmp_path / "dataset.jsonl"
        dataset_path.write_text(
            '{"id": "c1", "description": "d", "user_id": 1,'
            ' "messages": ["Paraty dia {next_saturday_br}"],'
            ' "expected_trip": {"destination": "Paraty",'
            ' "start_date": "{next_saturday}", "end_date": "{next_sunday}", "guests": 2},'
            ' "required_agents": [], "user_preferences": [],'
            ' "confirmation_message_index": null, "max_lodging_total": null,'
            ' "reference_answer": null}\n\n',
            encoding="utf-8",
        )

        [case] = load_dataset(dataset_path, today=date(2026, 9, 24))

        assert (case.messages, case.expected_trip.model_dump()) == (
            ["Paraty dia 26/09"],
            {
                "destination": "Paraty",
                "start_date": date(2026, 9, 26),
                "end_date": date(2026, 9, 27),
                "guests": 2,
            },
        )

    def test_committed_dataset_is_valid(self) -> None:
        cases = load_dataset(Path("evals/dataset.jsonl"), today=date(2026, 9, 24))

        assert len({case.id for case in cases}) == len(cases) == 8
        for case in cases:
            assert case.confirmation_message_index is None or (
                case.confirmation_message_index < len(case.messages)
            )
