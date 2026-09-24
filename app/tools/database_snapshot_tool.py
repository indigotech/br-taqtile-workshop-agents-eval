from pydantic import BaseModel

from app.core.tools import Tool
from app.data.accommodation_data_source import AccommodationDataSource
from app.data.city_data_source import CityDataSource
from app.data.models import (
    Accommodation,
    Budget,
    City,
    Preference,
    ReservationDetails,
    User,
)
from app.data.reservation_data_source import ReservationDataSource
from app.data.user_data_source import UserDataSource


class DatabaseSnapshotInput(BaseModel):
    pass


class UserSnapshot(BaseModel):
    user: User
    budget: Budget | None
    preferences: list[Preference]
    reservations: list[ReservationDetails]


class DatabaseSnapshotOutput(BaseModel):
    users: list[UserSnapshot]
    cities: list[City]
    accommodations: list[Accommodation]


class DatabaseSnapshotTool(Tool[DatabaseSnapshotInput, DatabaseSnapshotOutput]):
    name = "get_database_snapshot"
    description = (
        "Traz de uma vez todos os dados do banco: usuários com orçamentos, "
        "preferências e reservas, cidades e todo o catálogo de hospedagens."
    )
    input_model = DatabaseSnapshotInput
    output_model = DatabaseSnapshotOutput

    def __init__(
        self,
        user_data_source: UserDataSource,
        reservation_data_source: ReservationDataSource,
        city_data_source: CityDataSource,
        accommodation_data_source: AccommodationDataSource,
    ) -> None:
        self.user_data_source = user_data_source
        self.reservation_data_source = reservation_data_source
        self.city_data_source = city_data_source
        self.accommodation_data_source = accommodation_data_source

    def run(self, arguments: DatabaseSnapshotInput) -> DatabaseSnapshotOutput:
        return DatabaseSnapshotOutput(
            users=[
                UserSnapshot(
                    user=user,
                    budget=self.user_data_source.get_budget(user.id),
                    preferences=self.user_data_source.list_preferences(user.id),
                    reservations=self.reservation_data_source.list_by_user(user.id),
                )
                for user in self.user_data_source.list_users()
            ],
            cities=self.city_data_source.list_cities(),
            accommodations=self.accommodation_data_source.list_accommodations(),
        )
