import httpx

from app.data.nominatim_client import NominatimClient
from tests.helpers import mock_http_client


class TestGeocode:
    def test_first_result_is_parsed_with_its_country_code(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=[
                    {
                        "name": "Buenos Aires",
                        "display_name": "Buenos Aires, Argentina",
                        "lat": "-34.6083696",
                        "lon": "-58.4440583",
                        "importance": 0.8,
                        "address": {"city": "Buenos Aires", "country_code": "ar"},
                    }
                ],
            )

        result = NominatimClient(mock_http_client(handler)).geocode("Buenos Aires")

        assert result is not None
        assert result.model_dump() == {
            "name": "Buenos Aires",
            "display_name": "Buenos Aires, Argentina",
            "latitude": -34.6083696,
            "longitude": -58.4440583,
            "country_code": "ar",
        }

    def test_search_asks_for_the_address_without_restricting_the_country(
        self,
    ) -> None:
        requested_parameters: list[dict[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requested_parameters.append(dict(request.url.params))
            return httpx.Response(200, json=[])

        NominatimClient(mock_http_client(handler)).geocode("Lisboa")

        assert requested_parameters == [
            {
                "q": "Lisboa",
                "format": "jsonv2",
                "limit": "1",
                "addressdetails": "1",
                "accept-language": "pt-BR",
            }
        ]

    def test_no_results(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[])

        assert NominatimClient(mock_http_client(handler)).geocode("xyzzy") is None
