import sqlite3
import unicodedata

from app.data.models import City

_CITY_COLUMNS = "id, name, state, country, latitude, longitude"


class CityDataSource:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def find_by_name(self, name: str) -> City | None:
        # Compared in Python because SQLite's lower() only folds ASCII, so
        # "sao paulo" would never match "São Paulo" in SQL.
        wanted = _normalize(name)
        return next(
            (city for city in self.list_cities() if _normalize(city.name) == wanted),
            None,
        )

    def get_city(self, city_id: int) -> City | None:
        row = self.connection.execute(
            f"SELECT {_CITY_COLUMNS} FROM cities WHERE id = ?", (city_id,)
        ).fetchone()
        return City.model_validate(dict(row)) if row else None

    def list_cities(self) -> list[City]:
        rows = self.connection.execute(
            f"SELECT {_CITY_COLUMNS} FROM cities ORDER BY name"
        ).fetchall()
        return [City.model_validate(dict(row)) for row in rows]


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
