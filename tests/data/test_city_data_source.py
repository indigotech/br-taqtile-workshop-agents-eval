import sqlite3

from app.data.city_data_source import CityDataSource


class TestFindByName:
    def test_match_ignores_case_accents_and_surrounding_spaces(
        self, connection: sqlite3.Connection
    ) -> None:
        city = CityDataSource(connection).find_by_name("  campos do jordao ")

        assert city is not None
        assert city.model_dump() == {
            "id": 3,
            "name": "Campos do Jordão",
            "state": "SP",
            "country": "Brasil",
            "latitude": -22.7394,
            "longitude": -45.5914,
        }

    def test_city_outside_the_catalog(self, connection: sqlite3.Connection) -> None:
        assert CityDataSource(connection).find_by_name("Gramado") is None


class TestListCities:
    def test_cities_in_alphabetical_order(self, connection: sqlite3.Connection) -> None:
        names = [city.name for city in CityDataSource(connection).list_cities()]

        assert names == sorted(names)
        assert len(names) == 8
