"""Exemplo completo: seis regras de produto checadas com regex sobre o mesmo
roteiro, gerado uma única vez para o arquivo inteiro."""

import re
import uuid

import pytest

from app.agents.output_generator_agent import build_output_generator_agent
from app.core.agent import user_message
from app.core.model_client import ModelClient, prompt_cache_session
from app.core.observability import observe_turn

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

EMOJI = re.compile(
    "[\U0001f300-\U0001faff\U00002600-\U000027bf\U0001f000-\U0001f2ff⭐⭕]"
)

MONEY_MENTION = re.compile(r"R\$\s*\d[\d.,]*")
MONEY_BRAZILIAN = re.compile(r"R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?(?!\d)")
LODGING_TOTAL = re.compile(r"R\$\s?450(?:,00)?(?!\d)")

SATURDAY_DATE = re.compile(r"(?<!\d)10/10(?:/(?:20)?26)?(?!\d)")
SUNDAY_DATE = re.compile(r"(?<!\d)11/10(?:/(?:20)?26)?(?!\d)")
ISO_DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")

RESERVATION_NUMBER = re.compile(
    r"reserva\b[^\n]{0,30}?(?:#|\b(?:n[º°o.]|n[úu]mero|c[óo]digo|id))\W{0,6}5(?!\d)"
    r"|n[úu]mero da reserva\W{0,6}5(?!\d)",
    re.IGNORECASE,
)

SECTION_WORDS = {
    "hospedagem": r"hospedagem",
    "sábado": r"s[áa]bado",
    "domingo": r"domingo",
    "orçamento": r"or[çc]amento",
}

WORD = re.compile(r"\w+")
MAX_WORDS = 600


def test_itinerary_has_no_emoji(itineraries: list[str], runs: int) -> None:
    failures = {
        run: f"emoji {match.group()!r}"
        for run, itinerary in enumerate(itineraries)
        if (match := EMOJI.search(itinerary))
    }

    _assert_rule_holds("sem emoji", failures, runs)


def test_itinerary_writes_money_in_brazilian_format(
    itineraries: list[str], runs: int
) -> None:
    failures: dict[int, str] = {}
    for run, itinerary in enumerate(itineraries):
        mentions = [
            mention.rstrip(".,") for mention in MONEY_MENTION.findall(itinerary)
        ]
        badly_formatted = [
            mention for mention in mentions if not MONEY_BRAZILIAN.fullmatch(mention)
        ]
        if badly_formatted:
            failures[run] = f"fora do formato R$ 1.234,56: {badly_formatted}"
        elif not LODGING_TOTAL.search(itinerary):
            failures[run] = "total da hospedagem (R$ 450,00) ausente"

    _assert_rule_holds("dinheiro em formato brasileiro", failures, runs)


def test_itinerary_writes_dates_as_day_and_month(
    itineraries: list[str], runs: int
) -> None:
    failures: dict[int, str] = {}
    for run, itinerary in enumerate(itineraries):
        if iso_dates := ISO_DATE.findall(itinerary):
            failures[run] = f"data ISO: {iso_dates}"
        elif not SATURDAY_DATE.search(itinerary):
            failures[run] = "data do sábado (10/10) ausente"
        elif not SUNDAY_DATE.search(itinerary):
            failures[run] = "data do domingo (11/10) ausente"

    _assert_rule_holds("datas em DD/MM", failures, runs)


def test_itinerary_cites_the_reservation_number(
    itineraries: list[str], runs: int
) -> None:
    failures = {
        run: "número da reserva (5) ausente"
        for run, itinerary in enumerate(itineraries)
        if not RESERVATION_NUMBER.search(itinerary)
    }

    _assert_rule_holds("número da reserva citado", failures, runs)


def test_itinerary_has_the_required_sections(itineraries: list[str], runs: int) -> None:
    failures: dict[int, str] = {}
    for run, itinerary in enumerate(itineraries):
        missing = [
            section
            for section, word in SECTION_WORDS.items()
            if not _section_pattern(word).search(itinerary)
        ]
        if missing:
            failures[run] = f"seções ausentes: {missing}"

    _assert_rule_holds("seções obrigatórias", failures, runs)


def test_itinerary_fits_the_word_limit(itineraries: list[str], runs: int) -> None:
    failures = {
        run: f"{word_count} palavras"
        for run, itinerary in enumerate(itineraries)
        if (word_count := len(WORD.findall(itinerary))) > MAX_WORDS
    }

    _assert_rule_holds(f"no máximo {MAX_WORDS} palavras", failures, runs)


@pytest.fixture(scope="module")
def itineraries(runs: int) -> list[str]:
    # A module-scoped fixture is set up before the per-test trace exists, so it
    # opens a trace of its own to keep these model calls grouped and tagged.
    session_id = f"unit-test-{uuid.uuid4().hex[:8]}"
    with (
        prompt_cache_session(session_id),
        observe_turn(
            session_id=session_id,
            user_id=None,
            user_message=__name__,
            tags=["unit-test"],
        ),
    ):
        agent = build_output_generator_agent(ModelClient())
        return [agent.run([user_message(INSTRUCTIONS)]).text for _ in range(runs)]


def _assert_rule_holds(rule: str, failures: dict[int, str], runs: int) -> None:
    assert not failures, (
        f"{rule} falhou em {len(failures)} de {runs} execuções: {failures}"
    )


def _section_pattern(word: str) -> re.Pattern[str]:
    # A heading or a short line of its own, with or without markdown (###,
    # **bold**, __bold__), a leading symbol or a trailing colon around the word.
    return re.compile(
        rf"^\s*(?:#{{1,6}}\s*|\*\*|__)?[^\w\n]{{0,6}}[^\n]{{0,25}}{word}"
        rf"[^\n]{{0,40}}(?:\*\*|__|:)?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
