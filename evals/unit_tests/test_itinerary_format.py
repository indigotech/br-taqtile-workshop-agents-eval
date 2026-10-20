"""Base da atividade: o gerador escreve o roteiro de cada caso do golden dataset
(evals/dataset.json). Copie o teste para cada nova regra, trocando o padrão e
se ele deve ou não aparecer no roteiro. Os espaços das duas atividades estão
marcados abaixo do teste."""

import re

import pytest

from app.agents.output_generator_agent import build_output_generator_agent
from app.core.agent import user_message
from app.core.model_client import ModelClient
from app.evals.dataset import EvalCase
from app.evals.pass_metrics import pass_at_k, pass_hat_k
from evals.golden import golden_cases
from evals.unit_tests.parallel import run_in_parallel
from evals.unit_tests.tracing import unit_test_trace

ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF]")
# RESERVATION_IN_BRIEF = re.compile(r"Reserva nº (\d+) confirmada")
# def reservation_number(number: str) -> re.Pattern[str]:
#     return re.compile(
#         rf"reserva\D{{0,60}}(?:n\.?[º°]|número|#)\W{{0,3}}{number}\b", re.IGNORECASE
#     )


def test_itinerary_has_no_iso_dates(itineraries: list[str]) -> None:
    failures = 0
    for itinerary in itineraries:
        if ISO_DATE.search(itinerary):
            failures = failures + 1

    samples = len(itineraries)
    passed = samples - failures
    assert failures == 0, (
        f"data ISO em {failures} de {samples} roteiros "
        f"(pass@1 = {pass_at_k(samples, passed, 1):.2f}, "
        f"pass^{samples} = {pass_hat_k(samples, passed, samples):.2f})"
    )


# Atividade 1: o roteiro não tem nenhum emoji (a regex não pode casar).
def test_itinerary_has_no_emoji(itineraries: list[str]) -> None:
    pytest.skip("atividade: escreva este teste")


# Atividade 2: quando o resumo do caso (case.itinerary_brief) traz uma reserva
# confirmada, o roteiro cita o número dela (a regex tem que casar).
def test_itinerary_cites_the_reservation_number(
    case: EvalCase, itineraries: list[str]
) -> None:
    pytest.skip("atividade: escreva este teste")


@pytest.fixture(
    scope="module",
    params=[case for case in golden_cases() if case.itinerary_brief],
    ids=lambda case: case.id,
)
def case(request: pytest.FixtureRequest) -> EvalCase:
    golden_case: EvalCase = request.param
    return golden_case


@pytest.fixture(scope="module")
def itineraries(case: EvalCase, runs: int) -> list[str]:
    with unit_test_trace(__name__):
        agent = build_output_generator_agent(ModelClient())
        return run_in_parallel(
            runs, lambda: agent.run([user_message(case.itinerary_brief or "")]).text
        )
