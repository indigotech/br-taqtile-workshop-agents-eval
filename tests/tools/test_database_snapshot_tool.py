import sqlite3

from app.core.tools import ToolRegistry
from app.data.accommodation_data_source import AccommodationDataSource
from app.data.city_data_source import CityDataSource
from app.data.reservation_data_source import ReservationDataSource
from app.data.user_data_source import UserDataSource
from app.tools.database_snapshot_tool import DatabaseSnapshotTool


class TestDatabaseSnapshotTool:
    def test_snapshot_covers_every_user_city_and_accommodation(
        self, connection: sqlite3.Connection
    ) -> None:
        registry = ToolRegistry(
            [
                DatabaseSnapshotTool(
                    UserDataSource(connection),
                    ReservationDataSource(connection),
                    CityDataSource(connection),
                    AccommodationDataSource(connection),
                )
            ]
        )

        execution = registry.execute("get_database_snapshot", {})

        assert execution.output is not None
        assert (
            [snapshot["user"]["id"] for snapshot in execution.output["users"]],
            [len(snapshot["reservations"]) for snapshot in execution.output["users"]],
            len(execution.output["cities"]),
            len(execution.output["accommodations"]),
        ) == ([1, 2, 3, 4], [2, 0, 1, 1], 8, 15)
