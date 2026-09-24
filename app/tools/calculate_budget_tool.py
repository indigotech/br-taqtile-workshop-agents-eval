from typing import Literal

from pydantic import BaseModel, Field

from app.core.tools import Tool
from app.data.models import Budget
from app.data.user_data_source import UserDataSource

CostCategory = Literal["lodging", "food", "activities", "transport", "other"]


class CostItem(BaseModel):
    category: CostCategory = Field(
        description=(
            "lodging (hospedagem), food (alimentação), activities (passeios e "
            "eventos), transport (transporte) ou other (outros)"
        )
    )
    description: str = Field(description="O que é o gasto, ex.: '2 noites no Chalé'")
    amount: float = Field(ge=0, description="Valor total do item em reais")


class CalculateBudgetInput(BaseModel):
    user_id: int = Field(description="Id do usuário cujo orçamento será usado")
    items: list[CostItem] = Field(description="Todos os gastos estimados da viagem")


class CategoryBalance(BaseModel):
    category: CostCategory
    cost: float
    budget: float | None
    remaining: float | None


class CalculateBudgetOutput(BaseModel):
    budget_found: bool
    currency: str
    total_cost: float
    total_budget: float | None
    total_remaining: float | None
    fits_total_budget: bool | None
    categories_over_budget: list[CostCategory]
    categories: list[CategoryBalance]


class CalculateBudgetTool(Tool[CalculateBudgetInput, CalculateBudgetOutput]):
    name = "calculate_budget"
    description = (
        "Soma os gastos estimados por categoria e compara com o orçamento do "
        "usuário (total e por categoria: hospedagem, alimentação e atividades). "
        "Transporte e outros contam só no total. Faz as contas; não estima preços."
    )
    input_model = CalculateBudgetInput
    output_model = CalculateBudgetOutput

    def __init__(self, user_data_source: UserDataSource) -> None:
        self.user_data_source = user_data_source

    def run(self, arguments: CalculateBudgetInput) -> CalculateBudgetOutput:
        budget = self.user_data_source.get_budget(arguments.user_id)
        categories = [
            _balance(category, arguments.items, budget)
            for category in ("lodging", "food", "activities", "transport", "other")
        ]
        total_cost = round(sum(item.amount for item in arguments.items), 2)
        total_budget = budget.total_amount if budget else None
        return CalculateBudgetOutput(
            budget_found=budget is not None,
            currency=budget.currency if budget else "BRL",
            total_cost=total_cost,
            total_budget=total_budget,
            total_remaining=(
                round(total_budget - total_cost, 2)
                if total_budget is not None
                else None
            ),
            fits_total_budget=(
                total_cost <= total_budget if total_budget is not None else None
            ),
            categories_over_budget=[
                balance.category
                for balance in categories
                if balance.remaining is not None and balance.remaining < 0
            ],
            categories=categories,
        )


def _balance(
    category: CostCategory, items: list[CostItem], budget: Budget | None
) -> CategoryBalance:
    cost = round(sum(item.amount for item in items if item.category == category), 2)
    category_budget = _category_budget(category, budget)
    return CategoryBalance(
        category=category,
        cost=cost,
        budget=category_budget,
        remaining=(
            round(category_budget - cost, 2) if category_budget is not None else None
        ),
    )


def _category_budget(category: CostCategory, budget: Budget | None) -> float | None:
    if budget is None:
        return None
    match category:
        case "lodging":
            return budget.lodging_amount
        case "food":
            return budget.food_amount
        case "activities":
            return budget.activities_amount
        case _:
            return None
