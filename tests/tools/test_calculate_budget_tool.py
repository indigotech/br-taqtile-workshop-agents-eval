import sqlite3

from app.core.tools import ToolRegistry
from app.data.user_data_source import UserDataSource
from app.tools.calculate_budget_tool import CalculateBudgetTool


def _registry(connection: sqlite3.Connection) -> ToolRegistry:
    return ToolRegistry([CalculateBudgetTool(UserDataSource(connection))])


class TestCalculateBudgetTool:
    def test_trip_over_the_lodging_budget_but_within_the_total(
        self, connection: sqlite3.Connection
    ) -> None:
        execution = _registry(connection).execute(
            "calculate_budget",
            {
                "user_id": 1,
                "items": [
                    {"category": "lodging", "description": "2 noites", "amount": 760},
                    {"category": "food", "description": "refeições", "amount": 300.5},
                    {"category": "transport", "description": "ônibus", "amount": 180},
                ],
            },
        )

        assert execution.output == {
            "budget_found": True,
            "currency": "BRL",
            "total_cost": 1240.5,
            "total_budget": 1500.0,
            "total_remaining": 259.5,
            "fits_total_budget": True,
            "categories_over_budget": ["lodging"],
            "categories": [
                {
                    "category": "lodging",
                    "cost": 760.0,
                    "budget": 700.0,
                    "remaining": -60.0,
                },
                {
                    "category": "food",
                    "cost": 300.5,
                    "budget": 500.0,
                    "remaining": 199.5,
                },
                {
                    "category": "activities",
                    "cost": 0.0,
                    "budget": 300.0,
                    "remaining": 300.0,
                },
                {
                    "category": "transport",
                    "cost": 180.0,
                    "budget": None,
                    "remaining": None,
                },
                {"category": "other", "cost": 0.0, "budget": None, "remaining": None},
            ],
        }

    def test_trip_over_the_total_budget(self, connection: sqlite3.Connection) -> None:
        execution = _registry(connection).execute(
            "calculate_budget",
            {
                "user_id": 2,
                "items": [
                    {"category": "lodging", "description": "hotel", "amount": 610},
                ],
            },
        )

        assert execution.output is not None
        assert (
            execution.output["fits_total_budget"],
            execution.output["total_remaining"],
        ) == (False, -10.0)

    def test_user_without_budget_still_gets_the_totals(
        self, connection: sqlite3.Connection
    ) -> None:
        execution = _registry(connection).execute(
            "calculate_budget",
            {
                "user_id": 999,
                "items": [{"category": "food", "description": "jantar", "amount": 90}],
            },
        )

        assert execution.output is not None
        assert (
            execution.output["budget_found"],
            execution.output["total_cost"],
            execution.output["fits_total_budget"],
            execution.output["categories_over_budget"],
        ) == (False, 90.0, None, [])

    def test_negative_amount_is_rejected(self, connection: sqlite3.Connection) -> None:
        execution = _registry(connection).execute(
            "calculate_budget",
            {
                "user_id": 1,
                "items": [{"category": "food", "description": "x", "amount": -5}],
            },
        )

        assert execution.error is not None
        assert execution.error.startswith("Invalid arguments:")
