from app.agents.research_agent import build_research_agent
from app.core.agent import user_message
from tests.helpers import ScriptedModelClient, text_response


class TestResearchAgent:
    def test_suggestions_come_back_as_the_agent_text(self) -> None:
        model_client = ScriptedModelClient(
            [text_response("Festival de jazz no sábado.")]
        )
        agent = build_research_agent(model_client)

        result = agent.run([user_message("eventos em Paraty no fim de semana")])

        assert result.text == "Festival de jazz no sábado."
