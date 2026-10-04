import sqlite3

from app.data.models import City
from app.data.name_matching import normalize_name

_CITY_COLUMNS = "id, name, state, country, latitude, longitude"


class CityDataSource:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def find_by_name(self, name: str) -> City | None:
        wanted = normalize_name(name)
        return next(
            (
                city
                for city in self.list_cities()
                if normalize_name(city.name) == wanted
            ),
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

    def create_city(
        self, name: str, state: str, country: str, latitude: float, longitude: float
    ) -> City:
        cursor = self.connection.execute(
            "INSERT INTO cities (name, state, country, latitude, longitude)"
            " VALUES (?, ?, ?, ?, ?)",
            (name, state, country, latitude, longitude),
        )
        self.connection.commit()
        row = self.connection.execute(
            f"SELECT {_CITY_COLUMNS} FROM cities WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return City.model_validate(dict(row))
