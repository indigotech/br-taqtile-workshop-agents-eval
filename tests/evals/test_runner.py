from datetime import date

import httpx
from google.genai import errors, types

from app.evals.dataset import EvalCase, ExpectedTrip
from app.evals.runner import run_case
from tests.helpers import (
    ScriptedGeminiClient,
    function_call_response,
    mock_http_client,
    text_response,
)


def _case(messages: list[str]) -> EvalCase:
    return EvalCase(
        id="paraty",
        description="d",
        user_id=3,
        messages=messages,
        expected_trip=ExpectedTrip(
            destination="Paraty",
            start_date=date(2026, 10, 3),
            end_date=date(2026, 10, 4),
            guests=2,
        ),
        required_agents=[],
        user_preferences=[],
        confirmation_message_index=1,
        max_lodging_total=None,
        reference_answer=None,
    )


def _offline_http_client() -> httpx.Client:
    return mock_http_client(lambda request: httpx.Response(500))


class FailingGeminiClient(ScriptedGeminiClient):
    def _generate_content(
        self,
        model: str,
        contents: list[types.Content],
        config: types.GenerateContentConfig,
    ) -> types.GenerateContentResponse:
        raise errors.APIError(
            429,
            {
                "error": {
                    "code": 429,
                    "message": "quota",
                    "status": "RESOURCE_EXHAUSTED",
                }
            },
        )


class TestRunCase:
    def test_each_turn_records_agent_calls_and_reservations(self) -> None:
        gemini = ScriptedGeminiClient(
            [
                text_response("Casa Caiçara por R$ 260. Posso reservar?"),
                function_call_response(
                    ("execute_action", {"instructions": "reservar id 5, 03 a 04/10"})
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
                text_response("Reserva 5 feita."),
                text_response("Pronto, reservado!"),
            ]
        )

        record = run_case(
            _case(["Paraty dias 3 e 4", "pode reservar"]),
            run_index=2,
            gemini=gemini,
            http_client=_offline_http_client(),
            today=date(2026, 9, 24),
        )

        first_turn, second_turn = record.turns
        assert record.session_id.startswith("eval-paraty-2-")
        assert (record.run_index, record.model, record.run_date) == (
            2,
            "scripted-model",
            date(2026, 9, 24),
        )
        assert (
            first_turn.response,
            first_turn.agent_calls,
            first_turn.reservations_created,
        ) == (
            "Casa Caiçara por R$ 260. Posso reservar?",
            [],
            [],
        )
        assert [call.model_dump() for call in second_turn.agent_calls] == [
            {
                "name": "execute_action",
                "instructions": "reservar id 5, 03 a 04/10",
                "response": "Reserva 5 feita.",
                "error": None,
            }
        ]
        assert [
            (reservation.id, reservation.total_price)
            for reservation in second_turn.reservations_created
        ] == [(5, 260.0)]
        assert (second_turn.response, second_turn.error) == ("Pronto, reservado!", None)

    def test_api_error_ends_the_run_and_is_recorded(self) -> None:
        record = run_case(
            _case(["Paraty dias 3 e 4", "pode reservar"]),
            run_index=1,
            gemini=FailingGeminiClient([]),
            http_client=_offline_http_client(),
            today=date(2026, 9, 24),
        )

        assert len(record.turns) == 1
        assert record.turns[0].error == "429 RESOURCE_EXHAUSTED: quota"

    def test_runs_never_share_reservations(self) -> None:
        def booking_gemini() -> ScriptedGeminiClient:
            return ScriptedGeminiClient(
                [
                    function_call_response(
                        ("execute_action", {"instructions": "id 5"})
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
                    text_response("ok"),
                    text_response("ok"),
                ]
            )

        records = [
            run_case(
                _case(["reserve"]),
                run_index=run_index,
                gemini=booking_gemini(),
                http_client=_offline_http_client(),
                today=date(2026, 9, 24),
            )
            for run_index in (1, 2)
        ]

        assert [
            [reservation.id for reservation in record.turns[0].reservations_created]
            for record in records
        ] == [[5], [5]]
