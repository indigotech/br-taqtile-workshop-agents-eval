import httpx

from app.data.nominatim_client import NominatimClient
from tests.helpers import mock_http_client


class TestGeocode:
    def test_first_result_is_parsed_from_string_coordinates(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=[
                    {
                        "name": "Paraty",
                        "display_name": "Paraty, Rio de Janeiro, Brasil",
                        "lat": "-23.2196461",
                        "lon": "-44.7154196",
                        "importance": 0.5,
                    }
                ],
            )

        result = NominatimClient(mock_http_client(handler)).geocode("Paraty")

        assert result is not None
        assert result.model_dump() == {
            "name": "Paraty",
            "display_name": "Paraty, Rio de Janeiro, Brasil",
            "latitude": -23.2196461,
            "longitude": -44.7154196,
        }

    def test_no_results(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[])

        assert NominatimClient(mock_http_client(handler)).geocode("xyzzy") is None
