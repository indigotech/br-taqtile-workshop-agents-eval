import sqlite3
from datetime import date

import httpx

from app.agents.orchestrator_agent import build_orchestrator_agent
from app.core.agent import user_message
from tests.helpers import (
    ScriptedGeminiClient,
    declared_function_names,
    function_call_response,
    mock_http_client,
    text_response,
)

_TRIP_JSON = (
    '{"destination": "Paraty", "start_date": "2026-10-03", "end_date": "2026-10-04",'
    ' "guests": 2, "budget_amount": null, "preferences": [], "missing_information": []}'
)


def _offline_http_client() -> httpx.Client:
    return mock_http_client(lambda request: httpx.Response(500))


class TestOrchestratorAgent:
    def test_every_specialist_is_available_as_a_tool(
        self, connection: sqlite3.Connection
    ) -> None:
        gemini = ScriptedGeminiClient([text_response("Pra onde vamos?")])
        agent = build_orchestrator_agent(
            gemini,
            connection,
            _offline_http_client(),
            user_id=3,
            today=date(2026, 9, 24),
        )

        agent.run([user_message("oi")])

        config = gemini.requests[0].config
        assert declared_function_names(config) == [
            "interpret_request",
            "query_database",
            "query_public_data",
            "search_web",
            "analyze_budget",
            "execute_action",
            "generate_itinerary",
        ]
        assert "id 3. Hoje é 2026-09-24." in str(config.system_instruction)

    def test_proposal_then_confirmation_books_and_returns_the_itinerary(
        self, connection: sqlite3.Connection
    ) -> None:
        gemini = ScriptedGeminiClient(
            [
                # Turn 1 — orchestrator delegates, specialists answer, proposal.
                function_call_response(
                    (
                        "interpret_request",
                        {"instructions": "Paraty 3 e 4/10, 2 pessoas"},
                    )
                ),
                text_response(_TRIP_JSON),
                function_call_response(
                    ("query_database", {"instructions": "hospedagens em Paraty p/ 2"})
                ),
                function_call_response(
                    ("search_accommodations", {"city_name": "Paraty", "guests": 2})
                ),
                text_response("Casa Caiçara (id 5), R$ 260/noite."),
                text_response("Proposta: Casa Caiçara por R$ 520. Posso reservar?"),
                # Turn 2 — user confirms: action, then itinerary.
                function_call_response(
                    (
                        "execute_action",
                        {
                            "instructions": "Usuário confirmou: id 5, 03 a 04/10, 2 pessoas"
                        },
                    )
                ),
                function_call_response(
                    (
                        "create_reservation",
                        {
                            "user_id": 3,
                            "accommodation_id": 5,
                            "check_in": "2026-10-03",
                            "check_out": "2026-10-04",
                            "guests": 2,
                        },
                    )
                ),
                function_call_response(
                    (
                        "record_decision",
                        {"user_id": 3, "summary": "Paraty", "reservation_id": 5},
                    )
                ),
                text_response("Reserva 5 confirmada."),
                function_call_response(
                    ("generate_itinerary", {"instructions": "dados + reserva 5"})
                ),
                text_response("ROTEIRO PARATY"),
                text_response("ROTEIRO PARATY"),
            ]
        )
        agent = build_orchestrator_agent(
            gemini,
            connection,
            _offline_http_client(),
            user_id=3,
            today=date(2026, 9, 24),
        )

        first_turn = agent.run([user_message("Paraty dias 3 e 4, eu e a Bia")])
        second_turn = agent.run([*first_turn.contents, user_message("pode reservar")])

        assert first_turn.text == "Proposta: Casa Caiçara por R$ 520. Posso reservar?"
        assert second_turn.text == "ROTEIRO PARATY"
        assert [execution.name for execution in second_turn.tool_executions] == [
            "execute_action",
            "generate_itinerary",
        ]
        reservation = connection.execute(
            "SELECT user_id, accommodation_id, total_price FROM reservations WHERE id = 5"
        ).fetchone()
        assert dict(reservation) == {
            "user_id": 3,
            "accommodation_id": 5,
            "total_price": 260.0,
        }
        assert len(gemini.requests) == 13
