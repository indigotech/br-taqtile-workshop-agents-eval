from datetime import date

import httpx

from app.data.nager_date_client import NagerDateClient
from tests.helpers import mock_http_client


class TestPublicHolidays:
    def test_holidays_are_parsed_from_the_year_and_country_endpoint(self) -> None:
        requested_paths: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested_paths.append(request.url.path)
            return httpx.Response(
                200,
                json=[
                    {
                        "date": "2026-10-12",
                        "localName": "Nossa Senhora Aparecida",
                        "name": "Our Lady of Aparecida",
                        "countryCode": "BR",
                        "global": True,
                        "types": ["Public"],
                    }
                ],
            )

        holidays = NagerDateClient(mock_http_client(handler)).public_holidays(
            2026, "BR"
        )

        assert [holiday.model_dump() for holiday in holidays] == [
            {
                "date": date(2026, 10, 12),
                "local_name": "Nossa Senhora Aparecida",
                "name": "Our Lady of Aparecida",
                "nationwide": True,
            }
        ]
        assert requested_paths == ["/api/v3/PublicHolidays/2026/BR"]
