import httpx

from app.core.tools import ToolRegistry
from app.data.nager_date_client import NagerDateClient
from app.data.open_meteo_client import OpenMeteoClient
from app.tools.public_holidays_tool import PublicHolidaysTool
from app.tools.weather_forecast_tool import WeatherForecastTool
from tests.helpers import mock_http_client


def _holiday(day: str, name: str) -> dict[str, object]:
    return {"date": day, "localName": name, "name": name, "global": True}


class TestPublicHolidaysTool:
    def test_only_holidays_inside_the_period_across_years(self) -> None:
        years_requested: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            year = request.url.path.split("/")[-2]
            years_requested.append(year)
            return httpx.Response(
                200,
                json=[
                    _holiday(f"{year}-01-01", "Ano Novo"),
                    _holiday(f"{year}-12-25", "Natal"),
                ],
            )

        registry = ToolRegistry(
            [PublicHolidaysTool(NagerDateClient(mock_http_client(handler)))]
        )

        execution = registry.execute(
            "list_public_holidays",
            {
                "start_date": "2026-12-20",
                "end_date": "2027-01-02",
                "country_code": "br",
            },
        )

        assert execution.output is not None
        assert [holiday["date"] for holiday in execution.output["holidays"]] == [
            "2026-12-25",
            "2027-01-01",
        ]
        assert years_requested == ["2026", "2027"]


class TestWeatherForecastTool:
    def test_refused_range_is_reported_instead_of_failing(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": True, "reason": "too far"})

        registry = ToolRegistry(
            [WeatherForecastTool(OpenMeteoClient(mock_http_client(handler)))]
        )

        execution = registry.execute(
            "get_weather_forecast",
            {
                "latitude": -23.2,
                "longitude": -44.7,
                "start_date": "2026-12-26",
                "end_date": "2026-12-27",
            },
        )

        assert execution.output == {
            "available": False,
            "unavailable_reason": "too far",
            "days": [],
        }

    def test_network_failure_becomes_a_tool_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("offline")

        registry = ToolRegistry(
            [WeatherForecastTool(OpenMeteoClient(mock_http_client(handler)))]
        )

        execution = registry.execute(
            "get_weather_forecast",
            {
                "latitude": -23.2,
                "longitude": -44.7,
                "start_date": "2026-09-26",
                "end_date": "2026-09-27",
            },
        )

        assert execution.error == "Tool failed: offline"
