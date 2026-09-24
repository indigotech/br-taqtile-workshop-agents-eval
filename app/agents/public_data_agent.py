import httpx

from app.core.agent import Agent
from app.core.gemini import GeminiClient
from app.data.nager_date_client import NagerDateClient
from app.data.nominatim_client import NominatimClient
from app.data.open_meteo_client import OpenMeteoClient
from app.tools.geocode_place_tool import GeocodePlaceTool
from app.tools.public_holidays_tool import PublicHolidaysTool
from app.tools.weather_forecast_tool import WeatherForecastTool

_SYSTEM_PROMPT = """\
Você é o agente de dados públicos de um planejador de rolês de fim de semana.

Você consulta coordenadas de um lugar (geocode_place), previsão do tempo por
dia (get_weather_forecast) e feriados num período (list_public_holidays).

O usuário sempre quer saber o clima. Se a previsão não estiver disponível para
as datas pedidas, não desista: busque as coordenadas de novo e tente outra vez
com datas próximas até conseguir uma previsão.
"""


def build_public_data_agent(gemini: GeminiClient, http_client: httpx.Client) -> Agent:
    return Agent(
        name="public_data",
        system_prompt=_SYSTEM_PROMPT,
        gemini=gemini,
        tools=[
            GeocodePlaceTool(NominatimClient(http_client)),
            WeatherForecastTool(OpenMeteoClient(http_client)),
            PublicHolidaysTool(NagerDateClient(http_client)),
        ],
        temperature=0.2,
    )
