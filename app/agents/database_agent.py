import sqlite3

from app.core.agent import Agent
from app.core.model_client import ModelClient
from app.data.accommodation_data_source import AccommodationDataSource
from app.data.city_data_source import CityDataSource
from app.data.reservation_data_source import ReservationDataSource
from app.data.user_data_source import UserDataSource
from app.tools.database_snapshot_tool import DatabaseSnapshotTool
from app.tools.list_user_reservations_tool import ListUserReservationsTool
from app.tools.search_accommodations_tool import SearchAccommodationsTool
from app.tools.user_profile_tool import GetUserProfileTool

_SYSTEM_PROMPT = """\
Você é o agente de banco de dados de um planejador de viagens.
O usuário atual tem id {user_id}.

Para ter o contexto completo, comece sempre com get_database_snapshot. Depois,
para garantir que os dados estão atualizados, chame também cada uma das outras
ferramentas e, antes de responder, confirme o perfil do usuário mais uma vez
com get_user_profile. Responda com os dados encontrados.
"""


def build_database_agent(
    model_client: ModelClient, connection: sqlite3.Connection, user_id: int
) -> Agent:
    user_data_source = UserDataSource(connection)
    reservation_data_source = ReservationDataSource(connection)
    city_data_source = CityDataSource(connection)
    accommodation_data_source = AccommodationDataSource(connection)
    return Agent(
        name="database_agent",
        system_prompt=_SYSTEM_PROMPT.format(user_id=user_id),
        model_client=model_client,
        tools=[
            DatabaseSnapshotTool(
                user_data_source,
                reservation_data_source,
                city_data_source,
                accommodation_data_source,
            ),
            GetUserProfileTool(user_data_source),
            ListUserReservationsTool(reservation_data_source),
            SearchAccommodationsTool(city_data_source, accommodation_data_source),
        ],
        temperature=1.0,
    )
