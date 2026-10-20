"""Base da avaliação de ponta a ponta: lê o results.jsonl de um make run-dataset
e confere cada execução contra o esperado do seu caso no golden dataset. Pega o
mais recente em evals/runs/; RESULTS=evals/runs/<data-hora>/results.jsonl
escolhe outro. As checagens exatas não chamam o modelo; a similaridade e o juiz, sim."""

import math
import os
from pathlib import Path

import pytest
from pydantic import BaseModel

from app.core.agent import Agent, user_message
from app.core.model_client import ModelClient
from app.evals.pass_metrics import pass_at_k, pass_hat_k
from app.evals.records import RunRecord

RUNS_DIRECTORY = Path(__file__).parents[1] / "runs"
MIN_SIMILARITY = 0.70
MIN_JUDGE_SCORE = 0.8


def test_first_message_calls_the_required_agents(case_runs: list[RunRecord]) -> None:
    failures = 0
    for record in case_runs:
        called = {call.name for call in record.turns[0].agent_calls}
        if not set(record.case.required_agents) <= called:
            failures = failures + 1

    assert_every_run_passes(failures, case_runs, "faltou agente obrigatório")


def test_nothing_is_booked_before_the_user_confirms(
    case_runs: list[RunRecord],
) -> None:
    failures = 0
    for record in case_runs:
        confirmation = record.case.confirmation_message_index
        for turn_index, turn in enumerate(record.turns):
            confirmed = confirmation is not None and turn_index >= confirmation
            if turn.reservations_created and not confirmed:
                failures = failures + 1
                break

    assert_every_run_passes(failures, case_runs, "reserva sem confirmação")


def test_bookings_stay_within_the_lodging_limit(case_runs: list[RunRecord]) -> None:
    failures = 0
    for record in case_runs:
        limit = record.case.max_lodging_total
        if limit is not None and any(
            reservation.total_price > limit
            for turn in record.turns
            for reservation in turn.reservations_created
        ):
            failures = failures + 1

    assert_every_run_passes(failures, case_runs, "reserva acima do teto")


def test_bookings_match_the_expected_trip(case_runs: list[RunRecord]) -> None:
    failures = 0
    for record in case_runs:
        expected = record.case.expected_trip
        if any(
            reservation.city_name != expected.destination
            or reservation.check_in != expected.start_date
            or reservation.check_out != expected.end_date
            or reservation.guests != expected.guests
            for turn in record.turns
            for reservation in turn.reservations_created
        ):
            failures = failures + 1

    assert_every_run_passes(failures, case_runs, "reserva diferente da viagem pedida")


def test_final_answer_means_the_same_as_the_reference(
    case_runs: list[RunRecord], model_client: ModelClient
) -> None:
    reference = case_runs[0].case.reference_answer
    if reference is None:
        pytest.skip("o caso não tem resposta de referência")
    reference_vector, *answer_vectors = model_client.embed(
        [reference, *(final_answer(record) for record in case_runs)]
    )
    failures = 0
    for answer_vector in answer_vectors:
        if cosine_similarity(reference_vector, answer_vector) < MIN_SIMILARITY:
            failures = failures + 1

    assert_every_run_passes(failures, case_runs, "longe da referência")


def test_final_answer_respects_the_user_preferences(
    case_runs: list[RunRecord], judge: Agent
) -> None:
    failures = 0
    for record in case_runs:
        prompt = JUDGE_REQUEST.format(
            preferences="; ".join(record.case.user_preferences),
            answer=final_answer(record),
        )
        verdict = JudgeVerdict.model_validate_json(
            judge.run([user_message(prompt)]).text
        )
        if verdict.score < MIN_JUDGE_SCORE:
            failures = failures + 1

    assert_every_run_passes(failures, case_runs, "preferências ignoradas")


# Atividade: escreva uma checagem nova com um campo do caso que nenhum teste
# acima usa, ou troque a rubrica do juiz por uma com faixas de nota.


def assert_every_run_passes(
    failures: int, case_runs: list[RunRecord], problem: str
) -> None:
    samples = len(case_runs)
    passed = samples - failures
    assert failures == 0, (
        f"{problem} em {failures} de {samples} execuções "
        f"(pass@1 = {pass_at_k(samples, passed, 1):.2f}, "
        f"pass^{samples} = {pass_hat_k(samples, passed, samples):.2f})"
    )


def final_answer(record: RunRecord) -> str:
    # The itinerary is not always in the last turn: once Carla confirms, the
    # last answer is only "já está reservada".
    for turn in reversed(record.turns):
        if any(call.name == "generate_itinerary" for call in turn.agent_calls):
            return turn.response
    return record.turns[-1].response


def cosine_similarity(first: list[float], second: list[float]) -> float:
    dot_product = sum(
        first_value * second_value
        for first_value, second_value in zip(first, second, strict=True)
    )
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))
    return dot_product / (first_norm * second_norm)


class JudgeVerdict(BaseModel):
    score: float
    reason: str


JUDGE_PROMPT = """\
Você avalia respostas de um planejador de viagens. Dê uma nota de 0 a 1:
1 quando a resposta respeita todas as preferências do usuário, 0 quando ignora
todas, e valores no meio quando respeita só parte delas. Uma preferência que a
resposta não tem como atender (por exemplo, nada foi planejado ainda) não conta
contra ela. Responda com a nota e o motivo em uma frase.
"""

JUDGE_REQUEST = """\
Preferências do usuário: {preferences}

Resposta do planejador:
{answer}
"""


def load_run_records() -> list[RunRecord]:
    chosen = os.environ.get("RESULTS")
    if chosen:
        results_path = Path(chosen)
    else:
        latest = sorted(RUNS_DIRECTORY.glob("*/results.jsonl"))
        if not latest:
            return []
        results_path = latest[-1]
    return [
        RunRecord.model_validate_json(line)
        for line in results_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


RUN_RECORDS = load_run_records()
if not RUN_RECORDS:
    pytest.skip(
        "nenhum results.jsonl em evals/runs/: rode make run-dataset antes",
        allow_module_level=True,
    )


@pytest.fixture(
    scope="module",
    params=sorted({record.case.id for record in RUN_RECORDS}),
)
def case_runs(request: pytest.FixtureRequest) -> list[RunRecord]:
    return [record for record in RUN_RECORDS if record.case.id == request.param]


@pytest.fixture(scope="module")
def judge() -> Agent:
    return Agent(
        name="judge_agent",
        system_prompt=JUDGE_PROMPT,
        model_client=ModelClient(),
        response_model=JudgeVerdict,
        temperature=0,
    )
