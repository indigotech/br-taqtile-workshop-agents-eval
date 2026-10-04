import pytest

from app.core.agent import Agent, user_message
from app.core.agent_tool import AgentTool
from app.core.config import settings
from app.core.token_budget import TokenBudgetExceededError, turn_token_budget
from tests.helpers import (
    EchoTool,
    ScriptedModelClient,
    function_call_response,
    text_response,
)


def _echo_agent(model_client: ScriptedModelClient) -> Agent:
    return Agent(
        name="echoer",
        system_prompt="Repita.",
        model_client=model_client,
        tools=[EchoTool()],
    )


class TestTurnTokenBudget:
    def test_turn_under_the_budget_completes_and_counts_every_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "MODEL_TOKEN_BUDGET_PER_TURN", 100)
        model_client = ScriptedModelClient(
            [function_call_response(("echo", {"message": "a"})), text_response("a")]
        )

        with turn_token_budget() as budget:
            result = _echo_agent(model_client).run([user_message("oi")])

        assert (result.text, budget.tokens_used) == ("a", 30)

    def test_turn_that_crosses_the_budget_makes_no_further_model_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "MODEL_TOKEN_BUDGET_PER_TURN", 20)
        model_client = ScriptedModelClient(
            [
                function_call_response(("echo", {"message": "a"})),
                function_call_response(("echo", {"message": "b"})),
                text_response("nunca enviada"),
            ]
        )

        with (
            pytest.raises(TokenBudgetExceededError) as raised,
            turn_token_budget(),
        ):
            _echo_agent(model_client).run([user_message("oi")])

        assert (raised.value.limit, raised.value.tokens_used) == (20, 30)
        assert len(model_client.requests) == 2

    def test_budget_exceeded_inside_a_sub_agent_stops_the_orchestrator(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "MODEL_TOKEN_BUDGET_PER_TURN", 20)
        model_client = ScriptedModelClient(
            [
                function_call_response(("ask_echoer", {"instructions": "repita a"})),
                function_call_response(("echo", {"message": "a"})),
                text_response("nunca enviada pelo sub-agente"),
                text_response("nunca enviada pelo orquestrador"),
            ]
        )
        orchestrator = Agent(
            name="orchestrator",
            system_prompt="Delegue.",
            model_client=model_client,
            tools=[
                AgentTool(
                    _echo_agent(model_client), name="ask_echoer", description="Repete"
                )
            ],
        )

        with pytest.raises(TokenBudgetExceededError), turn_token_budget():
            orchestrator.run([user_message("oi")])

        assert len(model_client.requests) == 2

    def test_zero_budget_never_stops_a_turn(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "MODEL_TOKEN_BUDGET_PER_TURN", 0)
        model_client = ScriptedModelClient(
            [
                *[function_call_response(("echo", {"message": "a"}))] * 5,
                text_response("fim"),
            ]
        )

        with turn_token_budget() as budget:
            result = _echo_agent(model_client).run([user_message("oi")])

        assert (result.text, budget.tokens_used) == ("fim", 90)

    def test_completion_without_usage_counts_as_zero_tokens(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "MODEL_TOKEN_BUDGET_PER_TURN", 1)
        model_client = ScriptedModelClient(
            [text_response("sem uso").model_copy(update={"usage": None})]
        )

        with turn_token_budget() as budget:
            result = _echo_agent(model_client).run([user_message("oi")])

        assert (result.text, budget.tokens_used) == ("sem uso", 0)
