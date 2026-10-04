import logging

from pydantic import BaseModel, ConfigDict

from app.core.messages import ChatMessage, GenerationConfig
from app.core.model_client import ModelClient
from app.core.tools import ToolExecution, ToolRegistry

logger = logging.getLogger(__name__)


class ToolLoopResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    messages: list[ChatMessage]
    tool_executions: list[ToolExecution]
    iterations: int
    stopped_by_iteration_limit: bool


def run_tool_loop(
    *,
    model_client: ModelClient,
    messages: list[ChatMessage],
    registry: ToolRegistry,
    config: GenerationConfig,
    max_iterations: int,
    model: str | None = None,
    name: str = "tool_loop",
) -> ToolLoopResult:
    """Ask the model, run every tool call it makes, hand the results back and
    repeat until it answers in plain text (or the iteration limit hits).

    Running the loop here, instead of in a framework, is what lets each tool
    call become its own Langfuse span."""
    history = list(messages)
    tool_executions: list[ToolExecution] = []
    loop_config = config.model_copy(update={"tools": registry.declarations()})
    text = ""

    for iteration in range(1, max_iterations + 1):
        reply = model_client.generate(
            messages=history,
            config=loop_config,
            model=model,
            generation_name=f"{name}.generation",
        )
        history.append(reply)
        text = reply.content or ""

        if not reply.tool_calls:
            return ToolLoopResult(
                text=text,
                messages=history,
                tool_executions=tool_executions,
                iterations=iteration,
                stopped_by_iteration_limit=False,
            )

        for tool_call in reply.tool_calls:
            execution = registry.execute(tool_call.name, tool_call.arguments)
            tool_executions.append(execution)
            history.append(
                ChatMessage(
                    role="tool",
                    tool_call_id=tool_call.id,
                    content=execution.as_tool_result(),
                )
            )

    logger.warning("%s hit the limit of %s iterations", name, max_iterations)
    return ToolLoopResult(
        text=text,
        messages=history,
        tool_executions=tool_executions,
        iterations=max_iterations,
        stopped_by_iteration_limit=True,
    )
