import sqlite3
from typing import Any

from app.core.tools import ToolRegistry
from app.data.accommodation_data_source import AccommodationDataSource
from app.data.decision_data_source import DecisionDataSource
from app.data.reservation_data_source import ReservationDataSource
from app.tools.create_reservation_tool import CreateReservationTool
from app.tools.record_decision_tool import RecordDecisionTool


def _registry(connection: sqlite3.Connection) -> ToolRegistry:
    return ToolRegistry(
        [
            CreateReservationTool(
                AccommodationDataSource(connection), ReservationDataSource(connection)
            ),
            RecordDecisionTool(DecisionDataSource(connection)),
        ]
    )


def _reservation_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT user_id, accommodation_id, check_in, check_out, guests,"
        " total_price, status FROM reservations WHERE id > 4 ORDER BY id"
    ).fetchall()
    return [dict(row) for row in rows]


class TestCreateReservationTool:
    def test_reservation_is_priced_by_nights_and_persisted(
        self, connection: sqlite3.Connection
    ) -> None:
        execution = _registry(connection).execute(
            "create_reservation",
            {
                "user_id": 3,
                "accommodation_id": 4,
                "check_in": "2026-10-03",
                "check_out": "2026-10-05",
                "guests": 2,
            },
        )

        assert _reservation_rows(connection) == [
            {
                "user_id": 3,
                "accommodation_id": 4,
                "check_in": "2026-10-03",
                "check_out": "2026-10-05",
                "guests": 2,
                "total_price": 900.0,
                "status": "confirmed",
            }
        ]
        assert execution.output is not None
        assert (
            execution.output["created"],
            execution.output["reservation"]["id"],
            execution.output["reservation"]["accommodation_name"],
            execution.output["reservation"]["total_price"],
        ) == (True, 5, "Pousada do Porto", 900.0)

    def test_group_larger_than_the_place_is_refused_without_writing(
        self, connection: sqlite3.Connection
    ) -> None:
        execution = _registry(connection).execute(
            "create_reservation",
            {
                "user_id": 3,
                "accommodation_id": 4,
                "check_in": "2026-10-03",
                "check_out": "2026-10-05",
                "guests": 3,
            },
        )

        assert execution.output == {
            "created": False,
            "failure_reason": "Pousada do Porto fits at most 2 guests",
            "reservation": None,
        }
        assert _reservation_rows(connection) == []

    def test_unknown_accommodation_is_refused_without_writing(
        self, connection: sqlite3.Connection
    ) -> None:
        execution = _registry(connection).execute(
            "create_reservation",
            {
                "user_id": 3,
                "accommodation_id": 999,
                "check_in": "2026-10-03",
                "check_out": "2026-10-05",
                "guests": 1,
            },
        )

        assert execution.output is not None
        assert execution.output["failure_reason"] == "Accommodation 999 not found"
        assert _reservation_rows(connection) == []

    def test_check_out_before_check_in_is_rejected_as_invalid_arguments(
        self, connection: sqlite3.Connection
    ) -> None:
        execution = _registry(connection).execute(
            "create_reservation",
            {
                "user_id": 3,
                "accommodation_id": 4,
                "check_in": "2026-10-05",
                "check_out": "2026-10-05",
                "guests": 1,
            },
        )

        assert execution.error is not None
        assert "check_out must be after check_in" in execution.error
        assert _reservation_rows(connection) == []


class TestRecordDecisionTool:
    def test_decision_is_persisted_with_its_reservation(
        self, connection: sqlite3.Connection
    ) -> None:
        execution = _registry(connection).execute(
            "record_decision",
            {"user_id": 1, "summary": "Chalé em Campos", "reservation_id": 1},
        )

        row = connection.execute(
            "SELECT id, user_id, reservation_id, summary FROM decisions"
        ).fetchone()
        assert dict(row) == {
            "id": 1,
            "user_id": 1,
            "reservation_id": 1,
            "summary": "Chalé em Campos",
        }
        assert execution.output is not None
        assert execution.output["decision"]["id"] == 1
