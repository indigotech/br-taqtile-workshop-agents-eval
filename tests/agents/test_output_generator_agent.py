from app.agents.output_generator_agent import build_output_generator_agent
from app.core.agent import user_message
from tests.helpers import ScriptedModelClient, text_response


class TestOutputGeneratorAgent:
    def test_writes_from_the_given_data_without_tools(self) -> None:
        model_client = ScriptedModelClient([text_response("Roteiro: ...")])
        agent = build_output_generator_agent(model_client)

        result = agent.run([user_message("dados levantados: ...")])

        assert (model_client.requests[0].config.tools, result.text) == (
            [],
            "Roteiro: ...",
        )
