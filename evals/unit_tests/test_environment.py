"""Confere o .env antes do workshop: o primeiro teste chama o modelo de verdade,
o segundo manda um trace para o Langfuse Cloud e espera ele aparecer lá. Rode
com make test-model TEST_PATH=evals/unit_tests/test_environment.py RUNS=1."""

import time
from datetime import UTC, datetime, timedelta

import pytest
from langfuse.api import UnauthorizedError

from app.core.agent import user_message
from app.core.config import settings
from app.core.messages import GenerationConfig
from app.core.model_client import ModelClient
from app.core.observability import current_trace_id, flush, get_langfuse

# Langfuse Cloud ingests in the background, so a fresh trace takes a few seconds
# to become readable through its API.
TRACE_WAIT_SECONDS = 60
TRACE_POLL_SECONDS = 3


def test_model_answers(model_client: ModelClient) -> None:
    reply = model_client.generate(
        messages=[user_message("Responda apenas com a palavra: ok")],
        config=GenerationConfig(),
    )

    assert reply.content, f"o modelo {settings.MODEL} respondeu vazio"


def test_trace_reaches_langfuse(model_client: ModelClient) -> None:
    if not settings.LANGFUSE_TRACING_ENABLED:
        pytest.fail(
            "tracing desligado: preencha LANGFUSE_PUBLIC_KEY e LANGFUSE_SECRET_KEY "
            "no .env e deixe LANGFUSE_TRACING_ENABLED=true"
        )
    langfuse = get_langfuse()
    try:
        langfuse.auth_check()
    except UnauthorizedError:
        pytest.fail(
            f"o Langfuse em {settings.LANGFUSE_BASE_URL} recusou as chaves do .env: "
            "confira LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY e se LANGFUSE_BASE_URL "
            "é a região do seu projeto"
        )

    started_at = datetime.now(UTC) - timedelta(minutes=1)
    model_client.generate(
        messages=[user_message("Responda apenas com a palavra: ok")],
        config=GenerationConfig(),
    )
    trace_id = current_trace_id()
    assert trace_id is not None
    flush()

    deadline = time.monotonic() + TRACE_WAIT_SECONDS
    while time.monotonic() < deadline:
        # The v2 observations endpoint, since organizations created from
        # September 2026 on no longer have the legacy GET /traces/{id}.
        observations = langfuse.api.observations.get_many(
            trace_id=trace_id, from_start_time=started_at, limit=1
        )
        if observations.data:
            return
        time.sleep(TRACE_POLL_SECONDS)
    pytest.fail(
        f"o trace {trace_id} não apareceu em {settings.LANGFUSE_BASE_URL} em "
        f"{TRACE_WAIT_SECONDS} s: confira se LANGFUSE_BASE_URL é a região do seu projeto"
    )
