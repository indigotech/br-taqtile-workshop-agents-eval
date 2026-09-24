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
