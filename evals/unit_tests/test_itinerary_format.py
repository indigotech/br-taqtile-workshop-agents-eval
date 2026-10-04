"""Base da atividade: copie o teste para cada nova regra, trocando o padrão e
se ele deve ou não aparecer no roteiro. Os espaços das duas atividades estão
marcados abaixo do teste."""

import re

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

ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF]")
# RESERVATION_NUMBER = re.compile(r"reserva\D{0,20}\b5\b", re.IGNORECASE)


def test_itinerary_has_no_iso_dates(itineraries: list[str]) -> None:
    failures = 0
    for itinerary in itineraries:
        if ISO_DATE.search(itinerary):
            failures = failures + 1

    assert failures == 0, f"data ISO em {failures} de {len(itineraries)} roteiros"


# Atividade 1: o roteiro não tem nenhum emoji (a regex não pode casar).


# Atividade 2: o roteiro cita o número da reserva (a regex tem que casar).


@pytest.fixture(scope="module")
def itineraries(runs: int) -> list[str]:
    with unit_test_trace(__name__):
        agent = build_output_generator_agent(ModelClient())
        return [agent.run([user_message(INSTRUCTIONS)]).text for _ in range(runs)]
