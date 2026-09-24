from app.agents.research_agent import build_research_agent
from app.core.agent import user_message
from tests.helpers import ScriptedGeminiClient, text_response


class TestResearchAgent:
    def test_suggestions_come_back_as_the_agent_text(self) -> None:
        gemini = ScriptedGeminiClient([text_response("Festival de jazz no sábado.")])
        agent = build_research_agent(gemini)

        result = agent.run([user_message("eventos em Paraty no fim de semana")])

        assert result.text == "Festival de jazz no sábado."
