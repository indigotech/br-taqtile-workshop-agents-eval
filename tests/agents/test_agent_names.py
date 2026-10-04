import sqlite3
from datetime import date

import httpx

from app.agents.action_agent import build_action_agent
from app.agents.budget_analyst_agent import build_budget_analyst_agent
from app.agents.database_agent import build_database_agent
from app.agents.input_interpreter_agent import build_input_interpreter_agent
from app.agents.orchestrator_agent import build_orchestrator_agent
from app.agents.output_generator_agent import build_output_generator_agent
from app.agents.public_data_agent import build_public_data_agent
from app.agents.research_agent import build_research_agent
from app.data.user_data_source import UserDataSource
from tests.helpers import ScriptedModelClient, mock_http_client


class TestAgentNames:
    def test_every_agent_name_ends_in_agent_so_it_stands_out_in_traces(
        self, connection: sqlite3.Connection
    ) -> None:
        model_client = ScriptedModelClient([])
        http_client = mock_http_client(lambda request: httpx.Response(500))
        today = date(2026, 9, 24)

        agents = [
            build_orchestrator_agent(
                model_client, connection, http_client, user_id=3, today=today
            ),
            build_input_interpreter_agent(model_client, today),
            build_database_agent(model_client, connection, user_id=3),
            build_public_data_agent(model_client, http_client),
            build_research_agent(model_client),
            build_budget_analyst_agent(
                model_client, UserDataSource(connection), user_id=3
            ),
            build_action_agent(model_client, connection, user_id=3),
            build_output_generator_agent(model_client),
        ]

        assert [agent.name for agent in agents] == [
            "orchestrator_agent",
            "input_interpreter_agent",
            "database_agent",
            "public_data_agent",
            "research_agent",
            "budget_analyst_agent",
            "action_agent",
            "output_generator_agent",
        ]
