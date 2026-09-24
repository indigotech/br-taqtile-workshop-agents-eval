from datetime import date

from pydantic import BaseModel, Field

from app.core.tools import Tool
from app.data.nager_date_client import Holiday, NagerDateClient


class PublicHolidaysInput(BaseModel):
    start_date: date = Field(description="Início do período (AAAA-MM-DD)")
    end_date: date = Field(description="Fim do período (AAAA-MM-DD)")
    country_code: str = Field(
        default="BR", description="Código ISO do país com duas letras"
    )


class PublicHolidaysOutput(BaseModel):
    holidays: list[Holiday]


class PublicHolidaysTool(Tool[PublicHolidaysInput, PublicHolidaysOutput]):
    name = "list_public_holidays"
    description = (
        "Lista os feriados do país (Nager.Date) dentro de um período, útil pra "
        "saber se o fim de semana é prolongado."
    )
    input_model = PublicHolidaysInput
    output_model = PublicHolidaysOutput

    def __init__(self, nager_date_client: NagerDateClient) -> None:
        self.nager_date_client = nager_date_client

    def run(self, arguments: PublicHolidaysInput) -> PublicHolidaysOutput:
        holidays = [
            holiday
            for year in range(arguments.start_date.year, arguments.end_date.year + 1)
            for holiday in self.nager_date_client.public_holidays(
                year, arguments.country_code.upper()
            )
            if arguments.start_date <= holiday.date <= arguments.end_date
        ]
        return PublicHolidaysOutput(holidays=holidays)
