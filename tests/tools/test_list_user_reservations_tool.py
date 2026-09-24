import sqlite3

from app.core.tools import ToolRegistry
from app.data.reservation_data_source import ReservationDataSource
from app.tools.list_user_reservations_tool import ListUserReservationsTool


class TestListUserReservationsTool:
    def test_history_is_returned_through_the_registry(
        self, connection: sqlite3.Connection
    ) -> None:
        registry = ToolRegistry(
            [ListUserReservationsTool(ReservationDataSource(connection))]
        )

        execution = registry.execute("list_user_reservations", {"user_id": 3})

        assert execution.output == {
            "reservations": [
                {
                    "id": 3,
                    "accommodation_id": 8,
                    "accommodation_name": "Hotel Copacabana Mar",
                    "accommodation_kind": "hotel",
                    "city_name": "Rio de Janeiro",
                    "check_in": "2026-07-17",
                    "check_out": "2026-07-19",
                    "guests": 2,
                    "total_price": 1220.0,
                    "status": "confirmed",
                    "created_at": "2026-07-01 09:05:00",
                }
            ]
        }
