from app.agents.output_generator_agent import build_output_generator_agent
from app.core.agent import user_message
from tests.helpers import ScriptedGeminiClient, text_response


class TestOutputGeneratorAgent:
    def test_writes_from_the_given_data_without_tools(self) -> None:
        gemini = ScriptedGeminiClient([text_response("Roteiro: ...")])
        agent = build_output_generator_agent(gemini)

        result = agent.run([user_message("dados levantados: ...")])

        assert (gemini.requests[0].config.tools, result.text) == (None, "Roteiro: ...")
