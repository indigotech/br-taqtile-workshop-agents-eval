"""Base da atividade de pass@k: o gerador escreve RUNS roteiros para cada caso
do golden dataset (evals/dataset.json), e o teste conta quantos cabem no limite
de palavras. O critério de aprovação é a assertividade mínima sobre o pass^k:
pass^K >= MIN_PASS_HAT_K. Rode com ARGS="-s" para ver os números de cada caso,
mesmo quando ele passa."""

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

MAX_WORDS = 850
K = 3
MIN_PASS_HAT_K = 0.9


def test_itinerary_stays_within_the_word_limit(itineraries: list[str]) -> None:
    samples = len(itineraries)
    if samples < K:
        pytest.fail(
            f"pass^{K} precisa de pelo menos {K} roteiros: rode com RUNS >= {K}"
        )

    passed = 0
    for itinerary in itineraries:
        if len(re.findall(r"\w+", itinerary)) <= MAX_WORDS:
            passed = passed + 1

    summary = (
        f"{passed} de {samples} roteiros com até {MAX_WORDS} palavras: "
        f"pass@{K} = {pass_at_k(samples, passed, K):.2f}, "
        f"pass^{K} = {pass_hat_k(samples, passed, K):.2f}"
    )
    print(summary)
    assert pass_hat_k(samples, passed, K) >= MIN_PASS_HAT_K, (
        f"{summary} (mínimo de pass^{K}: {MIN_PASS_HAT_K})"
    )


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
