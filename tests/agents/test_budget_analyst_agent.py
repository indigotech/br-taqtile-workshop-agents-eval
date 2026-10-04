import sqlite3

from app.agents.budget_analyst_agent import build_budget_analyst_agent
from app.core.agent import user_message
from app.data.user_data_source import UserDataSource
from tests.helpers import (
    ScriptedModelClient,
    declared_function_names,
    function_call_response,
    text_response,
)


class TestBudgetAnalystAgent:
    def test_prompt_names_the_user_and_budget_tools_are_declared(
        self, connection: sqlite3.Connection
    ) -> None:
        model_client = ScriptedModelClient([text_response("ok")])
        agent = build_budget_analyst_agent(
            model_client, UserDataSource(connection), user_id=2
        )

        agent.run([user_message("cabe no orçamento?")])

        config = model_client.requests[0].config
        assert "id 2" in str(config.system_prompt)
        assert declared_function_names(config) == [
            "get_user_profile",
            "calculate_budget",
        ]

    def test_budget_verdict_comes_from_the_calculation_tool(
        self, connection: sqlite3.Connection
    ) -> None:
        model_client = ScriptedModelClient(
            [
                function_call_response(
                    (
                        "calculate_budget",
                        {
                            "budget_amount": 600,
                            "items": [
                                {
                                    "category": "lodging",
                                    "description": "hotel",
                                    "amount": 700,
                                }
                            ],
                        },
                    )
                ),
                text_response("Não cabe: estoura R$ 100."),
            ]
        )
        agent = build_budget_analyst_agent(
            model_client, UserDataSource(connection), user_id=2
        )

        result = agent.run([user_message("hotel de R$ 700 cabe em R$ 600?")])

        assert result.tool_executions[0].output is not None
        assert result.tool_executions[0].output["fits_total_budget"] is False
