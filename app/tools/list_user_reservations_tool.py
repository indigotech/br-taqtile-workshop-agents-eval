from pydantic import BaseModel, Field

from app.core.tools import Tool
from app.data.models import ReservationDetails
from app.data.reservation_data_source import ReservationDataSource


class ListUserReservationsInput(BaseModel):
    user_id: int = Field(description="Id do usuário no banco")


class ListUserReservationsOutput(BaseModel):
    reservations: list[ReservationDetails]


class ListUserReservationsTool(
    Tool[ListUserReservationsInput, ListUserReservationsOutput]
):
    name = "list_user_reservations"
    description = (
        "Lista o histórico de reservas de hospedagem do usuário, da mais recente "
        "para a mais antiga, incluindo as canceladas."
    )
    input_model = ListUserReservationsInput
    output_model = ListUserReservationsOutput

    def __init__(self, reservation_data_source: ReservationDataSource) -> None:
        self.reservation_data_source = reservation_data_source

    def run(self, arguments: ListUserReservationsInput) -> ListUserReservationsOutput:
        return ListUserReservationsOutput(
            reservations=self.reservation_data_source.list_by_user(arguments.user_id)
        )
