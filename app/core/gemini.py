import logging
from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.observability import observe_generation

logger = logging.getLogger(__name__)


class GeminiClient:
    """Thin wrapper over the google-genai SDK: picks the model from config and
    records every call as a Langfuse generation with its token usage."""

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
            )
        return response

    def _generate_content(
        self,
        model: str,
        contents: list[types.Content],
        config: types.GenerateContentConfig,
    ) -> types.GenerateContentResponse:
        # Created lazily so importing the app (and running tests with a fake
        # client) never needs a real API key.
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client.models.generate_content(
            model=model, contents=contents, config=config
        )


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
