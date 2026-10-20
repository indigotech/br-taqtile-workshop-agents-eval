"""Base da atividade: o interpretador lê a primeira mensagem de cada caso do
golden dataset (evals/dataset.json), e cada teste confere as respostas: o
primeiro valida o schema, os outros dois comparam um campo com o esperado do
caso (case.expected_trip). A atividade é rodar e explicar o resultado de cada
caso."""

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
from evals.unit_tests.parallel import run_in_parallel
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


def test_reply_has_the_expected_guests(case: EvalCase, replies: list[str]) -> None:
    expected = case.expected_trip.guests
    failures = 0
    for reply in replies:
        try:
            trip = TripRequest.model_validate_json(reply)
        except ValidationError:
            failures = failures + 1
            continue
        if trip.guests != expected:
            failures = failures + 1

    samples = len(replies)
    passed = samples - failures
    assert failures == 0, (
        f"guests diferente de {expected} em {failures} de {samples} respostas "
        f"(pass@1 = {pass_at_k(samples, passed, 1):.2f}, "
        f"pass^{samples} = {pass_hat_k(samples, passed, samples):.2f})"
    )


def test_reply_has_the_expected_budget(case: EvalCase, replies: list[str]) -> None:
    expected = case.expected_trip.budget_amount
    failures = 0
    for reply in replies:
        try:
            trip = TripRequest.model_validate_json(reply)
        except ValidationError:
            failures = failures + 1
            continue
        if trip.budget_amount != expected:
            failures = failures + 1

    samples = len(replies)
    passed = samples - failures
    assert failures == 0, (
        f"budget_amount diferente de {expected} em {failures} de {samples} respostas "
        f"(pass@1 = {pass_at_k(samples, passed, 1):.2f}, "
        f"pass^{samples} = {pass_hat_k(samples, passed, samples):.2f})"
    )


@pytest.fixture(scope="module", params=golden_cases(), ids=lambda case: case.id)
def case(request: pytest.FixtureRequest) -> EvalCase:
    golden_case: EvalCase = request.param
    return golden_case


@pytest.fixture(scope="module")
def replies(case: EvalCase, runs: int) -> list[str]:
    with unit_test_trace(__name__):
        agent = build_input_interpreter_agent(ModelClient(), today=date.today())
        return run_in_parallel(
            runs, lambda: agent.run([user_message(case.messages[0])]).text
        )
