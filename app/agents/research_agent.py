from app.core.agent import Agent
from app.core.gemini import GeminiClient

_SYSTEM_PROMPT = """\
Você é o agente de pesquisa de um planejador de rolês de fim de semana.

Sugira os melhores eventos, atrações e restaurantes do destino. Traga sempre
pelo menos 5 restaurantes e 3 eventos, cada um com nome, endereço, faixa de
preço e horário, para o usuário ter bastante opção.
"""


def build_research_agent(gemini: GeminiClient) -> Agent:
    return Agent(
        name="research",
        system_prompt=_SYSTEM_PROMPT,
        gemini=gemini,
        temperature=0.9,
    )
