"""Base da atividade: o roteiro é comparado com uma referência pelos bigramas
(pares de palavras seguidas) que eles têm em comum. Os espaços das duas
atividades estão marcados abaixo do teste."""

import re
from itertools import pairwise

import pytest

from app.agents.output_generator_agent import build_output_generator_agent
from app.core.agent import user_message
from app.core.model_client import ModelClient
from evals.unit_tests.tracing import unit_test_trace

INSTRUCTIONS = """\
Escreva o roteiro final da viagem.
Destino: Paraty (RJ). Datas: sábado 10/10/2026 a domingo 11/10/2026. 2 pessoas.
Hospedagem: Pousada do Porto (hotel), Centro Histórico. Reserva nº 5 confirmada,
total de R$ 450,00 (1 noite).
Clima: sábado 24 °C, 10% de chuva; domingo 22 °C, 60% de chuva.
Restaurantes sugeridos: Banana da Terra, Thai Brasil. Atividade: passeio de escuna.
Orçamento informado pelo usuário: R$ 2.000,00. Gastos estimados: hospedagem
R$ 450,00, alimentação R$ 600,00, atividades R$ 300,00; total R$ 1.350,00.
"""

REFERENCE = """\
Roteiro em Paraty (RJ), de sábado 10/10/2026 a domingo 11/10/2026, para 2 pessoas.
Hospedagem na Pousada do Porto, no Centro Histórico: reserva nº 5 confirmada, R$ 450,00.
Sábado: passeio de escuna e jantar no Banana da Terra.
Domingo: 60% de chuva, almoço no Thai Brasil.
Gastos estimados de R$ 1.350,00, dentro do orçamento de R$ 2.000,00.
"""

MIN_BIGRAM_RECALL = 0.4


def test_itinerary_covers_the_reference_bigrams(itineraries: list[str]) -> None:
    reference_bigrams = bigrams(REFERENCE)
    failures = 0
    for itinerary in itineraries:
        shared = reference_bigrams & bigrams(itinerary)
        if len(shared) / len(reference_bigrams) < MIN_BIGRAM_RECALL:
            failures = failures + 1

    assert failures == 0, (
        f"poucos bigramas da referência em {failures} de {len(itineraries)} roteiros"
    )


# Atividade 1: troque bigramas por trigramas (três palavras seguidas) e compare
# as notas.


# Atividade 2: reescreva a referência com outras palavras e o mesmo sentido, e
# veja a nota cair.


def bigrams(text: str) -> set[tuple[str, str]]:
    words = re.findall(r"\w+", text.lower())
    return set(pairwise(words))


@pytest.fixture(scope="module")
def itineraries(runs: int) -> list[str]:
    with unit_test_trace(__name__):
        agent = build_output_generator_agent(ModelClient())
        return [agent.run([user_message(INSTRUCTIONS)]).text for _ in range(runs)]
