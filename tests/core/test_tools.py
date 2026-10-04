from typing import Any

import pytest
from pydantic import BaseModel

from app.core.config import settings
from app.core.tools import Tool, ToolRegistry
from tests.helpers import EchoInput, EchoTool, ExplodingTool


class TestExecute:
    def test_valid_call_returns_the_tool_output(self) -> None:
        registry = ToolRegistry([EchoTool()])

        execution = registry.execute("echo", {"message": "oi", "times": 2})

        assert execution.model_dump(exclude={"duration_ms"}) == {
            "name": "echo",
            "arguments": {"message": "oi", "times": 2},
            "output": {"echoed": "oioi"},
            "error": None,
        }
        assert execution.as_tool_result() == '{"output": {"echoed": "oioi"}}'

    def test_arguments_failing_the_input_model_become_an_error_for_the_model(
        self,
    ) -> None:
        registry = ToolRegistry([EchoTool()])

        execution = registry.execute("echo", {"times": 2})

        assert execution.output is None
        assert execution.error is not None
        assert execution.error.startswith("Invalid arguments:")

    def test_unknown_tool_becomes_an_error_for_the_model(self) -> None:
        registry = ToolRegistry([EchoTool()])

        execution = registry.execute("missing", {})

        assert execution.as_tool_result() == '{"error": "Unknown tool \'missing\'"}'

    def test_exception_inside_the_tool_becomes_an_error_for_the_model(self) -> None:
        registry = ToolRegistry([ExplodingTool()])

        execution = registry.execute("explode", {"message": "oi"})

        assert execution.as_tool_result() == '{"error": "Tool failed: boom"}'

    def test_tool_forced_to_fail_returns_a_timeout_while_others_still_run(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "FORCE_TOOL_ERROR", "explode")
        registry = ToolRegistry([EchoTool(), ExplodingTool()])

        forced = registry.execute("explode", {"message": "oi"})
        untouched = registry.execute("echo", {"message": "oi", "times": 1})

        assert (forced.as_tool_result(), untouched.output) == (
            '{"error": "Tool failed: timed out"}',
            {"echoed": "oi"},
        )

    def test_raw_json_arguments_from_the_model_are_parsed(self) -> None:
        registry = ToolRegistry([EchoTool()])

        execution = registry.execute("echo", '{"message": "oi", "times": 2}')

        assert (execution.arguments, execution.output) == (
            {"message": "oi", "times": 2},
            {"echoed": "oioi"},
        )

    def test_malformed_json_arguments_become_an_error_for_the_model(self) -> None:
        registry = ToolRegistry([EchoTool()])

        execution = registry.execute("echo", '{"message": ')

        assert execution.output is None
        assert execution.error is not None
        assert execution.error.startswith("Arguments are not valid JSON:")


class TestRegistry:
    def test_duplicate_tool_names_are_rejected(self) -> None:
        with pytest.raises(ValueError, match="unique"):
            ToolRegistry([EchoTool(), EchoTool()])

    def test_declaration_exposes_the_input_model_json_schema(self) -> None:
        declarations = ToolRegistry([EchoTool()]).declarations()

        schema: dict[str, Any] = EchoInput.model_json_schema()
        assert [
            declaration.model_dump(exclude_none=True) for declaration in declarations
        ] == [
            {
                "name": "echo",
                "description": "Repeats a message",
                "parameters": schema,
            }
        ]


class Stop(BaseModel):
    city: str


class ItineraryInput(BaseModel):
    stops: list[Stop]


class ItineraryTool(Tool[ItineraryInput, Stop]):
    name = "itinerary"
    description = "Takes nested models"
    input_model = ItineraryInput
    output_model = Stop

    def run(self, arguments: ItineraryInput) -> Stop:
        return arguments.stops[0]


class TestDeclaration:
    def test_nested_models_are_inlined_instead_of_referenced(self) -> None:
        declaration = ItineraryTool().declaration()

        assert declaration.parameters == {
            "properties": {
                "stops": {
                    "items": {
                        "properties": {"city": {"title": "City", "type": "string"}},
                        "required": ["city"],
                        "title": "Stop",
                        "type": "object",
                    },
                    "title": "Stops",
                    "type": "array",
                }
            },
            "required": ["stops"],
            "title": "ItineraryInput",
            "type": "object",
        }
