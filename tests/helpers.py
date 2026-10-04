import itertools
import json
from collections.abc import Callable
from typing import Any

import httpx
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ChatCompletion
from pydantic import BaseModel, ConfigDict

from app.core.messages import ChatMessage, GenerationConfig
from app.core.model_client import ModelClient
from app.core.tools import Tool


class ScriptedModelClient(ModelClient):
    """Replays canned responses in order instead of calling the API, and keeps
    every request so tests can assert on what the model was sent."""

    def __init__(
        self,
        responses: list[ChatCompletion],
        embeddings: dict[str, list[float]] | None = None,
    ) -> None:
        super().__init__(model="scripted-model")
        self._responses = list(responses)
        self._embeddings = embeddings or {}
        self.requests: list[ScriptedRequest] = []
        self.embedded_texts: list[str] = []

    def _create_completion(
        self, model: str, messages: list[ChatMessage], config: GenerationConfig
    ) -> ChatCompletion:
        self.requests.append(
            ScriptedRequest(model=model, messages=list(messages), config=config)
        )
        if not self._responses:
            raise AssertionError("ScriptedModelClient ran out of responses")
        return self._responses.pop(0)

    def _create_embeddings(
        self, model: str, texts: list[str]
    ) -> CreateEmbeddingResponse:
        self.embedded_texts.extend(texts)
        return CreateEmbeddingResponse.model_validate(
            {
                "object": "list",
                "model": model,
                "data": [
                    {
                        "object": "embedding",
                        "index": index,
                        "embedding": self._embeddings[text],
                    }
                    for index, text in enumerate(texts)
                ],
                "usage": {"prompt_tokens": len(texts), "total_tokens": len(texts)},
            }
        )


class ScriptedRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    model: str
    messages: list[ChatMessage]
    config: GenerationConfig


def text_response(text: str) -> ChatCompletion:
    return _completion({"role": "assistant", "content": text})


def function_call_response(*calls: tuple[str, dict[str, Any]]) -> ChatCompletion:
    return _completion(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": f"call_{next(_call_ids)}",
                    "type": "function",
                    "function": {"name": name, "arguments": json.dumps(arguments)},
                }
                for name, arguments in calls
            ],
        }
    )


_call_ids = itertools.count(1)


def _completion(message: dict[str, Any]) -> ChatCompletion:
    return ChatCompletion.model_validate(
        {
            "id": "completion",
            "object": "chat.completion",
            "created": 0,
            "model": "scripted-model",
            "choices": [{"index": 0, "finish_reason": "stop", "message": message}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
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


def declared_function_names(config: GenerationConfig) -> list[str]:
    return [declaration.name for declaration in config.tools]


def mock_http_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))
