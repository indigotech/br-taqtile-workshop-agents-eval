import logging
from typing import Any

from openai import OpenAI
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ChatCompletion

from app.core.config import settings
from app.core.messages import ChatMessage, GenerationConfig, ToolCall
from app.core.observability import observe_embedding, observe_generation
from app.core.token_budget import charge_tokens, ensure_within_budget

logger = logging.getLogger(__name__)

# A single orchestrated turn makes a dozen or more calls, so a rate limit (429)
# or a transient 5xx would otherwise sink whole turns: the SDK retries those
# with exponential backoff, honoring the provider's retry-after.
_MAX_RETRIES = 5


class ModelClient:
    """Thin wrapper over the OpenAI SDK's Chat Completions: picks the model from
    config and records every call as a Langfuse generation (or embedding) with
    its usage. `MODEL_BASE_URL` points it at any provider that speaks the same
    API."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.MODEL
        self._client: OpenAI | None = None

    def generate(
        self,
        *,
        messages: list[ChatMessage],
        config: GenerationConfig,
        model: str | None = None,
        generation_name: str = "generation",
    ) -> ChatMessage:
        """The model's reply as an assistant message, ready to append to the
        history."""
        chosen_model = model or self.model
        ensure_within_budget()
        with observe_generation(
            name=generation_name,
            model=chosen_model,
            input=[
                message.model_dump(mode="json", exclude_none=True)
                for message in messages
            ],
            model_parameters=_model_parameters(config),
        ) as generation:
            logger.debug("Calling %s with %s messages", chosen_model, len(messages))
            completion = self._create_completion(chosen_model, messages, config)
            charge_tokens(_billed_tokens(completion))
            reply = _assistant_message(completion)
            generation.update(
                output=reply.model_dump(mode="json", exclude_none=True),
                usage_details=_usage_details(completion),
            )
        return reply

    def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """One embedding vector per text, in order."""
        chosen_model = model or settings.MODEL_EMBEDDING_MODEL
        with observe_embedding(
            name="embedding", model=chosen_model, input=texts
        ) as embedding:
            response = self._create_embeddings(chosen_model, texts)
            vectors = [
                item.embedding
                for item in sorted(response.data, key=lambda item: item.index)
            ]
            embedding.update(
                output={
                    "vectors": len(vectors),
                    "dimensions": len(vectors[0]) if vectors else 0,
                }
            )
        return vectors

    def _create_completion(
        self, model: str, messages: list[ChatMessage], config: GenerationConfig
    ) -> ChatCompletion:
        request: dict[str, Any] = {
            "model": model,
            "messages": _message_params(messages, config.system_prompt),
        }
        if settings.MODEL_REASONING_EFFORT is not None:
            request["reasoning_effort"] = settings.MODEL_REASONING_EFFORT
        if config.temperature is not None:
            request["temperature"] = config.temperature
        if config.tools:
            request["tools"] = [tool.as_param() for tool in config.tools]
        if config.response_json_schema is not None:
            request["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "schema": config.response_json_schema,
                },
            }
        completion: ChatCompletion = self._sdk_client().chat.completions.create(
            **request
        )
        return completion

    def _create_embeddings(
        self, model: str, texts: list[str]
    ) -> CreateEmbeddingResponse:
        return self._sdk_client().embeddings.create(model=model, input=list(texts))

    def _sdk_client(self) -> OpenAI:
        # Created lazily so importing the app (and running tests with a fake
        # client) never needs a real API key.
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.MODEL_API_KEY,
                base_url=settings.MODEL_BASE_URL,
                max_retries=_MAX_RETRIES,
            )
        return self._client


def _message_params(
    messages: list[ChatMessage], system_prompt: str | None
) -> list[dict[str, Any]]:
    system = [{"role": "system", "content": system_prompt}] if system_prompt else []
    return [*system, *(message.as_param() for message in messages)]


def _assistant_message(completion: ChatCompletion) -> ChatMessage:
    # An empty reply still has to land in the history as an assistant turn, or
    # the next call would send two user turns in a row.
    if not completion.choices:
        logger.warning("Model returned no choices")
        return ChatMessage(role="assistant")
    message = completion.choices[0].message
    return ChatMessage(
        role="assistant",
        content=message.content,
        tool_calls=[
            ToolCall(
                id=tool_call.id,
                name=tool_call.function.name,
                arguments=tool_call.function.arguments,
            )
            for tool_call in message.tool_calls or []
            if tool_call.type == "function"
        ],
    )


def _model_parameters(config: GenerationConfig) -> dict[str, Any]:
    parameters = {
        "temperature": config.temperature,
        "response_format": (
            "json_schema" if config.response_json_schema is not None else None
        ),
    }
    return {name: value for name, value in parameters.items() if value is not None}


def _usage_details(completion: ChatCompletion) -> dict[str, int]:
    usage = completion.usage
    if usage is None:
        return {}
    details = {
        "input": usage.prompt_tokens,
        "output": usage.completion_tokens,
        "reasoning": (
            usage.completion_tokens_details.reasoning_tokens
            if usage.completion_tokens_details is not None
            else None
        ),
        "total": usage.total_tokens,
    }
    return {name: count for name, count in details.items() if count is not None}


def _billed_tokens(completion: ChatCompletion) -> int:
    if completion.usage is None:
        return 0
    return completion.usage.prompt_tokens + completion.usage.completion_tokens
