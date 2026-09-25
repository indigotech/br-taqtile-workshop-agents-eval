import logging
from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.observability import observe_embedding, observe_generation

logger = logging.getLogger(__name__)

# The free tier allows only a handful of requests per minute, and a single
# orchestrated turn makes a dozen or more calls: rate-limit (429) and transient
# server errors are retried with exponential backoff instead of failing the turn.
_RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=6,
    initial_delay=2.0,
    max_delay=60.0,
    http_status_codes=[429, 500, 502, 503, 504],
)


class GeminiClient:
    """Thin wrapper over the google-genai SDK: picks the model from config and
    records every call as a Langfuse generation (or embedding) with its usage."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or settings.GEMINI_MODEL
        self._client: genai.Client | None = None

    def generate(
        self,
        *,
        contents: list[types.Content],
        config: types.GenerateContentConfig,
        model: str | None = None,
        generation_name: str = "gemini",
    ) -> types.GenerateContentResponse:
        chosen_model = model or self.model
        with observe_generation(
            name=generation_name,
            model=chosen_model,
            input=_serialize_contents(contents),
            model_parameters=_model_parameters(config),
        ) as generation:
            logger.debug("Calling %s with %s messages", chosen_model, len(contents))
            response = self._generate_content(chosen_model, contents, config)
            generation.update(
                output=_serialize_response(response),
                usage_details=_usage_details(response),
                metadata=_grounding_metadata(response),
            )
        return response

    def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """One embedding vector per text, in order."""
        chosen_model = model or settings.GEMINI_EMBEDDING_MODEL
        with observe_embedding(
            name="gemini.embedding", model=chosen_model, input=texts
        ) as embedding:
            response = self._embed_content(chosen_model, texts)
            vectors = [item.values or [] for item in response.embeddings or []]
            embedding.update(
                output={
                    "vectors": len(vectors),
                    "dimensions": len(vectors[0]) if vectors else 0,
                }
            )
        return vectors

    def _generate_content(
        self,
        model: str,
        contents: list[types.Content],
        config: types.GenerateContentConfig,
    ) -> types.GenerateContentResponse:
        return self._sdk_client().models.generate_content(
            model=model, contents=contents, config=config
        )

    def _embed_content(
        self, model: str, texts: list[str]
    ) -> types.EmbedContentResponse:
        return self._sdk_client().models.embed_content(
            model=model, contents=list(texts)
        )

    def _sdk_client(self) -> genai.Client:
        # Created lazily so importing the app (and running tests with a fake
        # client) never needs a real API key.
        if self._client is None:
            self._client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                http_options=types.HttpOptions(retry_options=_RETRY_OPTIONS),
            )
        return self._client


def _serialize_contents(contents: list[types.Content]) -> list[dict[str, Any]]:
    return [content.model_dump(mode="json", exclude_none=True) for content in contents]


def _serialize_response(response: types.GenerateContentResponse) -> Any:
    if not response.candidates or response.candidates[0].content is None:
        return None
    return response.candidates[0].content.model_dump(mode="json", exclude_none=True)


def _model_parameters(config: types.GenerateContentConfig) -> dict[str, Any]:
    parameters = {
        "temperature": config.temperature,
        "top_p": config.top_p,
        "max_output_tokens": config.max_output_tokens,
        "response_mime_type": config.response_mime_type,
    }
    return {name: value for name, value in parameters.items() if value is not None}


def _usage_details(response: types.GenerateContentResponse) -> dict[str, int]:
    usage = response.usage_metadata
    if usage is None:
        return {}
    details = {
        "input": usage.prompt_token_count,
        "output": usage.candidates_token_count,
        "reasoning": usage.thoughts_token_count,
        "total": usage.total_token_count,
    }
    return {name: count for name, count in details.items() if count is not None}


def _grounding_metadata(
    response: types.GenerateContentResponse,
) -> dict[str, Any] | None:
    if not response.candidates or response.candidates[0].grounding_metadata is None:
        return None
    metadata = response.candidates[0].grounding_metadata
    return {
        "web_search_queries": metadata.web_search_queries or [],
        "sources": [
            chunk.web.uri
            for chunk in metadata.grounding_chunks or []
            if chunk.web is not None
        ],
    }
