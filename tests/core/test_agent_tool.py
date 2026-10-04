from app.core.agent import Agent
from app.core.agent_tool import AgentTool
from app.core.tools import ToolRegistry
from tests.helpers import ScriptedModelClient, text_response


class TestAgentTool:
    def test_instructions_become_the_sub_agent_only_message(self) -> None:
        model_client = ScriptedModelClient([text_response("Feito.")])
        agent = Agent(name="helper", system_prompt="Ajude.", model_client=model_client)
        registry = ToolRegistry(
            [AgentTool(agent, name="ask_helper", description="Pede ajuda")]
        )

        execution = registry.execute("ask_helper", {"instructions": "Faça X"})

        assert execution.output == {"response": "Feito."}
        assert [
            message.model_dump(exclude_none=True)
            for message in model_client.requests[0].messages
        ] == [{"role": "user", "content": "Faça X", "tool_calls": []}]

    def test_declaration_uses_the_given_name_and_description(self) -> None:
        agent = Agent(
            name="helper", system_prompt="", model_client=ScriptedModelClient([])
        )

        declaration = AgentTool(
            agent, name="ask_helper", description="Pede ajuda"
        ).declaration()

        assert (declaration.name, declaration.description) == (
            "ask_helper",
            "Pede ajuda",
        )
