from google.genai import types

from app.core.agent import user_message
from app.core.tool_loop import run_tool_loop
from app.core.tools import ToolRegistry
from tests.helpers import (
    EchoTool,
    ScriptedGeminiClient,
    function_call_response,
    text_response,
)


class TestRunToolLoop:
    def test_plain_text_answer_ends_the_loop_without_tool_calls(self) -> None:
        gemini = ScriptedGeminiClient([text_response("Olá!")])

        result = run_tool_loop(
            gemini=gemini,
            contents=[user_message("oi")],
            registry=ToolRegistry([EchoTool()]),
            config=types.GenerateContentConfig(),
            max_iterations=5,
        )

        assert (result.text, result.iterations, result.tool_executions) == (
            "Olá!",
            1,
            [],
        )
        assert result.stopped_by_iteration_limit is False

    def test_function_call_result_is_sent_back_before_the_final_answer(
        self,
    ) -> None:
        gemini = ScriptedGeminiClient(
            [
                function_call_response(("echo", {"message": "ab", "times": 2})),
                text_response("Pronto: abab"),
            ]
        )

        result = run_tool_loop(
            gemini=gemini,
            contents=[user_message("repete ab duas vezes")],
            registry=ToolRegistry([EchoTool()]),
            config=types.GenerateContentConfig(),
            max_iterations=5,
        )

        assert result.text == "Pronto: abab"
        assert [execution.output for execution in result.tool_executions] == [
            {"echoed": "abab"}
        ]
        second_request_last_content = gemini.requests[1].contents[-1]
        assert second_request_last_content.model_dump(exclude_none=True) == {
            "role": "user",
            "parts": [
                {
                    "function_response": {
                        "name": "echo",
                        "response": {"output": {"echoed": "abab"}},
                    }
                }
            ],
        }
        assert [content.role for content in result.contents] == [
            "user",
            "model",
            "user",
            "model",
        ]

    def test_parallel_function_calls_are_all_answered_in_one_turn(self) -> None:
        gemini = ScriptedGeminiClient(
            [
                function_call_response(
                    ("echo", {"message": "a"}), ("echo", {"message": "b"})
                ),
                text_response("ok"),
            ]
        )

        result = run_tool_loop(
            gemini=gemini,
            contents=[user_message("oi")],
            registry=ToolRegistry([EchoTool()]),
            config=types.GenerateContentConfig(),
            max_iterations=5,
        )

        assert [execution.output for execution in result.tool_executions] == [
            {"echoed": "a"},
            {"echoed": "b"},
        ]
        assert len(gemini.requests) == 2

    def test_model_that_never_stops_calling_tools_is_cut_at_the_limit(self) -> None:
        gemini = ScriptedGeminiClient(
            [function_call_response(("echo", {"message": "de novo"}))] * 3
        )

        result = run_tool_loop(
            gemini=gemini,
            contents=[user_message("oi")],
            registry=ToolRegistry([EchoTool()]),
            config=types.GenerateContentConfig(),
            max_iterations=3,
        )

        assert (result.iterations, result.stopped_by_iteration_limit) == (3, True)
        assert len(result.tool_executions) == 3

    def test_tools_are_declared_and_automatic_function_calling_is_disabled(
        self,
    ) -> None:
        gemini = ScriptedGeminiClient([text_response("ok")])

        run_tool_loop(
            gemini=gemini,
            contents=[user_message("oi")],
            registry=ToolRegistry([EchoTool()]),
            config=types.GenerateContentConfig(temperature=0.2),
            max_iterations=1,
        )

        config = gemini.requests[0].config
        assert config.temperature == 0.2
        assert config.automatic_function_calling == (
            types.AutomaticFunctionCallingConfig(disable=True)
        )
        assert config.tools == [
            types.Tool(function_declarations=[EchoTool().declaration()])
        ]
