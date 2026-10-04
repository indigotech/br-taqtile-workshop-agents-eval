from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.config import settings
from app.core.messages import ChatMessage, GenerationConfig, history_for_next_turn
from app.core.model_client import ModelClient
from app.core.observability import observe_agent
from app.core.tool_loop import run_tool_loop
from app.core.tools import Tool, ToolExecution, ToolRegistry


class AgentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    agent_name: str
    text: str
    messages: list[ChatMessage]
    tool_executions: list[ToolExecution]
    stopped_by_iteration_limit: bool

    def next_turn_history(self) -> list[ChatMessage]:
        return history_for_next_turn(self.messages)


class Agent:
    """An LLM with a system prompt and a set of tools, run through the shared
    tool loop inside its own Langfuse agent span.

    Model, temperature and iteration limit are per agent so each one can be
    tuned (or deliberately mistuned) on its own. `response_model` asks for JSON
    matching that model's schema — the text still comes back unparsed, so a
    caller or an eval decides what to do when it does not validate."""

    def __init__(
        self,
        *,
        name: str,
        system_prompt: str,
        model_client: ModelClient,
        tools: Sequence[Tool[Any, Any]] = (),
        response_model: type[BaseModel] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_iterations: int | None = None,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.model_client = model_client
        self.registry = ToolRegistry(tools)
        self.response_model = response_model
        self.model = model
        self.temperature = temperature
        self.max_iterations = max_iterations or settings.TOOL_LOOP_MAX_ITERATIONS

    def run(self, messages: list[ChatMessage]) -> AgentResult:
        with observe_agent(name=self.name, input=_last_user_text(messages)) as span:
            loop_result = run_tool_loop(
                model_client=self.model_client,
                messages=messages,
                registry=self.registry,
                config=self._config(),
                max_iterations=self.max_iterations,
                model=self.model,
                name=self.name,
            )
            span.update(
                output=loop_result.text,
                metadata={
                    "iterations": loop_result.iterations,
                    "tool_calls": len(loop_result.tool_executions),
                    "stopped_by_iteration_limit": (
                        loop_result.stopped_by_iteration_limit
                    ),
                },
            )
        return AgentResult(
            agent_name=self.name,
            text=loop_result.text,
            messages=loop_result.messages,
            tool_executions=loop_result.tool_executions,
            stopped_by_iteration_limit=loop_result.stopped_by_iteration_limit,
        )

    def _config(self) -> GenerationConfig:
        return GenerationConfig(
            system_prompt=self.system_prompt,
            temperature=self.temperature,
            response_json_schema=(
                self.response_model.model_json_schema()
                if self.response_model is not None
                else None
            ),
        )


def user_message(text: str) -> ChatMessage:
    return ChatMessage(role="user", content=text)


def _last_user_text(messages: list[ChatMessage]) -> str | None:
    for message in reversed(messages):
        if message.role == "user" and message.content:
            return message.content
    return None
