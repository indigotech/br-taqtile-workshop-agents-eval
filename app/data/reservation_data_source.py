import sqlite3
from datetime import date

from app.data.models import ReservationDetails

_RESERVATION_DETAILS_QUERY = """
    SELECT
        reservations.id,
        reservations.accommodation_id,
        accommodations.name AS accommodation_name,
        accommodations.kind AS accommodation_kind,
        cities.name AS city_name,
        reservations.check_in,
        reservations.check_out,
        reservations.guests,
        reservations.total_price,
        reservations.status,
        reservations.created_at
    FROM reservations
    JOIN accommodations ON accommodations.id = reservations.accommodation_id
    JOIN cities ON cities.id = accommodations.city_id
"""


class ReservationDataSource:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list_by_user(self, user_id: int) -> list[ReservationDetails]:
        rows = self.connection.execute(
            _RESERVATION_DETAILS_QUERY
            + " WHERE reservations.user_id = ? ORDER BY reservations.check_in DESC",
            (user_id,),
        ).fetchall()
        return [ReservationDetails.model_validate(dict(row)) for row in rows]

    def create(
        self,
        user_id: int,
        accommodation_id: int,
        check_in: date,
        check_out: date,
        guests: int,
        total_price: float,
    ) -> ReservationDetails:
        cursor = self.connection.execute(
            "INSERT INTO reservations"
            " (user_id, accommodation_id, check_in, check_out, guests, total_price, status)"
            " VALUES (?, ?, ?, ?, ?, ?, 'confirmed')",
            (
                user_id,
                accommodation_id,
                check_in.isoformat(),
                check_out.isoformat(),
                guests,
                total_price,
            ),
        )
        self.connection.commit()
        row = self.connection.execute(
            _RESERVATION_DETAILS_QUERY + " WHERE reservations.id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return ReservationDetails.model_validate(dict(row))
