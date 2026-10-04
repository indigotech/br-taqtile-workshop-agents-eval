from typing import Literal

from pydantic import BaseModel, Field

from app.core.tools import Tool

CostCategory = Literal["lodging", "food", "activities", "transport", "other"]


class CostItem(BaseModel):
    category: CostCategory = Field(
        description=(
            "lodging (hospedagem), food (alimentação), activities (passeios e "
            "eventos), transport (transporte) ou other (outros)"
        )
    )
    description: str = Field(description="O que é o gasto, ex.: '2 noites no Chalé'")
    amount: float = Field(
        ge=0,
        description=(
            "Valor total do item em reais; gastos em moeda estrangeira vão "
            "convertidos para reais"
        ),
    )


class CalculateBudgetInput(BaseModel):
    budget_amount: float = Field(
        gt=0,
        description=(
            "Orçamento total desta viagem em reais, como o usuário informou na conversa"
        ),
    )
    items: list[CostItem] = Field(description="Todos os gastos estimados da viagem")


class CategoryCost(BaseModel):
    category: CostCategory
    cost: float


class CalculateBudgetOutput(BaseModel):
    currency: str
    total_cost: float
    total_budget: float
    total_remaining: float
    fits_total_budget: bool
    categories: list[CategoryCost]


class CalculateBudgetTool(Tool[CalculateBudgetInput, CalculateBudgetOutput]):
    name = "calculate_budget"
    description = (
        "Soma os gastos estimados por categoria e compara o total com o "
        "orçamento que o usuário informou para esta viagem. Faz as contas; não "
        "estima preços."
    )
    input_model = CalculateBudgetInput
    output_model = CalculateBudgetOutput

    def run(self, arguments: CalculateBudgetInput) -> CalculateBudgetOutput:
        total_cost = round(sum(item.amount for item in arguments.items), 2)
        return CalculateBudgetOutput(
            currency="BRL",
            total_cost=total_cost,
            total_budget=arguments.budget_amount,
            total_remaining=round(arguments.budget_amount - total_cost, 2),
            fits_total_budget=total_cost <= arguments.budget_amount,
            categories=[
                _category_cost(category, arguments.items)
                for category in ("lodging", "food", "activities", "transport", "other")
            ],
        )


def _category_cost(category: CostCategory, items: list[CostItem]) -> CategoryCost:
    return CategoryCost(
        category=category,
        cost=round(sum(item.amount for item in items if item.category == category), 2),
    )
