import sqlite3
from datetime import date

from app.data.reservation_data_source import ReservationDataSource


class TestListByUser:
    def test_reservations_with_place_details_newest_first(
        self, connection: sqlite3.Connection
    ) -> None:
        reservations = ReservationDataSource(connection).list_by_user(1)

        assert [reservation.model_dump() for reservation in reservations] == [
            {
                "id": 1,
                "accommodation_id": 2,
                "accommodation_name": "Chalé da Mantiqueira",
                "accommodation_kind": "airbnb",
                "city_name": "Campos do Jordão",
                "check_in": date(2026, 6, 12),
                "check_out": date(2026, 6, 14),
                "guests": 2,
                "total_price": 760.0,
                "status": "confirmed",
                "created_at": "2026-05-20 10:15:00",
            },
            {
                "id": 2,
                "accommodation_id": 7,
                "accommodation_name": "Loft Praia Grande",
                "accommodation_kind": "airbnb",
                "city_name": "Ubatuba",
                "check_in": date(2026, 3, 6),
                "check_out": date(2026, 3, 8),
                "guests": 1,
                "total_price": 380.0,
                "status": "cancelled",
                "created_at": "2026-02-11 18:40:00",
            },
        ]

    def test_user_without_reservations(self, connection: sqlite3.Connection) -> None:
        assert ReservationDataSource(connection).list_by_user(2) == []
