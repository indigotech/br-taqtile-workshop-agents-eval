from app.core.tools import ToolRegistry
from app.tools.calculate_budget_tool import CalculateBudgetTool


def _registry() -> ToolRegistry:
    return ToolRegistry([CalculateBudgetTool()])


class TestCalculateBudgetTool:
    def test_trip_within_the_budget_informed_for_it(self) -> None:
        execution = _registry().execute(
            "calculate_budget",
            {
                "budget_amount": 1500,
                "items": [
                    {"category": "lodging", "description": "2 noites", "amount": 760},
                    {"category": "food", "description": "refeições", "amount": 300.5},
                    {"category": "transport", "description": "ônibus", "amount": 180},
                ],
            },
        )

        assert execution.output == {
            "currency": "BRL",
            "total_cost": 1240.5,
            "total_budget": 1500.0,
            "total_remaining": 259.5,
            "fits_total_budget": True,
            "categories": [
                {"category": "lodging", "cost": 760.0},
                {"category": "food", "cost": 300.5},
                {"category": "activities", "cost": 0.0},
                {"category": "transport", "cost": 180.0},
                {"category": "other", "cost": 0.0},
            ],
        }

    def test_trip_over_the_budget(self) -> None:
        execution = _registry().execute(
            "calculate_budget",
            {
                "budget_amount": 600,
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

    def test_missing_budget_is_rejected_instead_of_guessed(self) -> None:
        execution = _registry().execute(
            "calculate_budget",
            {"items": [{"category": "food", "description": "jantar", "amount": 90}]},
        )

        assert execution.error is not None
        assert execution.error.startswith("Invalid arguments:")

    def test_negative_amount_is_rejected(self) -> None:
        execution = _registry().execute(
            "calculate_budget",
            {
                "budget_amount": 1500,
                "items": [{"category": "food", "description": "x", "amount": -5}],
            },
        )

        assert execution.error is not None
        assert execution.error.startswith("Invalid arguments:")
