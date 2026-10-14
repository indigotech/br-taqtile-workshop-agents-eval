"""Base da atividade: o roteiro e a referência viram embeddings, e o teste mede
a similaridade de cossenos entre eles. Os espaços das duas atividades estão
marcados abaixo do teste."""

import math

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

MIN_SIMILARITY = 0.75


def test_itinerary_means_the_same_as_the_reference(
    itineraries: list[str], model_client: ModelClient
) -> None:
    reference_vector, *itinerary_vectors = model_client.embed([REFERENCE, *itineraries])
    failures = 0
    for itinerary_vector in itinerary_vectors:
        if cosine_similarity(reference_vector, itinerary_vector) < MIN_SIMILARITY:
            failures = failures + 1

    assert failures == 0, (
        f"longe da referência em {failures} de {len(itineraries)} roteiros"
    )


# Atividade 1: gere o embedding de uma frase com model_client.embed e olhe o
# vetor: quantos números ele tem?


# Atividade 2: compare "A viagem cabe no orçamento." com "A viagem não cabe no
# orçamento." Quanto dá a similaridade?


def cosine_similarity(first: list[float], second: list[float]) -> float:
    dot_product = sum(
        first_value * second_value
        for first_value, second_value in zip(first, second, strict=True)
    )
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))
    return dot_product / (first_norm * second_norm)


@pytest.fixture(scope="module")
def itineraries(runs: int) -> list[str]:
    with unit_test_trace(__name__):
        agent = build_output_generator_agent(ModelClient())
        return [agent.run([user_message(INSTRUCTIONS)]).text for _ in range(runs)]
