from datetime import date

from app.agents.input_interpreter_agent import (
    TripRequest,
    build_input_interpreter_agent,
)
from app.core.agent import user_message
from tests.helpers import ScriptedModelClient, text_response


class TestInputInterpreterAgent:
    def test_prompt_carries_today_for_relative_dates(self) -> None:
        model_client = ScriptedModelClient([text_response("{}")])
        agent = build_input_interpreter_agent(model_client, today=date(2026, 9, 24))

        agent.run([user_message("quero ir pra Paraty no próximo fim de semana")])

        assert "Hoje é 2026-09-24." in str(
            model_client.requests[0].config.system_prompt
        )

    def test_answer_is_constrained_to_the_trip_request_schema(self) -> None:
        model_client = ScriptedModelClient([text_response("{}")])
        agent = build_input_interpreter_agent(model_client, today=date(2026, 9, 24))

        agent.run([user_message("quero ir pra Paraty")])

        assert model_client.requests[0].config.response_json_schema == (
            TripRequest.model_json_schema()
        )

    def test_well_formed_answer_validates_into_a_trip_request(self) -> None:
        answer = (
            '{"destination": "Paraty", "start_date": "2026-10-03",'
            ' "end_date": "2026-10-04", "guests": 2, "budget_amount": null,'
            ' "preferences": ["frutos do mar"]}'
        )
        model_client = ScriptedModelClient([text_response(answer)])
        agent = build_input_interpreter_agent(model_client, today=date(2026, 9, 24))

        result = agent.run([user_message("Paraty dias 3 e 4, eu e minha namorada")])

        assert TripRequest.model_validate_json(result.text).model_dump() == {
            "destination": "Paraty",
            "start_date": date(2026, 10, 3),
            "end_date": date(2026, 10, 4),
            "guests": 2,
            "budget_amount": None,
            "preferences": ["frutos do mar"],
        }
