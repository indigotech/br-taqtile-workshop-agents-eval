from datetime import date
from typing import Literal

from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    email: str
    home_city_id: int


class Budget(BaseModel):
    user_id: int
    total_amount: float
    lodging_amount: float
    food_amount: float
    activities_amount: float
    currency: str


class Preference(BaseModel):
    category: Literal["food", "activity", "lodging", "restriction"]
    value: str


class City(BaseModel):
    id: int
    name: str
    state: str
    country: str
    latitude: float
    longitude: float


class Accommodation(BaseModel):
    id: int
    city_id: int
    kind: Literal["airbnb", "hotel"]
    name: str
    neighborhood: str
    nightly_price: float
    max_guests: int
    rating: float


class ReservationDetails(BaseModel):
    id: int
    accommodation_id: int
    accommodation_name: str
    accommodation_kind: Literal["airbnb", "hotel"]
    city_name: str
    check_in: date
    check_out: date
    guests: int
    total_price: float
    status: Literal["confirmed", "cancelled"]
    created_at: str
