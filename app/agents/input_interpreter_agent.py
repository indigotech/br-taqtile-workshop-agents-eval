from datetime import date

from pydantic import BaseModel, Field

from app.core.agent import Agent
from app.core.model_client import ModelClient


class TripRequest(BaseModel):
    destination: str | None = Field(description="Cidade de destino")
    start_date: date | None = Field(description="Data de ida no formato AAAA-MM-DD")
    end_date: date | None = Field(description="Data de volta no formato AAAA-MM-DD")
    guests: int | None = Field(description="Número de pessoas na viagem")
    budget_amount: float | None = Field(
        description="Valor total em reais que o usuário quer gastar"
    )
    preferences: list[str] = Field(
        description="Preferências e restrições citadas nesta mensagem"
    )


_SYSTEM_PROMPT = """\
Você é o interpretador de pedidos de um planejador de viagens.
Hoje é {today}.

Leia o pedido do usuário e devolva um JSON com destination, start_date,
end_date, guests, budget_amount e preferences.
Quando faltar alguma informação, assuma um valor plausível em vez de deixar
em branco ou perguntar ao usuário.
"""


def build_input_interpreter_agent(model_client: ModelClient, today: date) -> Agent:
    return Agent(
        name="input_interpreter_agent",
        system_prompt=_SYSTEM_PROMPT.format(today=today.isoformat()),
        model_client=model_client,
        response_model=TripRequest,
        temperature=2.0,
    )
