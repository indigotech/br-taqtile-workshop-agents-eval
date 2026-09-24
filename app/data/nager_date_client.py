from datetime import date

import httpx
from pydantic import BaseModel, Field

_PUBLIC_HOLIDAYS_URL = (
    "https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
)


class Holiday(BaseModel):
    date: date
    local_name: str = Field(validation_alias="localName")
    name: str
    nationwide: bool = Field(validation_alias="global")


class NagerDateClient:
    def __init__(self, http_client: httpx.Client) -> None:
        self.http_client = http_client

    def public_holidays(self, year: int, country_code: str) -> list[Holiday]:
        response = self.http_client.get(
            _PUBLIC_HOLIDAYS_URL.format(year=year, country_code=country_code)
        )
        response.raise_for_status()
        return [Holiday.model_validate(holiday) for holiday in response.json()]
