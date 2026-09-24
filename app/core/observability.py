from collections.abc import Iterator
from contextlib import contextmanager
from functools import cache
from typing import Any

from langfuse import (
    Langfuse,
    LangfuseAgent,
    LangfuseGeneration,
    LangfuseSpan,
    LangfuseTool,
    propagate_attributes,
)

from app.core.config import settings


@contextmanager
def observe_turn(
    session_id: str, user_id: str | None, user_message: str
) -> Iterator[LangfuseSpan]:
    """One Langfuse trace per user turn, grouped into a Langfuse session per
    conversation.

    A single trace spanning a whole chat would only show its root once the chat
    ends; per-turn traces appear as soon as each answer is ready, and the
    session view still stitches the conversation back together."""
    with (
        get_langfuse().start_as_current_observation(
            name="turn", as_type="span", input=user_message
        ) as span,
        propagate_attributes(session_id=session_id, user_id=user_id, trace_name="turn"),
    ):
        yield span


@contextmanager
def observe_agent(name: str, input: Any) -> Iterator[LangfuseAgent]:
    with get_langfuse().start_as_current_observation(
        name=name, as_type="agent", input=input
    ) as span:
        yield span


@contextmanager
def observe_tool(name: str, input: Any) -> Iterator[LangfuseTool]:
    with get_langfuse().start_as_current_observation(
        name=name, as_type="tool", input=input
    ) as span:
        yield span


@contextmanager
def observe_generation(
    name: str, model: str, input: Any, model_parameters: dict[str, Any]
) -> Iterator[LangfuseGeneration]:
    with get_langfuse().start_as_current_observation(
        name=name,
        as_type="generation",
        model=model,
        input=input,
        model_parameters=model_parameters,
    ) as generation:
        yield generation


def current_trace_id() -> str | None:
    return get_langfuse().get_current_trace_id()


def flush() -> None:
    get_langfuse().flush()


@cache
def get_langfuse() -> Langfuse:
    return Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        base_url=settings.LANGFUSE_BASE_URL,
        tracing_enabled=settings.LANGFUSE_TRACING_ENABLED,
        environment=settings.ENVIRONMENT,
    )
