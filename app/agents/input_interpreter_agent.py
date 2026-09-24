from datetime import date

from pydantic import BaseModel, Field

from app.core.agent import Agent
from app.core.gemini import GeminiClient


class TripRequest(BaseModel):
    destination: str | None = Field(
        description="Cidade de destino, ou null se o usuário não disse"
    )
    start_date: date | None = Field(
        description="Data de ida no formato AAAA-MM-DD, ou null"
    )
    end_date: date | None = Field(
        description="Data de volta no formato AAAA-MM-DD, ou null"
    )
    guests: int | None = Field(description="Número de pessoas na viagem, ou null")
    budget_amount: float | None = Field(
        description="Valor total em reais que o usuário disse querer gastar, ou null"
    )
    preferences: list[str] = Field(
        description="Preferências e restrições citadas nesta mensagem"
    )
    missing_information: list[str] = Field(
        description="O que ainda falta perguntar ao usuário para planejar a viagem"
    )


_SYSTEM_PROMPT = """\
Você é o interpretador de pedidos de um planejador de rolês de fim de semana.
Hoje é {today}.

Leia o pedido do usuário e devolva um JSON com destination, start_date,
end_date, guests, budget_amount, preferences e missing_information.
As datas podem vir como o usuário falou (ex.: "03/10", "sábado que vem" ou
2026-10-03). Se quiser, explique brevemente como interpretou o pedido.
"""


def build_input_interpreter_agent(gemini: GeminiClient, today: date) -> Agent:
    return Agent(
        name="input_interpreter",
        system_prompt=_SYSTEM_PROMPT.format(today=today.isoformat()),
        gemini=gemini,
        temperature=0.9,
    )
