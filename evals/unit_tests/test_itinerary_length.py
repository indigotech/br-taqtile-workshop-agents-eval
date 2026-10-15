"""Base da atividade de pass@k: o gerador escreve RUNS roteiros e o teste
confere que cada um cabe no limite de palavras."""

import re

import pytest

from app.agents.output_generator_agent import build_output_generator_agent
from app.core.agent import user_message
from app.core.model_client import ModelClient
from app.evals.pass_metrics import pass_at_k, pass_hat_k
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

MAX_WORDS = 850


def test_itinerary_stays_within_the_word_limit(itineraries: list[str]) -> None:
    failures = 0
    for itinerary in itineraries:
        if len(re.findall(r"\w+", itinerary)) > MAX_WORDS:
            failures = failures + 1

    samples = len(itineraries)
    passed = samples - failures
    assert failures == 0, (
        f"mais de {MAX_WORDS} palavras em {failures} de {samples} roteiros "
        f"(pass@1 = {pass_at_k(samples, passed, 1):.2f}, "
        f"pass^{samples} = {pass_hat_k(samples, passed, samples):.2f})"
    )


@pytest.fixture(scope="module")
def itineraries(runs: int) -> list[str]:
    with unit_test_trace(__name__):
        agent = build_output_generator_agent(ModelClient())
        return [agent.run([user_message(INSTRUCTIONS)]).text for _ in range(runs)]
