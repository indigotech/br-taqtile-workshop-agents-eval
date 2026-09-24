import httpx

from app.agents.public_data_agent import build_public_data_agent
from app.core.agent import user_message
from tests.helpers import (
    ScriptedGeminiClient,
    declared_function_names,
    mock_http_client,
    text_response,
)


class TestPublicDataAgent:
    def test_public_data_tools_are_declared(self) -> None:
        gemini = ScriptedGeminiClient([text_response("ok")])
        http_client = mock_http_client(lambda request: httpx.Response(500))
        agent = build_public_data_agent(gemini, http_client)

        agent.run([user_message("vai chover em Paraty?")])

        assert declared_function_names(gemini.requests[0].config) == [
            "geocode_place",
            "get_weather_forecast",
            "list_public_holidays",
        ]
