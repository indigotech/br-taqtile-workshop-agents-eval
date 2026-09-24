from pydantic import BaseModel, Field

from app.core.agent import Agent, user_message
from app.core.tool_loop import WebSource
from app.core.tools import Tool


class AgentToolInput(BaseModel):
    instructions: str = Field(
        description=(
            "Tudo o que o agente precisa para executar a tarefa: o pedido do "
            "usuário, os dados já levantados por outros agentes e o que se "
            "espera da resposta. O agente não vê o resto da conversa."
        )
    )


class AgentToolOutput(BaseModel):
    response: str
    sources: list[WebSource]


class AgentTool(Tool[AgentToolInput, AgentToolOutput]):
    """Exposes an agent as a tool, so an orchestrator agent delegates to it with
    an ordinary function call. Each call starts a fresh conversation — the
    orchestrator passes along any context in `instructions` — which keeps the
    sub-agent's span in Langfuse self-contained."""

    input_model = AgentToolInput
    output_model = AgentToolOutput

    def __init__(self, agent: Agent, name: str, description: str) -> None:
        self.agent = agent
        self.name = name
        self.description = description

    def run(self, arguments: AgentToolInput) -> AgentToolOutput:
        result = self.agent.run([user_message(arguments.instructions)])
        return AgentToolOutput(response=result.text, sources=result.sources)
