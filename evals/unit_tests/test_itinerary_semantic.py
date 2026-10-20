"""Base da atividade: o gerador escreve o roteiro de cada caso do golden dataset
(evals/dataset.json); o roteiro e a resposta de referência do caso viram
embeddings, e o teste mede a similaridade de cossenos entre eles. Os espaços das duas atividades estão
marcados abaixo do teste."""

import math

import pytest

from app.agents.output_generator_agent import build_output_generator_agent
from app.core.agent import user_message
from app.core.model_client import ModelClient
from app.evals.dataset import EvalCase
from app.evals.pass_metrics import pass_at_k, pass_hat_k
from evals.golden import golden_cases
from evals.unit_tests.parallel import run_in_parallel
from evals.unit_tests.tracing import unit_test_trace

MIN_SIMILARITY = 0.70


def test_itinerary_means_the_same_as_the_reference(
    case: EvalCase, itineraries: list[str], model_client: ModelClient
) -> None:
    reference = case.reference_answer
    assert reference is not None, "este teste só roda em casos com reference_answer"

    texts = [reference]
    texts.extend(itineraries)
    # Uma chamada só para todos os textos. Os vetores voltam na mesma ordem em
    # que os textos foram enviados: primeiro a referência, depois os roteiros.
    vectors = model_client.embed(texts)
    reference_vector = vectors[0]
    itinerary_vectors = vectors[1:]

    failures = 0
    for itinerary_vector in itinerary_vectors:
        if cosine_similarity(reference_vector, itinerary_vector) < MIN_SIMILARITY:
            failures = failures + 1

    samples = len(itineraries)
    passed = samples - failures
    assert failures == 0, (
        f"longe da referência em {failures} de {samples} roteiros "
        f"(pass@1 = {pass_at_k(samples, passed, 1):.2f}, "
        f"pass^{samples} = {pass_hat_k(samples, passed, samples):.2f})"
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
