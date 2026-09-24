from google.genai import types

from app.agents.research_agent import build_research_agent
from app.core.agent import user_message
from tests.helpers import ScriptedGeminiClient, grounded_text_response


class TestResearchAgent:
    def test_uses_google_search_and_no_function_declarations(self) -> None:
        gemini = ScriptedGeminiClient(
            [
                grounded_text_response(
                    "Festival de jazz no sábado.",
                    queries=["eventos paraty setembro 2026"],
                    sources=[("Paraty Jazz", "https://example.com/jazz")],
                )
            ]
        )
        agent = build_research_agent(gemini)

        result = agent.run([user_message("eventos em Paraty no fim de semana")])

        assert gemini.requests[0].config.tools == [
            types.Tool(google_search=types.GoogleSearch())
        ]
        assert (
            result.web_search_queries,
            [source.uri for source in result.sources],
        ) == (
            ["eventos paraty setembro 2026"],
            ["https://example.com/jazz"],
        )
