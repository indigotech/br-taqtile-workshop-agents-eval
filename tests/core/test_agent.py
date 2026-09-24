from app.core.agent import Agent, user_message
from tests.helpers import (
    EchoTool,
    ScriptedGeminiClient,
    function_call_response,
    text_response,
)


class TestAgentRun:
    def test_agent_settings_reach_the_model_request(self) -> None:
        gemini = ScriptedGeminiClient([text_response("oi")])
        agent = Agent(
            name="tester",
            system_prompt="Seja breve.",
            gemini=gemini,
            model="other-model",
            temperature=0.9,
        )

        agent.run([user_message("olá")])

        request = gemini.requests[0]
        assert (
            request.model,
            request.config.system_instruction,
            request.config.temperature,
            request.config.tools,
        ) == ("other-model", "Seja breve.", 0.9, None)

    def test_result_carries_tool_executions_and_full_history(self) -> None:
        gemini = ScriptedGeminiClient(
            [function_call_response(("echo", {"message": "x"})), text_response("x")]
        )
        agent = Agent(
            name="tester", system_prompt="", gemini=gemini, tools=[EchoTool()]
        )

        result = agent.run([user_message("ecoa x")])

        assert (result.agent_name, result.text, len(result.contents)) == (
            "tester",
            "x",
            4,
        )
        assert [execution.name for execution in result.tool_executions] == ["echo"]

    def test_model_defaults_to_the_client_model(self) -> None:
        gemini = ScriptedGeminiClient([text_response("oi")])
        agent = Agent(name="tester", system_prompt="", gemini=gemini)

        agent.run([user_message("olá")])

        assert gemini.requests[0].model == "scripted-model"
