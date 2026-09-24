from pydantic import BaseModel, Field

from app.core.tools import Tool
from app.data.nominatim_client import GeocodingResult, NominatimClient


class GeocodePlaceInput(BaseModel):
    place: str = Field(
        description="Nome do lugar, de preferência com estado, ex.: 'Paraty, RJ'"
    )


class GeocodePlaceOutput(BaseModel):
    found: bool
    result: GeocodingResult | None


class GeocodePlaceTool(Tool[GeocodePlaceInput, GeocodePlaceOutput]):
    name = "geocode_place"
    description = "Converte o nome de um lugar em latitude e longitude (OpenStreetMap)."
    input_model = GeocodePlaceInput
    output_model = GeocodePlaceOutput

    def __init__(self, nominatim_client: NominatimClient) -> None:
        self.nominatim_client = nominatim_client

    def run(self, arguments: GeocodePlaceInput) -> GeocodePlaceOutput:
        result = self.nominatim_client.geocode(arguments.place)
        return GeocodePlaceOutput(found=result is not None, result=result)
