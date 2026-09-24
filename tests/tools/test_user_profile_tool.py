import sqlite3

from app.core.tools import ToolRegistry
from app.data.user_data_source import UserDataSource
from app.tools.user_profile_tool import GetUserProfileTool


class TestGetUserProfileTool:
    def test_profile_bundles_user_budget_and_preferences(
        self, connection: sqlite3.Connection
    ) -> None:
        registry = ToolRegistry([GetUserProfileTool(UserDataSource(connection))])

        execution = registry.execute("get_user_profile", {"user_id": 2})

        assert execution.output == {
            "found": True,
            "user": {
                "id": 2,
                "name": "Bruno Lima",
                "email": "bruno@example.com",
                "home_city_id": 1,
            },
            "budget": {
                "user_id": 2,
                "total_amount": 600.0,
                "lodging_amount": 250.0,
                "food_amount": 250.0,
                "activities_amount": 100.0,
                "currency": "BRL",
            },
            "preferences": [
                {"category": "food", "value": "comida de boteco"},
                {"category": "activity", "value": "shows de música ao vivo"},
                {"category": "restriction", "value": "sem carro"},
            ],
        }

    def test_unknown_user_is_reported_as_not_found(
        self, connection: sqlite3.Connection
    ) -> None:
        registry = ToolRegistry([GetUserProfileTool(UserDataSource(connection))])

        execution = registry.execute("get_user_profile", {"user_id": 999})

        assert execution.output == {
            "found": False,
            "user": None,
            "budget": None,
            "preferences": [],
        }
