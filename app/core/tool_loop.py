import logging

from google.genai import types
from pydantic import BaseModel, ConfigDict

from app.core.gemini import GeminiClient
from app.core.tools import ToolExecution, ToolRegistry

logger = logging.getLogger(__name__)


class ToolLoopResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    contents: list[types.Content]
    tool_executions: list[ToolExecution]
    iterations: int
    stopped_by_iteration_limit: bool


def run_tool_loop(
    *,
    gemini: GeminiClient,
    contents: list[types.Content],
    registry: ToolRegistry,
    config: types.GenerateContentConfig,
    max_iterations: int,
    model: str | None = None,
    name: str = "tool_loop",
) -> ToolLoopResult:
    """Ask the model, run every function call it makes, hand the results back
    and repeat until it answers in plain text (or the iteration limit hits).

    The SDK's automatic function calling is disabled on purpose: running the
    loop here is what lets each tool call become its own Langfuse span."""
    history = list(contents)
    tool_executions: list[ToolExecution] = []
    loop_config = _with_tools(config, registry)
    text = ""

    for iteration in range(1, max_iterations + 1):
        response = gemini.generate(
            contents=history,
            config=loop_config,
            model=model,
            generation_name=f"{name}.generation",
        )
        model_content = _first_candidate_content(response)
        history.append(model_content)
        text = _text_of(model_content)

        function_calls = [
            part.function_call
            for part in model_content.parts or []
            if part.function_call is not None
        ]
        if not function_calls:
            return ToolLoopResult(
                text=text,
                contents=history,
                tool_executions=tool_executions,
                iterations=iteration,
                stopped_by_iteration_limit=False,
            )

        response_parts: list[types.Part] = []
        for function_call in function_calls:
            function_name = function_call.name or ""
            execution = registry.execute(function_name, function_call.args or {})
            tool_executions.append(execution)
            response_parts.append(
                types.Part.from_function_response(
                    name=function_name, response=execution.as_function_response()
                )
            )
        history.append(types.Content(role="user", parts=response_parts))

    logger.warning("%s hit the limit of %s iterations", name, max_iterations)
    return ToolLoopResult(
        text=text,
        contents=history,
        tool_executions=tool_executions,
        iterations=max_iterations,
        stopped_by_iteration_limit=True,
    )


def _with_tools(
    config: types.GenerateContentConfig, registry: ToolRegistry
) -> types.GenerateContentConfig:
    update: dict[str, object] = {
        "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True)
    }
    if len(registry) > 0:
        update["tools"] = [types.Tool(function_declarations=registry.declarations())]
    return config.model_copy(update=update)


def _first_candidate_content(
    response: types.GenerateContentResponse,
) -> types.Content:
    # An empty candidate (safety block, max tokens with no text) still has to
    # land in the history as a model turn, or the next call would send two user
    # turns in a row.
    if not response.candidates or response.candidates[0].content is None:
        logger.warning("Model returned no content")
        return types.Content(role="model", parts=[])
    return response.candidates[0].content


def _text_of(content: types.Content) -> str:
    return "".join(
        part.text for part in content.parts or [] if part.text and not part.thought
    )
