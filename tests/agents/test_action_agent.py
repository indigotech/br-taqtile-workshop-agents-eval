import sqlite3

from app.agents.action_agent import build_action_agent
from app.core.agent import user_message
from tests.helpers import (
    ScriptedGeminiClient,
    declared_function_names,
    function_call_response,
    text_response,
)


class TestActionAgent:
    def test_prompt_names_the_user_and_action_tools_are_declared(
        self, connection: sqlite3.Connection
    ) -> None:
        gemini = ScriptedGeminiClient([text_response("ok")])
        agent = build_action_agent(gemini, connection, user_id=4)

        agent.run([user_message("reserve")])

        config = gemini.requests[0].config
        assert "id 4" in str(config.system_instruction)
        assert declared_function_names(config) == [
            "search_accommodations",
            "create_reservation",
            "record_decision",
        ]

    def test_reservation_then_decision_are_written(
        self, connection: sqlite3.Connection
    ) -> None:
        gemini = ScriptedGeminiClient(
            [
                function_call_response(
                    (
                        "create_reservation",
                        {
                            "user_id": 4,
                            "accommodation_id": 11,
                            "check_in": "2026-10-10",
                            "check_out": "2026-10-11",
                            "guests": 2,
                        },
                    )
                ),
                function_call_response(
                    (
                        "record_decision",
                        {"user_id": 4, "summary": "Ouro Preto", "reservation_id": 5},
                    )
                ),
                text_response("Reserva 5 feita."),
            ]
        )
        agent = build_action_agent(gemini, connection, user_id=4)

        agent.run([user_message("usuário confirmou a Casa da Ladeira, 10 a 11/10")])

        counts = connection.execute(
            "SELECT (SELECT COUNT(*) FROM reservations WHERE user_id = 4),"
            " (SELECT COUNT(*) FROM decisions WHERE reservation_id = 5)"
        ).fetchone()
        assert tuple(counts) == (2, 1)
