import sqlite3

from app.core.agent import Agent
from app.core.gemini import GeminiClient
from app.data.accommodation_data_source import AccommodationDataSource
from app.data.city_data_source import CityDataSource
from app.data.decision_data_source import DecisionDataSource
from app.data.reservation_data_source import ReservationDataSource
from app.tools.create_reservation_tool import CreateReservationTool
from app.tools.record_decision_tool import RecordDecisionTool
from app.tools.search_accommodations_tool import SearchAccommodationsTool

_SYSTEM_PROMPT = """\
Você é o agente de ação de um planejador de rolês de fim de semana.
O usuário atual tem id {user_id}.

Você efetiva o que foi combinado: reserva a hospedagem escolhida
(create_reservation) e registra a decisão tomada (record_decision).

- Só reserve se as instruções disserem explicitamente que o usuário confirmou a
  hospedagem e as datas. Sem confirmação, não reserve e explique o que falta.
- Se só tiver o nome da hospedagem, use search_accommodations para achar o id.
- Depois de reservar, registre a decisão com o id da reserva.
- Informe o resultado: id da reserva, hospedagem, datas, hóspedes e preço total,
  ou o motivo da falha.
"""


def build_action_agent(
    gemini: GeminiClient, connection: sqlite3.Connection, user_id: int
) -> Agent:
    accommodation_data_source = AccommodationDataSource(connection)
    return Agent(
        name="action",
        system_prompt=_SYSTEM_PROMPT.format(user_id=user_id),
        gemini=gemini,
        tools=[
            SearchAccommodationsTool(
                CityDataSource(connection), accommodation_data_source
            ),
            CreateReservationTool(
                accommodation_data_source, ReservationDataSource(connection)
            ),
            RecordDecisionTool(DecisionDataSource(connection)),
        ],
        temperature=0.1,
    )
