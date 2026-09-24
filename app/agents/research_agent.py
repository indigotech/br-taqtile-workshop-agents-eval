from google.genai import types

from app.core.agent import Agent
from app.core.gemini import GeminiClient

_SYSTEM_PROMPT = """\
Você é o agente de pesquisa de um planejador de rolês de fim de semana.

Pesquise na internet eventos, atrações e restaurantes no destino e nas datas
pedidas. Para cada sugestão, informe nome, tipo, bairro ou endereço, faixa de
preço estimada em reais e dia/horário quando for um evento. Leve em conta as
preferências e restrições informadas nas instruções.

Traga apenas lugares e eventos que apareceram na pesquisa; se não encontrar algo
para as datas pedidas, diga isso em vez de inventar.
"""


def build_research_agent(gemini: GeminiClient) -> Agent:
    return Agent(
        name="research",
        system_prompt=_SYSTEM_PROMPT,
        gemini=gemini,
        builtin_tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.4,
    )
