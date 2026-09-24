from datetime import date

from pydantic import BaseModel, Field

from app.core.tools import Tool
from app.data.open_meteo_client import (
    DailyForecast,
    ForecastUnavailableError,
    OpenMeteoClient,
)


class WeatherForecastInput(BaseModel):
    latitude: float = Field(description="Latitude do lugar")
    longitude: float = Field(description="Longitude do lugar")
    start_date: date = Field(description="Primeiro dia da previsão (AAAA-MM-DD)")
    end_date: date = Field(description="Último dia da previsão (AAAA-MM-DD)")


class WeatherForecastOutput(BaseModel):
    available: bool
    unavailable_reason: str | None
    days: list[DailyForecast]


class WeatherForecastTool(Tool[WeatherForecastInput, WeatherForecastOutput]):
    name = "get_weather_forecast"
    description = (
        "Previsão do tempo diária (Open-Meteo): condição, temperaturas máxima e "
        "mínima e chance de chuva. Só cobre cerca de 16 dias a partir de hoje; "
        "fora disso devolve available=false com o motivo."
    )
    input_model = WeatherForecastInput
    output_model = WeatherForecastOutput

    def __init__(self, open_meteo_client: OpenMeteoClient) -> None:
        self.open_meteo_client = open_meteo_client

    def run(self, arguments: WeatherForecastInput) -> WeatherForecastOutput:
        try:
            days = self.open_meteo_client.daily_forecast(
                arguments.latitude,
                arguments.longitude,
                arguments.start_date,
                arguments.end_date,
            )
        except ForecastUnavailableError as error:
            return WeatherForecastOutput(
                available=False, unavailable_reason=str(error), days=[]
            )
        return WeatherForecastOutput(available=True, unavailable_reason=None, days=days)
