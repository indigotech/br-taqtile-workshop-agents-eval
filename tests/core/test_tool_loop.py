from app.core.agent import user_message
from app.core.messages import GenerationConfig
from app.core.tool_loop import run_tool_loop
from app.core.tools import ToolRegistry
from tests.helpers import (
    EchoTool,
    ScriptedModelClient,
    function_call_response,
    text_response,
)


class TestRunToolLoop:
    def test_plain_text_answer_ends_the_loop_without_tool_calls(self) -> None:
        model_client = ScriptedModelClient([text_response("Olá!")])

        result = run_tool_loop(
            model_client=model_client,
            messages=[user_message("oi")],
            registry=ToolRegistry([EchoTool()]),
            config=GenerationConfig(),
            max_iterations=5,
        )

        assert (result.text, result.iterations, result.tool_executions) == (
            "Olá!",
            1,
            [],
        )
        assert result.stopped_by_iteration_limit is False

    def test_tool_call_result_is_sent_back_before_the_final_answer(self) -> None:
        model_client = ScriptedModelClient(
            [
                function_call_response(("echo", {"message": "ab", "times": 2})),
                text_response("Pronto: abab"),
            ]
        )

        result = run_tool_loop(
            model_client=model_client,
            messages=[user_message("repete ab duas vezes")],
            registry=ToolRegistry([EchoTool()]),
            config=GenerationConfig(),
            max_iterations=5,
        )

        assert result.text == "Pronto: abab"
        assert [execution.output for execution in result.tool_executions] == [
            {"echoed": "abab"}
        ]
        tool_call_id = result.messages[1].tool_calls[0].id
        assert model_client.requests[1].messages[-1].model_dump() == {
            "role": "tool",
            "content": '{"output": {"echoed": "abab"}}',
            "tool_calls": [],
            "tool_call_id": tool_call_id,
        }
        assert [message.role for message in result.messages] == [
            "user",
            "assistant",
            "tool",
            "assistant",
        ]

    def test_parallel_tool_calls_are_each_answered_before_the_next_request(
        self,
    ) -> None:
        model_client = ScriptedModelClient(
            [
                function_call_response(
                    ("echo", {"message": "a"}), ("echo", {"message": "b"})
                ),
                text_response("ok"),
            ]
        )

        result = run_tool_loop(
            model_client=model_client,
            messages=[user_message("oi")],
            registry=ToolRegistry([EchoTool()]),
            config=GenerationConfig(),
            max_iterations=5,
        )

        assert [execution.output for execution in result.tool_executions] == [
            {"echoed": "a"},
            {"echoed": "b"},
        ]
        assert [message.role for message in model_client.requests[1].messages] == [
            "user",
            "assistant",
            "tool",
            "tool",
        ]

    def test_model_that_never_stops_calling_tools_is_cut_at_the_limit(self) -> None:
        model_client = ScriptedModelClient(
            [function_call_response(("echo", {"message": "de novo"})) for _ in range(3)]
        )

        result = run_tool_loop(
            model_client=model_client,
            messages=[user_message("oi")],
            registry=ToolRegistry([EchoTool()]),
            config=GenerationConfig(),
            max_iterations=3,
        )

        assert (result.iterations, result.stopped_by_iteration_limit) == (3, True)
        assert len(result.tool_executions) == 3

    def test_registry_tools_are_declared_and_the_config_is_kept(self) -> None:
        model_client = ScriptedModelClient([text_response("ok")])

        run_tool_loop(
            model_client=model_client,
            messages=[user_message("oi")],
            registry=ToolRegistry([EchoTool()]),
            config=GenerationConfig(temperature=0.2),
            max_iterations=1,
        )

        config = model_client.requests[0].config
        assert (config.temperature, config.tools) == (0.2, [EchoTool().declaration()])

    def test_no_tools_at_all_declares_none(self) -> None:
        model_client = ScriptedModelClient([text_response("ok")])

        run_tool_loop(
            model_client=model_client,
            messages=[user_message("oi")],
            registry=ToolRegistry([]),
            config=GenerationConfig(),
            max_iterations=1,
        )

        assert model_client.requests[0].config.tools == []
