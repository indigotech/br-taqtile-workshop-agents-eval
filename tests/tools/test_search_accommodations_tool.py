import sqlite3

from app.core.tools import ToolRegistry
from app.data.accommodation_data_source import AccommodationDataSource
from app.data.city_data_source import CityDataSource
from app.tools.search_accommodations_tool import SearchAccommodationsTool


def _registry(connection: sqlite3.Connection) -> ToolRegistry:
    return ToolRegistry(
        [
            SearchAccommodationsTool(
                CityDataSource(connection), AccommodationDataSource(connection)
            )
        ]
    )


class TestSearchAccommodationsTool:
    def test_places_in_a_catalog_city(self, connection: sqlite3.Connection) -> None:
        execution = _registry(connection).execute(
            "search_accommodations",
            {"city_name": "paraty", "guests": 2, "max_nightly_price": 300},
        )

        assert execution.output is not None
        assert (
            execution.output["city_found"],
            execution.output["city"]["name"],
            [
                accommodation["name"]
                for accommodation in execution.output["accommodations"]
            ],
            execution.output["available_cities"],
        ) == (True, "Paraty", ["Casa Caiçara"], [])

    def test_unknown_city_lists_the_catalog_cities(
        self, connection: sqlite3.Connection
    ) -> None:
        execution = _registry(connection).execute(
            "search_accommodations", {"city_name": "Gramado", "guests": 2}
        )

        assert execution.output is not None
        assert (
            execution.output["city_found"],
            execution.output["accommodations"],
            len(execution.output["available_cities"]),
        ) == (False, [], 8)

    def test_zero_guests_is_rejected_before_reaching_the_database(
        self, connection: sqlite3.Connection
    ) -> None:
        execution = _registry(connection).execute(
            "search_accommodations", {"city_name": "Paraty", "guests": 0}
        )

        assert execution.error is not None
        assert execution.error.startswith("Invalid arguments:")
