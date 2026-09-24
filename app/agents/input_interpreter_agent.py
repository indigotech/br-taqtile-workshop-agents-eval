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


_WEEKDAYS = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)

_SYSTEM_PROMPT = """\
Você é o interpretador de pedidos de um planejador de rolês de fim de semana.
Hoje é {weekday}, {today}.

Extraia do pedido do usuário: destino, datas de ida e volta, número de pessoas,
orçamento total (se ele citar um valor) e preferências. Converta datas relativas
("próximo fim de semana", "sexta que vem") em datas absolutas a partir de hoje;
"fim de semana" sem mais detalhes vai de sábado a domingo. Use null para o que
não foi dito e liste em missing_information o que falta para planejar
(destino, datas e número de pessoas são indispensáveis).

Responda apenas com o JSON pedido.
"""


def build_input_interpreter_agent(gemini: GeminiClient, today: date) -> Agent:
    return Agent(
        name="input_interpreter",
        system_prompt=_SYSTEM_PROMPT.format(
            weekday=_WEEKDAYS[today.weekday()], today=today.isoformat()
        ),
        gemini=gemini,
        response_model=TripRequest,
        temperature=0.1,
    )
