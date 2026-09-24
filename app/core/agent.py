from collections.abc import Sequence
from typing import Any

from google.genai import types
from pydantic import BaseModel, ConfigDict

from app.core.config import settings
from app.core.gemini import GeminiClient
from app.core.observability import observe_agent
from app.core.tool_loop import WebSource, run_tool_loop
from app.core.tools import Tool, ToolExecution, ToolRegistry


class AgentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    agent_name: str
    text: str
    contents: list[types.Content]
    tool_executions: list[ToolExecution]
    web_search_queries: list[str]
    sources: list[WebSource]
    stopped_by_iteration_limit: bool


class Agent:
    """An LLM with a system prompt and a set of tools, run through the shared
    tool loop inside its own Langfuse agent span.

    Model, temperature and iteration limit are per agent so each one can be
    tuned (or deliberately mistuned) on its own. `builtin_tools` are Gemini's
    server-side tools (Google Search); `response_model` asks for JSON matching
    that model's schema — the text still comes back unparsed, so a caller or an
    eval decides what to do when it does not validate."""

    def __init__(
        self,
        *,
        name: str,
        system_prompt: str,
        gemini: GeminiClient,
        tools: Sequence[Tool[Any, Any]] = (),
        builtin_tools: Sequence[types.Tool] = (),
        response_model: type[BaseModel] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_iterations: int | None = None,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.gemini = gemini
        self.registry = ToolRegistry(tools)
        self.builtin_tools = list(builtin_tools)
        self.response_model = response_model
        self.model = model
        self.temperature = temperature
        self.max_iterations = max_iterations or settings.TOOL_LOOP_MAX_ITERATIONS

    def run(self, contents: list[types.Content]) -> AgentResult:
        with observe_agent(name=self.name, input=_last_user_text(contents)) as span:
            loop_result = run_tool_loop(
                gemini=self.gemini,
                contents=contents,
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
                    "web_search_queries": loop_result.web_search_queries,
                    "stopped_by_iteration_limit": (
                        loop_result.stopped_by_iteration_limit
                    ),
                },
            )
        return AgentResult(
            agent_name=self.name,
            text=loop_result.text,
            contents=loop_result.contents,
            tool_executions=loop_result.tool_executions,
            web_search_queries=loop_result.web_search_queries,
            sources=loop_result.sources,
            stopped_by_iteration_limit=loop_result.stopped_by_iteration_limit,
        )

    def _config(self) -> types.GenerateContentConfig:
        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            temperature=self.temperature,
            tools=list(self.builtin_tools) or None,
        )
        if self.response_model is not None:
            config.response_mime_type = "application/json"
            config.response_json_schema = self.response_model.model_json_schema()
        return config


def user_message(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part.from_text(text=text)])


def _last_user_text(contents: list[types.Content]) -> str | None:
    for content in reversed(contents):
        if content.role == "user":
            texts = [part.text for part in content.parts or [] if part.text]
            if texts:
                return "\n".join(texts)
    return None
