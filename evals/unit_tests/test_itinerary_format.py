"""Base da atividade: copie o teste para cada nova regra, trocando o padrão e
se ele deve ou não aparecer no roteiro."""

import re

from app.agents.output_generator_agent import build_output_generator_agent
from app.core.agent import user_message
from app.core.model_client import ModelClient

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


def test_itinerary_has_no_iso_dates(model_client: ModelClient, runs: int) -> None:
    itineraries = _write_itineraries(model_client, runs)

    failing_runs = [
        run for run, itinerary in enumerate(itineraries) if ISO_DATE.search(itinerary)
    ]

    assert not failing_runs, (
        f"data ISO em {len(failing_runs)} de {runs} execuções: {failing_runs}"
    )


def _write_itineraries(model_client: ModelClient, runs: int) -> list[str]:
    agent = build_output_generator_agent(model_client)
    return [agent.run([user_message(INSTRUCTIONS)]).text for _ in range(runs)]
