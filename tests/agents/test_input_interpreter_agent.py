from datetime import date

from app.agents.input_interpreter_agent import (
    TripRequest,
    build_input_interpreter_agent,
)
from app.core.agent import user_message
from tests.helpers import ScriptedGeminiClient, text_response


class TestInputInterpreterAgent:
    def test_prompt_anchors_relative_dates_on_today(self) -> None:
        gemini = ScriptedGeminiClient([text_response("{}")])
        agent = build_input_interpreter_agent(gemini, today=date(2026, 9, 24))

        agent.run([user_message("quero ir pra Paraty no próximo fim de semana")])

        assert "Hoje é quinta-feira, 2026-09-24." in str(
            gemini.requests[0].config.system_instruction
        )

    def test_requests_json_in_the_trip_request_schema(self) -> None:
        gemini = ScriptedGeminiClient([text_response("{}")])
        agent = build_input_interpreter_agent(gemini, today=date(2026, 9, 24))

        agent.run([user_message("oi")])

        config = gemini.requests[0].config
        assert (config.response_mime_type, config.response_json_schema) == (
            "application/json",
            TripRequest.model_json_schema(),
        )

    def test_well_formed_answer_validates_into_a_trip_request(self) -> None:
        answer = (
            '{"destination": "Paraty", "start_date": "2026-10-03",'
            ' "end_date": "2026-10-04", "guests": 2, "budget_amount": null,'
            ' "preferences": ["frutos do mar"], "missing_information": []}'
        )
        gemini = ScriptedGeminiClient([text_response(answer)])
        agent = build_input_interpreter_agent(gemini, today=date(2026, 9, 24))

        result = agent.run([user_message("Paraty dias 3 e 4, eu e minha namorada")])

        assert TripRequest.model_validate_json(result.text).model_dump() == {
            "destination": "Paraty",
            "start_date": date(2026, 10, 3),
            "end_date": date(2026, 10, 4),
            "guests": 2,
            "budget_amount": None,
            "preferences": ["frutos do mar"],
            "missing_information": [],
        }
