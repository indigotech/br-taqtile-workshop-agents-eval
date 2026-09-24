from datetime import date

import httpx
import pytest

from app.data.open_meteo_client import ForecastUnavailableError, OpenMeteoClient
from tests.helpers import mock_http_client

_FORECAST_BODY = {
    "daily": {
        "time": ["2026-09-26", "2026-09-27"],
        "weather_code": [1, 63],
        "temperature_2m_max": [24.0, 19.5],
        "temperature_2m_min": [14.0, 12.1],
        "precipitation_probability_max": [15, None],
    }
}


class TestDailyForecast:
    def test_parallel_daily_arrays_become_one_forecast_per_day(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json=_FORECAST_BODY)

        forecast = OpenMeteoClient(mock_http_client(handler)).daily_forecast(
            -22.7, -45.6, date(2026, 9, 26), date(2026, 9, 27)
        )

        assert [day.model_dump() for day in forecast] == [
            {
                "date": date(2026, 9, 26),
                "weather_code": 1,
                "weather_description": "predominantemente limpo",
                "temperature_max_celsius": 24.0,
                "temperature_min_celsius": 14.0,
                "precipitation_probability_percent": 15,
            },
            {
                "date": date(2026, 9, 27),
                "weather_code": 63,
                "weather_description": "chuva moderada",
                "temperature_max_celsius": 19.5,
                "temperature_min_celsius": 12.1,
                "precipitation_probability_percent": None,
            },
        ]
        assert dict(requests[0].url.params) == {
            "latitude": "-22.7",
            "longitude": "-45.6",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "start_date": "2026-09-26",
            "end_date": "2026-09-27",
        }

    def test_range_beyond_the_forecast_window_raises_with_the_api_reason(
        self,
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                400, json={"error": True, "reason": "out of allowed range"}
            )

        with pytest.raises(ForecastUnavailableError, match="out of allowed range"):
            OpenMeteoClient(mock_http_client(handler)).daily_forecast(
                -22.7, -45.6, date(2026, 12, 26), date(2026, 12, 27)
            )

    def test_server_error_propagates(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503)

        with pytest.raises(httpx.HTTPStatusError):
            OpenMeteoClient(mock_http_client(handler)).daily_forecast(
                -22.7, -45.6, date(2026, 9, 26), date(2026, 9, 27)
            )
