from app.agents.output_generator_agent import build_output_generator_agent
from app.core.agent import user_message
from tests.helpers import ScriptedGeminiClient, text_response


class TestOutputGeneratorAgent:
    def test_writes_from_the_given_data_without_tools(self) -> None:
        gemini = ScriptedGeminiClient([text_response("Roteiro: ...")])
        agent = build_output_generator_agent(gemini)

        result = agent.run([user_message("dados levantados: ...")])

        config = gemini.requests[0].config
        assert (config.tools, config.response_mime_type, result.text) == (
            None,
            None,
            "Roteiro: ...",
        )
        assert "R$ 1.234,56" in str(config.system_instruction)
