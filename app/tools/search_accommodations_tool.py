from pydantic import BaseModel, Field

from app.core.tools import Tool
from app.data.accommodation_data_source import AccommodationDataSource
from app.data.city_data_source import CityDataSource
from app.data.models import Accommodation, City


class SearchAccommodationsInput(BaseModel):
    city_name: str = Field(description="Nome da cidade de destino, ex.: 'Paraty'")
    guests: int = Field(ge=1, description="Número de pessoas que vão se hospedar")
    max_nightly_price: float | None = Field(
        default=None, description="Preço máximo por noite em reais, se houver"
    )


class SearchAccommodationsOutput(BaseModel):
    city_found: bool
    city: City | None
    accommodations: list[Accommodation]
    available_cities: list[str]


class SearchAccommodationsTool(
    Tool[SearchAccommodationsInput, SearchAccommodationsOutput]
):
    name = "search_accommodations"
    description = (
        "Busca airbnbs e hotéis do catálogo numa cidade, que comportem o número "
        "de pessoas e caibam no preço por noite, do mais barato ao mais caro. "
        "Se a cidade não estiver no catálogo, devolve as cidades disponíveis."
    )
    input_model = SearchAccommodationsInput
    output_model = SearchAccommodationsOutput

    def __init__(
        self,
        city_data_source: CityDataSource,
        accommodation_data_source: AccommodationDataSource,
    ) -> None:
        self.city_data_source = city_data_source
        self.accommodation_data_source = accommodation_data_source

    def run(self, arguments: SearchAccommodationsInput) -> SearchAccommodationsOutput:
        city = self.city_data_source.find_by_name(arguments.city_name)
        if city is None:
            return SearchAccommodationsOutput(
                city_found=False,
                city=None,
                accommodations=[],
                available_cities=[
                    available.name for available in self.city_data_source.list_cities()
                ],
            )
        return SearchAccommodationsOutput(
            city_found=True,
            city=city,
            accommodations=self.accommodation_data_source.search(
                city.id, arguments.guests, arguments.max_nightly_price
            ),
            available_cities=[],
        )
