"""Base da atividade: copie o teste para cada novo campo, trocando a conferência
feita em cada resposta. Os espaços das duas atividades estão marcados abaixo do
teste."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.agents.input_interpreter_agent import (
    TripRequest,
    build_input_interpreter_agent,
)
from app.core.agent import user_message
from app.core.model_client import ModelClient
from evals.unit_tests.tracing import unit_test_trace

TODAY = date(2026, 10, 7)
REQUEST = "Quero ir pra Paraty sábado que vem com minha namorada."


def test_reply_follows_the_trip_request_schema(replies: list[str]) -> None:
    failures = 0
    for reply in replies:
        try:
            TripRequest.model_validate_json(reply)
        except ValidationError:
            failures = failures + 1

    assert failures == 0, f"fora do schema em {failures} de {len(replies)} respostas"


# Atividade 1: o pedido diz "com minha namorada", então guests tem que ser 2.


# Atividade 2: o pedido não fala de orçamento, então budget_amount tem que ficar
# vazio (None).


@pytest.fixture(scope="module")
def replies(runs: int) -> list[str]:
    with unit_test_trace(__name__):
        agent = build_input_interpreter_agent(ModelClient(), today=TODAY)
        return [agent.run([user_message(REQUEST)]).text for _ in range(runs)]
