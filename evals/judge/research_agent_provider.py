"""Provider do promptfoo: manda o prompt de cada teste para o agente de pesquisa e
devolve a resposta dele para o juiz avaliar."""

import uuid
from typing import Any

from app.agents.research_agent import build_research_agent
from app.core.agent import user_message
from app.core.model_client import ModelClient, prompt_cache_session
from app.core.observability import flush, observe_turn
from app.core.token_budget import turn_token_budget


def call_api(
    prompt: str, options: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    session_id = f"llm-judge-{uuid.uuid4().hex[:8]}"
    try:
        with (
            prompt_cache_session(session_id),
            turn_token_budget(),
            observe_turn(
                session_id=session_id,
                user_id=None,
                user_message=prompt,
                tags=["llm-judge"],
            ),
        ):
            agent = build_research_agent(ModelClient())
            return {"output": agent.run([user_message(prompt)]).text}
    finally:
        # promptfoo may end the Python process right after the call, before
        # Langfuse's background exporter sends anything.
        flush()
