import httpx
from pydantic import BaseModel, Field

_SEARCH_URL = "https://nominatim.openstreetmap.org/search"


class GeocodingResult(BaseModel):
    name: str
    display_name: str
    latitude: float = Field(validation_alias="lat")
    longitude: float = Field(validation_alias="lon")


class NominatimClient:
    """Nominatim's usage policy requires an identifying User-Agent and at most
    one request per second — the http client passed in must carry that header."""

    def __init__(self, http_client: httpx.Client) -> None:
        self.http_client = http_client

    def geocode(self, query: str) -> GeocodingResult | None:
        response = self.http_client.get(
            _SEARCH_URL,
            params={
                "q": query,
                "format": "jsonv2",
                "limit": 1,
                "accept-language": "pt-BR",
            },
        )
        response.raise_for_status()
        results = response.json()
        return GeocodingResult.model_validate(results[0]) if results else None
