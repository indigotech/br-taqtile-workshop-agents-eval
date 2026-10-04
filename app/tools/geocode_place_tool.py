from pydantic import BaseModel, Field

from app.core.tools import Tool
from app.data.nominatim_client import GeocodingResult, NominatimClient


class GeocodePlaceInput(BaseModel):
    place: str = Field(
        description=(
            "Nome do lugar, de preferência com estado ou país, ex.: 'Paraty, RJ' "
            "ou 'Buenos Aires, Argentina'"
        )
    )


class GeocodePlaceOutput(BaseModel):
    found: bool
    result: GeocodingResult | None


class GeocodePlaceTool(Tool[GeocodePlaceInput, GeocodePlaceOutput]):
    name = "geocode_place"
    description = (
        "Converte o nome de um lugar em latitude, longitude e código do país "
        "(OpenStreetMap)."
    )
    input_model = GeocodePlaceInput
    output_model = GeocodePlaceOutput

    def __init__(self, nominatim_client: NominatimClient) -> None:
        self.nominatim_client = nominatim_client

    def run(self, arguments: GeocodePlaceInput) -> GeocodePlaceOutput:
        result = self.nominatim_client.geocode(arguments.place)
        return GeocodePlaceOutput(found=result is not None, result=result)
