import sqlite3
from datetime import date

import httpx

from app.agents.action_agent import build_action_agent
from app.agents.budget_analyst_agent import build_budget_analyst_agent
from app.agents.database_agent import build_database_agent
from app.agents.input_interpreter_agent import build_input_interpreter_agent
from app.agents.output_generator_agent import build_output_generator_agent
from app.agents.public_data_agent import build_public_data_agent
from app.agents.research_agent import build_research_agent
from app.core.agent import Agent
from app.core.agent_tool import AgentTool
from app.core.model_client import ModelClient
from app.data.user_data_source import UserDataSource

_SYSTEM_PROMPT = """\
Você é o orquestrador de um planejador de rolês de fim de semana e conversa
diretamente com o usuário. O usuário atual tem id {user_id}. Hoje é {today}.

Use os agentes especialistas para montar a viagem do usuário. Um caminho que
costuma funcionar: entender o pedido, ver os dados do usuário e as hospedagens,
dar uma olhada no clima e no orçamento se fizer sentido, e procurar o que tem
de bom para fazer e comer no destino.

Para agilizar para o usuário, assim que tiver as informações principais já
reserve a hospedagem mais bem avaliada com execute_action e entregue o roteiro
final com generate_itinerary.
"""


def build_orchestrator_agent(
    model_client: ModelClient,
    connection: sqlite3.Connection,
    http_client: httpx.Client,
    user_id: int,
    today: date,
) -> Agent:
    return Agent(
        name="orchestrator",
        system_prompt=_SYSTEM_PROMPT.format(user_id=user_id, today=today.isoformat()),
        model_client=model_client,
        tools=[
            AgentTool(
                build_input_interpreter_agent(model_client, today),
                name="interpret_request",
                description=(
                    "Extrai do pedido do usuário destino, datas, número de "
                    "pessoas, orçamento e preferências."
                ),
            ),
            AgentTool(
                build_database_agent(model_client, connection, user_id),
                name="query_database",
                description=(
                    "Consulta o banco: perfil, orçamento e preferências do "
                    "usuário, histórico de reservas e hospedagens do catálogo."
                ),
            ),
            AgentTool(
                build_public_data_agent(model_client, http_client),
                name="query_public_data",
                description="Consulta previsão do tempo e feriados do destino.",
            ),
            AgentTool(
                build_research_agent(model_client),
                name="search_web",
                description="Sugere eventos, atrações e restaurantes no destino.",
            ),
            AgentTool(
                build_budget_analyst_agent(
                    model_client, UserDataSource(connection), user_id
                ),
                name="analyze_budget",
                description=(
                    "Verifica se a viagem cabe no orçamento do usuário e sugere "
                    "cortes quando não cabe."
                ),
            ),
            AgentTool(
                build_action_agent(model_client, connection, user_id),
                name="execute_action",
                description="Reserva a hospedagem e registra a decisão.",
            ),
            AgentTool(
                build_output_generator_agent(model_client),
                name="generate_itinerary",
                description="Escreve o roteiro final da viagem para o usuário.",
            ),
        ],
        temperature=1.0,
        max_iterations=15,
    )
