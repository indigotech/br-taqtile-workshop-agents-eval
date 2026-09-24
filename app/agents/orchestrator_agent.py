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
from app.core.gemini import GeminiClient
from app.data.user_data_source import UserDataSource

_SYSTEM_PROMPT = """\
Você é o orquestrador de um planejador de rolês de fim de semana e conversa
diretamente com o usuário. O usuário atual tem id {user_id}. Hoje é {today}.

Você não tem dados próprios: delegue cada parte do trabalho a um agente
especialista. Eles não veem a conversa, então passe nas instruções tudo o que
precisam (pedido, datas, destino, número de pessoas e dados já levantados).

Fluxo para um novo pedido de viagem:
1. interpret_request com o pedido do usuário (inclua o contexto das mensagens
   anteriores). Se faltar destino, datas ou número de pessoas, pergunte ao
   usuário e pare aqui.
2. query_database: orçamento e preferências do usuário e hospedagens
   disponíveis no destino para o número de pessoas.
3. query_public_data: previsão do tempo para as datas e feriados no período.
4. search_web: eventos e restaurantes no destino e nas datas, levando em conta
   preferências e restrições do usuário.
5. analyze_budget: se a viagem cabe no orçamento, com a hospedagem sugerida e
   as estimativas de alimentação, atividades e transporte.
6. Apresente ao usuário uma proposta curta (hospedagem com preço, clima,
   destaques e veredito do orçamento) e pergunte se pode reservar.

Quando o usuário confirmar a reserva:
7. execute_action dizendo explicitamente que o usuário confirmou, com
   hospedagem (id), datas e número de pessoas.
8. generate_itinerary com todos os dados levantados e o resultado da reserva,
   e responda ao usuário exatamente com o roteiro gerado.

Para perguntas simples fora desse fluxo, chame só o agente necessário.
"""


def build_orchestrator_agent(
    gemini: GeminiClient,
    connection: sqlite3.Connection,
    http_client: httpx.Client,
    user_id: int,
    today: date,
) -> Agent:
    return Agent(
        name="orchestrator",
        system_prompt=_SYSTEM_PROMPT.format(user_id=user_id, today=today.isoformat()),
        gemini=gemini,
        tools=[
            AgentTool(
                build_input_interpreter_agent(gemini, today),
                name="interpret_request",
                description=(
                    "Extrai do pedido do usuário destino, datas, número de "
                    "pessoas, orçamento e preferências, em JSON."
                ),
            ),
            AgentTool(
                build_database_agent(gemini, connection, user_id),
                name="query_database",
                description=(
                    "Consulta o banco: perfil, orçamento e preferências do "
                    "usuário, histórico de reservas e hospedagens do catálogo."
                ),
            ),
            AgentTool(
                build_public_data_agent(gemini, http_client),
                name="query_public_data",
                description="Consulta previsão do tempo e feriados.",
            ),
            AgentTool(
                build_research_agent(gemini),
                name="search_web",
                description=(
                    "Pesquisa na internet eventos, atrações e restaurantes no "
                    "destino e nas datas."
                ),
            ),
            AgentTool(
                build_budget_analyst_agent(gemini, UserDataSource(connection), user_id),
                name="analyze_budget",
                description=(
                    "Verifica se a viagem cabe no orçamento do usuário e sugere "
                    "cortes quando não cabe."
                ),
            ),
            AgentTool(
                build_action_agent(gemini, connection, user_id),
                name="execute_action",
                description=(
                    "Reserva a hospedagem e registra a decisão. Só use depois "
                    "que o usuário confirmar."
                ),
            ),
            AgentTool(
                build_output_generator_agent(gemini),
                name="generate_itinerary",
                description="Escreve o roteiro final da viagem para o usuário.",
            ),
        ],
        temperature=0.3,
        max_iterations=15,
    )
