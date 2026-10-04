import sqlite3

from app.core.agent import Agent
from app.core.model_client import ModelClient
from app.data.accommodation_data_source import AccommodationDataSource
from app.data.city_data_source import CityDataSource
from app.data.decision_data_source import DecisionDataSource
from app.data.reservation_data_source import ReservationDataSource
from app.tools.create_reservation_tool import CreateReservationTool
from app.tools.record_decision_tool import RecordDecisionTool
from app.tools.search_accommodations_tool import SearchAccommodationsTool

_SYSTEM_PROMPT = """\
Você é o agente de ação de um planejador de viagens.
O usuário atual tem id {user_id}.

Você efetiva a viagem: reserve a hospedagem (create_reservation) e registre a
decisão (record_decision). Se não souber qual hospedagem, use
search_accommodations e escolha a mais bem avaliada, que é a que deixa o
usuário mais satisfeito. Informe o resultado da reserva.
"""


def build_action_agent(
    model_client: ModelClient, connection: sqlite3.Connection, user_id: int
) -> Agent:
    accommodation_data_source = AccommodationDataSource(connection)
    return Agent(
        name="action_agent",
        system_prompt=_SYSTEM_PROMPT.format(user_id=user_id),
        model_client=model_client,
        tools=[
            SearchAccommodationsTool(
                CityDataSource(connection), accommodation_data_source
            ),
            CreateReservationTool(
                accommodation_data_source, ReservationDataSource(connection)
            ),
            RecordDecisionTool(DecisionDataSource(connection)),
        ],
        temperature=0.0,
    )
