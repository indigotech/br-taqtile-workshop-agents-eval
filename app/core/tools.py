import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from google.genai import types
from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.observability import observe_tool

logger = logging.getLogger(__name__)


class Tool[InputT: BaseModel, OutputT: BaseModel](ABC):
    """A function the model can call. The input model is the contract shown to
    the model (its JSON schema becomes the function declaration) and the output
    model is what goes back to it."""

    name: str
    description: str
    input_model: type[InputT]
    output_model: type[OutputT]

    @abstractmethod
    def run(self, arguments: InputT) -> OutputT: ...

    def declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema=_inline_references(
                self.input_model.model_json_schema()
            ),
        )


class ToolExecution(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    arguments: dict[str, Any]
    output: dict[str, Any] | None
    error: str | None
    duration_ms: float

    def as_function_response(self) -> dict[str, Any]:
        if self.error is not None:
            return {"error": self.error}
        return {"output": self.output}


class ToolRegistry:
    def __init__(self, tools: Sequence[Tool[Any, Any]]) -> None:
        self._tools = {tool.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("Tool names must be unique within a registry")

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolExecution:
        """Run a tool the model asked for, never raising: any failure becomes an
        error the model reads back, so it can retry or answer without it."""
        with observe_tool(name=name, input=arguments) as span:
            started_at = time.perf_counter()
            output, error = self._run(name, arguments)
            execution = ToolExecution(
                name=name,
                arguments=arguments,
                output=output,
                error=error,
                duration_ms=(time.perf_counter() - started_at) * 1000,
            )
            if error is None:
                span.update(output=output)
            else:
                span.update(
                    output={"error": error}, level="ERROR", status_message=error
                )
        return execution

    def declarations(self) -> list[types.FunctionDeclaration]:
        return [tool.declaration() for tool in self._tools.values()]

    def __len__(self) -> int:
        return len(self._tools)

    def _run(
        self, name: str, arguments: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, str | None]:
        tool = self._tools.get(name)
        if tool is None:
            logger.warning("Model called unknown tool %s", name)
            return None, f"Unknown tool '{name}'"
        try:
            validated_arguments = tool.input_model.model_validate(arguments)
        except ValidationError as error:
            logger.warning("Invalid arguments for tool %s: %s", name, error)
            return None, f"Invalid arguments: {error}"
        try:
            result = tool.run(validated_arguments)
        except Exception as error:
            logger.exception("Tool %s failed", name)
            return None, f"Tool failed: {error}"
        logger.info("Tool %s succeeded", name)
        return result.model_dump(mode="json"), None


def _inline_references(schema: dict[str, Any]) -> dict[str, Any]:
    """Replace Pydantic's `$defs`/`$ref` with the definitions themselves.

    Function declarations get the plainest schema possible: nested models
    otherwise arrive as references, one more JSON Schema feature the model
    provider has to support for the tool to work."""
    definitions: dict[str, Any] = schema.get("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                return resolve(definitions[node["$ref"].split("/")[-1]])
            return {
                key: resolve(value) for key, value in node.items() if key != "$defs"
            }
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    resolved: dict[str, Any] = resolve(schema)
    return resolved
