import sqlite3

from app.agents.database_agent import build_database_agent
from app.core.agent import user_message
from tests.helpers import (
    ScriptedGeminiClient,
    declared_function_names,
    function_call_response,
    text_response,
)


class TestDatabaseAgent:
    def test_prompt_names_the_user_and_all_database_tools_are_declared(
        self, connection: sqlite3.Connection
    ) -> None:
        gemini = ScriptedGeminiClient([text_response("ok")])
        agent = build_database_agent(gemini, connection, user_id=2)

        agent.run([user_message("qual meu orçamento?")])

        config = gemini.requests[0].config
        assert "id 2" in str(config.system_instruction)
        assert declared_function_names(config) == [
            "get_user_profile",
            "list_user_reservations",
            "search_accommodations",
        ]

    def test_tool_results_come_from_the_real_database(
        self, connection: sqlite3.Connection
    ) -> None:
        gemini = ScriptedGeminiClient(
            [
                function_call_response(("get_user_profile", {"user_id": 2})),
                text_response("Seu orçamento é R$ 600."),
            ]
        )
        agent = build_database_agent(gemini, connection, user_id=2)

        result = agent.run([user_message("qual meu orçamento?")])

        assert result.tool_executions[0].output is not None
        assert result.tool_executions[0].output["budget"]["total_amount"] == 600.0
