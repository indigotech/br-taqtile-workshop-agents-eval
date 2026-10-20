"""Base da atividade: o interpretador lê a primeira mensagem de cada caso do
golden dataset (evals/dataset.json), e o teste confere cada resposta. Copie o
teste para cada novo campo, comparando com o esperado do caso. Os espaços das
duas atividades estão marcados abaixo do teste."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.agents.input_interpreter_agent import (
    TripRequest,
    build_input_interpreter_agent,
)
from app.core.agent import user_message
from app.core.model_client import ModelClient
from app.evals.dataset import EvalCase
from app.evals.pass_metrics import pass_at_k, pass_hat_k
from evals.golden import golden_cases
from evals.unit_tests.tracing import unit_test_trace


def test_reply_follows_the_trip_request_schema(replies: list[str]) -> None:
    failures = 0
    for reply in replies:
        try:
            TripRequest.model_validate_json(reply)
        except ValidationError:
            failures = failures + 1

    samples = len(replies)
    passed = samples - failures
    assert failures == 0, (
        f"fora do schema em {failures} de {samples} respostas "
        f"(pass@1 = {pass_at_k(samples, passed, 1):.2f}, "
        f"pass^{samples} = {pass_hat_k(samples, passed, samples):.2f})"
    )


# Atividade 1: guests é igual ao esperado do caso (case.expected_trip.guests).


# Atividade 2: budget_amount é igual ao esperado do caso
# (case.expected_trip.budget_amount).


@pytest.fixture(scope="module", params=golden_cases(), ids=lambda case: case.id)
def case(request: pytest.FixtureRequest) -> EvalCase:
    golden_case: EvalCase = request.param
    return golden_case


@pytest.fixture(scope="module")
def replies(case: EvalCase, runs: int) -> list[str]:
    with unit_test_trace(__name__):
        agent = build_input_interpreter_agent(ModelClient(), today=date.today())
        return [agent.run([user_message(case.messages[0])]).text for _ in range(runs)]
