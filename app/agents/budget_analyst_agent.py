from app.core.agent import Agent
from app.core.model_client import ModelClient
from app.data.user_data_source import UserDataSource
from app.tools.calculate_budget_tool import CalculateBudgetTool
from app.tools.user_profile_tool import GetUserProfileTool

_SYSTEM_PROMPT = """\
Você é o analista de orçamento de um planejador de rolês de fim de semana.
O usuário atual tem id {user_id}.

A partir do plano descrito nas instruções, responda se a viagem cabe no
orçamento do usuário:
1. Liste cada gasto com um valor estimado em reais (converta para reais o que
   for cobrado em moeda local): hospedagem (preço por noite vezes o número de
   noites), alimentação (por pessoa e por dia), atividades e transporte.
2. Chame calculate_budget com esses itens para fazer as contas; não some de
   cabeça.
3. Responda se cabe no total e em cada categoria. Se não couber, sugira cortes
   concretos (hospedagem mais barata, menos refeições fora, trocar atividade
   paga por gratuita) com a economia estimada de cada um.
"""


def build_budget_analyst_agent(
    model_client: ModelClient, user_data_source: UserDataSource, user_id: int
) -> Agent:
    return Agent(
        name="budget_analyst",
        system_prompt=_SYSTEM_PROMPT.format(user_id=user_id),
        model_client=model_client,
        tools=[
            GetUserProfileTool(user_data_source),
            CalculateBudgetTool(user_data_source),
        ],
        temperature=1.0,
    )
