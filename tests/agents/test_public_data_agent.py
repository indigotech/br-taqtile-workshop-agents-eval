import httpx

from app.agents.public_data_agent import build_public_data_agent
from app.core.agent import user_message
from tests.helpers import (
    ScriptedModelClient,
    declared_function_names,
    mock_http_client,
    text_response,
)


class TestPublicDataAgent:
    def test_public_data_tools_are_declared(self) -> None:
        model_client = ScriptedModelClient([text_response("ok")])
        http_client = mock_http_client(lambda request: httpx.Response(500))
        agent = build_public_data_agent(model_client, http_client)

        agent.run([user_message("vai chover em Paraty?")])

        assert declared_function_names(model_client.requests[0].config) == [
            "geocode_place",
            "get_weather_forecast",
            "list_public_holidays",
        ]
