import logging
from datetime import date

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_DAILY_VARIABLES = (
    "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
)

# WMO weather interpretation codes, as documented by Open-Meteo.
_WEATHER_DESCRIPTIONS = {
    0: "céu limpo",
    1: "predominantemente limpo",
    2: "parcialmente nublado",
    3: "nublado",
    45: "neblina",
    48: "neblina com geada",
    51: "garoa fraca",
    53: "garoa moderada",
    55: "garoa forte",
    61: "chuva fraca",
    63: "chuva moderada",
    65: "chuva forte",
    80: "pancadas de chuva fracas",
    81: "pancadas de chuva moderadas",
    82: "pancadas de chuva fortes",
    95: "trovoada",
    96: "trovoada com granizo fraco",
    99: "trovoada com granizo forte",
}


class DailyForecast(BaseModel):
    date: date
    weather_code: int
    weather_description: str
    temperature_max_celsius: float
    temperature_min_celsius: float
    precipitation_probability_percent: int | None


class ForecastUnavailableError(Exception):
    pass


class OpenMeteoClient:
    def __init__(self, http_client: httpx.Client) -> None:
        self.http_client = http_client

    def daily_forecast(
        self, latitude: float, longitude: float, start_date: date, end_date: date
    ) -> list[DailyForecast]:
        """Raises ForecastUnavailableError when Open-Meteo refuses the range —
        it only forecasts about 16 days ahead."""
        response = self.http_client.get(
            _FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": _DAILY_VARIABLES,
                "timezone": "auto",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
        if response.status_code == httpx.codes.BAD_REQUEST:
            reason = _OpenMeteoError.model_validate(response.json()).reason
            logger.info("Open-Meteo refused the forecast: %s", reason)
            raise ForecastUnavailableError(reason)
        response.raise_for_status()
        daily = _OpenMeteoResponse.model_validate(response.json()).daily
        return [
            DailyForecast(
                date=day,
                weather_code=code,
                weather_description=_WEATHER_DESCRIPTIONS.get(code, "desconhecido"),
                temperature_max_celsius=maximum,
                temperature_min_celsius=minimum,
                precipitation_probability_percent=precipitation,
            )
            for day, code, maximum, minimum, precipitation in zip(
                daily.time,
                daily.weather_code,
                daily.temperature_2m_max,
                daily.temperature_2m_min,
                daily.precipitation_probability_max,
                strict=True,
            )
        ]


class _OpenMeteoDaily(BaseModel):
    time: list[date]
    weather_code: list[int]
    temperature_2m_max: list[float]
    temperature_2m_min: list[float]
    precipitation_probability_max: list[int | None]


class _OpenMeteoResponse(BaseModel):
    daily: _OpenMeteoDaily


class _OpenMeteoError(BaseModel):
    reason: str
