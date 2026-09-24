from typing import Any

import pytest
from pydantic import BaseModel

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
        assert execution.as_function_response() == {"output": {"echoed": "oioi"}}

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

        assert execution.as_function_response() == {"error": "Unknown tool 'missing'"}

    def test_exception_inside_the_tool_becomes_an_error_for_the_model(self) -> None:
        registry = ToolRegistry([ExplodingTool()])

        execution = registry.execute("explode", {"message": "oi"})

        assert execution.as_function_response() == {"error": "Tool failed: boom"}


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
                "parameters_json_schema": schema,
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

        assert declaration.parameters_json_schema == {
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
