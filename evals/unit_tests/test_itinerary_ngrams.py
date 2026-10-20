"""Base da atividade: o gerador escreve o roteiro de cada caso do golden dataset
(evals/dataset.json), e o teste compara cada roteiro com a resposta de
referência do caso pelos bigramas (pares de palavras seguidas) em comum. Os espaços das duas
atividades estão marcados abaixo do teste."""

import re
from itertools import pairwise

import pytest

from app.agents.output_generator_agent import build_output_generator_agent
from app.core.agent import user_message
from app.core.model_client import ModelClient
from app.evals.dataset import EvalCase
from app.evals.pass_metrics import pass_at_k, pass_hat_k
from evals.golden import golden_cases
from evals.unit_tests.parallel import run_in_parallel
from evals.unit_tests.tracing import unit_test_trace

MIN_BIGRAM_RECALL = 0.3


def test_itinerary_covers_the_reference_bigrams(
    case: EvalCase, itineraries: list[str]
) -> None:
    reference_bigrams = bigrams(case.reference_answer or "")
    failures = 0
    for itinerary in itineraries:
        shared = reference_bigrams & bigrams(itinerary)
        if len(shared) / len(reference_bigrams) < MIN_BIGRAM_RECALL:
            failures = failures + 1

    samples = len(itineraries)
    passed = samples - failures
    assert failures == 0, (
        f"poucos bigramas da referência em {failures} de {samples} roteiros "
        f"(pass@1 = {pass_at_k(samples, passed, 1):.2f}, "
        f"pass^{samples} = {pass_hat_k(samples, passed, samples):.2f})"
    )


# Atividade 1: troque bigramas por trigramas (três palavras seguidas) e compare
# as notas.


# Atividade 2: reescreva inteira a resposta de referência de um caso no
# dataset, com outras palavras e as mesmas informações (nomes e valores iguais,
# como "Pousada do Porto"), e veja a nota cair.


def bigrams(text: str) -> set[tuple[str, str]]:
    words = re.findall(r"\w+", text.lower())
    return set(pairwise(words))


@pytest.fixture(
    scope="module",
    params=[
        case
        for case in golden_cases()
        if case.itinerary_brief and case.reference_answer
    ],
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
