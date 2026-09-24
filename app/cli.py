import logging
import sqlite3
import uuid

from google.genai import errors, types

from app.agents.assistant_agent import build_assistant_agent
from app.core.agent import user_message
from app.core.config import settings
from app.core.gemini import GeminiClient
from app.core.logging import setup_logging
from app.core.observability import current_trace_id, flush, get_langfuse, observe_turn
from app.data.database import connect, reset_database
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
    try:
        _chat(connection)
    finally:
        connection.close()
        flush()


def _chat(connection: sqlite3.Connection) -> None:
    user_data_source = UserDataSource(connection)
    user = _choose_user(user_data_source)
    agent = build_assistant_agent(GeminiClient(), user_data_source, user.id)
    session_id = str(uuid.uuid4())
    history: list[types.Content] = []

    print(f"\nOlá, {user.name}! Pra onde vamos? (digite 'sair' para encerrar)\n")
    while True:
        try:
            message = input("você> ").strip()
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
        except errors.APIError as error:
            # Keeps the chat alive: a bad key or a rate limit should cost one
            # message, not the whole conversation.
            logger.error("Gemini API error: %s", error)
            print(f"\n[erro na API do Gemini: {error.code} {error.status}]\n")
            continue
        history = result.contents

        print(f"\nplanejador> {result.text}\n")
        if settings.LANGFUSE_TRACING_ENABLED and trace_id:
            print(f"  trace: {get_langfuse().get_trace_url(trace_id=trace_id)}\n")


def _choose_user(user_data_source: UserDataSource) -> User:
    users = user_data_source.list_users()
    print("Quem é você?")
    for user in users:
        print(f"  {user.id}. {user.name}")
    while True:
        answer = input(f"id [{users[0].id}]> ").strip() or str(users[0].id)
        chosen = next((user for user in users if str(user.id) == answer), None)
        if chosen is not None:
            return chosen
        print("Id inválido, tente de novo.")


if __name__ == "__main__":
    main()
