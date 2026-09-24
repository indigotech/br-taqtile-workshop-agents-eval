import sqlite3

from app.data.accommodation_data_source import AccommodationDataSource


class TestSearch:
    def test_filters_by_capacity_and_orders_by_price(
        self, connection: sqlite3.Connection
    ) -> None:
        accommodations = AccommodationDataSource(connection).search(
            city_id=3, guests=2, max_nightly_price=None
        )

        assert [accommodation.id for accommodation in accommodations] == [3, 2, 1]

    def test_group_too_big_excludes_small_places(
        self, connection: sqlite3.Connection
    ) -> None:
        accommodations = AccommodationDataSource(connection).search(
            city_id=3, guests=3, max_nightly_price=None
        )

        assert [accommodation.id for accommodation in accommodations] == [2]

    def test_max_nightly_price_is_inclusive(
        self, connection: sqlite3.Connection
    ) -> None:
        accommodations = AccommodationDataSource(connection).search(
            city_id=3, guests=1, max_nightly_price=380.0
        )

        assert [accommodation.id for accommodation in accommodations] == [3, 2]


class TestGetAccommodation:
    def test_existing_accommodation(self, connection: sqlite3.Connection) -> None:
        accommodation = AccommodationDataSource(connection).get_accommodation(4)

        assert accommodation is not None
        assert accommodation.model_dump() == {
            "id": 4,
            "city_id": 4,
            "kind": "hotel",
            "name": "Pousada do Porto",
            "neighborhood": "Centro Histórico",
            "nightly_price": 450.0,
            "max_guests": 2,
            "rating": 4.7,
        }

    def test_missing_accommodation(self, connection: sqlite3.Connection) -> None:
        assert AccommodationDataSource(connection).get_accommodation(999) is None
