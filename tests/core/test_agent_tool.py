from app.core.agent import Agent
from app.core.agent_tool import AgentTool
from app.core.tools import ToolRegistry
from tests.helpers import ScriptedGeminiClient, grounded_text_response, text_response


class TestAgentTool:
    def test_instructions_become_the_sub_agent_only_message(self) -> None:
        gemini = ScriptedGeminiClient([text_response("Feito.")])
        agent = Agent(name="helper", system_prompt="Ajude.", gemini=gemini)
        registry = ToolRegistry(
            [AgentTool(agent, name="ask_helper", description="Pede ajuda")]
        )

        execution = registry.execute("ask_helper", {"instructions": "Faça X"})

        assert execution.output == {"response": "Feito.", "sources": []}
        assert [
            content.model_dump(exclude_none=True)
            for content in gemini.requests[0].contents
        ] == [{"role": "user", "parts": [{"text": "Faça X"}]}]

    def test_web_sources_of_the_sub_agent_are_passed_up(self) -> None:
        gemini = ScriptedGeminiClient(
            [
                grounded_text_response(
                    "Achei.", queries=["q"], sources=[("Site", "https://example.com")]
                )
            ]
        )
        agent = Agent(name="searcher", system_prompt="", gemini=gemini)
        registry = ToolRegistry([AgentTool(agent, name="search", description="Busca")])

        execution = registry.execute("search", {"instructions": "busque"})

        assert execution.output == {
            "response": "Achei.",
            "sources": [{"title": "Site", "uri": "https://example.com"}],
        }

    def test_declaration_uses_the_given_name_and_description(self) -> None:
        agent = Agent(name="helper", system_prompt="", gemini=ScriptedGeminiClient([]))

        declaration = AgentTool(
            agent, name="ask_helper", description="Pede ajuda"
        ).declaration()

        assert (declaration.name, declaration.description) == (
            "ask_helper",
            "Pede ajuda",
        )
