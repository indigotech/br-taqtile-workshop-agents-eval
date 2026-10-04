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
from app.core.model_client import ModelClient
from app.core.observability import current_trace_id, flush, get_langfuse, observe_turn
from app.core.terminal import Style, paint
from app.data.database import connect, reset_database
from app.data.http import build_http_client
from app.data.models import User
from app.data.user_data_source import UserDataSource

logger = logging.getLogger(__name__)

_EXIT_COMMANDS = {"sair", "exit", "quit"}


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
    user = _choose_user(UserDataSource(connection))
    agent = build_orchestrator_agent(
        ModelClient(), connection, http_client, user.id, date.today()
    )
    session_id = str(uuid.uuid4())
    history: list[ChatMessage] = []

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
            with observe_turn(
                session_id=session_id, user_id=str(user.id), user_message=message
            ) as span:
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
        history = result.messages

        print(f"\n{paint(f'planejador> {result.text}', Style.BOT_REPLY)}\n")
        if settings.LANGFUSE_TRACING_ENABLED and trace_id:
            trace_url = get_langfuse().get_trace_url(trace_id=trace_id)
            print(f"{paint(f'  trace: {trace_url}', Style.AUXILIARY)}\n")


def _choose_user(user_data_source: UserDataSource) -> User:
    users = user_data_source.list_users()
    print(paint("Quem é você?", Style.SYSTEM))
    for user in users:
        print(paint(f"  {user.id}. {user.name}", Style.SYSTEM))
    while True:
        answer = input(
            paint(f"id [{users[0].id}]> ", Style.USER_PROMPT)
        ).strip() or str(users[0].id)
        chosen = next((user for user in users if str(user.id) == answer), None)
        if chosen is not None:
            return chosen
        print(paint("Id inválido, tente de novo.", Style.SYSTEM))


if __name__ == "__main__":
    main()
