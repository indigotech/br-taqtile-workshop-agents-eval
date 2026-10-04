from pydantic import BaseModel

from app.core.agent import Agent, user_message
from tests.helpers import (
    EchoTool,
    ScriptedModelClient,
    function_call_response,
    text_response,
)


class TestAgentRun:
    def test_agent_settings_reach_the_model_request(self) -> None:
        model_client = ScriptedModelClient([text_response("oi")])
        agent = Agent(
            name="tester",
            system_prompt="Seja breve.",
            model_client=model_client,
            model="other-model",
            temperature=0.9,
        )

        agent.run([user_message("olá")])

        request = model_client.requests[0]
        assert (
            request.model,
            request.config.system_prompt,
            request.config.temperature,
            request.config.tools,
        ) == ("other-model", "Seja breve.", 0.9, [])

    def test_result_carries_tool_executions_and_full_history(self) -> None:
        model_client = ScriptedModelClient(
            [function_call_response(("echo", {"message": "x"})), text_response("x")]
        )
        agent = Agent(
            name="tester",
            system_prompt="",
            model_client=model_client,
            tools=[EchoTool()],
        )

        result = agent.run([user_message("ecoa x")])

        assert (result.agent_name, result.text, len(result.messages)) == (
            "tester",
            "x",
            4,
        )
        assert [execution.name for execution in result.tool_executions] == ["echo"]

    def test_model_defaults_to_the_client_model(self) -> None:
        model_client = ScriptedModelClient([text_response("oi")])
        agent = Agent(name="tester", system_prompt="", model_client=model_client)

        agent.run([user_message("olá")])

        assert model_client.requests[0].model == "scripted-model"


class Destination(BaseModel):
    city: str


class TestStructuredOutput:
    def test_response_model_requests_json_with_its_schema(self) -> None:
        model_client = ScriptedModelClient([text_response('{"city": "Paraty"}')])
        agent = Agent(
            name="tester",
            system_prompt="",
            model_client=model_client,
            response_model=Destination,
        )

        result = agent.run([user_message("quero ir pra Paraty")])

        config = model_client.requests[0].config
        assert config.response_json_schema == Destination.model_json_schema()
        assert result.text == '{"city": "Paraty"}'
