import logging
import sqlite3
import uuid
from datetime import date

import httpx
import openai

from app.agents.orchestrator_agent import build_orchestrator_agent
from app.core.agent import user_message
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.messages import ChatMessage
from app.core.model_client import ModelClient, prompt_cache_session
from app.core.observability import current_trace_id, flush, get_langfuse, observe_turn
from app.core.terminal import Style, paint
from app.core.token_budget import TokenBudgetExceededError, turn_token_budget
from app.core.tools import FORCED_DELAY_SECONDS
from app.data.city_data_source import CityDataSource
from app.data.database import connect, reset_database
from app.data.http import build_http_client
from app.data.models import City, User
from app.data.nominatim_client import NominatimClient
from app.data.user_data_source import UserDataSource

logger = logging.getLogger(__name__)

_EXIT_COMMANDS = {"sair", "exit", "quit"}
_YES_ANSWERS = {"s", "sim", "y", "yes"}
_NO_ANSWERS = {"n", "não", "nao", "no"}
_DEFAULT_COUNTRY = "Brasil"


def main() -> None:
    setup_logging()
    if not settings.DATABASE_PATH.exists():
        logger.info("No database at %s, creating one", settings.DATABASE_PATH)
        reset_database(settings.DATABASE_PATH)

    connection = connect(settings.DATABASE_PATH)
    http_client = build_http_client()
    try:
        _chat(connection, http_client)
    finally:
        http_client.close()
        connection.close()
        flush()


def _chat(connection: sqlite3.Connection, http_client: httpx.Client) -> None:
    user = onboard_user(
        UserDataSource(connection),
        CityDataSource(connection),
        NominatimClient(http_client),
    )
    if user is None:
        return
    agent = build_orchestrator_agent(
        ModelClient(), connection, http_client, user.id, date.today()
    )
    session_id = str(uuid.uuid4())
    history: list[ChatMessage] = []

    if settings.FORCE_TOOL_ERROR:
        notice = f"A tool {settings.FORCE_TOOL_ERROR} vai falhar em toda chamada."
        print(f"\n{paint(notice, Style.SYSTEM)}")
    if settings.FORCE_SLOW_TOOL:
        notice = (
            f"A tool {settings.FORCE_SLOW_TOOL} vai demorar "
            f"{FORCED_DELAY_SECONDS:g}s a mais em toda chamada."
        )
        print(f"\n{paint(notice, Style.SYSTEM)}")
    greeting = f"Olá, {user.name}! Pra onde vamos? (digite 'sair' para encerrar)"
    print(f"\n{paint(greeting, Style.SYSTEM)}\n")
    while True:
        try:
            message = input(paint("você> ", Style.USER_PROMPT)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not message:
            continue
        if message.lower() in _EXIT_COMMANDS:
            return

        try:
            with (
                prompt_cache_session(session_id),
                turn_token_budget(),
                observe_turn(
                    session_id=session_id, user_id=str(user.id), user_message=message
                ) as span,
            ):
                result = agent.run([*history, user_message(message)])
                span.update(output=result.text)
                trace_id = current_trace_id()
        except openai.APIError as error:
            # Keeps the chat alive: a bad key or a rate limit should cost one
            # message, not the whole conversation.
            logger.error("Model API error: %s", error)
            notice = f"[erro na API do modelo: {error.message}]"
            print(f"\n{paint(notice, Style.API_ERROR)}\n")
            continue
        except TokenBudgetExceededError as error:
            # The partial turn stays out of the history, like an API error.
            logger.error("Turn stopped by the token budget: %s", error)
            print(f"\n{paint(_token_budget_notice(error), Style.API_ERROR)}\n")
            continue
        history = result.next_turn_history()

        print(f"\n{paint(f'planejador> {result.text}', Style.BOT_REPLY)}\n")
        if settings.LANGFUSE_TRACING_ENABLED and trace_id:
            trace_url = get_langfuse().get_trace_url(trace_id=trace_id)
            print(f"{paint(f'  trace: {trace_url}', Style.AUXILIARY)}\n")


def _token_budget_notice(error: TokenBudgetExceededError) -> str:
    return (
        "[turno interrompido: atingiu o limite de tokens por turno "
        f"({error.tokens_used} de {error.limit}). A resposta foi descartada; "
        "comece uma nova conversa ('sair' e `make run` de novo).]"
    )


def onboard_user(
    user_data_source: UserDataSource,
    city_data_source: CityDataSource,
    nominatim_client: NominatimClient,
) -> User | None:
    """Find the person's registration by name, or register them. None means
    they left: declined to register, typed an exit command or closed stdin."""
    try:
        name = _ask_required(
            "Oi! Qual é o seu nome? Vou ver se você já tem cadastro. "
            "(digite 'sair' para encerrar)"
        )
        user = _pick_existing_user(
            user_data_source.find_by_name(name), city_data_source, name
        )
        if user is not None:
            return user
        if not _ask_yes_no("Quer fazer seu cadastro agora? (s/n)"):
            _say("Tudo bem! Obrigado pela visita e até a próxima.")
            return None
        return _register_user(
            name, user_data_source, city_data_source, nominatim_client
        )
    except _ConversationEndedError:
        return None


class _ConversationEndedError(Exception):
    pass


def _pick_existing_user(
    matches: list[User], city_data_source: CityDataSource, typed_name: str
) -> User | None:
    if not matches:
        _say(f"Não encontrei nenhum cadastro com o nome {typed_name}.")
        return None
    if len(matches) == 1:
        user = matches[0]
        question = (
            f"Encontrei o cadastro de {_describe_user(user, city_data_source)}. "
            "É você? (s/n)"
        )
        return user if _ask_yes_no(question) else None
    # A first name alone can match several people: let them pick instead of
    # guessing, with a way out for someone who is not on the list.
    options = "\n".join(
        f"  {position}. {_describe_user(user, city_data_source)}"
        for position, user in enumerate(matches, start=1)
    )
    question = (
        f"Encontrei mais de um cadastro com esse nome:\n{options}\n"
        "  0. Nenhum desses\nQual deles é você? (número)"
    )
    while True:
        answer = _ask_required(question)
        if answer == "0":
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(matches):
            return matches[int(answer) - 1]
        _say(f"Responda com um número de 0 a {len(matches)}, por favor.")


def _describe_user(user: User, city_data_source: CityDataSource) -> str:
    home_city = city_data_source.get_city(user.home_city_id)
    return f"{user.name}, de {home_city.name}" if home_city else user.name


def _register_user(
    typed_name: str,
    user_data_source: UserDataSource,
    city_data_source: CityDataSource,
    nominatim_client: NominatimClient,
) -> User:
    name = _ask(f"Qual é o seu nome completo? [{typed_name}]") or typed_name
    home_city = _ask_home_city(city_data_source, nominatim_client)
    email = _ask_email(user_data_source)
    user = user_data_source.create_user(name, email, home_city.id)
    logger.info("Registered user %s from city %s", user.id, home_city.id)
    _say(f"Pronto, cadastro feito! Você mora em {home_city.name}.")
    return user


def _ask_home_city(
    city_data_source: CityDataSource, nominatim_client: NominatimClient
) -> City:
    """A city outside `cities` is geocoded and added, since `home_city_id`
    must reference a row with coordinates."""
    while True:
        typed_city = _ask_required("Em que cidade você mora?")
        city = city_data_source.find_by_name(typed_city)
        if city is not None:
            return city
        state = _ask_required(
            f"Ainda não conheço {typed_city}. Em que estado ela fica? (ex.: PR)"
        )
        country = _ask(f"E em que país? [{_DEFAULT_COUNTRY}]") or _DEFAULT_COUNTRY
        try:
            location = nominatim_client.geocode(f"{typed_city}, {state}, {country}")
        except httpx.HTTPError as error:
            logger.warning("Geocoding %s failed: %s", typed_city, error)
            _say("Não consegui consultar o mapa agora. Tente de novo em instantes.")
            continue
        if location is None:
            _say(
                f"Não achei {typed_city} ({state}, {country}) no mapa. Confira o nome."
            )
            continue
        # The geocoder normalizes the spelling ("curitiba" becomes "Curitiba"),
        # which may turn out to be a city we already have.
        known_city = city_data_source.find_by_name(location.name)
        if known_city is not None:
            return known_city
        return city_data_source.create_city(
            location.name, state, country, location.latitude, location.longitude
        )


def _ask_email(user_data_source: UserDataSource) -> str:
    while True:
        email = _ask_required("Qual é o seu e-mail?").lower()
        if "@" not in email or " " in email:
            _say("Esse e-mail não parece válido. Tente de novo.")
        elif user_data_source.find_by_email(email) is not None:
            _say("Esse e-mail já está em outro cadastro. Use outro, por favor.")
        else:
            return email


def _ask_yes_no(question: str) -> bool:
    while True:
        answer = _ask_required(question).lower()
        if answer in _YES_ANSWERS:
            return True
        if answer in _NO_ANSWERS:
            return False
        _say("Responda com s ou n, por favor.")


def _ask_required(question: str) -> str:
    while True:
        answer = _ask(question)
        if answer:
            return answer


def _ask(question: str) -> str:
    _say(question)
    try:
        answer = input(paint("você> ", Style.USER_PROMPT)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise _ConversationEndedError from None
    if answer.lower() in _EXIT_COMMANDS:
        raise _ConversationEndedError
    return answer


def _say(text: str) -> None:
    print(paint(text, Style.SYSTEM))


if __name__ == "__main__":
    main()
