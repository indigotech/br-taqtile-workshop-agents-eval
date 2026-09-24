import sqlite3

from app.data.models import Accommodation

_ACCOMMODATION_COLUMNS = (
    "id, city_id, kind, name, neighborhood, nightly_price, max_guests, rating"
)


class AccommodationDataSource:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def search(
        self, city_id: int, guests: int, max_nightly_price: float | None
    ) -> list[Accommodation]:
        rows = self.connection.execute(
            f"SELECT {_ACCOMMODATION_COLUMNS} FROM accommodations"
            " WHERE city_id = ? AND max_guests >= ?"
            " AND (? IS NULL OR nightly_price <= ?)"
            " ORDER BY nightly_price",
            (city_id, guests, max_nightly_price, max_nightly_price),
        ).fetchall()
        return [Accommodation.model_validate(dict(row)) for row in rows]

    def get_accommodation(self, accommodation_id: int) -> Accommodation | None:
        row = self.connection.execute(
            f"SELECT {_ACCOMMODATION_COLUMNS} FROM accommodations WHERE id = ?",
            (accommodation_id,),
        ).fetchone()
        return Accommodation.model_validate(dict(row)) if row else None

    def list_accommodations(self) -> list[Accommodation]:
        rows = self.connection.execute(
            f"SELECT {_ACCOMMODATION_COLUMNS} FROM accommodations ORDER BY id"
        ).fetchall()
        return [Accommodation.model_validate(dict(row)) for row in rows]
