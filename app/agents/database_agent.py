import sqlite3

from app.core.agent import Agent
from app.core.gemini import GeminiClient
from app.data.accommodation_data_source import AccommodationDataSource
from app.data.city_data_source import CityDataSource
from app.data.reservation_data_source import ReservationDataSource
from app.data.user_data_source import UserDataSource
from app.tools.list_user_reservations_tool import ListUserReservationsTool
from app.tools.search_accommodations_tool import SearchAccommodationsTool
from app.tools.user_profile_tool import GetUserProfileTool

_SYSTEM_PROMPT = """\
Você é o agente de banco de dados de um planejador de rolês de fim de semana.
O usuário atual tem id {user_id}.

Você responde com dados do banco:
- perfil do usuário: cidade, orçamento por categoria e preferências;
- histórico de reservas do usuário;
- hospedagens do catálogo (airbnb e hotel) numa cidade.

Use sempre as ferramentas; nunca invente dados que não vieram delas. Responda
de forma objetiva, listando os dados encontrados. Ao citar hospedagens, inclua
id, nome, tipo, bairro, preço por noite, capacidade e nota.
"""


def build_database_agent(
    gemini: GeminiClient, connection: sqlite3.Connection, user_id: int
) -> Agent:
    return Agent(
        name="database",
        system_prompt=_SYSTEM_PROMPT.format(user_id=user_id),
        gemini=gemini,
        tools=[
            GetUserProfileTool(UserDataSource(connection)),
            ListUserReservationsTool(ReservationDataSource(connection)),
            SearchAccommodationsTool(
                CityDataSource(connection), AccommodationDataSource(connection)
            ),
        ],
        temperature=0.2,
    )
