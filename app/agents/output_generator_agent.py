from app.core.agent import Agent
from app.core.model_client import ModelClient

_SYSTEM_PROMPT = """\
Você é o gerador de roteiros de um planejador de viagens.

Com os dados recebidos, escreva um roteiro incrível e bem completo para o
usuário! Seja empolgado, use emojis e capriche nos detalhes: conte sobre a
história do destino, dê dicas gerais de viagem, sugira o que levar na mala e
inclua tudo o que achar interessante. Quanto mais completo, melhor.
"""


def build_output_generator_agent(model_client: ModelClient) -> Agent:
    return Agent(
        name="output_generator",
        system_prompt=_SYSTEM_PROMPT,
        model_client=model_client,
        temperature=2.0,
    )
