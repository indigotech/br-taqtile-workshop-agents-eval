from datetime import date
from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.core.tools import Tool
from app.data.accommodation_data_source import AccommodationDataSource
from app.data.models import ReservationDetails
from app.data.reservation_data_source import ReservationDataSource


class CreateReservationInput(BaseModel):
    user_id: int = Field(description="Id do usuário que está reservando")
    accommodation_id: int = Field(description="Id da hospedagem no catálogo")
    check_in: date = Field(description="Data de entrada (AAAA-MM-DD)")
    check_out: date = Field(description="Data de saída (AAAA-MM-DD)")
    guests: int = Field(ge=1, description="Número de hóspedes")

    @model_validator(mode="after")
    def _check_out_after_check_in(self) -> Self:
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be after check_in")
        return self


class CreateReservationOutput(BaseModel):
    created: bool
    failure_reason: str | None
    reservation: ReservationDetails | None


class CreateReservationTool(Tool[CreateReservationInput, CreateReservationOutput]):
    name = "create_reservation"
    description = (
        "Reserva uma hospedagem do catálogo (mock de airbnb/hotel) e grava no "
        "banco. O preço total é calculado como preço por noite vezes o número de "
        "noites. Esta ação é definitiva."
    )
    input_model = CreateReservationInput
    output_model = CreateReservationOutput

    def __init__(
        self,
        accommodation_data_source: AccommodationDataSource,
        reservation_data_source: ReservationDataSource,
    ) -> None:
        self.accommodation_data_source = accommodation_data_source
        self.reservation_data_source = reservation_data_source

    def run(self, arguments: CreateReservationInput) -> CreateReservationOutput:
        accommodation = self.accommodation_data_source.get_accommodation(
            arguments.accommodation_id
        )
        if accommodation is None:
            return _failure(f"Accommodation {arguments.accommodation_id} not found")
        if arguments.guests > accommodation.max_guests:
            return _failure(
                f"{accommodation.name} fits at most {accommodation.max_guests} guests"
            )
        nights = (arguments.check_out - arguments.check_in).days
        reservation = self.reservation_data_source.create(
            user_id=arguments.user_id,
            accommodation_id=accommodation.id,
            check_in=arguments.check_in,
            check_out=arguments.check_out,
            guests=arguments.guests,
            total_price=round(accommodation.nightly_price * nights, 2),
        )
        return CreateReservationOutput(
            created=True, failure_reason=None, reservation=reservation
        )


def _failure(reason: str) -> CreateReservationOutput:
    return CreateReservationOutput(
        created=False, failure_reason=reason, reservation=None
    )
