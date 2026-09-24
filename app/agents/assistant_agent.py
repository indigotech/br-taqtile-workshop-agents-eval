from app.core.agent import Agent
from app.core.gemini import GeminiClient
from app.data.user_data_source import UserDataSource
from app.tools.user_profile_tool import GetUserProfileTool

# Provisório da Fase 0: um agente único só pra exercitar o fluxo ponta a ponta
# (CLI → loop de tools → SQLite → Langfuse). O orquestrador da Fase 1 o substitui.
_SYSTEM_PROMPT = """\
Você é um assistente que ajuda a planejar rolês e viagens de fim de semana.
O usuário atual tem id {user_id}. Use as ferramentas disponíveis para consultar
o perfil dele quando precisar de orçamento ou preferências.
Responda em português.
"""


def build_assistant_agent(
    gemini: GeminiClient, user_data_source: UserDataSource, user_id: int
) -> Agent:
    return Agent(
        name="assistant",
        system_prompt=_SYSTEM_PROMPT.format(user_id=user_id),
        gemini=gemini,
        tools=[GetUserProfileTool(user_data_source)],
    )
