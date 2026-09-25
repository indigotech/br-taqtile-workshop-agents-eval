from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any

import httpx
from google.genai import types
from pydantic import BaseModel, ConfigDict

from app.core.gemini import GeminiClient
from app.core.tools import Tool
from app.evals.dataset import EvalCase, ExpectedTrip
from app.evals.records import RunRecord, TurnRecord


class ScriptedGeminiClient(GeminiClient):
    """Replays canned responses in order instead of calling the API, and keeps
    every request so tests can assert on what the model was sent."""

    def __init__(
        self,
        responses: list[types.GenerateContentResponse],
        embeddings: dict[str, list[float]] | None = None,
    ) -> None:
        super().__init__(model="scripted-model")
        self._responses = list(responses)
        self._embeddings = embeddings or {}
        self.requests: list[ScriptedRequest] = []
        self.embedded_texts: list[str] = []

    def _generate_content(
        self,
        model: str,
        contents: list[types.Content],
        config: types.GenerateContentConfig,
    ) -> types.GenerateContentResponse:
        self.requests.append(
            ScriptedRequest(model=model, contents=list(contents), config=config)
        )
        if not self._responses:
            raise AssertionError("ScriptedGeminiClient ran out of responses")
        return self._responses.pop(0)

    def _embed_content(
        self, model: str, texts: list[str]
    ) -> types.EmbedContentResponse:
        self.embedded_texts.extend(texts)
        return types.EmbedContentResponse(
            embeddings=[
                types.ContentEmbedding(values=self._embeddings[text]) for text in texts
            ]
        )


class ScriptedRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    model: str
    contents: list[types.Content]
    config: types.GenerateContentConfig


def text_response(text: str) -> types.GenerateContentResponse:
    return _response([types.Part.from_text(text=text)])


def function_call_response(
    *calls: tuple[str, dict[str, Any]],
) -> types.GenerateContentResponse:
    return _response(
        [types.Part.from_function_call(name=name, args=args) for name, args in calls]
    )


def _response(parts: list[types.Part]) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=parts))],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=10, candidates_token_count=5, total_token_count=15
        ),
    )


class EchoInput(BaseModel):
    message: str
    times: int = 1


class EchoOutput(BaseModel):
    echoed: str


class EchoTool(Tool[EchoInput, EchoOutput]):
    name = "echo"
    description = "Repeats a message"
    input_model = EchoInput
    output_model = EchoOutput

    def run(self, arguments: EchoInput) -> EchoOutput:
        return EchoOutput(echoed=arguments.message * arguments.times)


class ExplodingTool(Tool[EchoInput, EchoOutput]):
    name = "explode"
    description = "Always fails"
    input_model = EchoInput
    output_model = EchoOutput

    def run(self, arguments: EchoInput) -> EchoOutput:
        raise RuntimeError("boom")


def grounded_text_response(
    text: str, queries: list[str], sources: list[tuple[str, str]]
) -> types.GenerateContentResponse:
    response = text_response(text)
    assert response.candidates is not None
    response.candidates[0].grounding_metadata = types.GroundingMetadata(
        web_search_queries=queries,
        grounding_chunks=[
            types.GroundingChunk(web=types.GroundingChunkWeb(title=title, uri=uri))
            for title, uri in sources
        ],
    )
    return response


def declared_function_names(config: types.GenerateContentConfig) -> list[str]:
    return [
        declaration.name or ""
        for tool in config.tools or []
        if isinstance(tool, types.Tool)
        for declaration in tool.function_declarations or []
    ]


def mock_http_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def run_record(
    case_id: str = "paraty",
    run_index: int = 1,
    responses: tuple[str, ...] = ("ok",),
    error: str | None = None,
) -> RunRecord:
    return RunRecord(
        case=EvalCase(
            id=case_id,
            description="d",
            user_id=3,
            messages=[f"mensagem {index}" for index in range(len(responses))],
            expected_trip=ExpectedTrip(
                destination=None, start_date=None, end_date=None, guests=None
            ),
            required_agents=[],
            user_preferences=[],
            confirmation_message_index=None,
            max_lodging_total=None,
            reference_answer=None,
        ),
        run_index=run_index,
        session_id=f"eval-{case_id}-{run_index}",
        run_date=date(2026, 9, 24),
        started_at=datetime(2026, 9, 24, 12, 0, tzinfo=UTC),
        model="scripted-model",
        turns=[
            TurnRecord(
                user_message=f"mensagem {index}",
                response=response,
                agent_calls=[],
                reservations_created=[],
                trace_id=f"trace-{case_id}-{run_index}-{index}",
                latency_seconds=1.0,
                stopped_by_iteration_limit=False,
                error=error if index == len(responses) - 1 else None,
            )
            for index, response in enumerate(responses)
        ],
    )
