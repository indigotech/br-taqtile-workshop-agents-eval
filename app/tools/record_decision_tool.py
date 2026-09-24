from pydantic import BaseModel, Field

from app.core.tools import Tool
from app.data.decision_data_source import DecisionDataSource
from app.data.models import Decision


class RecordDecisionInput(BaseModel):
    user_id: int = Field(description="Id do usuário")
    summary: str = Field(
        description="Resumo do que foi decidido e por quê, em uma ou duas frases"
    )
    reservation_id: int | None = Field(
        default=None, description="Id da reserva criada, se houve reserva"
    )


class RecordDecisionOutput(BaseModel):
    decision: Decision


class RecordDecisionTool(Tool[RecordDecisionInput, RecordDecisionOutput]):
    name = "record_decision"
    description = "Registra no banco a decisão tomada para a viagem do usuário."
    input_model = RecordDecisionInput
    output_model = RecordDecisionOutput

    def __init__(self, decision_data_source: DecisionDataSource) -> None:
        self.decision_data_source = decision_data_source

    def run(self, arguments: RecordDecisionInput) -> RecordDecisionOutput:
        return RecordDecisionOutput(
            decision=self.decision_data_source.create(
                arguments.user_id, arguments.reservation_id, arguments.summary
            )
        )
