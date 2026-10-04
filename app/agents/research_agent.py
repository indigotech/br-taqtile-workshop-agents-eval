from app.core.agent import Agent
from app.core.model_client import ModelClient

_SYSTEM_PROMPT = """\
Você é o agente de pesquisa de um planejador de rolês de fim de semana.

Sugira os melhores eventos, atrações e restaurantes do destino. Traga sempre
pelo menos 5 restaurantes e 3 eventos, cada um com nome, endereço, faixa de
preço e horário, para o usuário ter bastante opção.
"""


def build_research_agent(model_client: ModelClient) -> Agent:
    return Agent(
        name="research",
        system_prompt=_SYSTEM_PROMPT,
        model_client=model_client,
        temperature=0.9,
    )
